"""Offline graph guarantees and semantic counterexamples; never model acceptance."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def probe():
    path = ROOT / "scripts/probe_consistency.py"
    assert path.exists(), "Offline consistency probe is missing"
    spec = importlib.util.spec_from_file_location("consistency_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def specimen(module, case_id="contradictory-deletion"):
    artifact, sources = module.saved_case(case_id)
    # Deliberately naive declaration: valid links do not prove semantic coverage.
    graph = module.untrusted_declaration(artifact, sources)
    graph["decisions"] = [
        {
            "id": "DEC-1",
            "question_index": 0,
            "options": ["first-alternative", "second-alternative"],
        }
    ]
    graph["criteria"][0]["decision_ids"] = ["DEC-1"]
    graph["criteria"][0]["guards"] = [
        {"decision_id": "DEC-1", "option_id": "first-alternative"}
    ]
    return artifact, sources, graph


def test_declared_guarded_graph_accepts_matching_alternative():
    module = probe()
    artifact, sources, graph = specimen(module)
    before = artifact.model_dump_json()
    module.validate_declarations(artifact, sources, graph)
    graph["criteria"][0]["guards"][0]["option_id"] = "second-alternative"
    # Both declared options exist. Whether prose matches the choice is not inferred.
    module.validate_declarations(artifact, sources, graph)
    assert artifact.model_dump_json() == before


@pytest.mark.parametrize(
    "mutation",
    [
        "stale_artifact",
        "stale_source",
        "absent_story",
        "absent_criterion",
        "absent_requirement",
        "wrong_story_requirement",
        "missing_criterion",
        "duplicate_criterion",
        "missing_guard",
        "absent_decision",
        "absent_option",
        "duplicate_decision",
        "absent_question",
        "uncovered_requirement",
        "self_approval",
    ],
)
def test_invalid_declared_graph_is_rejected(mutation):
    module = probe()
    artifact, sources, graph = specimen(module)
    row = graph["criteria"][0]
    if mutation == "stale_artifact":
        graph["artifact_digest"] = "0" * 64
    elif mutation == "stale_source":
        graph["source_digests"][sources[0].id] = "0" * 64
    elif mutation == "absent_story":
        row["story_id"] = "STORY-absent"
    elif mutation == "absent_criterion":
        row["criterion_index"] = 50
    elif mutation == "absent_requirement":
        row["requirement_ids"] = ["REQ-absent"]
    elif mutation == "wrong_story_requirement":
        row["requirement_ids"] = [artifact.stories[1].requirement_ids[0]]
    elif mutation == "missing_criterion":
        graph["criteria"].pop()
    elif mutation == "duplicate_criterion":
        graph["criteria"].append(copy.deepcopy(row))
    elif mutation == "missing_guard":
        row["guards"] = []
    elif mutation == "absent_decision":
        graph["decisions"] = []
    elif mutation == "absent_option":
        row["guards"][0]["option_id"] = "invented"
    elif mutation == "duplicate_decision":
        graph["decisions"].append(copy.deepcopy(graph["decisions"][0]))
    elif mutation == "absent_question":
        graph["decisions"][0]["question_index"] = 99
    elif mutation == "uncovered_requirement":
        # API story 1 implements two requirements; declaring only one leaves a gap.
        artifact, sources = module.saved_case("conflicting-api")
        graph = module.untrusted_declaration(artifact, sources)
        for criterion in graph["criteria"]:
            if criterion["story_id"] == artifact.stories[0].id:
                criterion["requirement_ids"] = [artifact.stories[0].requirement_ids[0]]
    elif mutation == "self_approval":
        graph["approved"] = True
    with pytest.raises(ValueError):
        module.validate_declarations(artifact, sources, graph)


@pytest.mark.parametrize(
    "case_id",
    [
        "notification-preferences",
        "contradictory-deletion",
        "conflicting-api",
    ],
)
def test_known_semantic_failures_survive_valid_graphs(case_id):
    module = probe()
    artifact, sources = module.saved_case(case_id)
    graph = module.untrusted_declaration(artifact, sources)
    module.validate_declarations(artifact, sources, graph)
    review = json.loads(
        (
            ROOT
            / "docs/evaluations/reasoning-low-comparison-2026-10-16/semantic-review.json"
        ).read_text()
    )
    assert review["cases"][case_id]["status"] == "fail"
    assert graph["decisions"] == []  # Undeclared dependencies cannot be inferred.


def test_report_preserves_failure_counts_and_frozen_evidence():
    module = probe()
    report = module.run_probe()
    assert report["network_calls"] == 0
    assert report["production_adoption"] == "not_justified_by_this_probe"
    assert len(report["counterexamples"]) == 3
    assert all(
        row["declared_graph"] == "valid" and row["semantic_result"] == "fail"
        for row in report["counterexamples"]
    )
    assert len(report["evidence_sha256"]) == 6
