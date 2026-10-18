"""Proven feature ancestry; legacy snapshots stay readable without invented links."""

import sqlite3
from typing import TYPE_CHECKING

from .models import Model, Revision
from .workbench_models import DecisionSnapshot

if TYPE_CHECKING:
    from .storage import Store


class FeatureRevision(Model):
    revision_id: str
    run_id: str
    parent_revision_id: str | None
    feature_number: int | None
    legacy_number: int
    created_at: str | None
    change_summary: str | None


class RevisionComparison(Model):
    base: Revision
    head: Revision
    base_decisions: DecisionSnapshot | None = None
    head_decisions: DecisionSnapshot | None = None


class FeatureHistory:
    def __init__(self, store: "Store"):
        self.store = store

    @staticmethod
    def require_run(db: sqlite3.Connection, project_id: str, run_id: str) -> None:
        from .storage import NotFound

        if not db.execute(
            "SELECT 1 FROM runs WHERE id=? AND project_id=?", (run_id, project_id)
        ).fetchone():
            raise NotFound("Feature not found")

    def head(
        self, project_id: str, run_id: str, connection: sqlite3.Connection | None = None
    ) -> Revision | None:
        if connection is None:
            with self.store.transaction() as db:
                return self.head(project_id, run_id, connection=db)
        self.require_run(connection, project_id, run_id)
        row = connection.execute(
            "SELECT r.data FROM feature_heads h JOIN revisions r ON r.id=h.revision_id AND r.project_id=h.project_id WHERE h.project_id=? AND h.run_id=?",
            (project_id, run_id),
        ).fetchone()
        return Revision.model_validate_json(row[0]) if row else None

    def list(
        self, project_id: str, run_id: str, before: int | None = None, limit: int = 20
    ) -> list[FeatureRevision]:
        if not 1 <= limit <= 50:
            raise ValueError("Choose 1–50 revisions")
        with self.store.transaction() as db:
            self.require_run(db, project_id, run_id)
            rows = db.execute(
                "SELECT l.*,r.number FROM revision_lineage l JOIN revisions r ON r.id=l.revision_id WHERE l.project_id=? AND l.run_id=? AND r.number<? ORDER BY r.number DESC LIMIT ?",
                (project_id, run_id, before or 2147483647, limit),
            )
            return [
                FeatureRevision(
                    revision_id=r["revision_id"],
                    run_id=run_id,
                    parent_revision_id=r["parent_revision_id"],
                    feature_number=r["feature_number"],
                    legacy_number=r["number"],
                    created_at=r["created_at"],
                    change_summary=r["change_summary"],
                )
                for r in rows
            ]

    def compare(
        self, project_id: str, run_id: str, base_id: str, head_id: str
    ) -> RevisionComparison:
        from .storage import NotFound

        with self.store.transaction() as db:
            self.require_run(db, project_id, run_id)
            for revision_id in (base_id, head_id):
                if not db.execute(
                    "SELECT 1 FROM revision_lineage WHERE project_id=? AND run_id=? AND revision_id=?",
                    (project_id, run_id, revision_id),
                ).fetchone():
                    raise NotFound("Feature revision not found")
            snapshots = []
            for revision_id in (base_id, head_id):
                row = db.execute(
                    "SELECT data FROM revision_decisions WHERE revision_id=?",
                    (revision_id,),
                ).fetchone()
                snapshots.append(
                    DecisionSnapshot.model_validate_json(row[0]) if row else None
                )
        return RevisionComparison(
            base_decisions=snapshots[0],
            head_decisions=snapshots[1],
            base=self.store.get_revision(project_id, base_id),
            head=self.store.get_revision(project_id, head_id),
        )
