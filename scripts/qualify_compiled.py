"""Preview-first, one synthetic plan request per case; deterministic assembly."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from handoff_plan import HandoffPlan, compile_plan
from qualify_provider import ROOT, preview_digest, source
from qualify_staged import _call, _options
from qualify_staged import prepare as staged_preview
from specbridge.models import Source
from specbridge.skills import SkillRegistry


def prepare(
    *, case_ids: list[str] | None = None, omit_output_cap: bool = False
) -> dict[str, Any]:
    base = staged_preview(case_ids=case_ids, omit_output_cap=omit_output_cap)
    skill = SkillRegistry(ROOT / "skills/experiments").load("handoff-plan")
    schema = HandoffPlan.model_json_schema()
    selected = []
    for c in base["cases"]:
        req = copy.deepcopy(c["analysis_request"])
        req["body"]["messages"][0]["content"] = (
            skill.body + "\nReturn JSON matching this schema:\n" + json.dumps(schema)
        )
        if req["body"]["response_format"]["type"] == "json_schema":
            req["body"]["response_format"]["json_schema"] = {
                "name": "handoff_plan",
                "strict": True,
                "schema": schema,
            }
        selected.append(
            {
                "id": c["id"],
                "sources": c["sources"],
                "source_hashes": c["source_hashes"],
                "request": req,
            }
        )
    return {
        "experiment": "typed-plan-deterministic-artifact-v1",
        "skill_digest": skill.digest,
        "skill_version": skill.metadata.version,
        "compiler_sha256": hashlib.sha256(
            (ROOT / "scripts/handoff_plan.py").read_bytes()
        ).hexdigest(),
        "maximum_calls": len(selected),
        "retries": 0,
        "omit_output_cap": omit_output_cap,
        "generation_timeout_seconds": base["generation_timeout_seconds"],
        "cases": selected,
    }


def execute(preview: dict[str, Any], approval: str, output: Path) -> dict[str, Any]:
    if (
        preview_digest(preview) != approval
        or preview_digest(
            prepare(
                case_ids=[c["id"] for c in preview["cases"]],
                omit_output_cap=preview["omit_output_cap"],
            )
        )
        != approval
    ):
        raise ValueError("preview_mismatch")
    options = _options(require_key=True)
    output.mkdir(parents=True, exist_ok=False)
    (output / "preview.json").write_text(json.dumps(preview, indent=2) + "\n")
    result = {
        "preview_sha256": approval,
        "maximum_calls": preview["maximum_calls"],
        "retries": 0,
        "results": [],
        "semantic_review": "pending; compiled is not approved",
    }
    for case in preview["cases"]:
        sources = [source(s) for s in case["sources"]]

        def validate(value: Any, sources: list[Source] = sources):
            compile_plan(value, sources)
            return HandoffPlan.model_validate(value)

        plan, record = _call(
            case["request"],
            options,
            validate,
            output / (case["id"] + ".plan.rejected.json"),
        )
        record["case"] = case["id"]
        record["compiled_artifact_sha256"] = None
        if plan is not None:
            (output / (case["id"] + ".plan.json")).write_text(
                plan.model_dump_json(indent=2) + "\n"
            )
            artifact = compile_plan(plan, sources)
            content = artifact.model_dump_json(indent=2) + "\n"
            (output / (case["id"] + ".artifact.json")).write_text(content)
            record["compiled_artifact_sha256"] = hashlib.sha256(
                content.encode()
            ).hexdigest()
        result["results"].append(record)
        (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(record), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--omit-output-cap", action="store_true")
    parser.add_argument("--execute", metavar="PREVIEW_SHA256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    preview = prepare(case_ids=args.case_ids, omit_output_cap=args.omit_output_cap)
    if args.execute:
        if args.output is None:
            parser.error("--execute requires a new --output directory")
        execute(preview, args.execute, args.output)
    else:
        print(json.dumps(preview, indent=2))
        print("Preview SHA256: " + preview_digest(preview))


if __name__ == "__main__":
    main()
