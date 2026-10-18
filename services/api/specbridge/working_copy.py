"""Optimistic durable previews and idempotent atomic handoff commits."""

import json
from collections import Counter
from typing import TYPE_CHECKING

from .models import Run, canonical, digest
from .storage import Conflict
from .workbench_models import (
    CommitInput,
    CommitReceipt,
    DecisionSnapshot,
    WorkingCopy,
    WorkingInput,
)

if TYPE_CHECKING:
    from .workbench import Workbench


class WorkingDrafts:
    def __init__(self, service: "Workbench"):
        self.service = service
        self.store = service.store
        self.history = service.history

    def get(self, project_id: str, run_id: str) -> WorkingCopy | None:
        with self.store.transaction() as db:
            self.history.require_run(db, project_id, run_id)
            row = db.execute(
                "SELECT data FROM working_copies WHERE project_id=? AND run_id=?",
                (project_id, run_id),
            ).fetchone()
            return WorkingCopy.model_validate_json(row[0]) if row else None

    def save(self, project_id: str, run_id: str, body: WorkingInput) -> WorkingCopy:
        with self.store.transaction() as db:
            head = self.history.head(project_id, run_id, connection=db)
            if (
                not head
                or head.id != body.base_revision_id
                or head.digest != body.base_digest
            ):
                raise Conflict("Feature changed; compare saved work before reconciling")
            row = db.execute(
                "SELECT version FROM working_copies WHERE project_id=? AND run_id=?",
                (project_id, run_id),
            ).fetchone()
            if (row[0] if row else 0) != body.expected_version:
                raise Conflict("Working preview changed; reload before saving")
            counter = db.execute(
                "SELECT version FROM working_versions WHERE run_id=?", (run_id,)
            ).fetchone()
            version = (counter[0] if counter else 0) + 1
            db.execute(
                "INSERT INTO working_versions VALUES (?,?) ON CONFLICT(run_id) DO UPDATE SET version=excluded.version",
                (run_id, version),
            )
            result = WorkingCopy(**body.model_dump(), version=version)
            db.execute(
                "INSERT INTO working_copies VALUES (?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET version=excluded.version,data=excluded.data",
                (run_id, project_id, version, result.model_dump_json()),
            )
            self.store.audit(db, project_id, "working_preview_saved", run_id)
            return result

    def discard(self, project_id: str, run_id: str, expected_version: int) -> None:
        with self.store.transaction() as db:
            self.history.require_run(db, project_id, run_id)
            row = db.execute(
                "SELECT version FROM working_copies WHERE project_id=? AND run_id=?",
                (project_id, run_id),
            ).fetchone()
            if (row[0] if row else 0) != expected_version:
                raise Conflict("Working preview changed; reload before discarding")
            db.execute(
                "DELETE FROM working_copies WHERE project_id=? AND run_id=?",
                (project_id, run_id),
            )
            self.store.audit(db, project_id, "working_preview_discarded", run_id)

    def commit(self, project_id: str, run_id: str, body: CommitInput) -> CommitReceipt:
        from .workflow import Workflow

        with self.store.transaction() as db:
            self.history.require_run(db, project_id, run_id)
            existing = db.execute(
                "SELECT data FROM commit_receipts WHERE run_id=? AND key=?",
                (run_id, body.idempotency_key),
            ).fetchone()
            if existing:
                result = CommitReceipt.model_validate_json(existing[0])
                if result.working_copy_version != body.working_copy_version:
                    raise Conflict("Commit key already identifies different work")
                return result
            row = db.execute(
                "SELECT data FROM working_copies WHERE project_id=? AND run_id=?",
                (project_id, run_id),
            ).fetchone()
            if not row:
                raise Conflict("Save your working preview before committing")
            copy = WorkingCopy.model_validate_json(row[0])
            if copy.version != body.working_copy_version:
                raise Conflict("Working preview changed; reload before committing")
            head = self.history.head(project_id, run_id, connection=db)
            if (
                not head
                or head.id != copy.base_revision_id
                or head.digest != copy.base_digest
            ):
                raise Conflict("Feature changed; compare revisions before committing")
            if head.artifact == copy.artifact:
                raise Conflict(
                    "No document changes to save; answers remain saved separately"
                )
            if len({q.question_id for q in copy.question_changes}) != len(
                copy.question_changes
            ) or len({r.request_id for r in copy.request_changes}) != len(
                copy.request_changes
            ):
                raise ValueError("Resolve each item only once")
            questions = []
            delta: Counter[str] = Counter()
            for change in copy.question_changes:
                q = self.service.question(db, project_id, run_id, change.question_id)
                if (
                    q.version != change.expected_question_version
                    or not q.latest_answer
                    or q.latest_answer.version != change.answer_version
                ):
                    raise Conflict(
                        "Question or answer changed; inspect the latest answer"
                    )
                self.service.targets(copy.artifact, change.targets)
                if change.action == "resolve":
                    if (
                        q.status != "answered"
                        or not db.execute(
                            "SELECT 1 FROM question_occurrences WHERE revision_id=? AND question_id=?",
                            (head.id, q.id),
                        ).fetchone()
                    ):
                        raise Conflict(
                            "Only answered current questions can be resolved"
                        )
                    delta[q.text] -= 1
                    changed = False
                    for target in change.targets:
                        if target in type(head.artifact).model_fields:
                            changed |= getattr(head.artifact, target) != getattr(
                                copy.artifact, target
                            )
                        else:
                            old = next(
                                (
                                    item
                                    for item in head.artifact.identified_items()
                                    if item.id == target
                                ),
                                None,
                            )
                            new = next(
                                (
                                    item
                                    for item in copy.artifact.identified_items()
                                    if item.id == target
                                ),
                                None,
                            )
                            changed |= old != new
                    if not changed:
                        raise ValueError(
                            "A resolution needs an explicit amendment to its target"
                        )
                else:
                    if q.status != "resolved":
                        raise Conflict(
                            "Only a resolved question can be reopened into the draft"
                        )
                    delta[q.text] += 1
                questions.append((q, change))
            before = Counter(head.artifact.open_questions)
            after = Counter(copy.artifact.open_questions)
            if any(
                after[text] != before[text] + count for text, count in delta.items()
            ):
                raise ValueError(
                    "Question additions/removals must match explicit resolutions"
                )
            requests = []
            for request_change in copy.request_changes:
                item = self.service.request(
                    db, project_id, run_id, request_change.request_id
                )
                if (
                    item.version != request_change.expected_version
                    or item.status != "open"
                ):
                    raise Conflict(
                        "Requested change updated; inspect it before resolving"
                    )
                requests.append(item)
            revision = self.store.save_revision(
                project_id,
                copy.artifact,
                head.digest,
                run_id=run_id,
                parent_revision_id=head.id,
                change_summary=copy.change_summary or None,
                reopened_question_ids=[
                    q.id for q, c in questions if c.action == "reopen"
                ],
                excluded_question_ids=[
                    q.id for q, c in questions if c.action == "resolve"
                ],
                connection=db,
                findings=Workflow.findings(copy.artifact),
            )
            snapshot_row = db.execute(
                "SELECT data FROM revision_decisions WHERE revision_id=?", (head.id,)
            ).fetchone()
            snapshot = (
                json.loads(snapshot_row[0])
                if snapshot_row
                else {"questions": [], "requests": []}
            )
            mapping = {
                old.id: new.id
                for old, new in zip(
                    copy.artifact.identified_items(),
                    revision.artifact.identified_items(),
                    strict=True,
                )
            }
            for q, change in questions:
                q = q.model_copy(
                    update={
                        "version": q.version + 1,
                        "status": "resolved"
                        if change.action == "resolve"
                        else "answered",
                        "resolution_revision_id": revision.id
                        if change.action == "resolve"
                        else None,
                        "in_current_draft": change.action == "reopen",
                        "current_index": None,
                    }
                )
                self.service.write_question(db, q)
                snapshot["questions"] = [
                    item for item in snapshot["questions"] if item["id"] != q.id
                ]
                if change.action == "resolve":
                    snapshot["questions"].append(
                        {
                            **q.model_dump(),
                            "targets": [mapping.get(t, t) for t in change.targets],
                        }
                    )
            for item in requests:
                item = item.model_copy(
                    update={
                        "version": item.version + 1,
                        "status": "addressed",
                        "resolution_revision_id": revision.id,
                    }
                )
                db.execute(
                    "UPDATE change_requests SET data=? WHERE id=?",
                    (item.model_dump_json(), item.id),
                )
                db.execute(
                    "INSERT INTO change_request_events VALUES (?,?,?)",
                    (item.id, item.version, item.model_dump_json()),
                )
                snapshot["requests"] = [
                    r for r in snapshot["requests"] if r["id"] != item.id
                ] + [item.model_dump()]
            DecisionSnapshot.model_validate(snapshot)
            db.execute(
                "INSERT INTO revision_decisions VALUES (?,?) ON CONFLICT(revision_id) DO UPDATE SET data=excluded.data",
                (revision.id, canonical(snapshot)),
            )
            run_row = db.execute(
                "SELECT data FROM runs WHERE id=? AND project_id=?",
                (run_id, project_id),
            ).fetchone()
            run = Run.model_validate_json(run_row[0]).model_copy(
                update={
                    "revision_id": revision.id,
                    "stage": "human_review",
                    "status": "review",
                }
            )
            db.execute(
                "UPDATE runs SET data=? WHERE id=?", (run.model_dump_json(), run_id)
            )
            number = db.execute(
                "SELECT feature_number FROM revision_lineage WHERE revision_id=?",
                (revision.id,),
            ).fetchone()[0]
            result = CommitReceipt(
                revision_id=revision.id,
                feature_number=number,
                idempotency_key=body.idempotency_key,
                working_copy_version=copy.version,
            )
            db.execute(
                "INSERT INTO commit_receipts VALUES (?,?,?,?)",
                (
                    run_id,
                    body.idempotency_key,
                    digest(copy.model_dump()),
                    result.model_dump_json(),
                ),
            )
            db.execute(
                "DELETE FROM working_copies WHERE run_id=? AND project_id=?",
                (run_id, project_id),
            )
            self.store.audit(db, project_id, "working_preview_committed", revision.id)
            return result
