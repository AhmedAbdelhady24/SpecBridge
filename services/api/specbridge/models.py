import hashlib
import json
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1, max_length=16384)]


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Statement(Model):
    text: Text
    source_ids: list[str] = Field(default_factory=list, max_length=20)
    kind: Literal[
        "user_provided", "verified", "recommendation", "assumption", "unknown"
    ] = "recommendation"


class Requirement(Statement):
    id: str = Field(pattern=r"^REQ-[a-zA-Z0-9-]{1,64}$")


class Story(Statement):
    id: str = Field(pattern=r"^STORY-[a-zA-Z0-9-]{1,64}$")
    requirement_ids: list[str] = Field(min_length=1, max_length=100)
    acceptance_criteria: list[Text] = Field(min_length=1, max_length=30)


class Artifact(Model):
    title: str = Field(min_length=1, max_length=200)
    purpose: Text
    scope: list[Statement] = Field(max_length=100)
    non_goals: list[Statement] = Field(max_length=100)
    requirements: list[Requirement] = Field(min_length=1, max_length=100)
    stories: list[Story] = Field(min_length=1, max_length=100)
    edge_cases: list[Statement] = Field(max_length=100)
    dependencies: list[Statement] = Field(max_length=100)
    risks: list[Statement] = Field(max_length=100)
    success_metrics: list[Statement] = Field(max_length=100)
    open_questions: list[Text] = Field(max_length=100)

    def identified_items(self) -> list[Requirement | Story]:
        return [*self.requirements, *self.stories]

    def statements(self) -> list[Statement]:
        return [
            *self.scope,
            *self.non_goals,
            *self.requirements,
            *self.stories,
            *self.edge_cases,
            *self.dependencies,
            *self.risks,
            *self.success_metrics,
        ]

    @model_validator(mode="after")
    def check_links(self) -> Self:
        requirements = {item.id for item in self.requirements}
        if len(requirements) != len(self.requirements) or len(
            {s.id for s in self.stories}
        ) != len(self.stories):
            raise ValueError("Artifact IDs must be unique")
        if any(set(story.requirement_ids) - requirements for story in self.stories):
            raise ValueError("Story references an absent requirement")
        return self


class Project(Model):
    id: str
    name: str


class Source(Model):
    id: str
    project_id: str
    text: str
    digest: str
    kind: Literal["user_provided"] = "user_provided"


class Finding(Model):
    code: str
    message: str
    severity: Literal["warning", "error"] = "warning"


class Revision(Model):
    id: str
    project_id: str
    number: int
    digest: str
    artifact: Artifact
    findings: list[Finding] = Field(default_factory=list)
    provenance: dict[str, str] = Field(default_factory=dict)


class Run(Model):
    id: str
    project_id: str
    source_ids: list[str]
    skill_id: str
    intent: str
    destination: str
    stage: str
    status: Literal["ready", "running", "failed", "review", "published"] = "ready"
    revision_id: str | None = None
    error: str | None = None
    attempts: int = 0
    history: list[str] = Field(default_factory=list)
    base_digest: str | None = None


class RunCreate(Model):
    source_ids: list[str] = Field(min_length=1, max_length=20)
    skill_id: str = Field(min_length=1, max_length=64)
    intent: str = Field(min_length=1, max_length=2000)
    acknowledged_destination: str


class AdvanceRequest(Model):
    retry_acknowledged: bool = False


class ReviewCreate(Model):
    disposition: Literal["reviewed", "rejected"]
    notes: str = Field(max_length=16384)


class ApprovalCreate(Model):
    digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class Candidate(Model):
    id: str
    project_id: str
    revision_id: str
    digest: str
    template_digest: str
    manifest: dict[str, str]
    approved: bool = False


class Review(Model):
    id: str
    project_id: str
    revision_id: str
    disposition: Literal["reviewed", "rejected"]
    notes: str


class ProviderInfo(Model):
    provider: Literal["fixture", "compatible"]
    model: str
    destination: str


class ProjectCreate(Model):
    name: str = Field(min_length=1, max_length=200)


class SourceCreate(Model):
    text: str = Field(min_length=1, max_length=32768)


class RevisionEdit(Model):
    expected_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact: Artifact
