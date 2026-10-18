"""Feature lineage must preserve old snapshots and never infer ambiguous ancestry."""

import json
import sqlite3
from uuid import uuid4

import pytest
from specbridge.feature_history import FeatureHistory
from specbridge.models import Artifact, Run
from specbridge.storage import NotFound, Store


def legacy_workspace(tmp_path, artifact_dict):
    store = Store(tmp_path / "legacy.db")
    project = store.create_project("History")
    other = store.create_project("Other")
    run = Run(
        id=str(uuid4()),
        project_id=project.id,
        source_ids=[],
        skill_id="feature-handoff",
        intent="Handoff",
        destination="fixture",
        stage="human_review",
    )
    with store.transaction() as db:
        db.execute(
            "INSERT INTO runs(id,project_id,data) VALUES (?,?,?)",
            (run.id, project.id, run.model_dump_json()),
        )
    first = store.save_revision(
        project.id,
        Artifact.model_validate(artifact_dict),
        None,
        provenance={"run_id": run.id},
    )
    run.revision_id = first.id
    with store.transaction() as db:
        db.execute("UPDATE runs SET data=? WHERE id=?", (run.model_dump_json(), run.id))
        db.execute(
            "INSERT INTO checkpoints VALUES (?,?,?)",
            (run.id, "validate", json.dumps({"revision_id": first.id})),
        )
        db.execute("DROP TABLE feature_heads")
        db.execute("DROP TABLE revision_lineage")
        db.execute("PRAGMA user_version=2")
    return store, project, other, run, first


def test_v2_migration_preserves_bytes_and_proves_root(tmp_path, artifact_dict):
    old, project, other, run, revision = legacy_workspace(tmp_path, artifact_dict)
    with sqlite3.connect(old.path) as db:
        before = db.execute("SELECT data,digest FROM revisions").fetchall()
    migrated = Store(old.path)
    history = FeatureHistory(migrated)
    assert history.head(project.id, run.id) == revision
    entries = history.list(project.id, run.id)
    assert len(entries) == 1
    assert entries[0].feature_number == 1
    assert entries[0].parent_revision_id is None
    with sqlite3.connect(old.path) as db:
        assert db.execute("SELECT data,digest FROM revisions").fetchall() == before
        assert db.execute("PRAGMA user_version").fetchone()[0] == 3
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert FeatureHistory(Store(old.path)).list(project.id, run.id) == entries
    with pytest.raises(NotFound):
        history.head(other.id, run.id)


def test_unassociated_and_conflicting_evidence_stay_legacy(tmp_path, artifact_dict):
    old, project, other, run, revision = legacy_workspace(tmp_path, artifact_dict)
    bad = Run(
        id=str(uuid4()),
        project_id=other.id,
        source_ids=[],
        skill_id="feature-handoff",
        intent="Other",
        destination="fixture",
        stage="validate",
    )
    with sqlite3.connect(old.path) as db:
        db.execute(
            "INSERT INTO runs(id,project_id,data) VALUES (?,?,?)",
            (bad.id, other.id, bad.model_dump_json()),
        )
        db.execute(
            "INSERT INTO checkpoints VALUES (?,?,?)",
            (bad.id, "validate", json.dumps({"revision_id": revision.id})),
        )
    migrated = Store(old.path)
    assert FeatureHistory(migrated).head(project.id, run.id) is None
    assert FeatureHistory(migrated).list(project.id, run.id) == []
    assert migrated.get_revision(project.id, revision.id) == revision


def test_migration_rolls_back_on_failure(tmp_path, artifact_dict, monkeypatch):
    old, _, _, _, _ = legacy_workspace(tmp_path, artifact_dict)
    from specbridge.migrations import migrate_lineage

    def interrupted(db):
        migrate_lineage(db)
        raise sqlite3.IntegrityError("migration failed")

    monkeypatch.setattr("specbridge.storage.migrate_lineage", interrupted)
    with pytest.raises(sqlite3.IntegrityError):
        Store(old.path)
    with sqlite3.connect(old.path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert not db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='revision_lineage'"
        ).fetchone()


def test_incomplete_schema_is_not_silently_repaired(tmp_path):
    store = Store(tmp_path / "partial.db")
    with sqlite3.connect(store.path) as db:
        db.execute("DROP TABLE feature_heads")
    with pytest.raises(ValueError, match="Incomplete"):
        Store(store.path)


def api_workspace(tmp_path):
    from fastapi.testclient import TestClient
    from specbridge.main import create_app

    app = create_app(
        data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
    )
    client = TestClient(
        app, base_url="http://127.0.0.1:8000", headers={"Authorization": "Bearer test"}
    )
    project = client.post("/api/projects", json={"name": "Two features"}).json()["id"]
    return app, client, f"/api/projects/{project}"


def create_run(client, base, text):
    source = client.post(base + "/sources", json={"text": text}).json()["id"]
    run = client.post(
        base + "/runs",
        json={
            "source_ids": [source],
            "skill_id": "feature-handoff",
            "intent": text,
            "acknowledged_destination": "fixture",
        },
    ).json()
    for _ in range(6):
        response = client.post(base + f"/runs/{run['id']}/advance", json={})
        assert response.status_code == 200, response.text
        run = response.json()
    return run, client.get(base + f"/revisions/{run['revision_id']}").json()


def test_two_features_edit_and_publish_independently(tmp_path):
    _, client, base = api_workspace(tmp_path)
    a, ar = create_run(client, base, "Export reports")
    b, br = create_run(client, base, "View care plans")

    def edit(revision, title):
        body = json.loads(json.dumps(revision["artifact"]))
        body["title"] = title
        return client.post(
            base + f"/revisions/{revision['id']}/edits",
            json={"expected_digest": revision["digest"], "artifact": body},
        )

    edited_a = edit(ar, "Export updated")
    assert edited_a.status_code == 201
    edited_b = edit(br, "Care plans updated")
    assert edited_b.status_code == 201
    assert edit(ar, "Stale export").status_code == 409
    for revision in (edited_a.json(), edited_b.json()):
        url = base + f"/revisions/{revision['id']}"
        assert (
            client.post(
                url + "/reviews",
                json={"disposition": "reviewed", "notes": "Fixture only"},
            ).status_code
            == 201
        )
        result = client.post(url + "/candidates")
        assert result.status_code == 201, result.text
        candidate = result.json()
        cu = base + f"/candidates/{candidate['id']}"
        assert (
            client.post(
                cu + "/approve", json={"digest": candidate["digest"]}
            ).status_code
            == 200
        )
        assert client.get(cu + "/download").status_code == 200
    hist = client.get(base + f"/runs/{a['id']}/history").json()
    assert [r["feature_number"] for r in hist] == [2, 1]
    assert hist[0]["parent_revision_id"] == ar["id"]
    assert (
        client.get(
            base + f"/runs/{a['id']}/compare",
            params={"base": ar["id"], "head": edited_a.json()["id"]},
        ).status_code
        == 200
    )
    assert (
        client.get(
            base + f"/runs/{a['id']}/compare",
            params={"base": ar["id"], "head": br["id"]},
        ).status_code
        == 404
    )
    assert client.get(base + f"/runs/{b['id']}/history?limit=51").status_code == 422


def test_new_run_root_does_not_depend_on_project_latest(tmp_path):
    app, client, base = api_workspace(tmp_path)
    _a, _ar = create_run(client, base, "First feature")
    b, _br = create_run(client, base, "Second feature")
    with app.state.store.transaction() as db:
        run = json.loads(
            db.execute("SELECT data FROM runs WHERE id=?", (b["id"],)).fetchone()[0]
        )
        assert run["base_digest"] is None
    assert (
        client.get(base + f"/runs/{b['id']}/history").json()[0]["parent_revision_id"]
        is None
    )


def test_unassociated_revision_cannot_be_edited_or_exported(tmp_path, artifact_dict):
    app, client, base = api_workspace(tmp_path)
    project_id = base.rsplit("/", 1)[-1]
    r = app.state.store.save_revision(
        project_id, Artifact.model_validate(artifact_dict), None
    )
    assert client.get(base + f"/revisions/{r.id}").status_code == 200
    assert client.post(base + f"/revisions/{r.id}/candidates").status_code == 409
    assert (
        client.post(
            base + f"/revisions/{r.id}/edits",
            json={"expected_digest": r.digest, "artifact": r.artifact.model_dump()},
        ).status_code
        == 409
    )


def test_preupgrade_inflight_run_does_not_keep_project_global_base(tmp_path):
    app, client, base = api_workspace(tmp_path)
    _, first = create_run(client, base, "Older feature")
    source = client.post(base + "/sources", json={"text": "New feature"}).json()["id"]
    run = client.post(
        base + "/runs",
        json={
            "source_ids": [source],
            "skill_id": "feature-handoff",
            "intent": "New",
            "acknowledged_destination": "fixture",
        },
    ).json()
    for _ in range(5):
        run = client.post(base + f"/runs/{run['id']}/advance", json={}).json()
    assert run["stage"] == "validate"
    with app.state.store.transaction() as db:
        run["base_digest"] = first["digest"]
        db.execute("UPDATE runs SET data=? WHERE id=?", (json.dumps(run), run["id"]))
    response = client.post(base + f"/runs/{run['id']}/advance", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "review"


def test_head_membership_without_root_evidence_has_unknown_number(
    tmp_path, artifact_dict
):
    old, project, _, run, revision = legacy_workspace(tmp_path, artifact_dict)
    with sqlite3.connect(old.path) as db:
        db.execute("DELETE FROM checkpoints")
    entry = FeatureHistory(Store(old.path)).list(project.id, run.id)[0]
    assert entry.revision_id == revision.id
    assert entry.feature_number is None
