"""Reproduce M2 recovery with temporary fixture data and no model/network calls."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))

from fastapi.testclient import TestClient
from specbridge.knowledge import (
    Knowledge,
    KnowledgeEdit,
    KnowledgeInput,
    SnapshotRequest,
)
from specbridge.main import create_app
from specbridge.providers import FixtureProvider
from specbridge.skills import SkillRegistry
from specbridge.storage import Store
from specbridge.workflow import Workflow


def verify() -> dict[str, object]:
    root = ROOT
    with TemporaryDirectory(prefix="specbridge-m2-recovery-") as directory:
        base = Path(directory)
        original = base / "original"
        original.mkdir()
        restored = base / "restored"
        restored.mkdir()
        store = Store(original / "specbridge.db")
        p = store.create_project("Recovery reference")
        evidence = store.add_source(
            p.id, "Record the requested export behavior. Owner and date remain unknown."
        )
        knowledge = Knowledge(store)
        entries = []
        for t in (
            "goal",
            "stakeholder",
            "decision",
            "risk",
            "dependency",
            "api_reference",
            "conversation",
        ):
            entries.append(
                knowledge.create(
                    p.id,
                    KnowledgeInput(
                        entity_type=t,
                        title=f"Reference {t}",
                        text="Unresolved project context.",
                        kind="unknown",
                        source_ids=[evidence.id],
                    ),
                )
            )
        first = entries[0]
        updated = knowledge.edit(
            p.id,
            first.id,
            KnowledgeEdit(
                expected_digest=first.digest,
                entry=KnowledgeInput(
                    entity_type="goal",
                    title=first.title,
                    text="Updated proposal, not an approved fact.",
                    kind="recommendation",
                    source_ids=[evidence.id],
                ),
            ),
        )
        snapshot = knowledge.snapshot(
            p.id,
            first.id,
            SnapshotRequest(version=updated.version, expected_digest=updated.digest),
        )
        workflow = Workflow(
            store, SkillRegistry(root / "skills/runtime"), FixtureProvider()
        )
        run = workflow.start(
            p.id, [evidence.id, snapshot.id], "handoff", "feature-handoff", "fixture"
        )
        for _ in range(3):
            run = workflow.advance(p.id, run.id)
        backup = base / "backup.db"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts/backup_workspace.py"),
                "backup",
                "--database",
                str(store.path),
                "--output",
                str(backup),
            ],
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts/backup_workspace.py"),
                "restore",
                "--database",
                str(backup),
                "--output",
                str(restored / "specbridge.db"),
            ],
            check=True,
        )
        c = TestClient(
            create_app(
                data_dir=restored,
                token="recovery-fixture-only",
                allowed_origin="http://127.0.0.1:5173",
            ),
            base_url="http://127.0.0.1:8000",
            headers={"Authorization": "Bearer recovery-fixture-only"},
        )
        b = f"/api/projects/{p.id}"
        assert len(c.get(b + "/knowledge").json()) == 7
        assert len(c.get(b + f"/knowledge/{first.id}/history").json()) == 2
        assert c.get(b + f"/sources/{snapshot.id}").json()["kind"] == "recommendation"
        for _ in range(3):
            response = c.post(b + f"/runs/{run.id}/advance", json={})
            assert response.status_code == 200
        assert response.json()["status"] == "review"
        assert c.get(b + "/revisions").json()[0]["number"] == 1
        report = {
            "status": "passed",
            "backup_cli": "passed",
            "restore_cli": "passed",
            "knowledge_types": 7,
            "immutable_goal_versions": 2,
            "selected_context_kind": "recommendation",
            "restored_checkpoint_resumed_to": "human_review",
            "new_artifact_revision": 1,
            "private_backup_mode": oct(backup.stat().st_mode & 0o777),
            "provider": "fixture; no network/model calls",
        }
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="Optional new JSON evidence path; refuses overwrite"
    )
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error("Evidence output already exists")
    report = verify()
    if args.output is not None:
        with args.output.open("x") as file:
            file.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
