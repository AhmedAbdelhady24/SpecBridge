# Safe generation failure diagnostics — 18 October 2026

Status: offline repair verified; live cause/retry awaiting explicit authorization. User reported a real Bask Health execute-stage failure via screenshot after the UX repair. Read-only saved-state inspection confirms two failed attempts with generic generation_failed; raw provider exception/response was intentionally discarded, so the original causes cannot be recovered. Safe configuration inspection confirms Flash/json_object, 3072 output tokens, reasoning none and no generation deadline. The cap is a possible constraint, not a proven diagnosis. No paid retry is authorized by this repair.

Scope: preserve an explicit allowlist of static ProviderFailure codes in failed execute records/audit; arbitrary exception strings/codes remain generic. Show clear fixed messages for known categories and explain legacy unknown failures honestly. Refresh the run picker in failure recovery so it agrees with the saved run. Do not relax artifact rules, change private provider settings, retry paid requests, retain raw model output or mutate old run failures.

Lead owns providers.py/workflow.py, frontend failure messages and progress recovery, backend/browser regressions and these docs. Existing app servers are stopped briefly for isolated fixture tests then restored with the same .env. No dependency or schema migration. Read-only security review after implementation. Use installed systematic debugging/TDD/verification; codebase graph unavailable, inspect exact sources/callers.

Acceptance: allowlisted failures survive reload with the exact safe code; arbitrary ProviderFailure code/exception text never enters run or audit; retry still needs explicit acknowledgment; error display distinguishes incomplete output, timeout, HTTP/transport failure and invalid output; a failed attempt updates the run selector; legacy generation_failed remains unknown rather than invented. Mock tests make zero paid requests. Backend/static/frontend/browser regressions pass; restore the local app, report unverified live generation separately.

Execution: pending red/green tests, implementation, review and results. Historical failure diagnosis is blocked by missing recorded detail, not inferred from token settings. M1 model integration/human acceptance remain separate.

## Verification

- Initial failure-category regression: 10 failed/1passed, proving generic recording erased known categories. After the allowlist fix, all cases including unknown-code redaction pass; reviewer requested invalid_configuration coverage, now included.
- Full backend:345passed/279subtests,2.68s. Ruff check/format40files and mypy11sources pass; bootstrap2checks pass. A single import-order lint error was fixed and rerun cleanly.
- Full browser suite:34passed in23.4s, including incomplete/legacy failure guidance, no raw provider message, current failed picker status and disabled unacknowledged retry. These transport simulations use fixture data and do not pretend to be live provider proof.
- Frontend typecheck/lint,2unit tests and production build pass. No contract or dependency changes. Static read-only review approved the allowlist, audit redaction and recovery behavior with no blocker.
- Original private runs were read only, not altered; no raw provider exception/model response was recovered or retained. Existing app's generation settings were not changed. New user authorization was requested for one exact latest-run paid retry with current settings; no call made while pending.

Files: providers.py, workflow.py, App.tsx, generationErrors.ts, workflow and browser regressions plus this plan. Applied existing debugging/TDD/verification skills; one read-only security reviewer, no implementation delegation needed for this narrow patch. This fixes diagnostic loss and stale UI state, not proven live generation correctness or M1 model promotion.
