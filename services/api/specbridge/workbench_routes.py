"""Scoped authenticated collaboration routes; existing middleware remains authoritative."""

from fastapi import FastAPI, Query

from .storage import Store
from .workbench import Workbench
from .workbench_models import (
    AnswerInput,
    AnswerVersion,
    CommitInput,
    CommitReceipt,
    DiscardInput,
    QuestionView,
    RequestInput,
    RequestView,
    StatusInput,
    WorkingCopy,
    WorkingInput,
)
from .working_copy import WorkingDrafts


def register_workbench_routes(app: FastAPI, store: Store) -> None:
    service = Workbench(store)
    drafts = WorkingDrafts(service)
    prefix = "/api/projects/{project_id}/runs/{run_id}"

    @app.get(prefix + "/questions")
    def questions(project_id: str, run_id: str) -> list[QuestionView]:
        return service.questions(project_id, run_id)

    @app.post(prefix + "/questions/{question_id}/answers", status_code=201)
    def answer(
        project_id: str, run_id: str, question_id: str, body: AnswerInput
    ) -> AnswerVersion:
        return service.save_answer(
            project_id, run_id, question_id, body.expected_version, body.text
        )

    @app.get(prefix + "/questions/{question_id}/answers")
    def answers(
        project_id: str,
        run_id: str,
        question_id: str,
        before: int = Query(default=2147483647, ge=1),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> list[AnswerVersion]:
        return service.answer_history(project_id, run_id, question_id, before, limit)

    @app.post(prefix + "/questions/{question_id}/status")
    def question_status(
        project_id: str, run_id: str, question_id: str, body: StatusInput
    ) -> QuestionView:
        return service.set_question_status(project_id, run_id, question_id, body)

    @app.get(prefix + "/change-requests")
    def requests(project_id: str, run_id: str) -> list[RequestView]:
        return service.requests(project_id, run_id)

    @app.post(prefix + "/change-requests", status_code=201)
    def request_change(project_id: str, run_id: str, body: RequestInput) -> RequestView:
        return service.create_request(project_id, run_id, body)

    @app.post(prefix + "/change-requests/{request_id}/status")
    def request_status(
        project_id: str, run_id: str, request_id: str, body: StatusInput
    ) -> RequestView:
        return service.set_request_status(project_id, run_id, request_id, body)

    @app.get(prefix + "/working-copy")
    def working_copy(project_id: str, run_id: str) -> WorkingCopy | None:
        return drafts.get(project_id, run_id)

    @app.put(prefix + "/working-copy")
    def save_working_copy(
        project_id: str, run_id: str, body: WorkingInput
    ) -> WorkingCopy:
        return drafts.save(project_id, run_id, body)

    @app.delete(prefix + "/working-copy")
    def discard_working_copy(
        project_id: str, run_id: str, body: DiscardInput
    ) -> dict[str, bool]:
        drafts.discard(project_id, run_id, body.expected_version)
        return {"discarded": True}

    @app.post(prefix + "/commits", status_code=201)
    def commit(project_id: str, run_id: str, body: CommitInput) -> CommitReceipt:
        return drafts.commit(project_id, run_id, body)
