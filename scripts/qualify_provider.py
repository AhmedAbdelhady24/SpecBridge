"""Preview-first synthetic provider evaluation; never retries or publishes."""

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
from specbridge.models import Source
from specbridge.providers import CompatibleProvider, ProviderFailure
from specbridge.skills import SkillRegistry

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "tests/fixtures/provider-qualification/cases.json"


def preview_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def provider_options() -> dict[str, Any]:
    return {
        "base_url": os.environ["SPECBRIDGE_LLM_BASE_URL"],
        "model": os.environ["SPECBRIDGE_LLM_MODEL"],
        "api_key": os.environ["SPECBRIDGE_LLM_API_KEY"],
        "output_mode": os.environ.get("SPECBRIDGE_LLM_OUTPUT_MODE", "json_schema"),
        "max_tokens": int(os.environ.get("SPECBRIDGE_LLM_MAX_TOKENS", "4096")),
        "reasoning_effort": os.environ.get("SPECBRIDGE_LLM_REASONING_EFFORT") or None,
    }


class Observation(CompatibleProvider):
    """Per-evaluation observer; the application Provider contract is unchanged."""

    def __init__(self, *, preview_only: bool = False, **options: Any):
        super().__init__(**options)
        self.preview_only = preview_only
        self.payload: dict[str, Any] = {}
        self.raw: bytes | None = None

    async def _request(self, payload: dict[str, Any]) -> bytes:
        self.payload = payload
        if self.preview_only:
            raise ProviderFailure("preview_only")
        self.raw = await super()._request(payload)
        if self._key.encode() in self.raw:
            raise ProviderFailure("secret_in_response")
        return self.raw


def source(value: dict[str, str]) -> Source:
    return Source(
        **value,
        project_id="synthetic-qualification",
        digest=hashlib.sha256(value["text"].encode()).hexdigest(),
    )


def active_skill():
    return SkillRegistry(ROOT / "skills/runtime").load(
        "feature-handoff", with_output_contract=True
    )


def prepare(*, case_ids: list[str] | None = None) -> dict[str, Any]:
    cases = json.loads(PACK.read_text())
    if case_ids is not None:
        available = {case["id"]: case for case in cases}
        if (
            not case_ids
            or len(set(case_ids)) != len(case_ids)
            or any(case_id not in available for case_id in case_ids)
        ):
            raise ValueError("invalid_case_selection")
        cases = [available[case_id] for case_id in case_ids]
    skill = active_skill()
    requests = []
    for case in cases:
        provider = Observation(preview_only=True, **provider_options())
        sources = [source(item) for item in case["sources"]]
        try:
            provider.generate(skill=skill, sources=sources)
        except ProviderFailure as error:
            if error.code != "preview_only":
                raise
        requests.append(
            {
                **case,
                "source_hashes": {
                    s.id: hashlib.sha256(s.text.encode()).hexdigest() for s in sources
                },
                "url": provider.destination + "/chat/completions",
                "body": provider.payload,
            }
        )
    return {
        "skill_digest": skill.digest,
        "skill_version": skill.metadata.version,
        "skill_instructions_sha256": hashlib.sha256(skill.body.encode()).hexdigest(),
        "maximum_calls": len(requests),
        "retries": 0,
        "requests": requests,
    }


class BoundTransport(httpx.AsyncHTTPTransport):
    def __init__(self, request_preview: dict[str, Any]):
        super().__init__(retries=0)
        self.expected = request_preview
        self.attempts = 0
        self.http_status: int | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.attempts += 1
        if (
            self.attempts != 1
            or str(request.url) != self.expected["url"]
            or json.loads(request.content) != self.expected["body"]
        ):
            raise ProviderFailure("preview_mismatch")
        response = await super().handle_async_request(request)
        self.http_status = response.status_code
        return response


def execute(preview: dict[str, Any], approval: str, output: Path) -> dict[str, Any]:
    if preview_digest(preview) != approval:
        raise ValueError("preview_mismatch")
    if (
        preview_digest(prepare(case_ids=[case["id"] for case in preview["requests"]]))
        != approval
    ):
        raise ValueError("preview_mismatch")
    output.mkdir(parents=True, exist_ok=False)
    (output / "preview.json").write_text(json.dumps(preview, indent=2) + "\n")
    result: dict[str, Any] = {
        "preview_sha256": approval,
        "maximum_calls": preview["maximum_calls"],
        "automatic_retries": 0,
        "results": [],
        "semantic_review": "pending; schema validity is not human acceptance",
        "cost": None,
    }
    for case in preview["requests"]:
        transport = BoundTransport(case)
        provider = Observation(transport=transport, **provider_options())
        started = time.monotonic()
        record: dict[str, Any] = {
            "case": case["id"],
            "request_sha256": preview_digest(case["body"]),
            "usage": None,
        }
        try:
            artifact = provider.generate(
                skill=active_skill(),
                sources=[source(item) for item in case["sources"]],
            )
            record["status"] = "validated"
            (output / (case["id"] + ".json")).write_text(
                artifact.model_dump_json(indent=2) + "\n"
            )
        except ProviderFailure as error:
            record["status"] = error.code
        record["attempts"] = transport.attempts
        record["http_status"] = transport.http_status
        record["duration_seconds"] = round(time.monotonic() - started, 2)
        if provider.raw is not None:
            if provider._key.encode() in provider.raw:
                record["status"] = "secret_in_response"
                (output / (case["id"] + ".json")).unlink(missing_ok=True)
            else:
                record["response_sha256"] = hashlib.sha256(provider.raw).hexdigest()
                try:
                    envelope = json.loads(provider.raw)
                    usage = envelope.get("usage", {})
                    record["usage"] = {
                        key: value
                        for key in (
                            "prompt_tokens",
                            "completion_tokens",
                            "total_tokens",
                        )
                        if type(value := usage.get(key)) is int and value >= 0
                    } or None
                    choice = envelope["choices"][0]
                    finish = choice.get("finish_reason")
                    record["finish_reason"] = (
                        finish
                        if finish in {"stop", "length", "content_filter"}
                        else None
                    )
                    if record["status"] != "validated":
                        # Retain bounded synthetic content for diagnosing rejection.
                        (output / (case["id"] + ".rejected.txt")).write_text(
                            str(choice["message"].get("content", ""))
                        )
                except (ValueError, KeyError, IndexError, TypeError, AttributeError):
                    pass
        result["results"].append(record)
        (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(record), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        action="append",
        dest="case_ids",
        help="Select a pack case; repeat to select multiple",
    )
    parser.add_argument("--execute", metavar="PREVIEW_SHA256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    preview = prepare(case_ids=args.case_ids)
    if args.execute:
        if args.output is None:
            parser.error("--execute requires a new --output directory")
        execute(preview, args.execute, args.output)
    else:
        print(json.dumps(preview, indent=2))
        print("Preview SHA256: " + preview_digest(preview))


if __name__ == "__main__":
    main()
