from copy import deepcopy

import pytest
from specbridge.models import Artifact
from specbridge.storage import Conflict, NotFound, Store


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "test.db")


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


def test_new_ids_links_and_removed_id_not_reused(store, artifact_dict):
    p = store.create_project("IDs")
    revision = store.save_revision(p.id, Artifact.model_validate(artifact_dict), None)
    body = revision.artifact.model_copy(deep=True)
    new_requirement = body.requirements[0].model_copy(update={"id": "REQ-new"})
    body.requirements.append(new_requirement)
    body.stories[0].requirement_ids.append("REQ-new")
    added = store.save_revision(p.id, body, revision.digest)
    added_id = added.artifact.requirements[-1].id
    assert added_id != "REQ-new"
    assert added_id in added.artifact.stories[0].requirement_ids
    removed_body = added.artifact.model_copy(deep=True)
    removed_body.requirements.pop()
    removed_body.stories[0].requirement_ids.remove(added_id)
    removed = store.save_revision(p.id, removed_body, added.digest)
    with pytest.raises(Conflict):
        store.save_revision(p.id, added.artifact, removed.digest)


def test_competing_writers_and_failure_rollback(store, artifact_dict):
    import sqlite3
    from concurrent.futures import ThreadPoolExecutor

    p = store.create_project("Concurrent")
    artifact = Artifact.model_validate(artifact_dict)

    def save():
        try:
            return store.save_revision(p.id, artifact, None)
        except Conflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: save(), range(2)))
    assert sum(result is not None for result in results) == 1
    revision = next(result for result in results if result is not None)
    with store.transaction() as db:
        db.execute(
            "CREATE TRIGGER reject_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT, 'test failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        store.save_revision(p.id, revision.artifact, revision.digest)
    with store.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM revisions").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 1


def test_saved_citations_stay_inside_export_evidence_bound(store, artifact_dict):
    p = store.create_project("Sources")
    sources = [store.add_source(p.id, str(index)) for index in range(21)]
    body = Artifact.model_validate(artifact_dict)
    body.requirements[0].source_ids = [source.id for source in sources[:20]]
    body.stories[0].source_ids = [sources[-1].id]
    with pytest.raises(ValueError):
        store.save_revision(p.id, body, None)
