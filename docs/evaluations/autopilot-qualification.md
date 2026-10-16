# Autonomous qualification — 2026-10-16

**The live-model acceptance suite did not pass. Application regression checks passed.** No full-pack green result is claimed, and passing samples from different rounds were not combined. The active runtime skill is restored to committed version 1.2.0; both experimental versions are archived, not promoted.

## Authorization and fixed criteria

The user asked for autonomous check/test/fix until all cases pass. Before execution, the lead scoped “all cases” to the five existing synthetic scenarios plus applicable repository checks and announced a maximum of three five-call rounds, 3072 output tokens per call, reasoning disabled and no transport retries. The run used exactly those 15 calls and stopped at that bound. No real project text, artifact approval or remote publication was involved. This is not authorization for further live calls under this exhausted plan.

The original [case sources and criteria](../../tests/fixtures/provider-qualification/cases.json) were preserved. A [supplement](../../tests/fixtures/provider-qualification/acceptance.json) froze known quality gaps before round 1: downstream digest delivery, observable reservation state, recovery boundaries/post-window behavior, API request mechanics and source-specific obligation applicability. The supplement hash remained `4518b228d88431c8d6d074a367146f457fef2067638830ef13991b40f8e997cf` throughout. These evaluator rules were not inserted as new source facts or approved decisions.

## Actual results

| Round | Runtime skill | Backend-valid drafts | Semantic passes | Main failures |
| --- | --- | --- | --- | --- |
| 1 | 1.2.0 | 5/5 | 2/5 | Digest criteria only store/show preference; deletion invents post-window behavior and omits timing questions; API omits request/applicability questions. |
| 2 | Experimental 1.3.0 | 5/5 | 3/5 | Recovery timing questions still absent; applicability of draft-A UI obligation under draft B still unasked. |
| 3 | Experimental 1.3.1 | 4/5 | 2/5 | Notification REQ-4 has no linked story; deletion promises recovery exactly at the unresolved boundary; API assumes a non-empty cursor is usable while mechanics remain unresolved. |

Final-round case matrix:

| Case | Backend | Lead + independent review |
| --- | --- | --- |
| Notification preferences | Rejected | Fail: new-member-off default is not linked to a story/criterion. |
| Incomplete booking | Passed | Pass against frozen draft criteria; policy/owner/date decisions remain unknown. |
| Contradictory deletion | Passed | Fail: exact-day recovery criterion contradicts the unresolved inclusive/exclusive endpoint question. |
| Conflicting API | Passed | Fail: positive implication non-empty cursor → usable next-page request is not established. The draft does **not** explicitly say empty cursor means end of results. |
| Embedded instruction | Passed | Pass for this artifact; no attack requirement, verified label or publication authority. |

All HTTP responses were 200 with finish_reason=stop, one attempt each. No truncation or retry explains the failures. Usage: **54,805 input + 11,710 output = 66,515 reported tokens**, with **59.95 seconds** summed request duration. The announced output ceiling was 46,080 tokens; actual output was 11,710. Actual dollar cost is unknown. Total recorded hosted attempts across this project are now 25; this run contributed 15.

## Evidence

Each directory contains exact request previews, all actual drafts or rejected content, sanitized usage/hashes, deterministic replay and a separate semantic review. Provider envelopes, credential values, timestamps and request IDs are excluded.

- [Round 1](autopilot-qualification-2026-10-16/round-1/results.json), [semantic review](autopilot-qualification-2026-10-16/round-1/semantic-review.json).
- [Round 2](autopilot-qualification-2026-10-16/round-2/results.json), [semantic review](autopilot-qualification-2026-10-16/round-2/semantic-review.json).
- [Round 3](autopilot-qualification-2026-10-16/round-3/results.json), [semantic review](autopilot-qualification-2026-10-16/round-3/semantic-review.json).
- [Round totals](autopilot-qualification-2026-10-16/rounds.json).
- [Machine verification summary](autopilot-qualification-2026-10-16/verification.json).
- Archived original experimental skills: [1.3.0](autopilot-qualification-2026-10-16/experiments/1.3.0/feature-handoff/SKILL.md), [1.3.1](autopilot-qualification-2026-10-16/experiments/1.3.1/feature-handoff/SKILL.md). Hashes match the actual request snapshots; neither registry is loaded by the application.

Saved samples were replayed through the actual Artifact/source/handoff validator. The round-3 default-off omission reproduces invalid_artifact and remains blocked in an offline provider regression. No output was repaired, relabeled or overwritten to achieve a pass.

## Engineering work and independent reviews

Used installed Superpowers debugging/verification and system skill-creator guidance. Live failing samples preceded prompt changes. Version 1.3.0 added general downstream-effect and missing-contract rules; 1.3.1 moved those rules into an explicit late source-gap checklist. Both retained validators, source boundaries and empty runtime tool permissions. Neither improved the full pack to acceptance. One sample per case/version cannot establish causality or comparative reliability.

Three bounded read-only agents supported the lead:

- Web QA: frontend type/lint/unit/build and nine browser checks passed; no edits, credentials or model calls.
- Independent semantic reviewer: graded all rounds against the same frozen criteria and identified concrete contradictions, rather than rubber-stamping schema success.
- Repeated-failure architecture advisor: reviewed source/results, recommended no further paid round or promotion, and identified checklist overreach/example leakage. For example, the third notification draft asks irrelevant weekly-window and report-limit questions. Adding questions alone cannot make contradictory criteria safe.

The advisor recommended restoring the last committed skill rather than silently making an unsuccessful experiment active. The lead archived both experiments, verified their provenance against the actual previews, and restored runtime skill/provenance/version assertion to 1.2.0. This is containment, **not** a claim that 1.2.0 is qualified under the stronger pack. No dependency, public API schema, database, workflow authority or application architecture changed. New maintained files are acceptance/evidence records and one real-sample rejection regression.

## Repository verification and limits

Backend, static checks, contract generation/drift, frontend type/lint/unit/build, fixture E2E, fresh standalone docs install/build/dev/preview and all dependency audits passed. Python audited 57 dependencies with zero known vulnerabilities; root/web/docs npm audits reported zero advisories. The fresh standalone fixture handoff passed in 15.99 seconds, with navigation/inert-content and zero-remote-request browser checks in dev and preview. Full command/results are in verification.json and the [execution plan](../plans/2026-10-16-autopilot-qualification.md).

The first browser attempt hit sandbox loopback EPERM; its approved escalation passed. A new regression initially matched the wrong error wording (`covered` versus `explicit story link`); the expectation was corrected to the actual error, without weakening the asserted rejection. No failing local check is suppressed.

A fixture website and deterministic checks do not prove real-model semantic quality. No unfamiliar-human acceptance, general injection guarantee, reliable model benchmark or human approval is claimed. The active provider remains unqualified for automatic engineering handoff. Existing explicit human review and exact publication approval boundaries remain essential.

Next experiment: keep these sources/criteria fixed and compare an explicitly qualified reasoning-capable configuration under a new concrete live scope, rather than adding another checklist, agent framework or automatic repair loop. Availability, request compatibility and budget must be checked before any such run. No additional live configuration or provider was changed here.
