# Review workspace UX and accessibility repairs — 18 October 2026

The user approved applying the prioritized audit recommendations. The supplied screenshot/session paths were not available as repository evidence; this work verifies source and actual fixture behavior instead of treating the audit's measurements or conformance statements as independently proven.

## Implemented scope

| Audit finding | Implemented behavior |
| --- | --- |
| F-01 / F-02 | Fixed Save/Discard bar, visible dirty explanation, disabled review/package actions while unsaved. Discard restores the exact saved revision; saving requires fresh review. |
| F-03 | Default readable draft, explicit Read/Edit controls, native disclosure sections and evidence labels. Editing starts with compact sections and optional expand/collapse all. |
| F-04 | Package form appears only for an active revision; new-feature controls require a selected project. Saved runs precede new intake. |
| F-05 | Failed authentication preserves the private input, focuses it and marks it invalid with local setup help. No token storage/logging added. |
| F-06 | Run dropdown uses the linked title, revision and actual recorded creation date; missing historical metadata uses intent or omits date. Metadata is batched server-side. |
| F-07 | Original-source evidence picker with bounded search, paging, checkboxes, selected previews and removal. Search changes preserve selection; selection changes invalidate verification consent. |
| F-08 | Single-column workspace through 900px, wrapping metadata and responsive editing actions. |
| F-09 | Keyboard jump links, focusable destinations and native disclosure sections; no claimed universal tab-count reduction. |
| F-10 | Skip link placement and focus behavior checked at mobile/tablet/desktop widths. |
| F-11 | Distinct stage pills with plain-language labels. |

Local removal has undo; subsequent edits clear that one-step undo to avoid overwriting newer work. Project changes, opening another run, new-project creation and generation guard unsaved artifact edits; reload uses the browser's unsaved-change warning. These protect artifact drafts, not every unsaved knowledge form.

## Boundaries and evidence

No blanket "Verified" artifact badge was introduced. Structural findings, human review, knowledge verification and exact-package approval remain distinct. Read mode renders plain React text, including hostile HTML literals. No Markdown/HTML execution or remote image loading was introduced. New read-only source/run-summary endpoints require existing local authentication and project scoping; knowledge snapshots are excluded from original evidence. Source results expose bounded previews and preserve backend verification checks. Persisted schema and provider behavior are unchanged.

The backend worker used isolated branch/worktree codex/ux-contracts, wrote failing tests first, and delivered two reviewed commits. Lead reviewed the enrichment queries and requested batching instead of full-artifact list fetches before integration. A separate read-only reviewer found Enter-key save and double-confirmation risks. Both were fixed, with explicit browser regressions; focused re-review found no remaining blocking issue.

Actual verification so far: 333 backend tests and 274 subtests pass; 32 combined browser checks pass. Ruff check/format (40 files), mypy (11 sources), frontend typecheck/lint, 2 unit tests and production build pass. Python and all four npm lockfiles have no known advisories from the executed audits. Refreshed fixture capture/download/independent Starlight build passes in 7.9s. Final focus checks and refreshed media verification are recorded in the execution plan.

Limitations: this is targeted Chromium fixture verification, not complete WCAG certification, screen-reader/device coverage, usability research or a repeat of the audit's Bask Health dataset. No paid call, owner-project write, external integration/publication or unfamiliar-engineer acceptance occurred. Milestone1 generation integration/human acceptance and Milestones3–6 remain open. See the [resumable plan](../plans/2026-10-18-review-workspace-ux.md) and [roadmap](../plans/roadmap-status-2026-10-16.md).

Final browser result: 32 passed in 22.0s. The last added regression first reproduced hidden required-field failure; Save now opens the containing disclosure before native validation focuses it. Responsive action-bar screenshots at390/768/1440 were visually inspected. Hyperframes strict check passed with zero warnings/errors, nine layout samples and32/32 sampled text contrast checks; refreshed MP4/GIF durations are30seconds. No full accessibility certification is inferred.
