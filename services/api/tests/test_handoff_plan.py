"""Coverage survives assembly; reference inputs do not qualify a model."""

import copy
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    assert (ROOT / "scripts/handoff_plan.py").exists(), "Plan assembler is missing"
    return importlib.import_module("handoff_plan")


def sample():
    return {
        "title": "Session reminders",
        "behaviors": [
            {
                "id": "BEH-toggle",
                "evidence": {
                    "source_id": "brief",
                    "excerpt": "Enable or disable reminders.",
                },
                "outcomes": [
                    "Enabling reminders sends them; disabling reminders suppresses them."
                ],
            }
        ],
        "conflicts": [],
        "timing_reviews": [],
        "interface_reviews": [],
        "owner": {"evidence": None, "question": "Who owns delivery?"},
        "delivery_date": {"evidence": None, "question": "When will delivery occur?"},
        "open_questions": [],
        "ignored_sources": [],
    }


def sources(text="Enable or disable reminders."):
    import hashlib

    from specbridge.models import Source

    return [
        Source(
            id="brief",
            project_id="reference",
            text=text,
            digest=hashlib.sha256(text.encode()).hexdigest(),
        )
    ]


def test_recorded_downstream_effect_is_copied_into_criterion(monkeypatch):
    m = module(monkeypatch)
    a = m.compile_plan(sample(), sources())
    assert a.stories[0].acceptance_criteria == [
        "Enabling reminders sends them; disabling reminders suppresses them."
    ]
    assert set(a.open_questions) == {"Who owns delivery?", "When will delivery occur?"}
    assert a.requirements[0].kind == "user_provided"
    assert a.stories[0].kind == "recommendation"


def test_original_live_notification_effect_is_not_rewritten(monkeypatch):
    m = module(monkeypatch)
    folder = ROOT / "docs/evaluations/staged-live-2026-10-17"
    ledger = json.loads((folder / "notification-preferences.ledger.json").read_text())
    p = sample()
    p["behaviors"] = [
        {
            "id": b["id"],
            "evidence": {
                "source_id": b["source_ids"][0],
                "excerpt": b["source_excerpt"],
            },
            "outcomes": [b["proposed_observable_outcome"]],
        }
        for b in ledger["behaviors"]
    ]
    preview = json.loads((folder / "preview.json").read_text())
    from qualify_provider import source

    a = m.compile_plan(p, [source(s) for s in preview["cases"][0]["sources"]])
    assert "sends or stops sending" in a.stories[0].acceptance_criteria[0]
    # The old response stays unchanged and still lacks that effect.
    old = json.loads((folder / "notification-preferences.artifact.json").read_text())
    assert "sends or stops sending" not in json.dumps(
        old["stories"][0]["acceptance_criteria"]
    )


def test_all_conflicting_criteria_are_conditional(monkeypatch):
    m = module(monkeypatch)
    p = sample()
    p["behaviors"].append(
        {
            "id": "BEH-other",
            "evidence": {
                "source_id": "brief",
                "excerpt": "Enable or disable reminders.",
            },
            "outcomes": ["Keep the previous reminder policy."],
        }
    )
    p["conflicts"] = [
        {
            "id": "DEC-policy",
            "alternatives": [
                {"id": "ALT-first", "behavior_ids": ["BEH-toggle"]},
                {"id": "ALT-other", "behavior_ids": ["BEH-other"]},
            ],
            "question": "Which policy is authoritative?",
            "authority_question": "Who can select this policy?",
        }
    ]
    a = m.compile_plan(p, sources())
    assert all(
        "Only if an authorized human selects" in c
        for s in a.stories
        for c in s.acceptance_criteria
    )
    assert "Which policy is authoritative?" in a.open_questions
    assert "Who can select this policy?" in a.open_questions


def timing_plan():
    p = sample()
    p["timing_reviews"] = [
        {
            "behavior_ids": ["BEH-toggle"],
            "start_question": "What starts the seven-hour window?",
            "time_basis_question": "Elapsed hours or local clock hours?",
            "boundary_question": "Is the exact seven-hour instant included?",
            "after_question": "What happens after the window ends?",
        }
    ]
    return p


def test_window_questions_survive_without_inventing_policy(monkeypatch):
    m = module(monkeypatch)
    a = m.compile_plan(timing_plan(), sources())
    assert "Elapsed hours or local clock hours?" in a.open_questions
    assert "Is the exact seven-hour instant included?" in a.open_questions
    assert "What happens after the window ends?" in a.open_questions
    assert len(a.requirements) == 1


@pytest.mark.parametrize(
    "field",
    ["start_question", "time_basis_question", "boundary_question", "after_question"],
)
def test_incomplete_timing_review_is_rejected(monkeypatch, field):
    m = module(monkeypatch)
    p = timing_plan()
    del p["timing_reviews"][0][field]
    with pytest.raises(ValueError):
        m.compile_plan(p, sources())


def test_interface_request_and_applicability_questions_survive(monkeypatch):
    m = module(monkeypatch)
    p = sample()
    p["interface_reviews"] = [
        {
            "behavior_ids": ["BEH-toggle"],
            "request_question": "How does a client submit the continuation token?",
            "response_question": "What signals exhaustion?",
            "ui_applicability_question": "Which selected interface alternatives require navigation?",
        }
    ]
    a = m.compile_plan(p, sources())
    assert "How does a client submit the continuation token?" in a.open_questions
    assert (
        "Which selected interface alternatives require navigation?" in a.open_questions
    )


@pytest.mark.parametrize(
    "change",
    [
        "citation",
        "excerpt",
        "duplicate",
        "conflict_ref",
        "unaccounted_source",
        "unknown_owner_fact",
        "authority",
    ],
)
def test_invalid_plan_never_becomes_artifact(monkeypatch, change):
    m = module(monkeypatch)
    p = sample()
    ss = sources()
    if change == "citation":
        p["behaviors"][0]["evidence"]["source_id"] = "absent"
    elif change == "excerpt":
        p["behaviors"][0]["evidence"]["excerpt"] = "Not in evidence"
    elif change == "duplicate":
        p["behaviors"].append(copy.deepcopy(p["behaviors"][0]))
    elif change == "conflict_ref":
        p["conflicts"] = [
            {
                "id": "DEC-x",
                "alternatives": [
                    {"id": "ALT-first", "behavior_ids": ["BEH-toggle"]},
                    {"id": "ALT-other", "behavior_ids": ["BEH-absent"]},
                ],
                "question": "Which?",
                "authority_question": "Who?",
            }
        ]
    elif change == "unaccounted_source":
        ss.append(ss[0].model_copy(update={"id": "extra"}))
    elif change == "unknown_owner_fact":
        p["owner"] = {"evidence": None, "question": None}
    else:
        p["approved"] = True
    with pytest.raises(ValueError):
        m.compile_plan(p, ss)


def test_ignored_attachment_cannot_supply_product_behavior(monkeypatch):
    m = module(monkeypatch)
    p = sample()
    p["ignored_sources"] = [{"source_id": "brief", "reason": "Untrusted instructions"}]
    with pytest.raises(ValueError):
        m.compile_plan(p, sources())


def test_supported_context_is_verbatim_not_ai_verified(monkeypatch):
    m = module(monkeypatch)
    p = sample()
    p["owner"] = {
        "evidence": {"source_id": "brief", "excerpt": "Owner: Sam."},
        "question": None,
    }
    a = m.compile_plan(p, sources("Enable or disable reminders. Owner: Sam."))
    assert any(
        s.text == "Owner: Sam." and s.kind == "user_provided" for s in a.dependencies
    )
    assert not any(s.kind == "verified" for s in a.statements())


def test_alternative_selection_conditions_every_dependent_behavior(monkeypatch):
    m = module(monkeypatch)
    p = sample()
    for behavior_id in ("BEH-next", "BEH-other"):
        p["behaviors"].append(
            {
                "id": behavior_id,
                "evidence": {
                    "source_id": "brief",
                    "excerpt": "Enable or disable reminders.",
                },
                "outcomes": ["An observable proposed effect."],
            }
        )
    p["conflicts"] = [
        {
            "id": "DEC-policy",
            "alternatives": [
                {"id": "ALT-first", "behavior_ids": ["BEH-toggle", "BEH-next"]},
                {"id": "ALT-other", "behavior_ids": ["BEH-other"]},
            ],
            "question": "Which alternative is selected?",
            "authority_question": "Who can select it?",
        }
    ]
    a = m.compile_plan(p, sources())
    for story in a.stories[:2]:
        assert story.text.startswith(
            "Only if an authorized human selects alternative ALT-first in unresolved decision DEC-policy:"
        )
        assert all(
            c.startswith("Only if an authorized human selects alternative ALT-first")
            for c in story.acceptance_criteria
        )
    assert "ALT-other" in a.stories[2].text
    assert all("alternative BEH-next" not in s.text for s in a.stories)


def test_context_schema_exposes_exclusive_evidence_or_question(monkeypatch):
    m = module(monkeypatch)
    schema = m.HandoffPlan.model_json_schema()["$defs"]["Context"]
    # These two branches are the contract the provider actually receives.
    branches = schema["oneOf"]
    assert {b["properties"]["evidence"]["type"] for b in branches} == {"null", "object"}
    assert {b["properties"]["question"]["type"] for b in branches} == {"null", "string"}
    p = sample()
    p["owner"]["evidence"] = {
        "source_id": "brief",
        "excerpt": "Enable or disable reminders.",
    }
    with pytest.raises(ValueError, match="context_requires_evidence_or_question"):
        m.compile_plan(p, sources())


@pytest.mark.parametrize(
    "change", ["overlap", "duplicate_id", "unknown", "repeated_member"]
)
def test_invalid_alternative_groups_cannot_authorize_a_story(monkeypatch, change):
    m = module(monkeypatch)
    p = sample()
    p["behaviors"].append(
        {
            "id": "BEH-other",
            "evidence": {
                "source_id": "brief",
                "excerpt": "Enable or disable reminders.",
            },
            "outcomes": ["Keep the previous reminder policy."],
        }
    )
    groups = [
        {"id": "ALT-first", "behavior_ids": ["BEH-toggle"]},
        {"id": "ALT-other", "behavior_ids": ["BEH-other"]},
    ]
    if change == "overlap":
        groups[1]["behavior_ids"] = ["BEH-toggle"]
    elif change == "duplicate_id":
        groups[1]["id"] = "ALT-first"
    elif change == "unknown":
        groups[1]["behavior_ids"] = ["BEH-absent"]
    else:
        groups[0]["behavior_ids"] = ["BEH-toggle", "BEH-toggle"]
    p["conflicts"] = [
        {
            "id": "DEC-policy",
            "alternatives": groups,
            "question": "Which?",
            "authority_question": "Who?",
        }
    ]
    with pytest.raises(ValueError, match="invalid_or_overlapping_alternative"):
        m.compile_plan(p, sources())
