"""Evaluation-only typed plan -> Artifact, with no generative rewrite or authority."""

from typing import Annotated, Any, ClassVar

from pydantic import ConfigDict, Field, StringConstraints, model_validator
from specbridge.models import Artifact, Model, Source
from specbridge.providers import validate_artifact, validate_sources

Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4096)
]
IDs = Annotated[list[Text], Field(min_length=1, max_length=100)]


class Evidence(Model):
    source_id: Text
    excerpt: Text


class PlanBehavior(Model):
    id: str = Field(pattern=r"^BEH-[a-zA-Z0-9-]{1,64}$")
    evidence: Evidence
    outcomes: list[Text] = Field(min_length=1, max_length=30)


class Alternative(Model):
    id: str = Field(pattern=r"^ALT-[a-zA-Z0-9-]{1,64}$")
    behavior_ids: IDs


class Conflict(Model):
    id: str = Field(pattern=r"^DEC-[a-zA-Z0-9-]{1,64}$")
    alternatives: list[Alternative] = Field(min_length=2, max_length=20)
    question: Text
    authority_question: Text


class TimingReview(Model):
    behavior_ids: IDs
    start_question: Text
    time_basis_question: Text
    boundary_question: Text
    after_question: Text


class InterfaceReview(Model):
    behavior_ids: IDs
    request_question: Text
    response_question: Text
    ui_applicability_question: Text


class Context(Model):
    model_config: ClassVar[ConfigDict] = {
        "json_schema_extra": {
            "oneOf": [
                {
                    "properties": {
                        "evidence": {"type": "object"},
                        "question": {"type": "null"},
                    }
                },
                {
                    "properties": {
                        "evidence": {"type": "null"},
                        "question": {"type": "string"},
                    }
                },
            ]
        }
    }
    evidence: Evidence | None
    question: Text | None

    @model_validator(mode="after")
    def evidence_or_question(self):
        if (self.evidence is None) == (self.question is None):
            raise ValueError("context_requires_evidence_or_question")
        return self


class IgnoredSource(Model):
    source_id: Text
    reason: Text


class HandoffPlan(Model):
    title: str = Field(min_length=1, max_length=200)
    behaviors: list[PlanBehavior] = Field(min_length=1, max_length=100)
    conflicts: list[Conflict] = Field(max_length=20)
    timing_reviews: list[TimingReview] = Field(max_length=20)
    interface_reviews: list[InterfaceReview] = Field(max_length=20)
    owner: Context
    delivery_date: Context
    open_questions: list[Text] = Field(max_length=100)
    ignored_sources: list[IgnoredSource] = Field(max_length=20)


def compile_plan(value: Any, sources: list[Source]) -> Artifact:
    """Preserve recorded coverage, not a claim of source completeness or approval."""
    validate_sources(sources)
    p = HandoffPlan.model_validate(value)
    source_text = {s.id: s.text for s in sources}
    behaviors = {b.id: b for b in p.behaviors}
    if len(behaviors) != len(p.behaviors):
        raise ValueError("duplicate_behavior")
    evidence = [b.evidence for b in p.behaviors] + [
        c.evidence for c in (p.owner, p.delivery_date) if c.evidence is not None
    ]
    for e in evidence:
        if e.source_id not in source_text or e.excerpt not in source_text[e.source_id]:
            raise ValueError("invalid_evidence")
    used = {e.source_id for e in evidence}
    ignored = {s.source_id for s in p.ignored_sources}
    if (
        len(ignored) != len(p.ignored_sources)
        or ignored & used
        or used | ignored != set(source_text)
    ):
        raise ValueError("unaccounted_or_reused_source")
    groups = {}
    conflict_ids = set()
    questions = list(p.open_questions)
    for c in [*p.timing_reviews, *p.interface_reviews]:
        if (
            len(set(c.behavior_ids)) != len(c.behavior_ids)
            or not set(c.behavior_ids) <= behaviors.keys()
        ):
            raise ValueError("invalid_behavior_reference")
        questions.extend(v for k, v in c.model_dump().items() if k.endswith("question"))
    for c in p.conflicts:
        if c.id in conflict_ids:
            raise ValueError("overlapping_or_duplicate_conflict")
        conflict_ids.add(c.id)
        alternative_ids = set()
        for alternative in c.alternatives:
            ids = alternative.behavior_ids
            if (
                alternative.id in alternative_ids
                or len(set(ids)) != len(ids)
                or not set(ids) <= behaviors.keys()
                or groups.keys() & set(ids)
            ):
                raise ValueError("invalid_or_overlapping_alternative")
            alternative_ids.add(alternative.id)
            groups.update({i: (c.id, alternative.id) for i in ids})
        questions.extend([c.question, c.authority_question])
    dependencies = []
    for c in (p.owner, p.delivery_date):
        if c.question is not None:
            questions.append(c.question)
        else:
            dependencies.append(
                {
                    "text": c.evidence.excerpt,
                    "kind": "user_provided",
                    "source_ids": [c.evidence.source_id],
                }
            )
    requirements, stories = [], []
    for index, b in enumerate(p.behaviors, 1):
        ids = [b.evidence.source_id]
        condition = (
            f"Only if an authorized human selects alternative {groups[b.id][1]} in unresolved decision {groups[b.id][0]}: "
            if b.id in groups
            else ""
        )
        requirements.append(
            {
                "id": f"REQ-{index}",
                "text": b.evidence.excerpt,
                "source_ids": ids,
                "kind": "user_provided",
            }
        )
        stories.append(
            {
                "id": f"STORY-{index}",
                "requirement_ids": [f"REQ-{index}"],
                "text": condition + b.evidence.excerpt,
                "source_ids": ids,
                "kind": "recommendation",
                "acceptance_criteria": [condition + outcome for outcome in b.outcomes],
            }
        )
    artifact = Artifact.model_validate(
        {
            "title": p.title,
            "purpose": "Proposed handoff assembled from source-linked outcomes; human source review and approval required.",
            "scope": [
                {
                    "text": b.evidence.excerpt,
                    "source_ids": [b.evidence.source_id],
                    "kind": "user_provided",
                }
                for b in p.behaviors
            ],
            "non_goals": [],
            "requirements": requirements,
            "stories": stories,
            "edge_cases": [],
            "dependencies": dependencies,
            "risks": [],
            "success_metrics": [],
            "open_questions": list(dict.fromkeys(questions)),
        }
    )
    return validate_artifact(artifact, sources)
