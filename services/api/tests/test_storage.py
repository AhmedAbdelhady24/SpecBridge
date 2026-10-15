from copy import deepcopy

import pytest
from specbridge.models import Artifact
from specbridge.storage import Conflict, NotFound, Store


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "test.db")


@pytest.fixture
def artifact_dict():
    return {
        "title": "Report export",
        "purpose": "Let customers use their reports",
        "scope": [
            {"text": "Export saved reports", "source_ids": [], "kind": "recommendation"}
        ],
        "non_goals": [],
        "requirements": [
            {
                "id": "REQ-1",
                "text": "Export a saved report",
                "source_ids": [],
                "kind": "recommendation",
            }
        ],
        "stories": [
            {
                "id": "STORY-1",
                "text": "As a customer I can export my report",
                "requirement_ids": ["REQ-1"],
                "acceptance_criteria": [
                    "Given a saved report, when export is selected, then a file is downloaded"
                ],
                "source_ids": [],
                "kind": "recommendation",
            }
        ],
        "edge_cases": [],
        "dependencies": [],
        "risks": [],
        "success_metrics": [],
        "open_questions": ["Which file format?"],
    }


def test_immutable_restart_and_project_scope(store, artifact_dict):
    p = store.create_project("First")
    other = store.create_project("Second")
    revision = store.save_revision(p.id, Artifact.model_validate(artifact_dict), None)
    assert revision.artifact.requirements[0].id != "REQ-1"
    assert Store(store.path).get_revision(p.id, revision.id) == revision
    with pytest.raises(NotFound):
        store.get_revision(other.id, revision.id)
    updated = revision.artifact.model_copy(deep=True)
    updated.title = "Export revised"
    next_revision = store.save_revision(p.id, updated, revision.digest)
    assert (
        next_revision.artifact.requirements[0].id
        == revision.artifact.requirements[0].id
    )
    assert store.get_revision(p.id, revision.id).artifact.title == "Report export"
    with pytest.raises(Conflict):
        store.save_revision(p.id, updated, revision.digest)


def test_bad_links_and_fabricated_verification_rejected(store, artifact_dict):
    p = store.create_project("First")
    bad = deepcopy(artifact_dict)
    bad["requirements"][0]["source_ids"] = ["absent"]
    with pytest.raises(NotFound):
        store.save_revision(p.id, Artifact.model_validate(bad), None)
    bad = deepcopy(artifact_dict)
    bad["requirements"][0]["kind"] = "verified"
    with pytest.raises(ValueError):
        store.save_revision(p.id, Artifact.model_validate(bad), None)


def test_future_schema_refused(tmp_path):
    import sqlite3

    path = tmp_path / "future.db"
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError):
        Store(path)


def test_source_size_uses_bytes(store):
    p = store.create_project("Test")
    with pytest.raises(ValueError):
        store.add_source(p.id, "é" * 20000)
