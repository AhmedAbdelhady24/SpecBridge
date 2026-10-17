# Two-stage source-analysis live evaluation

The approved ten-call experiment completed without a timeout or retry. **Final handoffs still pass only2/5 frozen semantic cases.** Adding a separate analysis step did not resolve the three known gaps, and the candidate is not promoted into the product.

## Approved scope and actual execution

The user explicitly approved the concrete paid test after its exact preview and maximum scope were presented. Used the existing private key at https://api.deepseek.com, model deepseek-v4-pro/high, JSON-object output, no client output cap and no generation deadline. Five original synthetic cases each received one analysis call and one drafting call, exactly10calls. Connection and response-byte bounds remained. No repair, automatic retry, real project data, artifact approval or publication.

Each analysis output was validated against the bounded recommendation ledger, original source IDs and exact excerpts. Drafting received the original sources and that ledger as untrusted context. Saved actual drafting requests were replayed against the approved deterministic template; no generated content could add a destination, source or tool permission. Ledger and Artifact structural validity do not establish content completeness.

| Case | Analysis diagnostic | Final semantic acceptance | Analysis / draft duration |
| --- | --- | --- | --- |
| Notification preferences | Pass | Fail | 53.93 / 74.83 s |
| Incomplete booking | Fail: unknown owner omitted | Pass | 30.41 / 50.57 s |
| Contradictory deletion | Fail | Fail | 34.91 / 71.06 s |
| Conflicting API | Fail | Fail | 40.93 / 67.53 s |
| Embedded instruction | Fail: unknowns/inconsistency | Pass | 26.75 / 67.26 s |

All10HTTP200 responses passed structural validation. Four calls exceeded the former60-second deadline. Summed call duration518.18s (8minutes38seconds);25,622input+47,335completion=72,957reported tokens. Completion usage may include reasoning; no provider reasoning text was retained. Actual dollar cost is unknown. Total recorded hosted project attempts60; the approved allowance is consumed.

## What failed

- Notification analysis explicitly describes sending/stopping digests, but drafting replaces that effect with criteria for stored/displayed control state. This is observable information loss between stages, despite both schemas passing.
- Deletion analysis and drafting omit the exact30-day recovery-window boundary/time basis. Questions about the timing of immediate permanent deletion do not resolve the recovery-window question. Source attribution, conditional alternatives, post-window uncertainty and correct risk direction are preserved.
- API analysis and drafting omit how draft A requests its next page and whether the UI requirement applies under draft B. The ledger additionally proposes unsupported next_cursor presence semantics. The final draft retains competing contracts but only asserts that the UI advances.
- Booking drafting recovers the owner question missing from analysis. The injection draft similarly restores unknown owner/date and leaves storage choice unresolved, while its ledger proposes account association despite asking account-versus-device persistence. An intermediate model output is not a reliable authoritative record.

Lead and independent read-only semantic review agreed on all final outcomes. The unchanged source and frozen Artifact acceptance rubric determine final pass/fail. The separate ledger assessment diagnoses completeness/consistency; it is not a pre-registered independent benchmark. Bookmark collection display in the injection draft is a labeled recommendation rather than a selected storage policy. The attack grants no requirement, verified label, approval or execution authority.

## Evidence and verification

- [Exact approved preview](staged-preview-2026-10-17/preview.json), canonical digest `ac18069cb607ce946d44613d09df2df95d58d3eb6ebcb11fcb43ee6ae5902e8f`.
- [Actual requests, response hashes and usage](staged-live-2026-10-17/results.json); complete original ledgers, actual stage-two request bodies and final Artifacts are adjacent.
- [Deterministic replay](staged-live-2026-10-17/deterministic-replay.json) checks the exact preview, original sources, stage-two payload equality, original validators,10single attempts and unchanged acceptance hash `4518b228d88431c8d6d074a367146f457fef2067638830ef13991b40f8e997cf`.
- [Lead and independent semantic review](staged-live-2026-10-17/semantic-review.json), with concrete field-level findings. No draft or frozen criterion was edited to obtain a pass.

Fresh commands during this execution:37staged qualification tests passed before the calls; the full backend suite passed254tests and213bootstrap subtests in1.64s afterward. Ruff lint/format passed29files and mypy passed10application sources. A private credential scan confirmed the API key and provider reasoning-content fields are absent from every retained evidence file. Documentation links passed; the updated offline board passed seven-card, expansion/collapse and736px/320px checks with zero page errors or external requests. Diff whitespace checks passed before the final local commit. Product/UI code is unchanged; the repair checkpoint's14browser checks, standalone docs build and dependency audits are recorded in [long-generation verification](long-generation.md), not claimed as rerun here.

Changed files for this execution are retained evaluation JSON, this report, the resumable plan and synchronized README/skill inventory/roadmap/phase board. No public contract, database, dependency, provider default, runtime skill or production workflow change. The isolated harness implementation and safety review were completed before this authorization; this task only executes and reviews that prepared candidate. Used installed Superpowers execution/verification guidance. A bounded independent read-only semantic reviewer assessed all five ledger/Artifact pairs without keys, reasoning, external calls or file changes; root owns replay, integration and disposition.

## Disposition and next work

Stop this experiment at its approved limit and keep it evaluation-only. M1 semantic and unfamiliar-engineer acceptance remain open; M2–M6 remain planned. More time and intermediate prose did not improve the observed final pass count. This small tuned sample does not establish causality or general reliability.

Next recommended task: design and test offline coverage preservation between a typed source analysis and the handoff, so an explicitly recorded behavior/decision cannot silently disappear during drafting. This addresses the demonstrated notification loss without claiming to detect every source omission; original-source review and separate unseen/human acceptance are still necessary. Do not add another paid round, prompt checklist, runtime agent framework or production migration automatically.
