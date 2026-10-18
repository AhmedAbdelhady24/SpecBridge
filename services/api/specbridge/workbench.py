"""Durable local collaboration; never invokes a model or grants publication authority."""

import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from .feature_history import FeatureHistory
from .models import Artifact, Source, digest
from .storage import Conflict, NotFound, Store
from .workbench_models import (
    AnswerInput,
    AnswerVersion,
    QuestionView,
    RequestInput,
    RequestView,
    StatusInput,
)


class Workbench:
    def __init__(self, store: Store):
        self.store = store
        self.history = FeatureHistory(store)

    def questions(self, project_id: str, run_id: str) -> list[QuestionView]:
        with self.store.transaction() as db:
            head = self.history.head(project_id, run_id, connection=db)
            active = {
                r[0]: r[1]
                for r in db.execute(
                    "SELECT question_id,position FROM question_occurrences WHERE revision_id=?",
                    (head.id if head else None,),
                )
            }
            return [
                QuestionView.model_validate_json(r[0]).model_copy(
                    update={
                        "in_current_draft": r["id"] in active,
                        "current_index": active.get(r["id"]),
                    }
                )
                for r in db.execute(
                    "SELECT q.data,q.id FROM questions q LEFT JOIN question_occurrences o ON o.question_id=q.id AND o.revision_id=? WHERE q.project_id=? AND q.run_id=? AND (o.position IS NOT NULL OR json_extract(q.data,'$.status')!='unresolved') ORDER BY CASE WHEN o.position IS NULL THEN 1 ELSE 0 END,o.position,q.rowid DESC LIMIT 200",
                    (head.id if head else None, project_id, run_id),
                )
                if r["id"] in active
                or QuestionView.model_validate_json(r["data"]).status != "unresolved"
            ]

    @staticmethod
    def question(
        db: sqlite3.Connection, project_id: str, run_id: str, question_id: str
    ) -> QuestionView:
        row = db.execute(
            "SELECT data FROM questions WHERE id=? AND project_id=? AND run_id=?",
            (question_id, project_id, run_id),
        ).fetchone()
        if not row:
            raise NotFound("Question not found")
        return QuestionView.model_validate_json(row[0])

    @staticmethod
    def write_question(db: sqlite3.Connection, q: QuestionView) -> None:
        db.execute(
            "UPDATE questions SET data=? WHERE id=?", (q.model_dump_json(), q.id)
        )
        db.execute(
            "INSERT INTO question_events VALUES (?,?,?)",
            (q.id, q.version, q.model_dump_json()),
        )

    def save_answer(
        self,
        project_id: str,
        run_id: str,
        question_id: str,
        expected_version: int,
        text: str,
    ) -> AnswerVersion:
        body = AnswerInput(expected_version=expected_version, text=text)
        with self.store.transaction() as db:
            q = self.question(db, project_id, run_id, question_id)
            if q.version != body.expected_version:
                raise Conflict("Answer changed; reload before saving")
            if q.status in ("resolved", "dismissed"):
                raise Conflict("Reopen this question before changing its answer")
            source = Source(
                id=str(uuid4()),
                project_id=project_id,
                text=body.text,
                digest=digest(body.text),
            )
            db.execute(
                "INSERT INTO sources VALUES (?,?,?)",
                (source.id, project_id, source.model_dump_json()),
            )
            answer = AnswerVersion(
                question_id=q.id,
                version=q.version + 1,
                text=body.text,
                source_id=source.id,
                created_at=datetime.now(UTC).isoformat(),
            )
            db.execute(
                "INSERT INTO question_answers VALUES (?,?,?)",
                (q.id, answer.version, answer.model_dump_json()),
            )
            q = q.model_copy(
                update={
                    "version": answer.version,
                    "status": "answered",
                    "latest_answer": answer,
                    "resolution_revision_id": None,
                    "dismissal_reason": None,
                }
            )
            self.write_question(db, q)
            self.store.audit(db, project_id, "question_answered", q.id)
            return answer

    def answer_history(
        self,
        project_id: str,
        run_id: str,
        question_id: str,
        before: int = 2147483647,
        limit: int = 20,
    ) -> list[AnswerVersion]:
        with self.store.transaction() as db:
            self.question(db, project_id, run_id, question_id)
            return [
                AnswerVersion.model_validate_json(r[0])
                for r in db.execute(
                    "SELECT data FROM question_answers WHERE question_id=? AND version<? ORDER BY version DESC LIMIT ?",
                    (question_id, before, limit),
                )
            ]

    def set_question_status(
        self, project_id: str, run_id: str, question_id: str, body: StatusInput
    ) -> QuestionView:
        with self.store.transaction() as db:
            q = self.question(db, project_id, run_id, question_id)
            if q.version != body.expected_version:
                raise Conflict("Question changed; reload before updating")
            if q.status == "resolved":
                raise Conflict(
                    "Reopen resolved questions through an explicit working-draft change"
                )
            status = (
                "dismissed"
                if body.status == "dismissed"
                else ("answered" if q.latest_answer else "unresolved")
            )
            q = q.model_copy(
                update={
                    "version": q.version + 1,
                    "status": status,
                    "dismissal_reason": body.reason if status == "dismissed" else None,
                    "resolution_revision_id": None,
                }
            )
            self.write_question(db, q)
            self.store.audit(db, project_id, "question_status_changed", q.id)
            return q

    def requests(self, project_id: str, run_id: str) -> list[RequestView]:
        with self.store.transaction() as db:
            self.history.require_run(db, project_id, run_id)
            return [
                RequestView.model_validate_json(r[0])
                for r in db.execute(
                    "SELECT data FROM change_requests WHERE project_id=? AND run_id=? ORDER BY rowid DESC",
                    (project_id, run_id),
                )
            ]

    @staticmethod
    def targets(artifact: Artifact, targets: list[str]) -> None:
        permitted = {
            "title",
            "purpose",
            "scope",
            "non_goals",
            "requirements",
            "stories",
            "edge_cases",
            "dependencies",
            "risks",
            "success_metrics",
        } | {item.id for item in artifact.identified_items()}
        if set(targets) - permitted or len(set(targets)) != len(targets):
            raise ValueError("Choose distinct existing draft sections or item IDs")

    def create_request(
        self, project_id: str, run_id: str, body: RequestInput
    ) -> RequestView:
        comparison = self.history.compare(
            project_id, run_id, body.base_revision_id, body.base_revision_id
        )
        self.targets(comparison.base.artifact, body.target_ids)
        if not body.text.strip():
            raise ValueError("Describe the requested change")
        item = RequestView(**body.model_dump(), id=str(uuid4()))
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO change_requests VALUES (?,?,?,?)",
                (item.id, project_id, run_id, item.model_dump_json()),
            )
            db.execute(
                "INSERT INTO change_request_events VALUES (?,?,?)",
                (item.id, item.version, item.model_dump_json()),
            )
            self.store.audit(db, project_id, "change_requested", item.id)
        return item

    @staticmethod
    def request(
        db: sqlite3.Connection, project_id: str, run_id: str, request_id: str
    ) -> RequestView:
        row = db.execute(
            "SELECT data FROM change_requests WHERE id=? AND project_id=? AND run_id=?",
            (request_id, project_id, run_id),
        ).fetchone()
        if not row:
            raise NotFound("Requested change not found")
        return RequestView.model_validate_json(row[0])

    def set_request_status(
        self, project_id: str, run_id: str, request_id: str, body: StatusInput
    ) -> RequestView:
        with self.store.transaction() as db:
            item = self.request(db, project_id, run_id, request_id)
            if item.version != body.expected_version:
                raise Conflict("Requested change updated; reload before saving")
            item = item.model_copy(
                update={
                    "version": item.version + 1,
                    "status": "dismissed" if body.status == "dismissed" else "open",
                    "dismissal_reason": body.reason
                    if body.status == "dismissed"
                    else None,
                    "resolution_revision_id": None,
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
            self.store.audit(db, project_id, "change_request_status_changed", item.id)
            return item
