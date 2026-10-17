"""SQLite backup restores actual immutable knowledge and artifacts, never overwrites."""

import importlib
import sqlite3
from pathlib import Path

import pytest
from specbridge.storage import Store

ROOT = Path(__file__).resolve().parents[3]


def backup_module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    assert (ROOT / "scripts/backup_workspace.py").exists(), "Backup utility missing"
    return importlib.import_module("backup_workspace")


def test_backup_restore_preserve_workspace_and_private_mode(
    monkeypatch, tmp_path, artifact_dict
):
    m = backup_module(monkeypatch)
    from specbridge.knowledge import Knowledge, KnowledgeInput
    from specbridge.models import Artifact

    original = Store(tmp_path / "original.db")
    p = original.create_project("Restore me")
    r = original.save_revision(p.id, Artifact.model_validate(artifact_dict), None)
    k = Knowledge(original).create(
        p.id,
        KnowledgeInput(
            entity_type="decision",
            title="Unresolved policy",
            text="No policy chosen",
            kind="unknown",
        ),
    )
    first = tmp_path / "backup.db"
    second = tmp_path / "restored.db"
    m.copy_database(original.path, first)
    m.copy_database(first, second)
    assert first.stat().st_mode & 0o777 == 0o600
    restored = Store(second)
    assert restored.get_revision(p.id, r.id) == r
    assert Knowledge(restored).history(p.id, k.id, 999, 20) == [k]
    with sqlite3.connect(second) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    with pytest.raises(FileExistsError):
        m.copy_database(original.path, first)
    assert Store(first).projects() == [p]


@pytest.mark.parametrize("bad", ["missing", "invalid", "future", "symlink"])
def test_invalid_backups_do_not_create_restore_target(monkeypatch, tmp_path, bad):
    m = backup_module(monkeypatch)
    src = tmp_path / "input.db"
    target = tmp_path / "output.db"
    if bad == "invalid":
        src.write_text("not a SQLite database")
    elif bad == "future":
        with sqlite3.connect(src) as db:
            db.execute("PRAGMA user_version=99")
    elif bad == "symlink":
        actual = tmp_path / "actual.db"
        Store(actual)
        src.symlink_to(actual)
    with pytest.raises((ValueError, FileNotFoundError, sqlite3.DatabaseError)):
        m.copy_database(src, target)
    assert not target.exists()


def test_backup_excludes_an_uncommitted_transaction(monkeypatch, tmp_path):
    m = backup_module(monkeypatch)
    original = Store(tmp_path / "live.db")
    p = original.create_project("Committed")
    with sqlite3.connect(original.path) as writer:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute(
            "INSERT INTO projects VALUES (?,?)", ("not-committed", "Pending")
        )
        m.copy_database(original.path, tmp_path / "snapshot.db")
        writer.rollback()
    assert Store(tmp_path / "snapshot.db").projects() == [p]
