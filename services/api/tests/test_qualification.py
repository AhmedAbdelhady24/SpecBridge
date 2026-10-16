"""Safety regressions for the opt-in live evaluation runner."""

import importlib.util
import json
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]


def runner():
    path = ROOT / "scripts/qualify_provider.py"
    assert path.exists(), "The reusable qualification runner is missing"
    spec = importlib.util.spec_from_file_location("qualification", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pack_has_distinct_cases_and_explicit_conflict_review():
    cases = json.loads(
        (ROOT / "tests/fixtures/provider-qualification/cases.json").read_text()
    )
    assert len(cases) == len({c["id"] for c in cases}) == 5
    assert all(c["sources"] and len(c["review_criteria"]) >= 3 for c in cases)
    assert len(cases[2]["sources"]) == len(cases[3]["sources"]) == 2
    assert all("CSV" not in s["text"] for c in cases for s in c["sources"])


def test_preview_is_offline_and_changes_bind_authorization(monkeypatch):
    module = runner()
    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "private-test-key")
    monkeypatch.setenv("SPECBRIDGE_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("SPECBRIDGE_LLM_MODEL", "deepseek-flash")
    monkeypatch.setenv("SPECBRIDGE_LLM_OUTPUT_MODE", "json_object")
    monkeypatch.setenv("SPECBRIDGE_LLM_MAX_TOKENS", "3072")

    async def forbidden(*args, **kwargs):
        pytest.fail("Preview must not access network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)
    preview = module.prepare()
    assert len(preview["requests"]) == 5
    assert "private-test-key" not in json.dumps(preview)
    before = module.preview_digest(preview)
    monkeypatch.setenv("SPECBRIDGE_LLM_MODEL", "another-model")
    assert module.preview_digest(module.prepare()) != before


def test_mismatched_authorization_does_not_create_output(tmp_path):
    module = runner()
    output = tmp_path / "evidence"
    with pytest.raises(ValueError, match="preview_mismatch"):
        module.execute({"requests": []}, "wrong", output)
    assert not output.exists()


def test_failure_is_recorded_without_retry(tmp_path, monkeypatch):
    module = runner()
    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "private-test-key")
    monkeypatch.setenv("SPECBRIDGE_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("SPECBRIDGE_LLM_MODEL", "deepseek-flash")
    monkeypatch.setenv("SPECBRIDGE_LLM_OUTPUT_MODE", "json_object")
    monkeypatch.setenv("SPECBRIDGE_LLM_MAX_TOKENS", "3072")
    preview = module.prepare()
    calls = []

    async def fail(self, request):
        calls.append(request)
        return httpx.Response(500, request=request, text="private-test-key")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", fail)
    output = tmp_path / "evidence"
    result = module.execute(preview, module.preview_digest(preview), output)
    assert len(calls) == 5
    assert len(result["results"]) == 5
    assert all(r["status"] == "provider_http_error" for r in result["results"])
    assert "private-test-key" not in (output / "results.json").read_text()
    with pytest.raises(FileExistsError):
        module.execute(preview, module.preview_digest(preview), output)
    assert len(calls) == 5


def test_success_and_rejected_draft_keep_usage_and_evidence(
    tmp_path, monkeypatch, artifact_dict
):
    module = runner()
    for name, value in {
        "BASE_URL": "https://api.deepseek.com",
        "MODEL": "deepseek-flash",
        "API_KEY": "private-test-key",
        "OUTPUT_MODE": "json_object",
        "MAX_TOKENS": "3072",
    }.items():
        monkeypatch.setenv("SPECBRIDGE_LLM_" + name, value)
    preview = module.prepare()
    count = 0

    async def respond(self, request):
        nonlocal count
        count += 1
        # The first artifact is valid; later responses violate requirement coverage.
        candidate = json.loads(json.dumps(artifact_dict))
        if count > 1:
            candidate["stories"] = []
        return httpx.Response(
            200,
            request=request,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(candidate)},
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 200,
                    "total_tokens": 300,
                },
                "id": "private-provider-envelope-id",
            },
        )

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", respond)
    output = tmp_path / "success-and-rejection"
    result = module.execute(preview, module.preview_digest(preview), output)
    assert result["results"][0]["status"] == "validated"
    assert (output / "notification-preferences.json").exists()
    assert all(r["status"] != "validated" for r in result["results"][1:])
    assert (output / "incomplete-booking.rejected.txt").exists()
    assert result["results"][0]["usage"]["total_tokens"] == 300
    assert "private-provider-envelope-id" not in (output / "results.json").read_text()


def test_secret_response_is_not_saved_as_artifact(tmp_path, monkeypatch, artifact_dict):
    module = runner()
    for name, value in {
        "BASE_URL": "https://api.deepseek.com",
        "MODEL": "deepseek-flash",
        "API_KEY": "private-test-key",
        "OUTPUT_MODE": "json_object",
        "MAX_TOKENS": "3072",
    }.items():
        monkeypatch.setenv("SPECBRIDGE_LLM_" + name, value)
    preview = module.prepare()
    artifact_dict["purpose"] = "private-test-key"

    async def respond(self, request):
        return httpx.Response(
            200,
            request=request,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(artifact_dict)},
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", respond)
    output = tmp_path / "secret-response"
    result = module.execute(preview, module.preview_digest(preview), output)
    assert all(r["status"] == "secret_in_response" for r in result["results"])
    assert sorted(p.name for p in output.iterdir()) == ["preview.json", "results.json"]
    assert "private-test-key" not in (output / "results.json").read_text()


def test_selected_cases_bound_live_calls_and_reject_changed_selection(
    tmp_path, monkeypatch
):
    module = runner()
    for name, value in {
        "BASE_URL": "https://api.deepseek.com",
        "MODEL": "deepseek-flash",
        "API_KEY": "private-test-key",
        "OUTPUT_MODE": "json_object",
        "MAX_TOKENS": "3072",
    }.items():
        monkeypatch.setenv("SPECBRIDGE_LLM_" + name, value)
    selected = ["contradictory-deletion", "conflicting-api"]
    preview = module.prepare(case_ids=selected)
    assert [c["id"] for c in preview["requests"]] == selected
    assert preview["maximum_calls"] == 2
    calls = []

    async def fail(self, request):
        calls.append(request)
        return httpx.Response(500, request=request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", fail)
    module.execute(preview, module.preview_digest(preview), tmp_path / "selected")
    assert len(calls) == 2
    changed = module.prepare(case_ids=["notification-preferences"])
    with pytest.raises(ValueError, match="preview_mismatch"):
        module.execute(changed, module.preview_digest(preview), tmp_path / "changed")
    assert len(calls) == 2


@pytest.mark.parametrize(
    "selection", [[], ["missing"], ["conflicting-api", "conflicting-api"]]
)
def test_invalid_case_selection_is_rejected_before_provider_configuration(
    selection, monkeypatch
):
    module = runner()
    monkeypatch.delenv("SPECBRIDGE_LLM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="invalid_case_selection"):
        module.prepare(case_ids=selection)


def test_saved_autopilot_uncovered_default_is_rejected_without_repair():
    from specbridge.models import Artifact, Source, validate_handoff
    from specbridge.providers import CompatibleProvider, ProviderFailure
    from specbridge.skills import SkillRegistry

    folder = ROOT / "docs/evaluations/autopilot-qualification-2026-10-16/round-3"
    raw = (folder / "notification-preferences.rejected.txt").read_text()
    preview = json.loads((folder / "preview.json").read_text())
    case = next(c for c in preview["requests"] if c["id"] == "notification-preferences")
    sources = [
        Source(**s, project_id="synthetic", digest="synthetic") for s in case["sources"]
    ]
    artifact = Artifact.model_validate_json(raw)
    assert {r.id for r in artifact.requirements} - {
        r for story in artifact.stories for r in story.requirement_ids
    } == {"REQ-4"}
    with pytest.raises(ValueError, match="explicit story link"):
        validate_handoff(artifact, sources)
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"finish_reason": "stop", "message": {"content": raw}}]},
        )

    provider = CompatibleProvider(
        base_url="https://model.example/v1",
        model="test",
        api_key="SECRET",
        transport=httpx.MockTransport(respond),
    )
    skill = SkillRegistry(ROOT / "skills/runtime").load(
        "feature-handoff", with_output_contract=True
    )
    with pytest.raises(ProviderFailure, match="invalid_artifact"):
        provider.generate(skill=skill, sources=sources)
    assert len(calls) == 1
    assert (folder / "notification-preferences.rejected.txt").read_text() == raw


def test_omitting_cap_changes_only_token_fields_and_binds_execution_mode(
    monkeypatch, tmp_path
):
    module = runner()
    for name, value in {
        "BASE_URL": "https://api.deepseek.com",
        "MODEL": "deepseek-flash",
        "API_KEY": "private-test-key",
        "OUTPUT_MODE": "json_object",
        "MAX_TOKENS": "3072",
    }.items():
        monkeypatch.setenv("SPECBRIDGE_LLM_" + name, value)
    normal = module.prepare(case_ids=["notification-preferences"])
    omitted = module.prepare(
        case_ids=["notification-preferences"], omit_output_cap=True
    )
    assert normal["requests"][0]["body"]["max_tokens"] == 3072
    expected = dict(normal["requests"][0]["body"])
    expected.pop("max_tokens")
    assert omitted["requests"][0]["body"] == expected
    assert "max_completion_tokens" not in omitted["requests"][0]["body"]
    calls = []

    async def fail(self, request):
        calls.append(request)
        body = json.loads(request.content)
        assert "max_tokens" not in body and "max_completion_tokens" not in body
        return httpx.Response(500, request=request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", fail)
    altered = json.loads(json.dumps(omitted))
    altered["omit_output_cap"] = False
    with pytest.raises(ValueError, match="preview_mismatch"):
        module.execute(altered, module.preview_digest(altered), tmp_path / "wrong-mode")
    assert not calls
    assert not (tmp_path / "wrong-mode").exists()
    result = module.execute(
        omitted, module.preview_digest(omitted), tmp_path / "omitted"
    )
    assert result["client_output_cap_omitted"] is True
    assert len(calls) == 1
    assert result["results"][0]["status"] == "provider_http_error"


def test_strict_mode_diagnostic_omits_completion_cap(monkeypatch):
    module = runner()
    for name, value in {
        "BASE_URL": "https://model.example/v1",
        "MODEL": "test-model",
        "API_KEY": "private-test-key",
        "OUTPUT_MODE": "json_schema",
        "MAX_TOKENS": "3072",
    }.items():
        monkeypatch.setenv("SPECBRIDGE_LLM_" + name, value)
    normal = module.prepare(case_ids=["notification-preferences"])
    omitted = module.prepare(
        case_ids=["notification-preferences"], omit_output_cap=True
    )
    expected = dict(normal["requests"][0]["body"])
    assert expected.pop("max_completion_tokens") == 3072
    assert omitted["requests"][0]["body"] == expected
    assert "max_tokens" not in omitted["requests"][0]["body"]


@pytest.mark.parametrize(
    "reported,expected",
    [(42, 42), (0, 0), (None, None), ("42", None), (True, None), (-1, None)],
)
def test_reasoning_usage_is_optional_and_private_text_is_not_saved(
    reported, expected, tmp_path, monkeypatch, artifact_dict
):
    module = runner()
    for name, value in {
        "BASE_URL": "https://api.deepseek.com",
        "MODEL": "deepseek-flash",
        "API_KEY": "private-test-key",
        "OUTPUT_MODE": "json_object",
        "MAX_TOKENS": "3072",
        "REASONING_EFFORT": "low",
    }.items():
        monkeypatch.setenv("SPECBRIDGE_LLM_" + name, value)
    preview = module.prepare(case_ids=["incomplete-booking"], omit_output_cap=True)

    async def respond(self, request):
        return httpx.Response(
            200,
            request=request,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(artifact_dict),
                            "reasoning_content": "private-provider-reasoning-for-test",
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 200,
                    "total_tokens": 300,
                    "completion_tokens_details": {"reasoning_tokens": reported},
                },
            },
        )

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", respond)
    output = tmp_path / "metered"
    result = module.execute(preview, module.preview_digest(preview), output)
    record = result["results"][0]
    assert record["status"] == "validated"
    assert record["reasoning_tokens"] == expected
    assert record["reasoning_content_present"] is True
    assert all(
        "private-provider-reasoning-for-test" not in f.read_text()
        for f in output.iterdir()
    )
