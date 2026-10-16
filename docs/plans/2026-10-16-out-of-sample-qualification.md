# Out-of-sample hosted checks

Status: verified testing; provider qualification incomplete. User asked “okay test it” after the targeted success and the recommendation to test unrelated features. Execute five synthetic cases through the existing configured DeepSeek adapter, at most one request per case, 3072 output tokens each, reasoning disabled, no retries. No new provider, publication, product approval or dependencies. Dollar cost stays unknown; the output-token ceiling is 15360 across the five calls and input tokens are additional.

Inspect existing provider, skill loader, Artifact validation and prior qualification plan. Own only the synthetic pack, opt-in runner, runner regressions and evaluation/plan records. No production contract changes or workflow usage-metering expansion. Work sequentially because this is one small shared runner.

Acceptance:
- Five distinct non-CSV cases with stable source IDs, known facts/unknowns and explicit review criteria, including both sides of each conflict.
- Default runner previews exact request bodies without network; execution requires the preview hash, one attempt per case and an unused output directory. Configuration/skill/source changes invalidate the preview. Capture sanitized status, duration, reported usage and draft or validation failure, never credentials/provider envelopes.
- Offline tests prove preview sends nothing, altered previews reject before network, and a failed case never retries. Run the full backend regression suite and lint.
- Execute once under user instruction; review saved artifacts against fixed criteria, record every failure and retain raw synthetic drafts for diagnosis. Passing schema does not mean semantic acceptance. No LLM self-grading.

Reproduce preview: `PYTHONPATH=services/api uv run --env-file .env python scripts/qualify_provider.py`. Execution uses the printed digest and `--execute HASH --output NEW_PATH`; never rerun a paid command automatically. Review before any later authorized paid repetition. Existing ignored .env remains private; no environment file changes needed.

Next: create pack and safety tests first, implement minimal runner, verify offline, then run five calls and review. Broader human acceptance, per-request application usage persistence and standalone handoff remain separate work.

Execution:
- [x] Five fixed unrelated cases and review criteria prepared before network.
- [x] Preview-first bounded runner; safety regressions observed red then green.
- [x] Exactly five DeepSeek calls executed, no retries: three validated, two rejected for missing story IDs. API case additionally breaks exact-excerpt policy.
- [x] Lead reviewed all saved drafts against the predetermined criteria; recorded semantic weaknesses in both accepted and rejected drafts. No human approval claimed.
- [x] Saved exact sanitized requests, actual outputs/rejections, hashes, usage and diagnosis in docs/evaluations/deepseek-out-of-sample-2026-10-16/.

Result: testing complete; provider qualification is not passed. [Actual outcomes and next corrective task](../evaluations/deepseek-out-of-sample.md). This consumed five newly authorized calls (eight total across recorded hosted trials); no additional calls authorized by this run. Output cap stays 3072: all five completions stopped naturally, so these failures are unrelated to truncation. Next action is a narrow prompt/contract correction with offline regressions, followed by separately authorized failed-case retesting.

Final checks: `.venv/bin/python -m pytest -q` passed 136 tests and 112 bootstrap subtests; Ruff lint and formatting passed (25 files), mypy passed (10 application sources), `git diff --check` passed. The new runner has six safety/recording regressions. An unnecessary invocation of `node scripts/check_docs.mjs` without its required URL/directory arguments failed with Invalid URL; that script is a standalone website browser harness, not a Markdown checker. No website-build claim is made for this test-only change; local Markdown links are checked by the passing bootstrap suite. No application UI or exporter code changed.
