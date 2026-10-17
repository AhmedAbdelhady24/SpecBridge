"""Evaluation-only staged generation authorization and data boundaries."""

import importlib.util
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]


def runner(monkeypatch):
    path = ROOT / "scripts/qualify_staged.py"
    assert path.exists(), "The staged evaluation runner is not implemented"
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("staged", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("SPECBRIDGE_LLM_BASE_URL", "https://model.example/v1")
    monkeypatch.setenv("SPECBRIDGE_LLM_MODEL", "synthetic-test")
    monkeypatch.setenv("SPECBRIDGE_LLM_OUTPUT_MODE", "json_object")
    monkeypatch.setenv("SPECBRIDGE_LLM_TIMEOUT_SECONDS", "none")
    return module


def ledger(preview):
    source = preview["cases"][0]["sources"][0]
    return {
        "kind": "recommendation",
        "behaviors": [
            {
                "id": "BEH-1",
                "source_ids": [source["id"]],
                "source_excerpt": source["text"],
                "proposed_observable_outcome": "The requested behavior can be observed after the triggering action.",
            }
        ],
        "open_decisions": [],
    }


def envelope(content):
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(content),
                    "reasoning_content": "DO-NOT-STORE-REASONING",
                },
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


def test_staged_preview_is_offline_keyless_and_bounded(monkeypatch):
    module = runner(monkeypatch)
    monkeypatch.delenv("SPECBRIDGE_LLM_API_KEY", raising=False)

    async def forbidden(*args, **kwargs):
        pytest.fail("Preview attempted network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)
    preview = module.prepare(omit_output_cap=True)
    assert preview["maximum_calls"] == 10
    assert preview["retries"] == 0
    assert preview["generation_timeout_seconds"] is None
    assert len(preview["cases"]) == 5
    for case in preview["cases"]:
        assert "review_criteria" not in case
        assert "max_tokens" not in case["analysis_request"]["body"]
        assert "max_completion_tokens" not in case["analysis_request"]["body"]
        assert case["stage2_template"]["ledger_context"] == "VALIDATED_LEDGER_JSON"


@pytest.mark.parametrize("change", ["approval", "config", "source", "skill", "target"])
def test_staged_preview_mismatch_prevents_output_and_requests(
    monkeypatch, tmp_path, change
):
    module = runner(monkeypatch)
    preview = module.prepare(case_ids=["incomplete-booking"])
    approval = module.preview_digest(preview)
    if change == "approval":
        approval = "wrong"
    elif change == "config":
        monkeypatch.setenv("SPECBRIDGE_LLM_REASONING_EFFORT", "high")
    elif change == "source":
        preview["cases"][0]["sources"][0]["text"] += " changed"
    elif change == "skill":
        preview["analysis_skill_digest"] = "wrong"
    else:
        preview["cases"][0]["analysis_request"]["url"] = "https://other.example"
    if change in {"source", "skill", "target"}:
        approval = module.preview_digest(preview)
    requests = []

    async def forbidden(*args, **kwargs):
        requests.append(True)
        pytest.fail("Mismatch attempted network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)
    output = tmp_path / "evidence"
    with pytest.raises(ValueError, match="preview_mismatch"):
        module.execute(preview, approval, output)
    assert not output.exists() and not requests


@pytest.mark.parametrize(
    "fault",
    [
        "authority",
        "excerpt",
        "source",
        "behavior-ref",
        "duplicate",
        "alternative",
        "blank",
    ],
)
def test_analysis_ledger_rejects_unsupported_authority_and_provenance(
    monkeypatch, fault
):
    module = runner(monkeypatch)
    preview = module.prepare(case_ids=["incomplete-booking"])
    candidate = ledger(preview)
    if fault == "authority":
        candidate["approved"] = True
    elif fault == "excerpt":
        candidate["behaviors"][0]["source_excerpt"] = "Invented requirement"
    elif fault == "source":
        candidate["behaviors"][0]["source_ids"] = ["foreign"]
    elif fault == "duplicate":
        candidate["behaviors"] *= 2
    elif fault == "blank":
        candidate["behaviors"][0]["proposed_observable_outcome"] = " "
    else:
        candidate["open_decisions"] = [
            {
                "question": "Which behavior applies?",
                "source_ids": [preview["cases"][0]["sources"][0]["id"]],
                "affected_behavior_ids": [
                    "MISSING" if fault == "behavior-ref" else "BEH-1"
                ],
                "alternatives": ["Option A", "Option A"]
                if fault == "alternative"
                else ["Option A", "Option B"],
            }
        ]
    with pytest.raises((ValueError, ValidationError)):
        module.validate_ledger(
            candidate, [module.source(s) for s in preview["cases"][0]["sources"]]
        )


def test_invalid_analysis_stops_before_drafting(monkeypatch, tmp_path):
    module = runner(monkeypatch)
    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "private-test-key")
    preview = module.prepare(case_ids=["incomplete-booking"])
    calls = []

    async def handler(self, request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json=envelope({"approved": True}), request=request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", handler)
    output = tmp_path / "evidence"
    result = module.execute(preview, module.preview_digest(preview), output)
    assert len(calls) == 1
    assert result["results"][0]["analysis"]["status"] == "invalid_analysis"
    assert result["results"][0]["draft"] is None
    assert not list(output.glob("*.artifact.json"))


def test_mocked_two_stage_keeps_original_sources_and_sanitized_evidence(
    monkeypatch, tmp_path
):
    module = runner(monkeypatch)
    from specbridge.providers import FixtureProvider

    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "private-test-key")
    preview = module.prepare(case_ids=["incomplete-booking"], omit_output_cap=True)
    candidate = ledger(preview)
    sources = [module.source(s) for s in preview["cases"][0]["sources"]]
    artifact = FixtureProvider().generate(skill=module.active_skill(), sources=sources)
    calls = []

    async def handler(self, request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            assert body == preview["cases"][0]["analysis_request"]["body"]
            content = candidate
        else:
            context = json.loads(body["messages"][-1]["content"])
            assert context["original_sources"] == preview["cases"][0]["sources"]
            assert context["untrusted_provisional_ledger"] == candidate
            assert "review_criteria" not in json.dumps(body)
            content = artifact.model_dump()
        return httpx.Response(200, json=envelope(content), request=request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", handler)
    output = tmp_path / "evidence"
    result = module.execute(preview, module.preview_digest(preview), output)
    assert len(calls) == 2
    assert result["results"][0]["draft"]["status"] == "validated"
    stored_request = json.loads(
        (output / "incomplete-booking.stage2-request.json").read_text()
    )
    assert stored_request["body"] == calls[1]
    assert result["results"][0]["draft"]["request_sha256"] == module.preview_digest(
        calls[1]
    )
    evidence = "".join(path.read_text() for path in output.iterdir())
    assert "DO-NOT-STORE-REASONING" not in evidence
    assert "private-test-key" not in evidence
    assert result["results"][0]["analysis"]["usage"]["total_tokens"] == 30
    assert {s for statement in artifact.statements() for s in statement.source_ids} == {
        sources[0].id
    }
    with pytest.raises(FileExistsError):
        module.execute(preview, module.preview_digest(preview), output)
    assert len(calls) == 2


@pytest.mark.parametrize(
    "fault", ["length", "tool", "refusal", "secret", "oversize", "deep", "transport"]
)
def test_stage_one_response_failures_never_retry_or_draft(monkeypatch, tmp_path, fault):
    module = runner(monkeypatch)
    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "private-test-key")
    preview = module.prepare(case_ids=["incomplete-booking"])
    calls = []

    async def handler(self, request):
        calls.append(True)
        if fault == "transport":
            raise httpx.ReadError("private-test-key")
        if fault == "oversize":
            return httpx.Response(200, content=b"x" * 262145, request=request)
        if fault == "deep":
            return httpx.Response(
                200, content="[" * 10000 + "]" * 10000, request=request
            )
        content = envelope(ledger(preview))
        if fault == "length":
            content["choices"][0]["finish_reason"] = "length"
        elif fault == "tool":
            content["choices"][0]["message"]["tool_calls"] = [
                {"function": {"name": "shell"}}
            ]
        elif fault == "refusal":
            content["choices"][0]["message"]["refusal"] = "declined"
        elif fault == "secret":
            content["choices"][0]["message"]["content"] = "private-test-key"
        return httpx.Response(200, json=content, request=request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", handler)
    output = tmp_path / "evidence"
    result = module.execute(preview, module.preview_digest(preview), output)
    assert len(calls) == 1
    assert result["results"][0]["draft"] is None
    assert result["results"][0]["analysis"]["status"] != "validated"
    evidence = "".join(path.read_text() for path in output.iterdir())
    assert (
        "private-test-key" not in evidence and "DO-NOT-STORE-REASONING" not in evidence
    )


@pytest.mark.parametrize("kind", ["approved", "verified", "selected"])
def test_ledger_cannot_grant_itself_authority(monkeypatch, kind):
    module = runner(monkeypatch)
    preview = module.prepare(case_ids=["incomplete-booking"])
    candidate = ledger(preview)
    candidate["kind"] = kind
    with pytest.raises(ValidationError):
        module.validate_ledger(
            candidate, [module.source(s) for s in preview["cases"][0]["sources"]]
        )


def test_all_cited_sources_must_contain_the_excerpt(monkeypatch):
    module = runner(monkeypatch)
    preview = module.prepare(case_ids=["contradictory-deletion"])
    candidate = ledger(preview)
    candidate["behaviors"][0]["source_ids"] = [
        s["id"] for s in preview["cases"][0]["sources"]
    ]
    with pytest.raises(ValueError):
        module.validate_ledger(
            candidate, [module.source(s) for s in preview["cases"][0]["sources"]]
        )


def test_analysis_skill_is_explicitly_isolated_from_runtime_registry(monkeypatch):
    module = runner(monkeypatch)
    from specbridge.skills import SkillRegistry

    runtime = SkillRegistry(ROOT / "skills/runtime")
    experimental = SkillRegistry(ROOT / "skills/experiments")
    assert "source-analysis" not in {
        skill.name for skill in runtime.search("source analysis")
    }
    skill = experimental.load("source-analysis")
    assert skill.metadata.version == "0.1.0" and skill.tool_allowlist == []
    assert module.prepare()["analysis_skill_digest"] == skill.digest


@pytest.mark.parametrize("fault", ["ledger-citation", "decoded-secret"])
def test_invalid_stage_two_never_persists_artifact(monkeypatch, tmp_path, fault):
    module = runner(monkeypatch)
    from specbridge.providers import FixtureProvider

    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "private-test-key")
    preview = module.prepare(case_ids=["incomplete-booking"])
    candidate = ledger(preview)
    sources = [module.source(s) for s in preview["cases"][0]["sources"]]
    artifact = (
        FixtureProvider()
        .generate(skill=module.active_skill(), sources=sources)
        .model_dump()
    )
    if fault == "ledger-citation":
        artifact["requirements"][0]["source_ids"] = ["BEH-1"]
    else:
        artifact["purpose"] = "private-test-key"
    calls = []

    async def handler(self, request):
        calls.append(True)
        content = candidate if len(calls) == 1 else artifact
        raw = json.dumps(envelope(content))
        if len(calls) == 2 and fault == "decoded-secret":
            # A JSON-escaped secret must be caught after decoding as well.
            raw = raw.replace("private-test-key", "private-test-\\u006bey")
            assert "private-test-key" not in raw
        return httpx.Response(200, content=raw, request=request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", handler)
    output = tmp_path / "evidence"
    result = module.execute(preview, module.preview_digest(preview), output)
    assert len(calls) == 2
    assert result["results"][0]["draft"]["status"] != "validated"
    assert not list(output.glob("*.artifact.json"))
    assert "private-test-key" not in "".join(p.read_text() for p in output.iterdir())


@pytest.mark.parametrize(
    "value", [[], ["unknown"], ["incomplete-booking"] * 2, ["incomplete-booking"] * 6]
)
def test_invalid_case_selection_never_constructs_a_batch(monkeypatch, value):
    module = runner(monkeypatch)
    with pytest.raises(ValueError, match="invalid_case_selection"):
        module.prepare(case_ids=value)


def test_cli_defaults_to_offline_preview(monkeypatch, capsys):
    module = runner(monkeypatch)
    monkeypatch.delenv("SPECBRIDGE_LLM_API_KEY", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        ["qualify_staged.py", "--case", "incomplete-booking", "--omit-output-cap"],
    )
    module.main()
    text = capsys.readouterr().out
    assert "Preview SHA256:" in text
    assert '"maximum_calls": 2' in text


@pytest.mark.parametrize("field", ["behaviors", "open_decisions"])
def test_analysis_array_limits_are_enforced(monkeypatch, field):
    module = runner(monkeypatch)
    preview = module.prepare(case_ids=["incomplete-booking"])
    candidate = ledger(preview)
    if field == "behaviors":
        candidate[field] = [
            {**candidate["behaviors"][0], "id": f"BEH-{i}"} for i in range(101)
        ]
    else:
        candidate[field] = [
            {
                "question": f"Question {i}?",
                "source_ids": candidate["behaviors"][0]["source_ids"],
                "affected_behavior_ids": ["BEH-1"],
                "alternatives": [],
            }
            for i in range(101)
        ]
    with pytest.raises(ValidationError) as error:
        module.validate_ledger(
            candidate, [module.source(s) for s in preview["cases"][0]["sources"]]
        )
    assert any(
        item["loc"] == (field,) and item["type"] == "too_long"
        for item in error.value.errors()
    )
