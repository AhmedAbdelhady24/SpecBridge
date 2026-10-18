"""Collaboration metadata is separate from immutable generated artifact schemas."""

from typing import Annotated, Literal

from pydantic import Field, field_validator

from .models import Artifact, Model, Text

Id = Annotated[str, Field(min_length=1, max_length=128)]
Version = Annotated[int, Field(ge=0)]


class AnswerVersion(Model):
    question_id: str
    version: int
    text: Text
    source_id: str
    created_at: str


class QuestionView(Model):
    id: str
    text: str
    origin_revision_id: str
    origin_index: int
    version: int = 0
    status: Literal["unresolved", "answered", "dismissed", "resolved"] = "unresolved"
    latest_answer: AnswerVersion | None = None
    resolution_revision_id: str | None = None
    dismissal_reason: str | None = None
    in_current_draft: bool = True
    current_index: int | None = None


class AnswerInput(Model):
    expected_version: Version
    text: Text

    @field_validator("text")
    @classmethod
    def substantive(cls, value: str) -> str:
        if not value.strip() or len(value.encode()) > 32768:
            raise ValueError("Answer must contain 1–32768 UTF-8 bytes")
        return value


class StatusInput(Model):
    expected_version: Version
    status: Literal["dismissed", "unanswered"]
    reason: Text

    @field_validator("reason")
    @classmethod
    def substantive(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Explain this status change")
        return value


class RequestInput(Model):
    base_revision_id: Id
    text: Text
    target_ids: list[Id] = Field(default_factory=list, max_length=100)


class RequestView(RequestInput):
    id: str
    version: int = 0
    status: Literal["open", "dismissed", "addressed"] = "open"
    resolution_revision_id: str | None = None
    dismissal_reason: str | None = None


class QuestionChange(Model):
    question_id: Id
    expected_question_version: Version
    answer_version: Version
    action: Literal["resolve", "reopen"] = "resolve"
    targets: list[Id] = Field(min_length=1, max_length=100)


class RequestChange(Model):
    request_id: Id
    expected_version: Version


class WorkingInput(Model):
    expected_version: Version
    base_revision_id: Id
    base_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact: Artifact
    question_changes: list[QuestionChange] = Field(default_factory=list, max_length=100)
    request_changes: list[RequestChange] = Field(default_factory=list, max_length=100)
    change_summary: str = Field(default="", max_length=2000)


class WorkingCopy(WorkingInput):
    version: int


class CommitInput(Model):
    working_copy_version: Annotated[int, Field(ge=1)]
    idempotency_key: str = Field(
        pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    )


class CommitReceipt(Model):
    working_copy_version: int
    revision_id: str
    feature_number: int | None
    idempotency_key: str


class DiscardInput(Model):
    expected_version: Version
