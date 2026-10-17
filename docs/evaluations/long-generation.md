# Long-generation fix and uncapped-wait retest

Generation can now wait without a total/read deadline when explicitly configured, and an active workflow renews its lease rather than becoming falsely interrupted. **The real five-case retest completed all five requests, including two above73 seconds; semantic acceptance remains2/5.** The timeout problem is fixed independently of the still-open content problem.

## Implemented behavior

`SPECBRIDGE_LLM_TIMEOUT_SECONDS=none` disables generation total/read/write/pool deadlines; connection establishment remains bounded to at most30 seconds. Positive finite seconds configure a whole-request deadline, and unset retains the60-second default. Invalid, nonfinite, boolean and nonpositive values are rejected with sanitized configuration errors. The user's ignored private .env now explicitly selects none without exposing/changing the key; restart an existing API to load changed settings. No model setting was promoted. Response byte limits and zero automatic retries remain.

While generation runs, an owned120-second SQLite lease renews every30 seconds. Renewal samples time after acquiring the writer lock and uses a compare-and-set on token and unexpired ownership. Final checkpoint writes also require matching unexpired ownership. The heartbeat stops/joins after success or failure. Database renewal failure is sticky, discards any returned result and records a sanitized failure. A stopped process stops renewal, so interruption recovery and explicit potentially billable retry acknowledgement remain available. A stalled provider request may continue after heartbeat failure until it returns or the process is stopped; the lost-owner result cannot checkpoint or overwrite a newer attempt.

Evaluation preview fingerprints now bind the timeout policy as well as exact payloads. Changing the wait after preview fails before network/output creation. No request body field, public API schema, database schema, active runtime skill, dependency or approval boundary changed.

Changed application/testing paths: `services/api/specbridge/providers.py`, `workflow.py`, their regression tests, `scripts/qualify_provider.py`, its tests, `.env.example`, README and threat model. Provider implementation was isolated in the native `codex/long-model-wait` worktree, reviewed and integrated as `ce0aedf`; lead workflow/runner integration was committed as `0d0bf02`. Failed work/tests and worktree were retained. Used installed versioned Superpowers debugging/TDD/worktree/verification guidance. Independent read-only lease review found no material issue and independently passed121 focused tests.

## Actual retest

The user explicitly requested waiting for higher-effort responses. Ran exactly one five-call Pro/high round with no client output cap, no generation deadline and zero retries. All sources, schema, active skill1.2.0 and request bodies are identical to the previous Pro comparison; only client wait policy changes. Both formerly missing scenarios now returned complete drafts. Two current requests exceeded the old60-second limit; single samples do not establish why other durations varied.

| Case | Backend | Semantic review | Duration |
| --- | --- | --- | --- |
| Notification preferences | Valid | Fail: no digest delivery/suppression criteria | 42.94 s |
| Incomplete booking | Valid | Pass | 37.22 s |
| Contradictory deletion | Valid | Fail: missing exact timing/boundary questions | 42.71 s |
| Conflicting API | Valid | Fail: missing request/applicability decisions | 73.39 s |
| Embedded instruction | Valid | Pass | 73.15 s |

All HTTP200/stop, one attempt each, no truncation or timeout. Reported usage:17,175 input+25,145 completion=42,320 tokens, including21,359 reported reasoning tokens. Completion usage is not assumed to be final-answer-only. Summed duration269.41s; dollar cost unknown. Project hosted attempts now50. This retest scope is consumed; no extra round is implied.

Evidence: [exact preview](unlimited-pro-retest-2026-10-17/preview.json), [usage/status/hashes](unlimited-pro-retest-2026-10-17/results.json), [deterministic replay](unlimited-pro-retest-2026-10-17/deterministic-replay.json), [lead and independent semantic review](unlimited-pro-retest-2026-10-17/semantic-review.json). All five complete Artifacts remain adjacent. No provider reasoning text/envelope or credential was saved. Frozen acceptance supplement hash remains `4518b228d88431c8d6d074a367146f457fef2067638830ef13991b40f8e997cf`.

## Verification and remaining scope

Provider TDD first observed34 failures for missing wait support, then passed86 focused provider checks. Workflow TDD observed missing-heartbeat failures and a separate expired-lease resurrection race before correction. Seven new workflow cases cover renewal beyond original expiry, duplicate advance rejection, expired/replaced ownership, sticky database failure, cleanup on provider exception and acknowledged crash recovery. Three evaluation cases first failed before timeout binding/execution support, then passed.

Combined baseline checks passed217 tests and203 bootstrap subtests; all14 real-browser fixture checks passed in11.7s. OpenAPI/types regenerated with no diff; web type/lint/2 unit tests/production build passed; Ruff and strict application typing passed. The final integrated staged-harness check passed254 tests and207 bootstrap subtests, Ruff lint/format29files and mypy10sources. Python and all three npm audits reported no known vulnerabilities. Standalone package verification passed; the offline Kanban passed expansion/collapse and736px/320px checks with zero page errors or remote requests.

The requested semantic corrections require a distinct generation approach. An evaluation-only source-analysis/drafting candidate is implemented, independently reviewed and mock-tested, retaining original sources and treating intermediate analysis as untrusted. Its concrete maximum-ten-call preview awaits authorization; no staged live call has been made. It is not an active product workflow or a semantic guarantee. Do not repair benchmark output, weaken criteria or mark M1 complete because requests now finish. Unfamiliar-human handoff remains open.

Later update: the separately approved [staged live test](staged-generation.md) completed all10calls but retained the same2/5 final semantic pass count. Its allowance is consumed and the candidate is not promoted. The earlier waiting-for-authorization statements above describe that checkpoint.
