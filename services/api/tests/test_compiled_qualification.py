"""One-call evaluation preserves target/approval/secret boundaries."""

import importlib
import json
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]


def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    assert (ROOT / "scripts/qualify_compiled.py").exists(), "Compiled runner missing"
    monkeypatch.setenv("SPECBRIDGE_LLM_BASE_URL", "https://model.example/v1")
    monkeypatch.setenv("SPECBRIDGE_LLM_MODEL", "synthetic-test")
    monkeypatch.setenv("SPECBRIDGE_LLM_OUTPUT_MODE", "json_object")
    monkeypatch.setenv("SPECBRIDGE_LLM_TIMEOUT_SECONDS", "none")
    monkeypatch.setenv("SPECBRIDGE_LLM_API_KEY", "private-test-key")
    return importlib.import_module("qualify_compiled")


def response(preview):
    s = preview["cases"][0]["sources"][0]
    return {
        "title": "Proposed reservation",
        "behaviors": [
            {
                "id": "BEH-reserve",
                "evidence": {
                    "source_id": s["id"],
                    "excerpt": "Let visitors reserve a place in a workshop.",
                },
                "outcomes": ["Completing reservation records the reserved place."],
            }
        ],
        "conflicts": [],
        "timing_reviews": [],
        "interface_reviews": [],
        "owner": {"evidence": None, "question": "Who owns this?"},
        "delivery_date": {"evidence": None, "question": "When is delivery?"},
        "open_questions": ["Is payment required?"],
        "ignored_sources": [],
    }


def test_keyless_preview_never_calls_network_and_uses_five_calls(monkeypatch):
    m = runner(monkeypatch)
    monkeypatch.delenv("SPECBRIDGE_LLM_API_KEY")

    async def forbidden(*args, **kwargs):
        pytest.fail("Preview called network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)
    p = m.prepare(omit_output_cap=True)
    assert (
        p["maximum_calls"] == 5
        and p["retries"] == 0
        and p["generation_timeout_seconds"] is None
    )
    assert len(p["compiler_sha256"]) == 64
    for c in p["cases"]:
        assert "max_tokens" not in c["request"]["body"]
        assert "max_completion_tokens" not in c["request"]["body"]
        assert "review_criteria" not in c


@pytest.mark.parametrize("change", ["compiler", "config", "approval"])
def test_changed_scope_is_rejected_before_network_or_directory(
    monkeypatch, tmp_path, change
):
    m = runner(monkeypatch)
    p = m.prepare(case_ids=["incomplete-booking"])
    h = m.preview_digest(p)
    if change == "compiler":
        p["compiler_sha256"] = "changed"
        h = m.preview_digest(p)
    elif change == "config":
        monkeypatch.setenv("SPECBRIDGE_LLM_MODEL", "different")
    else:
        h = "wrong"

    async def forbidden(*args, **kwargs):
        pytest.fail("Unapproved request sent")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)
    with pytest.raises(ValueError, match="preview_mismatch"):
        m.execute(p, h, tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("invalid", [False, True])
def test_single_request_compiles_or_retains_rejection_without_retry(
    monkeypatch, tmp_path, invalid
):
    m = runner(monkeypatch)
    p = m.prepare(case_ids=["incomplete-booking"], omit_output_cap=True)
    content = response(p)
    if invalid:
        content["behaviors"][0]["evidence"]["excerpt"] = "Invented excerpt"
    requests = []

    async def handler(self, request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(content),
                            "reasoning_content": "DO-NOT-STORE-REASONING",
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            },
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", handler)
    out = tmp_path / "output"
    r = m.execute(p, m.preview_digest(p), out)
    assert len(requests) == 1
    assert json.loads(requests[0].content) == p["cases"][0]["request"]["body"]
    assert "DO-NOT-STORE-REASONING" not in "".join(f.read_text() for f in out.iterdir())
    if invalid:
        assert not (out / "incomplete-booking.artifact.json").exists()
        assert (out / "incomplete-booking.plan.rejected.json").exists()
    else:
        a = json.loads((out / "incomplete-booking.artifact.json").read_text())
        assert a["stories"][0]["acceptance_criteria"] == [
            "Completing reservation records the reserved place."
        ]
        assert (out / "incomplete-booking.plan.json").exists()
        assert r["results"][0]["compiled_artifact_sha256"]
