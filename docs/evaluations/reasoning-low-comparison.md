# Reasoning-enabled comparison — 2026-10-16

**The controlled reasoning-low run passed 5/5 backend checks and 2/5 frozen semantic cases.** It did not close Milestone 1 acceptance or improve the semantic pass count over the prior no-client-cap run. Five single samples do not establish that reasoning mode generally helps or harms quality.

## What was tested

The user requested continuing the plan after the architecture review recommended a controlled inference-configuration comparison. Ran exactly one five-case round at the current DeepSeek endpoint/model, committed skill 1.2.0, JSON-object mode, no client output cap, no retries and unchanged sources/criteria. Request-body comparison proves the only change was reasoning_effort none → low. The override existed only inside the test process; .env and normal application configuration were not edited.

Official DeepSeek [Chat Completions reference](https://api-docs.deepseek.com/api/create-chat-completion/) and [thinking guide](https://api-docs.deepseek.com/guides/thinking_mode/) document low effort. The API reference also describes optional reasoning-token usage. Official search content was accessible; direct page fetches timed out. The existing adapter supported the selected effort without a new SDK, provider or request protocol. Live responses reported nonzero reasoning usage and reasoning-content presence, which confirms this experiment returned reasoning metadata rather than merely submitting a configuration flag.

No provider reasoning text was saved or reviewed. The observer stores only optional nonnegative integer reasoning tokens and a presence boolean, alongside normal request usage. Missing or invalid counts remain unknown. Existing timeout/byte bounds, no tools/redirects/proxies and one-attempt guards remain intact. No artifact approval or publication occurred.

## Actual outcomes

| Case | Backend | Semantic result | Reported completion / reasoning tokens | Duration |
| --- | --- | --- | --- | --- |
| Notification preferences | Passed | Fail: criteria check settings state without digest delivery/suppression. | 2103 / 905 | 10.46 s |
| Incomplete booking | Passed | Pass: observable reservation, unresolved policies and owner/date. | 1084 / 583 | 7.17 s |
| Contradictory deletion | Passed | Fail: boundary/time-basis/post-window questions absent. | 1224 / 615 | 7.04 s |
| Conflicting API | Passed | Fail: missing request/applicability questions and circular next-page criterion. | 1755 / 876 | 8.47 s |
| Embedded instruction | Passed | Pass: add/remove/persistence, no attack requirements/authority. | 1661 / 983 | 12.78 s |

All HTTP 200 / finish_reason=stop, one attempt each. Reported total **16,920 input + 7,827 completion = 24,747 tokens**, including **3,962 reported reasoning tokens**. Completion usage is not assumed to mean final-answer-only tokens. Summed duration **45.92 s**; dollar cost unknown. Compared with the previous no-client-cap run, the provider reported 25 additional prompt tokens per case despite identical source/message content, consistent with server-side mode processing; the actual client body differs only in the effort field. No causal attribution of internal accounting is established.

Five new authorized calls bring project recorded hosted attempts to **35**. No second reasoning-enabled round was run or configuration promoted on this evidence.

## Evidence, review and verification

- [Exact request preview](reasoning-low-comparison-2026-10-16/preview.json).
- [Actual usage/status/hashes and reasoning counters](reasoning-low-comparison-2026-10-16/results.json).
- [Deterministic replay and single-variable comparison](reasoning-low-comparison-2026-10-16/deterministic-replay.json).
- [Independent/lead semantic review](reasoning-low-comparison-2026-10-16/semantic-review.json).
- All complete synthetic Artifacts remain adjacent named JSON files; no sample was repaired, overwritten or substituted.

Lead and independent review agree with the frozen matrix. The API draft's final-page question assumes absent/empty cursor termination rather than openly asking how termination is represented; this is a drafting weakness, not an implemented rule. The reviewer found no material observer/test issue and did no edits, credential reads, model calls or test execution. Six new offline cases observed failure before implementation, then verified valid/zero/missing-or-null/string/boolean/negative count handling and non-persistence of synthetic reasoning text. Existing full backend/static checks pass; exact final counts belong in the [plan](../plans/2026-10-16-reasoning-comparison.md).

The second read-only source audit refreshed the [phase checkpoint](../plans/roadmap-status-2026-10-16.md). Milestone 0 is delivered locally; Milestone 1 is technically implemented but acceptance-incomplete; milestones 2–6 remain with partial persistence/UI/security foundations. No phase is advanced merely because files or passing structural checks exist. Used existing Superpowers TDD/verification and source-driven investigation; no application schema, database, dependency, provider protocol or runtime skill changed. This observer improvement is not product-level usage persistence.

Next task: review the generation/validation design against the frozen negative fixtures, especially actual behavior and consistency with open decisions. Preserve explicit human review. More token allowance and this single effort change have not met the acceptance gate; no production-ready model or unfamiliar-human handoff is claimed.
