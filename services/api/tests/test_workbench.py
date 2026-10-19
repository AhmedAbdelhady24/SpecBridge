"""Question answers and working copies must not mutate the canonical handoff."""

import json

import pytest
from test_feature_history import api_workspace, create_run


@pytest.fixture
def workbench(tmp_path):
    app, c, b = api_workspace(tmp_path)
    run, rev = create_run(c, b, "Report export")
    # Deliberately identical questions still represent two distinct occurrences.
    artifact = rev["artifact"]
    artifact["open_questions"] = ["Which format?", "Which format?"]
    response = c.post(
        b + f"/revisions/{rev['id']}/edits",
        json={"artifact": artifact, "expected_digest": rev["digest"]},
    )
    assert response.status_code == 201
    revision = response.json()
    return app, c, b, run, revision, b + f"/runs/{run['id']}"


def test_answers_survive_restart_without_changing_artifact(
    workbench, tmp_path, monkeypatch
):
    app, c, b, run, revision, url = workbench
    from specbridge.providers import FixtureProvider

    def forbidden(*args, **kwargs):
        raise AssertionError("No generation is authorized by answering")

    monkeypatch.setattr(FixtureProvider, "generate", forbidden)
    response = c.get(url + "/questions")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) == 2 and questions[0]["id"] != questions[1]["id"]
    q = questions[0]
    saved = c.post(
        url + f"/questions/{q['id']}/answers",
        json={"expected_version": q["version"], "text": "Use CSV."},
    )
    assert saved.status_code == 201, saved.text
    answer = saved.json()
    assert answer["text"] == "Use CSV."
    assert c.get(b + f"/revisions/{revision['id']}").json() == revision
    assert c.get(url + "/questions").json()[1]["latest_answer"] is None
    from specbridge.storage import Store
    from specbridge.workbench import Workbench

    reopened = Workbench(Store(app.state.store.path)).questions(
        run["project_id"], run["id"]
    )
    assert reopened[0].latest_answer.text == "Use CSV."
    stale = c.post(
        url + f"/questions/{q['id']}/answers",
        json={"expected_version": q["version"], "text": "PDF"},
    )
    assert stale.status_code == 409
    assert c.get(url + f"/questions/{q['id']}/answers").json()[0]["text"] == "Use CSV."
    source = c.get(b + f"/sources/{answer['source_id']}").json()
    assert source["text"] == "Use CSV." and source["kind"] == "user_provided"


def test_question_status_and_scope_enforced(workbench):
    _, c, b, _run, _revision, url = workbench
    q = c.get(url + "/questions").json()[0]
    status_url = url + f"/questions/{q['id']}/status"
    assert (
        c.post(
            status_url,
            json={
                "expected_version": q["version"],
                "status": "resolved",
                "reason": "skip",
            },
        ).status_code
        == 422
    )
    assert (
        c.post(
            status_url,
            json={
                "expected_version": q["version"],
                "status": "dismissed",
                "reason": "",
            },
        ).status_code
        == 422
    )
    dismissed = c.post(
        status_url,
        json={
            "expected_version": q["version"],
            "status": "dismissed",
            "reason": "Outside this feature",
        },
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"
    other, _ = create_run(c, b, "Other feature")
    other_url = b + f"/runs/{other['id']}/questions/{q['id']}/answers"
    assert (
        c.post(
            other_url, json={"expected_version": q["version"], "text": "No"}
        ).status_code
        == 404
    )


def test_request_is_not_resolved_by_answer_save(workbench):
    _, c, _b, _run, revision, url = workbench
    response = c.post(
        url + "/change-requests",
        json={
            "base_revision_id": revision["id"],
            "text": "Clarify permitted format",
            "target_ids": [revision["artifact"]["requirements"][0]["id"]],
        },
    )
    assert response.status_code == 201, response.text
    request = response.json()
    q = c.get(url + "/questions").json()[0]
    assert (
        c.post(
            url + f"/questions/{q['id']}/answers",
            json={"expected_version": q["version"], "text": "CSV"},
        ).status_code
        == 201
    )
    assert c.get(url + "/change-requests").json()[0]["status"] == "open"
    assert (
        c.post(
            url + f"/change-requests/{request['id']}/status",
            json={
                "expected_version": request["version"],
                "status": "addressed",
                "reason": "done",
            },
        ).status_code
        == 422
    )


def save_copy(c, url, revision, **changes):
    body = {
        "expected_version": 0,
        "base_revision_id": revision["id"],
        "base_digest": revision["digest"],
        "artifact": json.loads(json.dumps(revision["artifact"])),
        "question_changes": [],
        "request_changes": [],
        "change_summary": "Clarify CSV",
    }
    body.update(changes)
    return c.put(url + "/working-copy", json=body)


def test_working_preview_atomic_commit_and_idempotency(workbench, monkeypatch):
    _app, c, b, _run, revision, url = workbench
    from specbridge.providers import FixtureProvider

    def forbidden(*args, **kwargs):
        raise AssertionError("No model call during editing")

    monkeypatch.setattr(FixtureProvider, "generate", forbidden)
    original_questions = c.get(url + "/questions").json()
    q = original_questions[0]
    answer = c.post(
        url + f"/questions/{q['id']}/answers",
        json={"expected_version": q["version"], "text": "Use CSV."},
    ).json()
    q = c.get(url + "/questions").json()[0]
    artifact = json.loads(json.dumps(revision["artifact"]))
    artifact["requirements"][0].update(
        text=answer["text"], source_ids=[answer["source_id"]], kind="user_provided"
    )
    artifact["open_questions"].pop(0)
    copied = save_copy(
        c,
        url,
        revision,
        artifact=artifact,
        question_changes=[
            {
                "question_id": q["id"],
                "expected_question_version": q["version"],
                "answer_version": answer["version"],
                "targets": [artifact["requirements"][0]["id"]],
            }
        ],
    )
    assert copied.status_code == 200, copied.text
    working = copied.json()
    assert c.get(b + f"/revisions/{revision['id']}").json() == revision
    assert c.get(url + "/working-copy").json() == working
    from uuid import uuid4

    body = {"working_copy_version": working["version"], "idempotency_key": str(uuid4())}
    committed = c.post(url + "/commits", json=body)
    assert committed.status_code == 201, committed.text
    assert c.post(url + "/commits", json=body).json() == committed.json()
    assert len(c.get(url + "/history").json()) == 3
    assert c.get(url + "/working-copy").json() is None
    resolved = next(
        item for item in c.get(url + "/questions").json() if item["id"] == q["id"]
    )
    assert (
        next(
            item
            for item in c.get(url + "/questions").json()
            if item["in_current_draft"]
        )["id"]
        == original_questions[1]["id"]
    )
    assert resolved["status"] == "resolved"
    assert resolved["resolution_revision_id"] == committed.json()["revision_id"]
    receipt = committed.json()
    newer = c.get(b + f"/revisions/{receipt['revision_id']}").json()
    changed = json.loads(json.dumps(newer["artifact"]))
    changed["title"] = "New preview"
    second = save_copy(c, url, newer, artifact=changed)
    assert second.status_code == 200
    assert (
        c.post(
            url + "/commits",
            json={**body, "working_copy_version": second.json()["version"]},
        ).status_code
        == 409
    )


def test_stale_and_invalid_commits_do_not_partially_resolve(workbench):
    _, c, b, _run, revision, url = workbench
    artifact = json.loads(json.dumps(revision["artifact"]))
    artifact["title"] = "Working title"
    copied = save_copy(c, url, revision, artifact=artifact).json()
    update = json.loads(json.dumps(revision["artifact"]))
    update["title"] = "Concurrent edit"
    assert (
        c.post(
            b + f"/revisions/{revision['id']}/edits",
            json={"artifact": update, "expected_digest": revision["digest"]},
        ).status_code
        == 201
    )
    from uuid import uuid4

    assert (
        c.post(
            url + "/commits",
            json={
                "working_copy_version": copied["version"],
                "idempotency_key": str(uuid4()),
            },
        ).status_code
        == 409
    )
    assert c.get(url + "/working-copy").json()["artifact"]["title"] == "Working title"
    assert c.get(url + "/questions").json()[0]["status"] == "unresolved"
    assert (
        c.request(
            "DELETE",
            url + "/working-copy",
            json={"expected_version": copied["version"]},
        ).status_code
        == 200
    )
    assert c.get(url + "/working-copy").json() is None


def test_commit_failure_rolls_back_resolution_head_and_receipt(workbench):
    app, c, _b, _run, revision, url = workbench
    q = c.get(url + "/questions").json()[0]
    answer = c.post(
        url + f"/questions/{q['id']}/answers",
        json={"expected_version": q["version"], "text": "CSV"},
    ).json()
    q = c.get(url + "/questions").json()[0]
    artifact = json.loads(json.dumps(revision["artifact"]))
    artifact["title"] = "Clarified format"
    artifact["open_questions"].pop(0)
    copy = save_copy(
        c,
        url,
        revision,
        artifact=artifact,
        question_changes=[
            {
                "question_id": q["id"],
                "expected_question_version": q["version"],
                "answer_version": answer["version"],
                "targets": ["title"],
            }
        ],
    ).json()
    with app.state.store.transaction() as db:
        db.execute(
            "CREATE TRIGGER fail_receipt BEFORE INSERT ON commit_receipts BEGIN SELECT RAISE(ABORT,'injected'); END"
        )
    import sqlite3
    from uuid import uuid4

    with pytest.raises(sqlite3.IntegrityError):
        c.post(
            url + "/commits",
            json={
                "working_copy_version": copy["version"],
                "idempotency_key": str(uuid4()),
            },
        )
    assert c.get(url).json()["revision_id"] == revision["id"]
    assert (
        next(x for x in c.get(url + "/questions").json() if x["id"] == q["id"])[
            "status"
        ]
        == "answered"
    )
    assert c.get(url + "/working-copy").json()["version"] == copy["version"]
    assert len(c.get(url + "/history").json()) == 2


def test_invalid_coverage_cannot_commit_but_work_is_recoverable(workbench):
    _, c, _b, _run, revision, url = workbench
    artifact = json.loads(json.dumps(revision["artifact"]))
    artifact["requirements"].append(
        {
            "id": "REQ-new",
            "text": "Unlinked requirement",
            "kind": "recommendation",
            "source_ids": [],
        }
    )
    copied = save_copy(c, url, revision, artifact=artifact)
    assert copied.status_code == 200
    from uuid import uuid4

    committed = c.post(
        url + "/commits",
        json={
            "working_copy_version": copied.json()["version"],
            "idempotency_key": str(uuid4()),
        },
    )
    assert committed.status_code == 422
    assert len(c.get(url + "/history").json()) == 2
    assert c.get(url + "/working-copy").json()["artifact"] == artifact


def test_discarded_versions_are_never_reused(workbench):
    _, c, _b, _run, revision, url = workbench
    a = save_copy(c, url, revision).json()
    assert (
        c.request(
            "DELETE", url + "/working-copy", json={"expected_version": a["version"]}
        ).status_code
        == 200
    )
    b = save_copy(c, url, revision).json()
    assert b["version"] > a["version"]
    assert (
        c.request(
            "DELETE", url + "/working-copy", json={"expected_version": a["version"]}
        ).status_code
        == 409
    )
    assert c.get(url + "/working-copy").json()["version"] == b["version"]


def test_explicit_reopen_preserves_question_identity_and_export_history(workbench):
    app, c, b, _run, revision, url = workbench
    originals = c.get(url + "/questions").json()
    q = originals[0]
    answer = c.post(
        url + f"/questions/{q['id']}/answers",
        json={"expected_version": q["version"], "text": "CSV"},
    ).json()
    q = c.get(url + "/questions").json()[0]
    artifact = json.loads(json.dumps(revision["artifact"]))
    artifact["title"] = "CSV decided"
    artifact["open_questions"].pop(0)
    change = {
        "question_id": q["id"],
        "expected_question_version": q["version"],
        "answer_version": answer["version"],
        "targets": ["title"],
    }
    copy = save_copy(
        c, url, revision, artifact=artifact, question_changes=[change]
    ).json()
    from uuid import uuid4

    result = c.post(
        url + "/commits",
        json={"working_copy_version": copy["version"], "idempotency_key": str(uuid4())},
    ).json()
    resolved = c.get(b + f"/revisions/{result['revision_id']}").json()
    updated = json.loads(json.dumps(resolved["artifact"]))
    updated["purpose"] = "Reviewed purpose"
    manual = c.post(
        b + f"/revisions/{resolved['id']}/edits",
        json={"expected_digest": resolved["digest"], "artifact": updated},
    ).json()
    with app.state.store.transaction() as db:
        snapshot = db.execute(
            "SELECT data FROM revision_decisions WHERE revision_id=?", (manual["id"],)
        ).fetchone()
        assert snapshot and json.loads(snapshot[0])["questions"][0]["id"] == q["id"]
    q = next(item for item in c.get(url + "/questions").json() if item["id"] == q["id"])
    reopened = json.loads(json.dumps(manual["artifact"]))
    reopened["open_questions"].append(q["text"])
    reopened["open_questions"].append("Who approves?")
    copy = save_copy(
        c,
        url,
        manual,
        artifact=reopened,
        question_changes=[
            {**change, "expected_question_version": q["version"], "action": "reopen"}
        ],
    ).json()
    committed = c.post(
        url + "/commits",
        json={"working_copy_version": copy["version"], "idempotency_key": str(uuid4())},
    )
    assert committed.status_code == 422, committed.text
    assert c.get(url + "/working-copy").json()["version"] == copy["version"]
    reopened["open_questions"].pop()
    copy = save_copy(
        c,
        url,
        manual,
        artifact=reopened,
        expected_version=copy["version"],
        question_changes=[
            {**change, "expected_question_version": q["version"], "action": "reopen"}
        ],
    ).json()
    committed = c.post(
        url + "/commits",
        json={"working_copy_version": copy["version"], "idempotency_key": str(uuid4())},
    )
    assert committed.status_code == 201, committed.text
    active = [
        item for item in c.get(url + "/questions").json() if item["in_current_draft"]
    ]
    assert {item["id"] for item in active} == {item["id"] for item in originals}
    assert (
        next(item for item in active if item["id"] == q["id"])["latest_answer"]["text"]
        == "CSV"
    )


def test_exact_package_preview_is_authenticated_bounded_and_inert(workbench):
    app, c, b, _run, revision, _url = workbench
    candidate = c.post(b + f"/revisions/{revision['id']}/candidates").json()
    url = b + f"/candidates/{candidate['id']}/preview"
    result = c.get(url)
    assert result.status_code == 200, result.text
    preview = result.json()
    assert preview["digest"] == candidate["digest"]
    assert "src/content/docs/requirements.md" in [f["path"] for f in preview["files"]]
    doc = c.get(url, params={"path": "src/content/docs/requirements.md"})
    assert doc.status_code == 200
    from specbridge.publisher import text

    assert "## Requirement 1" in doc.json()["content"]
    assert (
        text(revision["artifact"]["requirements"][0]["text"]) in doc.json()["content"]
    )
    assert revision["artifact"]["requirements"][0]["id"] not in doc.json()["content"]
    assert c.get(url, params={"path": "../.env"}).status_code == 404
    assert c.get(url, params={"path": "astro.config.mjs"}).status_code == 404
    other = c.post("/api/projects", json={"name": "Other"}).json()["id"]
    assert (
        c.get(f"/api/projects/{other}/candidates/{candidate['id']}/preview").status_code
        == 404
    )
    # A candidate can be previewed, but preview never grants download authority.
    assert c.get(b + f"/candidates/{candidate['id']}/download").status_code == 409
    with app.state.store.transaction() as db:
        db.execute(
            "UPDATE candidates SET zip=CAST(zip || X'00' AS BLOB) WHERE id=?",
            (candidate["id"],),
        )
    assert c.get(url).status_code == 409


def test_request_paging_and_status_history_remain_scoped(workbench):
    _, c, _b, _run, revision, url = workbench
    for index in range(21):
        result = c.post(
            url + "/change-requests",
            json={
                "base_revision_id": revision["id"],
                "text": f"Change {index}",
                "target_ids": [],
            },
        )
        assert result.status_code == 201
    first = c.get(url + "/change-requests").json()
    assert len(first) == 20
    second = c.get(url + "/change-requests", params={"before": first[-1]["id"]}).json()
    assert len(second) == 1 and second[0]["text"] == "Change 0"
    item = first[0]
    assert (
        c.post(
            url + f"/change-requests/{item['id']}/status",
            json={
                "expected_version": item["version"],
                "status": "dismissed",
                "reason": "Superseded",
            },
        ).status_code
        == 200
    )
    history = c.get(url + f"/change-requests/{item['id']}/history").json()
    assert [event["status"] for event in history] == ["dismissed", "open"]
    assert c.get(url + "/change-requests?limit=51").status_code == 422


def test_ambiguous_duplicate_edit_preserves_answer_identity(workbench):
    _, c, _b, _run, revision, url = workbench
    q = c.get(url + "/questions").json()[0]
    answer = c.post(
        url + f"/questions/{q['id']}/answers",
        json={"expected_version": q["version"], "text": "CSV"},
    )
    assert answer.status_code == 201
    artifact = json.loads(json.dumps(revision["artifact"]))
    artifact["open_questions"].append("Another question?")
    copied = save_copy(c, url, revision, artifact=artifact).json()
    from uuid import uuid4

    assert (
        c.post(
            url + "/commits",
            json={
                "working_copy_version": copied["version"],
                "idempotency_key": str(uuid4()),
            },
        ).status_code
        == 422
    )
    assert (
        next(
            item for item in c.get(url + "/questions").json() if item["id"] == q["id"]
        )["in_current_draft"]
        is True
    )
    assert c.get(url + "/working-copy").json()["version"] == copied["version"]
