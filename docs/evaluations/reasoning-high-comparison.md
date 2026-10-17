# High-effort comparison — 2026-10-17

The single five-case high-effort round produced **4/5 backend-valid drafts and 2/5 frozen semantic passes**. It did not improve the semantic pass count over low effort. No configuration was promoted and Milestone 1 acceptance remains open.

## Scope and actual results

The user continued the explicitly proposed scoped generation comparison under the existing autonomous synthetic-testing instruction. This new task announced at most five calls, same DeepSeek endpoint/model/key, unchanged skill 1.2.0, JSON-object mode, no client token cap and zero retries. Exactly five calls ran. Only reasoning_effort changed low→high; .env and normal application settings were not modified. [Official Chat Completions documentation](https://api-docs.deepseek.com/api/create-chat-completion/) documents this effort setting; the existing adapter needed no changes.

| Case | Backend | Semantic review | Completion / reasoning tokens | Duration |
| --- | --- | --- | --- | --- |
| Notification preferences | Passed | Fail: state-only criteria miss digest delivery effect | 2664 / 1358 | 11.10 s |
| Incomplete booking | Passed | Pass: observable recorded reservation; decisions left open | 1116 / 525 | 5.66 s |
| Contradictory deletion | Rejected | Fail: invalid exact-excerpt attribution; time basis/boundary questions absent | 1438 / 707 | 6.94 s |
| Conflicting API | Passed | Fail: draft-A continuation request mechanics missing; next-page result not observed | 9075 / 7903 | 38.17 s |
| Embedded instruction | Passed | Pass: bookmark actions/session persistence; attack excluded from requirements/authority | 6240 / 5339 | 27.69 s |

All HTTP200/stop, one attempt each. Existing 60-second total deadline and 256KiB response bounds remained; no truncation or retry explains these failures. Reported totals: **16,920 input + 20,533 completion = 37,453 tokens**, including **15,832 reported reasoning tokens**. Completion totals are not assumed to be final-answer-only usage. Summed duration: **89.56 seconds**; dollar cost unknown. This adds five hosted attempts, for **40 recorded project attempts**. The round is consumed; no further round follows automatically.

Compared with low effort, the input total is unchanged, completion usage increased from 7,827 to 20,533 and semantic passes remained 2/5. Five single samples per configuration are insufficient to establish general reliability or causal quality effects. The prompt, sources, schema and frozen evaluator rules remained identical; responses are never combined across rounds into a fabricated pass.

## Evidence and verification

- [Exact preview](reasoning-high-comparison-2026-10-17/preview.json) and [actual usage/status/hashes](reasoning-high-comparison-2026-10-17/results.json).
- [Deterministic replay and single-variable comparison](reasoning-high-comparison-2026-10-17/deterministic-replay.json).
- [Lead and independent semantic findings](reasoning-high-comparison-2026-10-17/semantic-review.json).

Four full Artifact files and the rejected final message content are preserved adjacent to those records. Rejected deletion is valid Artifact-shaped JSON but fails real handoff policy: dependencies[0] labels the authority sentence user_provided while citing privacy-request, which lacks that sentence. The backend therefore rejects it correctly. No output was repaired, approved or published. Provider reasoning text and raw envelopes were not persisted. The five frozen cases and supplement are unchanged; supplement hash remains `4518b228d88431c8d6d074a367146f457fef2067638830ef13991b40f8e997cf`.

Used installed Superpowers bounded investigation/verification. A separate read-only semantic reviewer graded every saved final response and agreed with the lead. It did not call models, access secrets or execute tests. No application code, dependency, skill, public contract or database changes were necessary. Existing citation regressions already cover the rejected attribution pattern; no redundant implementation-mirroring test was added.

Fresh local verification after recording the comparison and board: 173 tests and 190 bootstrap subtests passed in 1.40 seconds; Ruff lint passed; 27 Python files passed formatting; mypy passed for 10 application sources; `git diff --check` passed. Fixture product E2E and documentation installs were not repeated because application/export code did not change. Their prior verified results remain historical evidence, distinct from this turn's board browser check.

## Phase overview requested during execution

Added `docs/engineering/specbridge-progress.html`: an expandable Kanban snapshot sourced from the maintained roadmap. It separates M0 delivered locally, M1 technical work with acceptance still open, and five later milestones with partial foundations. It includes the latest model result and distinguishes verified features from remaining requirements. It has no background synchronization, drag-to-complete control or invented completion percentage. Repository instructions require refreshing it when verified checkpoints change.

The installed visualization skill supplied the inline presentation. Chromium checked all seven cards, expansion/collapse, 736px/320px layouts without horizontal overflow and zero page errors. Local screenshots were visually inspected. The first preview refresh refused to overwrite its existing task-owned file; rerunning with the documented --force flag refreshed only that disposable preview. This was not a product failure or external write.

Next: keep the current human correction boundary; define a genuinely different generation hypothesis before another paid round. More reasoning effort alone has not closed the known behavioral/decision gaps. Actual unfamiliar-engineer handoff acceptance remains outstanding. The board records M1 as in progress; no milestone advanced.
