# Typed-plan live qualification — 18 October 2026

The corrected candidate passes **5/5 frozen semantic cases in one live round**, with all five original-source/Artifact validations passing. Lead and independent read-only review agree. This closes the recorded candidate's five-case qualification target; runtime adoption and unfamiliar-engineer acceptance remain open. The current application still uses runtime skill1.2.0 and its configured provider; no default or private key was changed.

## Results and actual execution

| Original case | Compiled0.1 round | Corrected0.2 round |
| --- | --- | --- |
| Notification preferences | Pass, with cross-link defect | Pass |
| Incomplete booking | Rejected Context structure | Pass |
| Contradictory deletion | Fail: invented post-window policy | Pass |
| Conflicting API | Fail: dependent UI/protocol assumptions | Pass |
| Embedded instruction | Pass, with duplicated compound requirements | Pass |

The initial five-call round remained2/5; it is preserved unchanged. After offline correction and review, a separate complete five-call round passed5/5. No case was borrowed from another round, no response was repaired, and no frozen source or criterion was edited. Additional active handoff defects in the first round are recorded separately from its frozen score.

User authorization was the explicit instruction to resolve the quoted pending paid retest until5/5. Execution stayed within two concrete five-call previews. Both used https://api.deepseek.com/chat/completions, deepseek-v4-pro/high, JSON-object output, synthetic original briefs only, zero retries, no client output-token cap and no generation deadline. Connection and response-byte safeguards remained; six calls exceeded60seconds. No model-generated code, external integration write, artifact approval or publication occurred.

| Round | Actual calls | Input / completion / total reported tokens | Sum of call durations |
| --- | --- | --- | --- |
| Compiled0.1 | 5 | 11,000 /31,321 /42,321 | 311.46s |
| Corrected0.2 | 5 | 14,000 /33,657 /47,657 | 325.74s |
| This execution | 10 | 25,000 /64,978 /89,978 | 637.20s |

Recorded project hosted attempts now 70, previously 60. Dollar cost is unknown. Reported completion usage may include reasoning; provider reasoning text and raw response envelopes were not retained.

## Why the correction worked on these outputs

One generated typed plan is deterministically assembled into the Artifact. Recorded outcomes and questions survive without a second generative rewrite. The correction addresses defects demonstrated by the first round:

- Context's existing exclusive evidence-or-question rule is now expressed in the model-facing JSON schema and examples. Unknown owner/date use null evidence plus a question.
- Conflict alternatives now group behaviors. Draft A's response and dependent UI share one selectable alternative; the compiler conditions every grouped story and criterion on that same human decision.
- Criteria are restricted to their source behavior, with atomic excerpts or complete coverage of a compound excerpt. Unrelated security criteria and half-implemented duplicate bookmark requirements disappear in the new outputs.
- Guidance distinguishes observable source effects from policy invention. Open decisions cannot also be asserted as outcomes. The new deletion draft leaves post-window behavior unresolved; the API draft leaves request mechanics and draft-B UI applicability unresolved.

There is no case-name routing, benchmark answer table, new agent framework or dependency. Compiler checks cannot establish that extraction found every fact or chose every relevant group. Semantic review remains necessary.

## Retained, independently inspectable evidence

- Initial [approved preview and call results](compiled-live-2026-10-18/results.json), [semantic findings](compiled-live-2026-10-18/semantic-review.json), and [exact replay including reproduced rejection](compiled-live-2026-10-18/deterministic-replay.json).
- Corrected [exact preview](compiled-preview-v2-2026-10-18/preview.json), canonical SHA256 `aace7d6e533e4d9435a470718ffa27c0c0c5357b8b7660bb0b78ab5ae2207efb`.
- Corrected [actual single-attempt calls, hashes, duration and usage](compiled-v2-live-2026-10-18/results.json), [field-level semantic review](compiled-v2-live-2026-10-18/semantic-review.json), and [deterministic replay](compiled-v2-live-2026-10-18/deterministic-replay.json).
- Complete original plans, compiled Artifacts, trusted compiler source snapshots, skill text and hashed provenance are adjacent to each round's results. The rejected booking JSON is retained separately. Snapshots are engineer-authored code, never generated model code.
- Replays verified both exact preview digests, original synthetic sources, one attempt per case, original validators, compiler/provenance hashes and byte-identical compiled Artifacts. Frozen acceptance SHA256 remains `4518b228d88431c8d6d074a367146f457fef2067638830ef13991b40f8e997cf`.

## Verification, review and limits

Two added component checks were observed RED before the correction, then GREEN; four malformed-group regressions cover overlap, duplicate alternative IDs, unknown IDs and repeated members. Full backend suite 305 tests and 247 subtests passed, including 30 compiler/runner tests. Bootstrap unittest checks passed. Ruff lint/format, application mypy, skill validation and diff checks passed. The system-Python skill validator initially lacked PyYAML; the locked project interpreter passed. A Ruff mutable-config warning was corrected. No failures are suppressed and no dependency was installed.

A private scan found neither the API key nor provider reasoning-content fields in retained round evidence. Source/rubric files and application contracts are unchanged. Product UI/runtime code is unchanged, so prior M2 browser/build/audit evidence is retained in [Milestone2 verification](milestone-2.md); those product checks are not claimed as rerun here. The updated offline board passed seven-card, expansion/collapse, visible5/5checkpoint and736px/320px checks with zero page errors or external requests; expanded mobile content was visually inspected.

Used versioned Superpowers debugging/TDD/review/verification guidance and the installed system skill-creator. One existing bounded read-only reviewer assessed source changes and every live output without keys, reasoning, writes or model calls. Root owns code, execution, deterministic replay, integration and final disposition. Code changes are limited to `scripts/handoff_plan.py`, its regressions and the original experimental skill/provenance; remaining changes preserve evidence and synchronize documentation.

A consistency check during review distinguished an explicit queued-message policy from ambiguous next-send wording, applying the same frozen gate across rounds. Notification cutoff wording remains a clarification for human handoff; this score does not silently settle it. No remaining cross-link or partial compound-requirement defect was found in this round. One sample on a tuned pack is not broad reliability or unfamiliar-human acceptance, and empty optional Artifact sections are not a complete general-purpose PRD.

Next task: integrate the qualified plan/assembler into the application through an explicit provider path, validate its workflow/recovery/skill provenance boundaries, then run unseen cases and an unfamiliar-engineer handoff. Do not mark M1 complete, approve these drafts or silently promote a different provider configuration from this benchmark alone. M0 and M2 remain delivered locally; M3–M6 remain planned.
