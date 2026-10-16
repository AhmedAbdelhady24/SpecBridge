# Revised handoff rules: live check — 2026-10-16

The user authorized continuing with the prepared revised-prompt test. Exactly one request used the same synthetic CSV-export brief, DeepSeek `deepseek-flash`, runtime skill 1.1.0 with its output contract injected, `reasoning_effort=none`, 3072 maximum output tokens and no retries. Earlier requests were not repeated. Overall live calls so far: 3.

## Observed result

HTTP 200, `finish_reason=stop`, completed in 3.02 seconds. DeepSeek reported 2383 prompt tokens + 610 completion tokens = 2993 total tokens. The Artifact/source and current handoff-policy validators passed. The response contains 2 requirements, 1 story and 4 open questions. The configured output limit remains 3072; it was not reduced from one short response.

- [Complete generated draft](deepseek-handoff-rules-live-draft.json).
- [Sanitized result, usage, hashes and targeted checks](deepseek-handoff-rules-live-result.json).
- [Injected rules and implementation verification](handoff-rules-results.md).

The original two defects are absent in this case:

| Check | Actual response |
| --- | --- |
| Unstated story motivation | No external-tools benefit or “so that” clause |
| Synthesized wording labeled as evidence | Constructed story uses recommendation; user-provided scope/requirements quote the source exactly |
| Headers requirement omitted from links | STORY-1 explicitly links REQ-1 and REQ-2, with separate observable criteria for CSV data and headers |
| Unknowns turned into requirements | Owner, date, maximum size and permissions remain dependencies/questions; only the two supplied requests are requirements |

The extra empty-report edge-case check is labeled recommendation, rather than attributed to the source. No owner, deadline or numerical business target was invented in this response. These conclusions are deterministic checks plus lead inspection of the recorded sample, not an unfamiliar human's acceptance decision.

## Evidence and limits

The transport checked the outgoing body against the prepared preview before transmission and allowed exactly one attempt. Response bytes were bounded, credentials were checked absent from saved response bytes, and only sanitized metadata plus the synthetic Artifact are committed. The full response envelope stays in ignored local `.cache/deepseek-handoff-rules-response.json`; provider request IDs and timestamps are not published. Actual dollar cost was not calculated.

This is a targeted regression success, not general semantic qualification. The prompt's worked example also uses CSV export, so the evaluation is not out-of-sample and may benefit from that overlap. The result does not establish performance on other feature domains, contradictions, conflicting API references or adversarial documents. Excerpt matching does not prove contextual truth; ID coverage does not prove every criterion is semantically sufficient.

No artifact approval, Jira/Git write, remote publication or documentation overwrite occurred. The original model draft and lead-corrected example remain unchanged, separate evidence. No new production code or dependency changed in this step; files changed are evaluation records, current status/plans and README. Existing TDD/verification methods were used; no subagent was needed for the one-call measurement. The next task is the bounded out-of-sample qualification pack and human review described in the [provider plan](../plans/2026-10-16-hosted-provider-qualification.md), with any further live calls explicitly budgeted and authorized. Full Milestone 1 acceptance remains open.
