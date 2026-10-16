# Retest without a client output-token cap — 2026-10-16

**Omitting the client cap did not resolve the observed failures: 5/5 drafts passed backend validation, but 2/5 passed the frozen semantic criteria.** Every response ended naturally with finish_reason=stop, using 323–1114 completion tokens, below the previous 3072 client cap. No further model calls were made after this five-case run.

## Controlled request change

The user explicitly requested “remove the tokens cap and try again.” Ran one full five-case round at the same DeepSeek URL/model, active committed runtime skill 1.2.0, JSON-object mode and reasoning_effort=none. The actual outgoing requests omitted both max_tokens and max_completion_tokens. Each remaining request-body field exactly matches the capped 1.2.0 baseline from autonomous round 1; selected source hashes and the frozen acceptance supplement are unchanged.

Provider defaults still apply. This is not a claim of unlimited server output; the server's default cap was not measured. Existing total timeout, byte bound, no redirects/proxies, single attempt and no retry rules remained active. Credentials stayed in local environment configuration. No artifact approval, external write or publication occurred.

## Actual result and independent review

| Case | Backend | Frozen semantic result | Output tokens | Duration |
| --- | --- | --- | --- | --- |
| Notification preferences | Passed | Fail: criteria check settings display, without digest delivery/suppression behavior. | 1114 | 5.20 s |
| Incomplete booking | Passed | Pass: reservation observable; missing policies/owner/date remain questions. | 323 | 1.98 s |
| Contradictory deletion | Passed | Fail: closes the recovery obligation at 30 elapsed days, without boundary/time-basis/post-window decisions. | 690 | 3.48 s |
| Conflicting API | Passed | Fail: missing draft-A request-mechanics and draft-B UI-applicability questions; assumes usable continuation. | 752 | 3.50 s |
| Embedded instruction | Passed | Pass: bookmark behavior preserved; malicious instructions excluded from requirements/authority. | 623 | 3.12 s |

All HTTP 200 / stop, one attempt each, zero retries. Reported total: **16,795 input + 3,502 output = 20,297 tokens**, **17.28 seconds** summed call duration. Cost unknown. This is five new authorized calls, 30 total recorded hosted attempts across project trials.

Lead and independent read-only review agree on the matrix. The deletion wording does not assert a purge: it says the image is “no longer required to remain recoverable,” which still prematurely settles an unresolved endpoint obligation. The API draft invents no request-field name but hides missing continuation mechanics. These distinctions are retained rather than overstating the defects.

The matching capped baseline also had five backend passes and two semantic passes. Cap omission is the only request-body change, but separate stochastic generations do not prove causal equivalence or rule out all token-budget effects. This run simply did not achieve acceptance, and none of these replies approached the old cap.

## Evidence and reproduction

- [Exact outgoing request preview](no-client-cap-retest-2026-10-16/preview.json).
- [Per-call status, reported usage and hashes](no-client-cap-retest-2026-10-16/results.json).
- [Deterministic replay/body comparison](no-client-cap-retest-2026-10-16/deterministic-replay.json).
- [Independent/lead semantic review](no-client-cap-retest-2026-10-16/semantic-review.json).
- All five complete synthetic drafts are adjacent files named for the cases; no rejected, repaired or cherry-picked sample was substituted.

Added `--omit-output-cap` explicitly to the opt-in qualification runner. Default evaluation and normal application cap configuration remain as committed; this flag omits limit fields only in the diagnostic observer. Mode participates in preview binding. Preview command: `PYTHONPATH=services/api uv run --env-file .env python scripts/qualify_provider.py --omit-output-cap`. Live execution additionally requires `--execute HASH --output NEW_DIRECTORY` and a concrete new operator-authorized scope; do not repeat this paid measurement automatically.

Two regressions first failed for the missing mode, then passed: payload parity/actual omission/mode mismatch/no retry, and strict-mode max_completion_tokens omission. No actual strict-schema endpoint was called. Full backend, Ruff and application typing checks passed; current counts are in the [execution plan](../plans/2026-10-16-no-client-cap-retest.md). Independent code review found no material issue; reviewer did no edits, credential reads or network calls and did not rerun tests. Used existing Superpowers TDD/verification guidance. No runtime skill, application API, dependency, .env or database changed. UI/exporter code is unchanged, so this step makes no new browser/build claim beyond the earlier full repository verification.

Provider qualification remains open. The next investigation should address missing behavior and consistency between criteria and unresolved decisions; these observed failures were not output truncation. A larger output allowance alone has not delivered an engineering-ready handoff in this test.
