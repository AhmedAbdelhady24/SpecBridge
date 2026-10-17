# Milestone 2 verification

The local persistent-knowledge milestone is implemented. The user explicitly authorized executing it while Milestone 1's model and unfamiliar-human acceptance remain open. This is separate from the unqualified2/5 model result; no new hosted call or provider promotion occurred in this work.

## Functionality and boundaries

Seven project knowledge types now have append-only versions, stable IDs, project-scoped evidence and version-bound concurrency digests. Search retrieves bounded current knowledge/original-source context with deterministic ranking. Explicit selection captures an immutable labeled source for generation, preserving the entry/version reference. Artifact and knowledge history can be browsed; archived entries remain in history and are excluded from active context.

Human verification is a distinct saved-version action with original evidence, note and strict boolean confirmation. Unsaved substantive changes block verification, edited payloads clear confirmation, and saving any edit removes prior verification. A knowledge record or retrieved instruction cannot approve a package. Generated user_provided claims cannot cite non-user-provided knowledge as original facts.

Schema 1→2 migration preserves all preexisting table rows, checkpoint state, reviews, approvals and package ZIP bytes. Private SQLite backup/restore refuses overwrite and validates integrity/foreign keys. [Actual clean recovery evidence](milestone-2-recovery.json) exercises the CLI, reconnects to a restored workspace and resumes a workflow using its exact stored context. [Recovery instructions](../engineering/workspace-recovery.md) and [ADR](../decisions/0002-versioned-project-knowledge.md) describe the implementation and limits.

## Actual verification

[Machine-readable verification](milestone-2-verification.json) records the final command outcomes.

The full 18 browser cases passed in 14.4s, including all original handoff/security flows plus knowledge durability/context selection, verification reset, delayed cross-project selection and unsaved-content verification. Web typecheck/lint,2 client tests and production build passed after the final review correction. The standalone documentation package passed clean install/build/dev/preview in 15.17s. Python and all three npm lockfile audits reported no known vulnerabilities. OpenAPI/types were regenerated twice with no subsequent generation drift.

Final backend verification passed299tests/232bootstrap subtests in2.05s, Ruff lint/format38Pythonfiles and mypy11application sources. Full command evidence is also in the execution plan. The earlier combined run passed 298 tests/221 bootstrap subtests; an additional migration preservation regression was added after independent review, then both migration cases passed. Ruff and strict application typing passed. The maintained recovery runner completed successfully using fixture data and private 0600 backup output. No real user database, token or provider key was used by those checks.

## Findings and corrections

- Tests first observed missing knowledge/history routes and schema migration; implementation then passed. Backup tests first observed missing utility, then passed restore/privacy/no-overwrite/invalid-input and uncommitted-write cases.
- Three code-review edge cases reproduced before correction: content reversion revived an old edit digest; archived knowledge snapshots reappeared as current context; snapshots could supply circular verification evidence. Identity/version-bound digests, original-source filtering and verification restrictions fixed them.
- A numeric1passed the original literal-true confirmation validator. A strict boolean plus explicit true check now rejects it; regression first failed then passed. UTF-8 limits also first failed, then passed with a snapshotable byte bound.
- Browser checks found ambiguous label associations after select/textarea values changed; explicit label IDs fixed both flows. Failed traces were retained locally. A later narrow-screen test with a long unbroken context value exposed overflow; expandable selected context and safe wrapping fixed it, and the full 18-browser suite passed at 360px for that flow.
- A cross-project async selection regression was proven by removing the project guard: a B request received A's context (two sources instead of one). Restoring the guard passed the complete suite; server project isolation also rejected the invalid request.
- Independent review found one Important UI mismatch: verification could apply to saved claim A while unsaved claim B was displayed. The new browser regression failed against that behavior; verification is now disabled until saving and confirmation clears on changes. All18browser tests passed afterward.
- Review also identified missing direct migration evidence for revisions/checkpoints. The expanded case now compares every preexisting table and original approved ZIP, and reconnects to unchanged workflow state. Its initial assertion used pre-approval state; the baseline was corrected to the actual published state before migration, without changing product behavior.

The independent backend/contract reviewer inspected actual project isolation, concurrency, verification, classification, migration and backup paths, then the UI context/verification and recovery runner. No other material finding remains from that scoped review. The earlier architecture advisor hit a usage limit and did not produce a review; it was not counted as a successful review. Lead owns implementation/integration and the final correction pass. No overlapping implementation agent edits.

## Files, methods and remaining work

Backend changes are models/storage/providers/main plus the dedicated knowledge module; new backup and recovery scripts; generated OpenAPI/TypeScript contracts; KnowledgePanel/App/styles; backend/browser regressions; this evidence, plan, ADR and onboarding. No new dependency/service or database engine. Existing installed Superpowers debugging/TDD/verification and frontend UI engineering guidance were used; system skill-creator guided the separate original handoff-plan experiment.

No known failing check or unaddressed material M2 review finding remains at this checkpoint. This is scoped evidence, not a guarantee that unknown debt does not exist. Lexical search, local-only authorization and bounded recent-history UI are deliberate constraints; semantic retrieval, a full dashboard and external/multi-user operations remain later milestone scope.

M1 semantic qualification is still open. The typed-plan/deterministic-assembly candidate fixes recorded outcome loss in offline regressions, but its new five-call live preview awaits explicit paid authorization. Do not count component fixtures as a live 5/5 result or mark M1 accepted. M3–M6 remain planned; this milestone's completion does not authorize external Git/Jira writes or publication.
