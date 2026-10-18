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
