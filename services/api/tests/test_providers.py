import json
from pathlib import Path

import httpx
import pytest
from specbridge.models import Source
from specbridge.providers import (
    CompatibleProvider,
    FixtureProvider,
    ProviderFailure,
    provider_from_env,
)
from specbridge.skills import SkillRegistry


def skill_fixture():
    return SkillRegistry(Path(__file__).resolve().parents[3] / "skills/runtime").load(
        "feature-handoff", with_output_contract=True
    )


def source_fixtures():
    return [
        Source(id="source-1", project_id="p", text="Build a library app", digest="d")
    ]


def output():
    return (
        FixtureProvider()
        .generate(skill=skill_fixture(), sources=source_fixtures())
        .model_dump()
    )


def provider(handler, output_mode="json_schema"):
    return CompatibleProvider(
        base_url="https://model.example/v1",
        model="test-model",
        api_key="SECRET",
        transport=httpx.MockTransport(handler),
        output_mode=output_mode,
    )


def generate(instance):
    return instance.generate(skill=skill_fixture(), sources=source_fixtures())


def test_fixture_is_default_without_network(monkeypatch):
    monkeypatch.delenv("SPECBRIDGE_PROVIDER", raising=False)
    assert isinstance(provider_from_env(), FixtureProvider)
    first = generate(FixtureProvider())
    assert first == generate(FixtureProvider())
    assert "DEMO" in first.title
    assert first.open_questions
    assert all(s.kind == "recommendation" for s in first.statements())
    assert {i for s in first.statements() for i in s.source_ids} == {"source-1"}
    assert "Build a library app" not in first.purpose


def test_structured_request_and_response():
    requests = []

    def handler(request):
        requests.append(request)
        body = json.loads(request.content)
        assert body["response_format"]["json_schema"]["strict"] is True
        assert "tools" not in body
        assert body["model"] == "test-model"
        assert body["max_completion_tokens"] == 4096
        assert "max_tokens" not in body
        assert "reasoning_effort" not in body
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(output())}}]}
        )

    instance = provider(handler)
    assert generate(instance).requirements
    assert str(requests[0].url) == "https://model.example/v1/chat/completions"
    assert instance.destination == "https://model.example/v1"
    assert instance.mode == "compatible" and instance.model == "test-model"
    assert "SECRET" not in repr(instance)


@pytest.mark.parametrize("status", [302, 400, 401, 429, 500])
@pytest.mark.parametrize("output_mode", ["json_schema", "json_object"])
def test_http_failure_no_retry(status, output_mode):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            status, headers={"Location": "https://other.example"}, text="SECRET"
        )

    with pytest.raises(ProviderFailure) as error:
        generate(provider(handler, output_mode))
    assert len(calls) == 1
    assert "SECRET" not in str(error.value)


@pytest.mark.parametrize(
    "payload", ["bad-json", "{}", "extra", "verified", "foreign-source", "tool"]
)
def test_bad_output(payload):
    artifact = output()
    if payload == "extra":
        artifact["extra"] = True
    elif payload == "verified":
        artifact["requirements"][0]["kind"] = "verified"
    elif payload == "foreign-source":
        artifact["requirements"][0]["source_ids"] = ["unknown"]
    content = payload if payload in ["bad-json", "{}"] else json.dumps(artifact)
    message = {"content": content}
    if payload == "tool":
        message["tool_calls"] = [{"function": {"name": "shell"}}]
    with pytest.raises(ProviderFailure):
        generate(
            provider(
                lambda request: httpx.Response(
                    200, json={"choices": [{"message": message}]}
                )
            )
        )


def test_oversize_and_sanitized_transport():
    with pytest.raises(ProviderFailure, match="response_too_large"):
        generate(provider(lambda request: httpx.Response(200, content=b"x" * 262145)))

    def fail(request):
        raise httpx.ConnectError("SECRET")

    with pytest.raises(ProviderFailure) as error:
        generate(provider(fail))
    assert "SECRET" not in str(error.value)


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.example",
        "https://u:pass@example.com",
        "https://example.com/?key=x",
        "https://example.com/#x",
        "file:///tmp/x",
    ],
)
def test_invalid_destination(url):
    with pytest.raises(ProviderFailure):
        CompatibleProvider(base_url=url, model="x", api_key="SECRET")


def test_loopback_http_and_missing_configuration(monkeypatch):
    assert CompatibleProvider(
        base_url="http://127.0.0.1:1234/v1", model="local", api_key="x"
    ).destination.startswith("http:")
    monkeypatch.setenv("SPECBRIDGE_PROVIDER", "compatible")
    for name in [
        "SPECBRIDGE_LLM_BASE_URL",
        "SPECBRIDGE_LLM_MODEL",
        "SPECBRIDGE_LLM_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ProviderFailure, match="configuration"):
        provider_from_env()
    monkeypatch.setenv("SPECBRIDGE_PROVIDER", "unknown")
    with pytest.raises(ProviderFailure):
        provider_from_env()


def test_malformed_message_and_timeout_are_sanitized():
    with pytest.raises(ProviderFailure, match="invalid_response"):
        generate(
            provider(
                lambda request: httpx.Response(
                    200, json={"choices": [{"message": ["SECRET"]}]}
                )
            )
        )

    def timeout(request):
        raise httpx.ReadTimeout("SECRET")

    with pytest.raises(ProviderFailure, match="provider_timeout") as error:
        generate(provider(timeout))
    assert "SECRET" not in str(error.value)


def test_strict_schema_requires_nested_properties_without_changing_backend_defaults():
    from specbridge.models import Artifact

    original = Artifact.model_json_schema()

    def check(value):
        if isinstance(value, dict):
            assert "default" not in value
            if value.get("type") == "object":
                assert set(value["required"]) == set(value["properties"])
                assert value["additionalProperties"] is False
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)

    def handler(request):
        schema = json.loads(request.content)["response_format"]["json_schema"]["schema"]
        check(schema)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(output())}}]}
        )

    assert generate(provider(handler)).requirements
    assert Artifact.model_json_schema() == original


def test_deep_json_is_sanitized():
    nested = "[" * 10000 + '"SECRET"' + "]" * 10000
    with pytest.raises(ProviderFailure, match="invalid_response"):
        generate(provider(lambda request: httpx.Response(200, content=nested)))


@pytest.mark.parametrize("phase", ["headers", "body"])
def test_total_deadline_cancels_slow_response(monkeypatch, phase):
    import asyncio
    import time

    from specbridge import providers

    monkeypatch.setattr(providers, "TOTAL_TIMEOUT", 0.05, raising=False)
    payload = json.dumps(
        {"choices": [{"message": {"content": json.dumps(output())}}]}
    ).encode()
    closed = []

    class Drip(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            for offset in range(0, len(payload), len(payload) // 10):
                time.sleep(0.02)
                yield payload[offset : offset + len(payload) // 10]

        async def __aiter__(self):
            for offset in range(0, len(payload), len(payload) // 10):
                await asyncio.sleep(0.02)
                yield payload[offset : offset + len(payload) // 10]

        def close(self):
            closed.append(True)

        async def aclose(self):
            closed.append(True)

    class SlowTransport(httpx.BaseTransport, httpx.AsyncBaseTransport):
        def handle_request(self, request):
            if phase == "headers":
                time.sleep(0.2)
            return httpx.Response(200, stream=Drip())

        async def handle_async_request(self, request):
            if phase == "headers":
                await asyncio.sleep(0.2)
            return httpx.Response(200, stream=Drip())

    instance = CompatibleProvider(
        base_url="https://model.example/v1",
        model="x",
        api_key="SECRET",
        transport=SlowTransport(),
    )
    started = time.monotonic()
    with pytest.raises(ProviderFailure, match="provider_timeout"):
        generate(instance)
    assert time.monotonic() - started < 0.2
    if phase == "body":
        assert closed == [True]


def test_json_object_mode_sends_schema_and_token_cap_without_network_retry():
    calls = []

    def handler(request):
        calls.append(request)
        body = json.loads(request.content)
        assert body["response_format"] == {"type": "json_object"}
        assert body["max_tokens"] == 2048
        assert "max_completion_tokens" not in body
        prompt = body["messages"][0]["content"]
        assert '"requirements"' in prompt and '"acceptance_criteria"' in prompt
        assert "JSON" in prompt
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(output())},
                    }
                ]
            },
        )

    instance = CompatibleProvider(
        base_url="https://api.deepseek.com",
        model="test-model",
        api_key="SECRET",
        output_mode="json_object",
        max_tokens=2048,
        transport=httpx.MockTransport(handler),
    )
    assert generate(instance).stories
    assert len(calls) == 1
    assert str(calls[0].url) == "https://api.deepseek.com/chat/completions"


@pytest.mark.parametrize("fault", ["extra", "verified", "foreign-source"])
def test_json_object_mode_keeps_local_validation(fault):
    artifact = output()
    if fault == "extra":
        artifact["extra"] = True
    elif fault == "verified":
        artifact["requirements"][0]["kind"] = "verified"
    else:
        artifact["requirements"][0]["source_ids"] = ["foreign"]
    instance = CompatibleProvider(
        base_url="https://api.deepseek.com",
        model="test",
        api_key="SECRET",
        output_mode="json_object",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps(artifact)}}]},
            )
        ),
    )
    with pytest.raises(ProviderFailure):
        generate(instance)


@pytest.mark.parametrize("reason", ["length", "content_filter", "tool_calls"])
def test_incomplete_finish_reason_rejected_even_with_valid_json(reason):
    instance = provider(
        lambda request: httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": reason,
                        "message": {"content": json.dumps(output())},
                    }
                ]
            },
        )
    )
    with pytest.raises(ProviderFailure, match="incomplete_response"):
        generate(instance)


def test_provider_env_output_mode_and_limits(monkeypatch):
    monkeypatch.setenv("SPECBRIDGE_PROVIDER", "compatible")
    monkeypatch.setenv("SPECBRIDGE_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("SPECBRIDGE_LLM_MODEL", "test")
    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "SECRET")
    monkeypatch.setenv("SPECBRIDGE_LLM_OUTPUT_MODE", "json_object")
    monkeypatch.setenv("SPECBRIDGE_LLM_MAX_TOKENS", "2048")
    instance = provider_from_env()
    assert instance.output_mode == "json_object" and instance.max_tokens == 2048
    for mode, limit in [
        ("bad", "2048"),
        ("json_object", "0"),
        ("json_object", "16385"),
        ("json_object", "bad"),
    ]:
        monkeypatch.setenv("SPECBRIDGE_LLM_OUTPUT_MODE", mode)
        monkeypatch.setenv("SPECBRIDGE_LLM_MAX_TOKENS", limit)
        with pytest.raises(ProviderFailure, match="invalid_configuration"):
            provider_from_env()


@pytest.mark.parametrize("choices", [["SECRET"], [None], {"0": "SECRET"}])
def test_malformed_choices_are_sanitized(choices):
    with pytest.raises(ProviderFailure, match="invalid_response"):
        generate(
            provider(lambda request: httpx.Response(200, json={"choices": choices}))
        )


def test_explicit_reasoning_effort_is_sent_without_raising_output_budget(monkeypatch):
    monkeypatch.setenv("SPECBRIDGE_PROVIDER", "compatible")
    monkeypatch.setenv("SPECBRIDGE_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("SPECBRIDGE_LLM_MODEL", "test")
    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "SECRET")
    monkeypatch.setenv("SPECBRIDGE_LLM_OUTPUT_MODE", "json_object")
    monkeypatch.setenv("SPECBRIDGE_LLM_MAX_TOKENS", "4096")
    monkeypatch.setenv("SPECBRIDGE_LLM_REASONING_EFFORT", "none")
    configured = provider_from_env()

    def handler(request):
        body = json.loads(request.content)
        assert body["reasoning_effort"] == "none"
        assert body["max_tokens"] == 4096
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(output())},
                    }
                ]
            },
        )

    configured._transport = httpx.MockTransport(handler)
    assert generate(configured).requirements
    monkeypatch.setenv("SPECBRIDGE_LLM_REASONING_EFFORT", "invalid")
    with pytest.raises(ProviderFailure, match="invalid_configuration"):
        provider_from_env()


def test_unsupported_user_provided_story_is_rejected():
    artifact = output()
    artifact["stories"][0].update(
        text="As a customer I export CSV so I can use external tools",
        kind="user_provided",
    )
    with pytest.raises(ProviderFailure, match="invalid_artifact"):
        generate(
            provider(
                lambda request: httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": json.dumps(artifact)}}]},
                )
            )
        )


def test_uncovered_requirement_is_rejected():
    artifact = output()
    artifact["requirements"].append(
        dict(
            artifact["requirements"][0], id="REQ-headers", text="Include column headers"
        )
    )
    with pytest.raises(ProviderFailure, match="invalid_artifact"):
        generate(
            provider(
                lambda request: httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": json.dumps(artifact)}}]},
                )
            )
        )


def test_exact_source_excerpt_and_synthesized_story_pass():
    artifact = output()
    artifact["requirements"][0].update(text="Build a library app", kind="user_provided")
    assert generate(
        provider(
            lambda request: httpx.Response(
                200, json={"choices": [{"message": {"content": json.dumps(artifact)}}]}
            )
        )
    ).requirements


def test_unknown_requirement_must_remain_an_open_question():
    artifact = output()
    artifact["requirements"][0].update(
        text="The system shall enforce an unknown report-size limit", kind="unknown"
    )
    with pytest.raises(ProviderFailure, match="invalid_artifact"):
        generate(
            provider(
                lambda request: httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": json.dumps(artifact)}}]},
                )
            )
        )


def test_original_live_draft_is_readable_and_corrected_example_meets_policy():
    from specbridge.models import Artifact, validate_handoff

    root = Path(__file__).resolve().parents[3] / "docs/evaluations"
    source = Source(
        id="smoke-source-1",
        project_id="synthetic",
        text="Customers need to export their saved reports as CSV. Exports must include column headers. Owner, delivery date, maximum report size, and permission rules are unknown.",
        digest="synthetic",
    )
    original = Artifact.model_validate_json(
        (root / "deepseek-complete-csv-draft.json").read_text()
    )
    with pytest.raises(ValueError):
        validate_handoff(original, [source])
    corrected = Artifact.model_validate_json(
        (root / "handoff-corrected-csv-example.json").read_text()
    )
    validate_handoff(corrected, [source])


def test_request_schema_excludes_self_verification_and_unknown_requirements():
    def handler(request):
        schema = json.loads(request.content)["response_format"]["json_schema"]["schema"]
        for name in ["Statement", "Requirement", "Story"]:
            assert "verified" not in schema["$defs"][name]["properties"]["kind"]["enum"]
        assert (
            "unknown"
            not in schema["$defs"]["Requirement"]["properties"]["kind"]["enum"]
        )
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(output())}}]}
        )

    assert generate(provider(handler)).requirements


@pytest.mark.parametrize("mode", ["json_schema", "json_object"])
def test_request_contains_valid_decision_conditional_conflict_example(mode):
    import re

    from specbridge.models import Artifact, validate_handoff

    def handler(request):
        instructions = json.loads(request.content)["messages"][0]["content"]
        examples = [
            json.loads(block)
            for block in re.findall(r"```json\n(.*?)\n```", instructions, re.DOTALL)
        ]
        artifacts = [value for value in examples if "requirements" in value]
        assert len(artifacts) == 1, (
            "A complete conflict Artifact example must be injected"
        )
        example = Artifact.model_validate(artifacts[0])
        sources = [
            Source(
                id="example-immediate",
                project_id="example",
                text="Settings changes take effect immediately.",
                digest="example",
            ),
            Source(
                id="example-approval",
                project_id="example",
                text="Settings changes take effect only after an administrator approves them.",
                digest="example",
            ),
        ]
        validate_handoff(example, sources)
        assert len(example.requirements) == len(example.stories) == 2
        assert all(story.kind == "recommendation" for story in example.stories)
        assert all(
            "selected" in criterion
            for story in example.stories
            for criterion in story.acceptance_criteria
        )
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(output())}}]}
        )

    assert generate(provider(handler, output_mode=mode)).requirements


@pytest.mark.parametrize("case_id", ["contradictory-deletion", "conflicting-api"])
def test_saved_conflict_failures_remain_rejected_and_explicit_corrections_pass(case_id):
    from pydantic import ValidationError
    from specbridge.models import Artifact, validate_handoff

    root = Path(__file__).resolve().parents[3]
    cases = json.loads(
        (root / "tests/fixtures/provider-qualification/cases.json").read_text()
    )
    case = next(c for c in cases if c["id"] == case_id)
    sources = [
        Source(**s, project_id="synthetic", digest="synthetic") for s in case["sources"]
    ]
    path = (
        root
        / "docs/evaluations/deepseek-out-of-sample-2026-10-16"
        / (case_id + ".rejected.txt")
    )
    original = path.read_bytes()
    candidate = json.loads(original)
    with pytest.raises(ValidationError) as error:
        Artifact.model_validate(candidate)
    assert all(
        e["type"] == "missing" and e["loc"][0] == "stories" and e["loc"][-1] == "id"
        for e in error.value.errors()
    )

    # Explicit, lead-authored in-memory correction, never a silent provider repair.
    for i, story in enumerate(candidate["stories"], start=1):
        story["id"] = f"STORY-{i}"
    with_ids = Artifact.model_validate(candidate)
    if case_id == "conflicting-api":
        with pytest.raises(ValueError, match="excerpt"):
            validate_handoff(with_ids, sources)
        candidate["requirements"][1]["text"] = (
            "UI must support moving to the next page."
        )
        candidate["dependencies"][0]["text"] = (
            "the authoritative contract has not been selected."
        )
        candidate["dependencies"][1]["text"] = "Neither draft is approved;"
    validate_handoff(Artifact.model_validate(candidate), sources)
    assert path.read_bytes() == original
