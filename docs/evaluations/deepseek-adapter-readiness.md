# DeepSeek adapter readiness — 2026-10-16

Status: adapter implemented and mock-tested. The first approved live request was accepted but truncated; a later explicitly authorized measurement completed and passed structural/source validation. See [complete response, selected limit and quality gaps](deepseek-complete-response.md). The remainder records the initial readiness/first-call evidence.

The existing compatible adapter now accepts explicit `json_object` mode. It sends the Artifact schema in the system instructions, requests JSON-object output and applies the same Pydantic/source validators after parsing. `json_schema` remains the default. There is no automatic format fallback or retry. `SPECBRIDGE_LLM_MAX_TOKENS` accepts 1–16384 (default 4096); JSON-object requests send `max_tokens`, strict-schema requests send `max_completion_tokens`. An explicitly non-stop completion reason is rejected even if content happens to parse as JSON. Providers omitting finish_reason retain existing behavior: local parsing/validation remains required.

Changed paths: `services/api/specbridge/providers.py`, provider tests, `.env.example`, README, scoped plan and execution/evaluation documents. Local `.env` received output-mode/token-cap settings while the existing key line was preserved exactly. An optional `SPECBRIDGE_LLM_REASONING_EFFORT` is also supported (`none`, `low`, `medium`, `high`); it is omitted when unset. After the first live truncation, local DeepSeek configuration was changed to `none` without raising the cap. Its request behavior is mock-tested; a second live call needs separate authorization. No public response schema, dependency, workflow interface or runtime tool permission changed.

Used the TDD and verification-before-completion methods. Lead implemented and reviewed the narrow diff; no subagent was needed. New JSON-mode/configuration and completion-status tests failed before implementation. Additional malformed-choice regressions exposed an AttributeError during the finish-reason change; validating the choices container/item types corrected it. HTTP-failure tests now cover both formats and assert one attempt, preserving the no-fallback/no-retry rule.

Actual verification:

- Full suite: 116 tests plus bootstrap link/source subtests passed.
- Ruff lint/format and strict mypy: passed.
- Browser fixture/security suite: 9/9 passed in 5.1 seconds.
- Environment loading: nonempty key detected, 0600 confirmed; initial uv default-cache sandbox refusal resolved using project-local `UV_CACHE_DIR` with `--no-sync`. No new package or permission change needed.
- Configured destination/model: `https://api.deepseek.com`, `deepseek-flash`, JSON-object mode, 4096 output-token cap. A mock transport captured the actual credential-free request body in ignored local `.cache/deepseek-smoke-preview.json`. It contains only the runtime instructions/schema and a synthetic CSV-export brief. The preview used a dummy credential and made zero live calls.

Prepared next action: one smoke call, no retries, using the synthetic brief “Customers need to export their saved reports as CSV. Exports must include column headers. Owner, delivery date, maximum report size, and permission rules are unknown.” The operator explicitly approved one smoke request with this synthetic brief, a 4096 output-token cap and no retries. The call result is recorded separately; no broader live run is authorized by that approval.

## First approved live request

Exactly one attempt to the reviewed endpoint/model returned HTTP 200 in 22.55 seconds. DeepSeek reported 1471 prompt tokens, 4096 completion tokens and 5567 total tokens. Its `finish_reason` was `length`; SpecBridge raised sanitized `incomplete_response` and accepted no Artifact. No retry occurred and no package was approved/published. [Exact sanitized result](deepseek-smoke-2026-10-16.json). Actual dollar cost is unknown; no pricing inference was made.

This proves the key/endpoint accepted that request. It does not prove a complete usable model artifact or factual quality. The observed failure is token-budget exhaustion. DeepSeek documents thinking enabled by default; its contribution was not captured, so it remains a hypothesis rather than a measured explanation. A second preview keeps the exact synthetic input/token cap and adds only `reasoning_effort=none`, a documented way to disable thinking. The operator has been asked to approve one additional attempt. Until that approval, no second request will be sent.

Remaining: complete artifact/model compatibility, application-level usage accounting and semantic quality need actual qualification. The token cap is not a dollar budget, and a total HTTP deadline does not guarantee remote billing stops. DeepSeek thinking/output behavior under this cap may cause truncation; report that result rather than retry or raise the budget silently. Native Claude and local-model support are outside this change. Continue with the [hosted qualification proposal](../plans/2026-10-16-hosted-provider-qualification.md), including human-reviewed references and per-request usage metadata, before claiming full Milestone 1 acceptance.
