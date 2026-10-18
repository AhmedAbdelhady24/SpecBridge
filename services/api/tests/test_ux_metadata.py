"""Readable run metadata and project-scoped evidence picker contracts."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from specbridge.main import create_app
from specbridge.models import Run


@pytest.fixture
def workspace(tmp_path):
    app = create_app(
        data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
    )
    client = TestClient(
        app, base_url="http://127.0.0.1:8000", headers={"Authorization": "Bearer test"}
    )
    project = client.post("/api/projects", json={"name": "UX"}).json()["id"]
    return client, app.state.store, project, f"/api/projects/{project}"


def test_run_metadata_uses_linked_revision_and_original_utc_creation(workspace):
    c, store, project, base = workspace
    destination = c.get("/api/config").json()["destination"]
    source = c.post(base + "/sources", json={"text": "CSV export"}).json()["id"]
    run = c.post(
        base + "/runs",
        json={
            "source_ids": [source],
            "skill_id": "feature-handoff",
            "intent": "Readable fallback intent",
            "acknowledged_destination": destination,
        },
    ).json()
    with store.transaction() as db:
        db.execute(
            "UPDATE audit SET at='2026-10-18 12:34:56' WHERE subject=?", (run["id"],)
        )
        db.execute(
            "INSERT INTO audit(project_id,action,subject,at) VALUES (?,?,?,?)",
            (project, "workflow_created", run["id"], "2026-10-19 01:00:00"),
        )
    summary = c.get(base + "/runs").json()[0]
    assert summary["title"] == "Readable fallback intent"
    assert summary["revision_number"] is None
    assert summary["created_at"] == "2026-10-18T12:34:56Z"
    assert datetime.fromisoformat(summary["created_at"]).tzinfo == UTC
    for _ in range(6):
        run = c.post(base + "/runs/" + run["id"] + "/advance", json={}).json()
    revision = c.get(base + "/revisions/" + run["revision_id"]).json()
    artifact = revision["artifact"]
    artifact["title"] = "Clinician-reviewed CSV scope"
    result = c.post(
        base + "/revisions/" + revision["id"] + "/edits",
        json={"expected_digest": revision["digest"], "artifact": artifact},
    )
    assert result.status_code == 201
    summary = c.get(base + "/runs").json()[0]
    assert summary["title"] == "Clinician-reviewed CSV scope"
    assert summary["revision_number"] == 2
    assert summary["created_at"] == "2026-10-18T12:34:56Z"


def test_missing_run_metadata_does_not_invent_values_or_change_expired_lease(workspace):
    c, store, project, base = workspace
    run = Run(
        id="historic",
        project_id=project,
        source_ids=[],
        skill_id="feature-handoff",
        intent="Historical intent",
        destination="fixture",
        stage="execute",
        status="running",
        revision_id="missing",
    )
    with store.transaction() as db:
        db.execute(
            "INSERT INTO runs(id,project_id,data,lease_until) VALUES (?,?,?,?)",
            (run.id, project, run.model_dump_json(), 0),
        )
    summary = c.get(base + "/runs").json()[0]
    assert summary["title"] == "Historical intent"
    assert summary["revision_number"] is None
    assert summary["created_at"] is None
    assert summary["status"] == "failed"
    assert summary["error"] == "interrupted_retry_may_repeat_billing"
    with store.transaction() as db:
        assert (
            Run.model_validate_json(
                db.execute("SELECT data FROM runs WHERE id='historic'").fetchone()[0]
            ).status
            == "running"
        )


def test_source_picker_pages_original_evidence_without_full_content(workspace):
    c, store, project, base = workspace
    originals = [
        store.add_source(project, f"Source {i}: " + "x" * 400) for i in range(23)
    ]
    snapshot = originals[0].model_copy(
        update={"id": "snapshot", "knowledge_ref": "entry:1"}
    )
    other = store.create_project("Other")
    other_source = store.add_source(other.id, "Other private evidence")
    with store.transaction() as db:
        db.execute(
            "INSERT INTO sources VALUES (?,?,?)",
            (snapshot.id, project, snapshot.model_dump_json()),
        )
    first = c.get(base + "/sources").json()
    assert [s["id"] for s in first] == [s.id for s in originals[:20]]
    assert all(len(s["preview"]) == 320 and "text" not in s for s in first)
    second = c.get(base + "/sources", params={"after": first[-1]["id"]}).json()
    assert [s["id"] for s in second] == [s.id for s in originals[20:]]
    assert (
        c.get(base + "/sources", params={"after": other_source.id}).status_code == 404
    )
    assert c.get(base + "/sources", params={"after": snapshot.id}).status_code == 404
    assert c.get("/api/projects/absent/sources").status_code == 404
    assert c.get(f"/api/projects/{other.id}/sources").json()[0]["id"] == other_source.id


@pytest.mark.parametrize("query", ["%", "_", "'", "CSV"])
def test_source_search_is_literal_and_case_insensitive(workspace, query):
    c, store, project, base = workspace
    match = store.add_source(project, "Export csv: 50% of 'saved_reports'")
    store.add_source(project, "Unrelated evidence")
    response = c.get(base + "/sources", params={"query": query})
    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == [match.id]


@pytest.mark.parametrize(
    "params", [{"query": "x" * 201}, {"limit": 0}, {"limit": 51}, {"limit": -1}]
)
def test_source_picker_bounds(workspace, params):
    c, _store, _project, base = workspace
    assert c.get(base + "/sources", params=params).status_code == 422


def test_run_metadata_cannot_read_other_project_revision_or_audit(
    workspace, artifact_dict
):
    from specbridge.models import Artifact

    c, store, project, base = workspace
    other = store.create_project("Private")
    artifact = Artifact.model_validate(artifact_dict)
    artifact.title = "Other project confidential title"
    revision = store.save_revision(other.id, artifact, None)
    run = Run(
        id="unlinked",
        project_id=project,
        source_ids=[],
        skill_id="feature-handoff",
        intent="Local intent",
        destination="fixture",
        stage="intake",
        revision_id=revision.id,
    )
    with store.transaction() as db:
        db.execute(
            "INSERT INTO runs(id,project_id,data) VALUES (?,?,?)",
            (run.id, project, run.model_dump_json()),
        )
        store.audit(db, other.id, "workflow_created", run.id)
    summary = c.get(base + "/runs").json()[0]
    assert summary["title"] == "Local intent"
    assert summary["revision_number"] is None
    assert summary["created_at"] is None


def test_run_metadata_resolves_linked_revision_beyond_recent_history(
    workspace, artifact_dict
):
    from specbridge.models import Artifact

    c, store, project, base = workspace
    artifact = Artifact.model_validate(artifact_dict)
    revision = store.save_revision(project, artifact, None)
    first = revision
    for number in range(2, 24):
        artifact = revision.artifact.model_copy(
            update={"title": f"Newer revision {number}"}
        )
        revision = store.save_revision(project, artifact, revision.digest)
    run = Run(
        id="older",
        project_id=project,
        source_ids=[],
        skill_id="feature-handoff",
        intent="Intent",
        destination="fixture",
        stage="human_review",
        revision_id=first.id,
    )
    with store.transaction() as db:
        db.execute(
            "INSERT INTO runs(id,project_id,data) VALUES (?,?,?)",
            (run.id, project, run.model_dump_json()),
        )
    summary = c.get(base + "/runs").json()[0]
    assert summary["title"] == "Report export"
    assert summary["revision_number"] is None
    assert summary["legacy_revision_number"] == 1


def test_source_picker_excludes_non_original_kinds_and_authenticates(workspace):
    c, store, project, base = workspace
    source = store.add_source(project, "Original evidence")
    with store.transaction() as db:
        for index, kind in enumerate(
            ["verified", "recommendation", "assumption", "unknown"]
        ):
            copy = source.model_copy(
                update={"id": f"non-original-{index}", "kind": kind}
            )
            db.execute(
                "INSERT INTO sources VALUES (?,?,?)",
                (copy.id, project, copy.model_dump_json()),
            )
    assert [s["id"] for s in c.get(base + "/sources").json()] == [source.id]
    assert (
        c.get(base + "/sources", headers={"Authorization": "Bearer wrong"}).status_code
        == 401
    )


def test_run_summary_does_not_require_full_historical_artifact_validation(workspace):
    """A list label can read historical title metadata without parsing obsolete bodies."""
    c, store, project, base = workspace
    run = Run(
        id="historic-body",
        project_id=project,
        source_ids=[],
        skill_id="feature-handoff",
        intent="Historical fallback",
        destination="fixture",
        stage="human_review",
        revision_id="historic-revision",
    )
    with store.transaction() as db:
        db.execute(
            "INSERT INTO revisions(id,project_id,number,digest,data) VALUES (?,?,?,?,?)",
            (
                "historic-revision",
                project,
                1,
                "0" * 64,
                '{"artifact":{"title":"Historical title"},"obsolete_body":true}',
            ),
        )
        db.execute(
            "INSERT INTO runs(id,project_id,data) VALUES (?,?,?)",
            (run.id, project, run.model_dump_json()),
        )
    response = c.get(base + "/runs")
    assert response.status_code == 200
    assert response.json()[0]["title"] == "Historical title"
    assert response.json()[0]["revision_number"] is None
    assert response.json()[0]["legacy_revision_number"] == 1


def test_source_cursor_input_is_bounded(workspace):
    c, _store, _project, base = workspace
    assert c.get(base + "/sources", params={"after": "x" * 101}).status_code == 422
