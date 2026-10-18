# Review workspace UX repairs — 18 October 2026

Status: verified locally. The user approved the prioritized UI/UX recommendations in conversation. Execute autonomously with isolated fixture verification; no paid model call or mutation of the owner's project data.

## Outcome and accepted design

Keep the current editorial design and backend approval authority. Default to a readable artifact with native disclosure sections, explicit Edit draft, section navigation and an always reachable Save/Discard bar while editing. Unsaved changes explain disabled review controls. Discard restores the current immutable revision; a saved revision requires fresh review/approval. Undo a local removal without inventing persistent deletion. Hide package controls until a revision exists. Retain failed token input with inline/focused error feedback. Use real run titles/revision numbers/recorded UTC timestamps and original-evidence selection with bounded search/paging instead of typing UUIDs. Stack at <=900px, center the skip link, and label stage pills in plain language. Never call a structurally valid draft "verified".

## Source inspection and contracts

Inspected App.tsx, ArtifactEditor.tsx, KnowledgePanel.tsx, styles.css, Playwright helpers and current knowledge/handoff tests, first-slice architecture, media plan, models and knowledge summaries. Codebase-memory skill read, but graph tools unavailable; exact source fallback used. Current Run omits title/date; workflow_created audit records provide actual UTC dates. Context retrieval merges knowledge and sources under shared budgets, so it cannot reliably serve as the evidence picker.

Minimal additive API contracts: RunSummary extends Run with title, nullable revision_number and nullable created_at. GET project/runs returns summaries without changing persisted Run JSON or expired-lease semantics. GET project/sources returns SourceSummary {id, project_id, kind, digest, preview}, restricted to original user_provided sources, with literal query<=200, limit20/max50 and project-scoped after cursor. No migration/new write. Backend remains source/approval authority. Lead regenerates OpenAPI/TS after reviewed integration.

## Ownership and ordered work

1. Lead writes browser acceptance checks first and observes failures against existing UI. Use isolated fixture config; temporarily stop the lead-started local dev servers and restart with existing private configuration afterward.
2. Backend worker owns models.py, workflow.py, main.py and focused tests in .worktrees/ux-contracts (codex/ux-contracts). Read-only discovery agent has completed contract research. Worker commits independently; lead reviews/integrates before generated contracts.
3. Lead owns App, new ArtifactPreview/ArtifactWorkspace/EvidencePicker components, ArtifactEditor, KnowledgePanel, styles and browser tests/helpers. Keep trusted plain React text rendering, native disclosure/navigation and no new dependencies. Add dirty navigation guards and local undo; no autonomous workflow actions.
4. Lead integrates tested backend commit, regenerates OpenAPI/types, runs full regression/static/build/security/dependency checks, reviews combined diff. Fresh read-only review after integration.
5. Refresh README captures/video to match changed UI using existing isolated capture runner. Record actual results here and update engineering/README docs. No milestone acceptance change.

## Acceptance and tests

- Auth error retains token, focuses invalid password input with useful help; no token logs/storage.
- New connection has no premature package form. Generated/opened artifact defaults to read mode, with no artifact textarea; evidence labels/IDs/source links and all content retained inertly.
- Edit title: Save/Discard controls remain visible after scrolling at desktop/mobile, dirty explanation blocks review/package controls. Discard restores exact current revision and previous approval eligibility; save creates a new revision and requires review again. Navigation cannot silently discard edits.
- Read/Edit and keyboard section links work; collapsed editor sections reduce initial controls; expand all is available for deliberate bulk editing. Local removal can be undone, with no unintended overwrites.
- Run labels use title/revision/date where recorded, truthful fallback otherwise, and update after saved edits.
- Evidence picker handles >20 results, literal searches, selected items outside current results, edits and project switches; changing selection clears verification confirmation. Snapshot and cross-project source IDs cannot authorize verification.
- <=900px single column, no horizontal overflow at390/768/1440; visible focus and non-overlapping skip link; stage pills distinguish structure/review/approval states without a blanket verification claim.
- Existing source-validation, rejection, stale-package, edit/review, context-race and history regressions continue to pass. Paid generation is never part of browser checks.

Commands: root npm run test:e2e (fixture ports8000/5173), uv run pytest -q, root bootstrap unittest, Ruff/format/mypy, web typecheck/lint/unit/build, generated-contract comparison and locked dependency audits. Existing readme-media runner now explicitly selects edit mode for editor captures, then Hyperframes strict check/render and decoded-frame inspection. A fixture or review-agent report does not imply live semantics or human acceptance.

## Execution record

- New auth acceptance failed first because the token input was cleared. Backend worker wrote failing API tests before implementation; batching/cursor regressions also failed before their fixes.
- Read-only discovery agent established truthful metadata/source contracts. Backend worker delivered 23e3685 + aa75243 from isolated codex/ux-contracts; lead reviewed and integrated as bad1bc3 + e0fc638, then regenerated both contract artifacts. No full-artifact fetches for run labels and no persistence migration.
- Lead implemented all listed UX findings. Independent reviewer identified Enter-submit and double-confirmation edge cases; both fixed and explicitly regression tested. Focused re-review confirmed fixes, and its requested dirty new-project test now passes (one confirmation, zero writes on cancellation, successful switch on acceptance).
- A final red/green skip-link test exposed mobile logo overlap despite centering. Focused skip now occupies a separate row; main/section focus destinations are real. Desktop/tablet/mobile checks pass without horizontal overflow.
- Full browser suite: 32 passed in 22.0s, including all 19 original cases and 13 UX checks. Discard preserves exact saved approval; saving invalidates the previous package. Hostile text stays inert in read mode; no paid provider calls.
- Full backend suite: 333 passed and 274 subtests in 3.40s. Ruff check/format (40 Python files), mypy (11 sources), frontend typecheck/lint, 2 unit tests and production build pass. OpenAPI/TS regeneration has no drift against generated output.
- Python audit and all four npm lockfile audits: zero known vulnerabilities. CI now includes media lockfile auditing. No new application dependency added.
- Final refreshed Playwright capture: 1 passed in 7.9s, with exact requirement binding, approved synthetic ZIP, locked install, independent Starlight build and preview shutdown assertion. README screenshots and demo are refreshed. This capture uses no owner-project data.
- Current roadmap and phase-board foundations updated, with no milestone status promotion. Detailed findings/results are in docs/evaluations/review-workspace-ux.md. Reproduction: npm run test:e2e; npm exec playwright test -- --config scripts/readme-media.config.ts with PLAYWRIGHT_BROWSERS_PATH=.cache/playwright; npm --prefix docs/media run check/render.

## Decisions, limits and continuation

Native disclosure and ordinary React state preserve the existing design without a new component library or workflow framework. Structured validation, human review and approval remain separate claims. Recorded run dates are used only when available. Evidence selection is project-scoped and original-only; selected IDs remain across bounded searches and paging. Backend checks remain authoritative. Unsaved guards protect artifact edits; unsaved knowledge-form drafts are not a new persistence feature. No full WCAG/screen-reader certification or user research is claimed. Unfamiliar-engineer acceptance and generator integration remain the next M1 task; M3–M6 are not complete.

Rollback: revert this scoped changeset and its two backend integration commits; persisted Run JSON/schema remain backward-compatible. Do not delete .data. The app is restarted using the owner's existing private configuration after tests; starting it does not generate or approve anything.

Final hidden-field regression failed before correction: a closed required section prevented usable native validation. Save now reveals its containing disclosures first; the full32-case browser suite passes. Final media: strict Hyperframes check zero findings, 32/32 sampled text contrast checks, nine layout samples; 30-second MP4 (1,706,299bytes) and GIF (1,499,105bytes). Updated read-mode frame and responsive editing screenshots visually inspected. No claim of WCAG certification or paid-provider requalification.

Local app restored after fixture verification: API health and interface both returned HTTP200 on ports8000/5173 using the existing private configuration. No generation action was triggered. Runtime and UX implementation commit58a6828 follows backend integration bad1bc3/e0fc638; docs/media recorded separately.
