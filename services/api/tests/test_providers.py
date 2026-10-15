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
        "feature-handoff"
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


def provider(handler):
    return CompatibleProvider(
        base_url="https://model.example/v1",
        model="test-model",
        api_key="SECRET",
        transport=httpx.MockTransport(handler),
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
def test_http_failure_no_retry(status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            status, headers={"Location": "https://other.example"}, text="SECRET"
        )

    with pytest.raises(ProviderFailure) as error:
        generate(provider(handler))
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
