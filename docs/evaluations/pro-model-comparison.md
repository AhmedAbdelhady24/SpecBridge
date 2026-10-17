# Pro model comparison — 2026-10-17

The approved five-case round yielded **one semantic pass, two semantic failures and two timeouts with no assessable draft**. Three complete artifacts passed backend validation. The round does not qualify the model or close Milestone 1; no active configuration was promoted.

## Exact scope and results

The user's “okay continue with the plan” followed the explicit new-model approval request and approved this prepared round. Exactly five synthetic requests ran at the existing DeepSeek endpoint with the local key. Request bodies match the prior high-effort baseline except model deepseek-flash→deepseek-v4-pro. Skill1.2.0, sources/order, schema, JSON-object mode, high effort, omitted client token caps, 60-second whole-request deadline and 256KiB response bound were preserved. There were no retries, repairs, real project inputs, settings changes or publication.

| Case | Transport/backend | Semantic result | Reported completion / reasoning tokens | Duration |
| --- | --- | --- | --- | --- |
| Notification preferences | Timeout; HTTP200 headers, no complete body | Not assessable | Unknown | 60.01 s |
| Incomplete booking | Backend-valid | Pass: observable reservation; constraints remain open | 3701 / 3149 | 38.48 s |
| Contradictory deletion | Backend-valid | Fail: boundary/time basis missing; dependency claims incompatible requests can both be satisfied | 5320 / 4452 | 50.70 s |
| Conflicting API | Backend-valid | Fail: continuation mechanics/applicability questions missing; unsupported protocol/applicability commitments | 5746 / 4600 | 54.82 s |
| Embedded instruction | Timeout; HTTP200 headers, no complete body | Not assessable | Unknown | 60.01 s |

All five were attempted once. Three complete replies had finish_reason=stop; timeouts have no complete final response, finish reason or usage. Their partial transport data was not saved, so no partial reasoning text is persisted. Timeout is a delivery-budget failure, not evidence that the absent draft would fail semantic review.

Known usage from **three of five requests**: **10,283 input + 14,767 completion = 25,050 tokens**, including **12,201 reported reasoning tokens**. This is not a complete billing total; both timeout requests have unknown usage and dollar cost is unknown. Completion usage includes reported reasoning rather than being assumed final-answer-only. Summed request time: **264.02 seconds**. Five new hosted attempts bring the project record to **45**. This allowance is consumed.

Only the requested client model changed. We cannot establish underlying model identity, provider-version stability or causal quality effects from these small alias-based samples. The Pro proposal used the current official model table at preparation time; no stronger-quality assumption was used in grading. No timeout or failed sample is replaced by a passing sample from another round.

## Evidence and review

- [Exact executed preview](pro-model-comparison-2026-10-17/preview.json), bound to canonical digest `11154ee258d2e26a51f643cebea1d6962f9f218db63db57a77926fd5759a6341` and the previously reviewed proposal.
- [Actual transport, usage and response hashes](pro-model-comparison-2026-10-17/results.json).
- [Single-variable comparison and real-policy replay](pro-model-comparison-2026-10-17/deterministic-replay.json).
- [Lead and independent frozen-rubric assessment](pro-model-comparison-2026-10-17/semantic-review.json).

Three complete Artifacts are retained adjacent to the evidence. There is intentionally no artifact for either timeout. Replay passes all three through current Artifact/source/handoff policy; transport failures are marked non-replayable without content rather than represented as validator failures. The source fixtures and frozen acceptance supplement are unchanged; supplement hash remains `4518b228d88431c8d6d074a367146f457fef2067638830ef13991b40f8e997cf`.

The read-only semantic reviewer agreed with the lead: booking passes; deletion and API fail on specific missing decisions and contradictions. It did not access credentials, call providers, modify files or execute tests. Lead owns execution, request comparison, replay, grading, documentation and board updates. Used installed versioned Superpowers verification guidance. No implementation agent/worktree was needed: application, runtime skill, contract, database and dependency code did not change.

Final local verification: 173 tests and 203 bootstrap subtests passed in 1.40 seconds; Ruff lint passed; all 27 Python files passed formatting; mypy passed for 10 application sources; diff check passed. The refreshed offline phase-board export passed seven-card expansion/collapse, 736px/320px overflow checks, zero page errors and zero external requests. Canonical board and browser export both reflect this result. Application E2E and documentation package installs were not repeated because application/exporter/template code did not change; earlier checks remain historical evidence rather than fresh claims.

## Decision and next task

Stop this model-selection experiment without promotion. Under unchanged application limits, Pro did not complete all five cases and the completed conflict drafts retained the known semantic gaps. This does not establish that Pro is generally worse or incapable; a different timeout would be a different experiment.

The next distinct hypothesis is an evaluation-only two-stage flow: extract source-attributed behaviors, conflicts and unresolved prerequisites, then draft the existing Artifact using that ledger **and the original sources**. Keep the ledger untrusted, inspect extraction and synthesis failures separately, and add no automatic judge or repair loop. Design and offline checks precede any new live scope; the consumed five-call approval does not authorize ten additional calls. Human correction/review remains essential, and unfamiliar-engineer handoff is still outstanding. Milestone 1 stays in progress; milestones2–6 remain.
