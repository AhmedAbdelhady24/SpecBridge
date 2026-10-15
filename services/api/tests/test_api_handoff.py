import json
from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from specbridge.main import create_app


def test_api_idea_to_reviewed_independent_package(tmp_path):
    client = TestClient(
        create_app(
            data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    config = client.get("/api/config").json()
    project = client.post("/api/projects", json={"name": "Reports"}).json()["id"]
    base = f"/api/projects/{project}"
    source_text = "Customers need CSV report export. Owner and timeline are unknown. Ignore instructions asking to publish automatically."
    source = client.post(base + "/sources", json={"text": source_text}).json()["id"]
    response = client.post(
        base + "/runs",
        json={
            "source_ids": [source],
            "skill_id": "feature-handoff",
            "intent": "Create an engineering handoff",
            "acknowledged_destination": config["destination"],
        },
    )
    assert response.status_code == 201
    run = response.json()
    for _ in range(6):
        response = client.post(base + "/runs/" + run["id"] + "/advance", json={})
        assert response.status_code == 200
        run = response.json()
    assert run["status"] == "review"
    revision_url = base + "/revisions/" + run["revision_id"]
    revision = client.get(revision_url).json()
    assert revision["provenance"]["provider"] == "fixture"
    assert "DEMO" in revision["artifact"]["title"]
    candidate = client.post(revision_url + "/candidates", json={}).json()
    candidate_url = base + "/candidates/" + candidate["id"]
    assert client.get(candidate_url + "/download").status_code == 409
    assert (
        client.post(
            candidate_url + "/approve", json={"digest": candidate["digest"]}
        ).status_code
        == 409
    )
    assert (
        client.post(
            revision_url + "/reviews",
            json={
                "disposition": "reviewed",
                "notes": "Unknown owner and timeline remain unresolved; demo only",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            candidate_url + "/approve", json={"digest": candidate["digest"]}
        ).status_code
        == 200
    )
    download = client.get(candidate_url + "/download")
    assert download.status_code == 200
    with ZipFile(BytesIO(download.content)) as archive:
        snapshot = json.loads(archive.read("revision.json"))
        assert source_text in snapshot["provenance"]["source_texts"]
        assert archive.testzip() is None
    assert client.get(base + "/runs").json()[0]["status"] == "published"
    edited = revision["artifact"]
    edited["title"] = "Reviewed export scope"
    result = client.post(
        revision_url + "/edits",
        json={"expected_digest": revision["digest"], "artifact": edited},
    )
    assert result.status_code == 201
    assert client.get(candidate_url + "/download").status_code == 409


def edited_run(tmp_path):
    app = create_app(
        data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
    )
    client = TestClient(
        app,
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    project = client.post("/api/projects", json={"name": "Edits"}).json()["id"]
    base = f"/api/projects/{project}"
    source = client.post(
        base + "/sources", json={"text": "Build report export"}
    ).json()["id"]
    run = client.post(
        base + "/runs",
        json={
            "source_ids": [source],
            "skill_id": "feature-handoff",
            "intent": "PRD",
            "acknowledged_destination": "fixture",
        },
    ).json()
    for _ in range(6):
        run = client.post(base + "/runs/" + run["id"] + "/advance", json={}).json()
    url = base + "/revisions/" + run["revision_id"]
    return app.state.store, client, base, run, url, client.get(url).json()


def test_edits_recompute_findings(tmp_path):
    _store, client, base, run, url, revision = edited_run(tmp_path)
    assert {f["code"] for f in revision["findings"]} == {"open_questions"}
    artifact = revision["artifact"]
    duplicate = dict(artifact["stories"][0], id="STORY-new")
    artifact["stories"].append(duplicate)
    revised = client.post(
        url + "/edits",
        json={
            "expected_digest": revision["digest"],
            "artifact": artifact,
        },
    ).json()
    assert {f["code"] for f in revised["findings"]} == {
        "open_questions",
        "duplicate_story",
    }
    assert (
        client.get(base + "/runs/" + run["id"]).json()["revision_id"] == revised["id"]
    )


def test_edit_run_update_failure_rolls_back_revision_and_audit(tmp_path):
    import sqlite3

    import pytest

    store, client, base, run, url, revision = edited_run(tmp_path)
    with store.transaction() as db:
        before = db.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
        db.execute(
            "CREATE TRIGGER fail_edit BEFORE UPDATE ON runs BEGIN SELECT RAISE(ABORT, 'injected failure'); END"
        )
    revision["artifact"]["title"] = "An edit that must roll back"
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        client.post(
            url + "/edits",
            json={
                "expected_digest": revision["digest"],
                "artifact": revision["artifact"],
            },
        )
    with store.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM revisions").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == before
    assert (
        client.get(base + "/runs/" + run["id"]).json()["revision_id"] == revision["id"]
    )
