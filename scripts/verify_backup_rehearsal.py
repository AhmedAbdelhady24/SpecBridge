"""Production backup and restore rehearsal verification script.

Tests end-to-end SQLite backup, integrity verification, restore, and failure recovery
on an isolated database containing full Milestone 0-5 state without touching user data.
"""

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))

from specbridge.git_collaboration import GitPublishReceipt, GitTarget
from specbridge.storage import Store


def run_rehearsal() -> dict[str, object]:
    with TemporaryDirectory(prefix="specbridge-backup-rehearsal-") as temp_dir:
        base = Path(temp_dir)
        live_dir = base / "live"
        live_dir.mkdir(parents=True, exist_ok=True)
        live_db_path = live_dir / "specbridge.db"

        backup_dir = base / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / "backup-2026-10-19.db"

        restored_dir = base / "restored"
        restored_dir.mkdir(parents=True, exist_ok=True)
        restored_db_path = restored_dir / "specbridge.db"

        # 1. Initialize store and populate representative production data
        store = Store(live_db_path)
        project = store.create_project("Production Rehearsal Project")

        source = store.add_source(
            project.id,
            "Patients should see clinician-published care plans. Conflict remains unresolved.",
        )

        # Git target & audit
        target = GitTarget(
            project_id=project.id,
            target_type="local",
            repo_path="/tmp/mock-repo",
            base_branch="main",
            docs_path="docs",
        )
        store.save_git_target(target)

        receipt = GitPublishReceipt(
            id="audit-1234",
            project_id=project.id,
            commit_sha="a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e",
            branch_name="feature/care-plans",
            pr_url=None,
            pr_number=None,
            changeset_digest="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            status="published",
            timestamp="2026-10-19T12:00:00Z",
        )
        store.record_git_audit(project.id, "publish", receipt)

        # Delivery audit
        with store.transaction() as db:
            store.audit(db, project.id, "delivery_jira_sync", "sync-5678")

        # 2. Run backup CLI
        backup_cmd = [
            sys.executable,
            str(ROOT / "scripts/backup_workspace.py"),
            "backup",
            "--database",
            str(live_db_path),
            "--output",
            str(backup_file),
        ]
        result = subprocess.run(backup_cmd, capture_output=True, text=True, check=True)
        assert "Workspace copied and integrity-checked" in result.stdout

        # Verify backup permissions (must be 0o600)
        mode = backup_file.stat().st_mode & 0o777
        assert mode == 0o600, f"Expected 0o600 permissions, got {oct(mode)}"

        # 3. Run restore CLI
        restore_cmd = [
            sys.executable,
            str(ROOT / "scripts/backup_workspace.py"),
            "restore",
            "--database",
            str(backup_file),
            "--output",
            str(restored_db_path),
        ]
        result = subprocess.run(restore_cmd, capture_output=True, text=True, check=True)
        assert "Workspace copied and integrity-checked" in result.stdout

        # 4. Verify restored database integrity and exact contents
        restored_store = Store(restored_db_path)
        with restored_store.transaction() as db:
            # Check PRAGMA integrity
            integrity = [
                tuple(r) for r in db.execute("PRAGMA integrity_check").fetchall()
            ]
            assert integrity == [("ok",)], f"Integrity check failed: {integrity}"

            fk_check = db.execute("PRAGMA foreign_key_check").fetchall()
            assert not fk_check, f"Foreign key check failed: {fk_check}"

            # Verify tables
            tables = {
                r[0]
                for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            assert "git_targets" in tables
            assert "git_audits" in tables
            assert "projects" in tables

            # Verify rows match
            p_row = db.execute(
                "SELECT name FROM projects WHERE id = ?", (project.id,)
            ).fetchone()
            assert p_row and p_row[0] == "Production Rehearsal Project"

            src_row = db.execute(
                "SELECT data FROM sources WHERE id = ?", (source.id,)
            ).fetchone()
            assert src_row and "Patients should see" in src_row[0]

        gt = restored_store.get_git_target(project.id)
        assert gt is not None
        assert gt.target_type == "local"
        assert gt.docs_path == "docs"

        audits = restored_store.list_git_audits(project.id)
        assert len(audits) == 1
        assert audits[0]["commit_sha"] == "a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e"

        # 5. Verify refusal to overwrite existing target file
        refuse_overwrite_cmd = [
            sys.executable,
            str(ROOT / "scripts/backup_workspace.py"),
            "backup",
            "--database",
            str(live_db_path),
            "--output",
            str(backup_file),  # already exists
        ]
        proc = subprocess.run(
            refuse_overwrite_cmd, capture_output=True, text=True, check=False
        )
        assert proc.returncode != 0, "Backup must fail when output file already exists"
        assert (
            "FileExistsError" in proc.stderr
            or "already exists" in proc.stderr
            or proc.returncode != 0
        )

        return {
            "status": "passed",
            "backup_permissions": oct(mode),
            "integrity_check": "ok",
            "foreign_key_check": "clean",
            "git_targets_restored": 1,
            "git_audits_restored": 1,
            "overwrite_refusal_verified": True,
        }


def main() -> None:
    receipt = run_rehearsal()
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
