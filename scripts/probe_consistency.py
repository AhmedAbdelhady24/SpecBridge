"""Offline falsification probe, NOT a runtime schema or semantic quality gate.

Run with PYTHONPATH=services/api .venv/bin/python scripts/probe_consistency.py.
No provider, environment credentials, network, persistence or approval operations.
"""

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field
from specbridge.models import Artifact, Model, Source, digest, validate_handoff

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evaluations/reasoning-low-comparison-2026-10-16"
Nonempty = Annotated[str, Field(min_length=1, max_length=200)]


class Decision(Model):
    id: Nonempty
    question_index: int = Field(ge=0)
    options: list[Nonempty] = Field(min_length=1, max_length=20)


class Guard(Model):
    decision_id: Nonempty
    option_id: Nonempty


class CriterionLinks(Model):
    story_id: Nonempty
    criterion_index: int = Field(ge=0)
    requirement_ids: list[Nonempty] = Field(min_length=1, max_length=100)
    decision_ids: list[Nonempty] = Field(max_length=100)
    guards: list[Guard] = Field(max_length=100)


class Declaration(Model):
    schema_version: Literal[1]
    artifact_digest: str
    source_digests: dict[str, str]
    decisions: list[Decision] = Field(max_length=100)
    criteria: list[CriterionLinks] = Field(max_length=3000)


def validate_declarations(
    artifact: Artifact, sources: list[Source], value: dict
) -> None:
    """Validate DECLARED graph structure; prose and omitted dependencies are opaque."""
    graph = Declaration.model_validate(value)
    validate_handoff(artifact, sources)
    source_digests = {
        s.id: hashlib.sha256(s.text.encode()).hexdigest() for s in sources
    }
    if graph.artifact_digest != digest(artifact.model_dump()) or (
        graph.source_digests != source_digests or len(source_digests) != len(sources)
    ):
        raise ValueError("stale_evidence")
    decisions = {decision.id: decision for decision in graph.decisions}
    if len(decisions) != len(graph.decisions):
        raise ValueError("duplicate_decision")
    for decision in decisions.values():
        if decision.question_index >= len(artifact.open_questions) or len(
            set(decision.options)
        ) != len(decision.options):
            raise ValueError("invalid_decision")
    stories = {story.id: story for story in artifact.stories}
    expected = {
        (s.id, index)
        for s in artifact.stories
        for index in range(len(s.acceptance_criteria))
    }
    seen: set[tuple[str, int]] = set()
    coverage: dict[str, set[str]] = {s.id: set() for s in artifact.stories}
    for criterion in graph.criteria:
        coordinate = (criterion.story_id, criterion.criterion_index)
        if coordinate not in expected or coordinate in seen:
            raise ValueError("invalid_criterion_coordinate")
        seen.add(coordinate)
        requirements = set(criterion.requirement_ids)
        if len(requirements) != len(criterion.requirement_ids) or requirements - set(
            stories[criterion.story_id].requirement_ids
        ):
            raise ValueError("invalid_requirement_link")
        coverage[criterion.story_id].update(requirements)
        dependencies = set(criterion.decision_ids)
        guard_ids = [guard.decision_id for guard in criterion.guards]
        if len(dependencies) != len(criterion.decision_ids) or (
            set(guard_ids) != dependencies or len(guard_ids) != len(dependencies)
        ):
            raise ValueError("missing_or_duplicate_guard")
        for guard in criterion.guards:
            decision = decisions.get(guard.decision_id)
            if decision is None or guard.option_id not in decision.options:
                raise ValueError("invalid_guard_reference")
    if seen != expected or any(
        coverage[story.id] != set(story.requirement_ids) for story in artifact.stories
    ):
        raise ValueError("incomplete_criterion_coverage")


def saved_case(case_id: str) -> tuple[Artifact, list[Source]]:
    cases = json.loads(
        (ROOT / "tests/fixtures/provider-qualification/cases.json").read_text()
    )
    case = next(case for case in cases if case["id"] == case_id)
    sources = [
        Source(
            **source,
            project_id="offline-probe",
            digest=hashlib.sha256(source["text"].encode()).hexdigest(),
        )
        for source in case["sources"]
    ]
    artifact = Artifact.model_validate_json((EVIDENCE / f"{case_id}.json").read_text())
    return artifact, sources


def untrusted_declaration(artifact: Artifact, sources: list[Source]) -> dict:
    """DELIBERATELY dishonest baseline: all story links copied, dependencies omitted.

    Never use this to assess coverage or to annotate real handoffs. Its purpose is
    to falsify the claim that reference integrity proves semantic correctness.
    """
    return {
        "schema_version": 1,
        "artifact_digest": digest(artifact.model_dump()),
        "source_digests": {
            s.id: hashlib.sha256(s.text.encode()).hexdigest() for s in sources
        },
        "decisions": [],
        "criteria": [
            {
                "story_id": s.id,
                "criterion_index": i,
                "requirement_ids": s.requirement_ids,
                "decision_ids": [],
                "guards": [],
            }
            for s in artifact.stories
            for i in range(len(s.acceptance_criteria))
        ],
    }


def run_probe() -> dict:
    review_path = EVIDENCE / "semantic-review.json"
    review = json.loads(review_path.read_text())
    cases = ["notification-preferences", "contradictory-deletion", "conflicting-api"]
    counterexamples = []
    paths = [
        review_path,
        ROOT / "tests/fixtures/provider-qualification/cases.json",
        ROOT / "tests/fixtures/provider-qualification/acceptance.json",
    ]
    for case_id in cases:
        artifact, sources = saved_case(case_id)
        validate_declarations(
            artifact, sources, untrusted_declaration(artifact, sources)
        )
        counterexamples.append(
            {
                "case": case_id,
                "declared_graph": "valid",
                "semantic_result": review["cases"][case_id]["status"],
                "findings": review["cases"][case_id]["findings"],
            }
        )
        paths.append(EVIDENCE / f"{case_id}.json")
    return {
        "scope": "offline declared-link falsification only",
        "network_calls": 0,
        "production_adoption": "not_justified_by_this_probe",
        "counterexamples": counterexamples,
        "evidence_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_probe(), indent=2))
