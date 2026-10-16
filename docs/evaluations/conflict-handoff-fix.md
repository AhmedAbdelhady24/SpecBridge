# Conditional conflict handoff: correction and live retest — 2026-10-16

**Both previously rejected cases now pass Artifact/source/handoff validation and their original narrow review criteria.** This is two targeted regression samples, not full provider qualification or an accepted engineering handoff.

## What changed

The [previous five-case evaluation](deepseek-out-of-sample.md) found missing story IDs in both conflict responses and non-exact source excerpts in the API case. It also found unconditional conflicting criteria and a reversed deletion-risk statement.

Runtime `feature-handoff` is now version 1.2.0. Its injected output contract lists all six Story fields, distinguishes `id` from `requirement_ids`, reinforces exact case/punctuation for source excerpts, and gives a complete settings-activation example with mutually exclusive policies. Every alternative story and criterion is conditional on human selection; lack of approval stays in dependencies/questions. The example is original project text, structurally validated against the actual Artifact model and sources. It uses neither of the two retest domains.

The opt-in runner now accepts repeated `--case` arguments. Selection is included in the preview and reconstructed from the checked-in pack before execution; changed selection/configuration/skill/sources invalidates the hash. Empty, duplicate or unknown selections fail before provider configuration. No output schema, validation rule, dependency, permission, database or auto-repair loop changed. The configured token limit remains 3072.

## Actual live execution

User approved “okay lets do that” after the explicit recommendation to strengthen story structure/conflict criteria and retest the two failures. Before network, the lead stated two calls at the existing 3072 cap each and no retries. Ran exactly `contradictory-deletion` and `conflicting-api` through `https://api.deepseek.com/chat/completions`, requested model `deepseek-flash`, JSON-object mode, reasoning disabled. No other case was rerun; no publication or artifact approval occurred.

| Case | Old result | New result | Prompt / output tokens | Duration |
| --- | --- | --- | --- | --- |
| Contradictory deletion | Missing story IDs | Valid; both alternatives conditional; correct risk direction | 3352 / 715 | 4.44 s |
| Conflicting API | Missing IDs and edited excerpts | Valid; IDs/excerpts correct; alternatives conditional | 3378 / 1069 | 6.64 s |

Both HTTP 200, finish_reason=stop, one attempt each. Total **6730 input + 1784 output = 8514 tokens**, **11.08 s** summed request duration. No truncation; dollar cost remains unknown. Inputs and source hashes are unchanged. The revised prompt adds 941 reported input tokens per case compared with the earlier run; this small experiment does not establish cost effectiveness or latency reliability. Ten hosted calls have now been recorded across all trials; further paid repetition is not included in this authorization.

- [Exact two-request preview and provenance/source hashes](deepseek-conflict-retest-2026-10-16/preview.json).
- [Actual results and usage](deepseek-conflict-retest-2026-10-16/results.json).
- [Deletion draft](deepseek-conflict-retest-2026-10-16/contradictory-deletion.json).
- [API draft](deepseek-conflict-retest-2026-10-16/conflicting-api.json).
- [Saved-sample checks and review boundary](deepseek-conflict-retest-2026-10-16/review.json).

Old rejected outputs were not edited. New evidence contains only synthetic drafts and sanitized metadata, without provider envelopes, request IDs, timestamps or credentials.

## Review, verification and remaining limits

Lead review and a bounded independent read-only reviewer both found the original narrow criteria satisfied. Both policies/API shapes remain traceable to their sources, the human decision is unresolved, IDs and links are complete, and criteria are explicitly conditional. The reviewer found no material issue in the code/prompt changes and ran 98 targeted offline tests. It neither read credentials, changed files nor made network calls.

Remaining handoff ambiguities are material to later refinement:

- API draft A specifies a `next_cursor` response field but no request parameter/mechanism. STORY-2 delegates advancement to a contract that is incomplete. A proposed edge case treats a cursor value as requestable; it is labeled recommendation and says the behavior is undefined, but request mechanics should be an explicit open question before implementation.
- Deletion still lacks precise 30-day boundary/timezone and post-window behavior. Do not infer a purge policy or settle retention from this sample.

Tests prove structural rejection and source-excerpt checking, not semantic entailment. The two known failures were reused for targeted retesting; the other three cases were not rerun under version 1.2.0, and no new held-out quality set or unfamiliar human handoff has passed. A matching preview hash binds payload/configuration, not human authorization by itself. Prompt examples cannot make a draft approved.

Used system skill-creator and Superpowers TDD/verification. Five new selection/prompt tests failed before implementation, then passed. Saved rejected responses are regression fixtures: still rejected for missing IDs; after explicit in-memory ID correction the API case still fails excerpt policy, while exact excerpt corrections pass. These test-only corrections never modify provider output or stored evidence. Actual final test/lint/type/skill-validation results are recorded in the [execution plan](../plans/2026-10-16-conflict-handoff-fix.md). Scope is runtime guidance, runner/tests and evidence; no UI/exporter changes or new browser/build claim.

Next: review the drafts with the product/API owner, collect the missing cursor and retention decisions, and exercise one reviewed model artifact through the existing human-review/ZIP/local-website flow. Keep broader held-out qualification and product usage persistence separate. Do not keep adding worked answers or paid retries to hide unresolved information.
