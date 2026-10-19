# Readable evidence, conversation workspace and split revision review

Date:19 October2026. User requested replacing opaque reference UUIDs with source quotes/readable highlighted links, supplied a GitHub-like revision-diff screenshot, and confirmed a chat-first view with the draft beside it.

## Delivered scope

- Feature history sidebar, conversation-centered saved answers and change-request composer, complete specification on the right. Explicit answer/request intent prevents pretending every chat message edits a specification. The composer has its own footer beside a scrolling thread; it cannot cover amendment/history controls. Mobile preserves Task/Draft access and all existing loss/reauth protections.
- Source references load authenticated original text on demand, quote it verbatim and offer the full source. Literal matching wording is highlighted. Source-ID-only records do not contain precise passage offsets: the UI says so when no exact wording matches. A matching phrase is not presented as semantic verification. UUIDs remain only in technical disclosures/immutable snapshots.
- Readable requirement/story labels include the clause text. Activating them reveals a collapsed target, highlights it and moves focus. Stable IDs remain unchanged internally.
- Revision comparison groups changes by readable section, indexes/filter sections, shows split red/green before/after text and word-level changes. An expanded native dialog supplies more space, keyboard containment, Escape/Close and focus restoration. Long text uses a bounded deterministic fallback that reconstructs both inputs exactly. Evidence-only changes remain inspectable on both sides, including whole statements and new requirements/stories.
- New standalone exports use readable requirement/story headings and links to escaped original source quotations. Technical mappings remain in the provenance/snapshot. Existing approved ZIP bytes are unchanged. No new dependency, schema, OpenAPI contract, provider, automatic AI rewrite or model call was introduced.

## Evidence

Backend368 tests/294subtests passed in4.31s. Frontend8 unit tests, typecheck/lint/build, Ruff check/format49files, mypy17sources, bootstrap2 and diff checks passed. Full browser55/55 passed in38.6s; final repeat after the last label fix is recorded in the implementation plan. Isolated fixture ports18000/15173, fresh databases, no owner mutations. Coverage includes quote loading, literal highlights, collapsed clause links, split word marks, modal focus restoration, shared request create/dismiss/reopen state, source-only scope changes and added requirements, plus all prior security/recovery/approval scenarios.

Standalone handoff runner passed16.57s, including locked install/build/dev/preview and browser verification without a running SpecBridge session. Media capture passed1/1 in7.9s, including independent website build. Six synthetic screenshots now include source-reference and expanded revisions views; all inspected. Hyperframes strict check reported0issues and32/32 sampled text contrast checks. Local video/GIF refreshed; no private screen capture, hosted rendering or model API.

Tests were run red first for missing quotes, composer controls, changed-section navigation, pure matching/word-diff modules and exporter UUID headings. Failures discovered/fixed during regression: a sticky composer covered controls; old tests expected primary UUID visibility; one mark assertion expected a full phrase instead of separate changed words. An interrupted fixture run was stopped after identifying its exact process; owner app was untouched. No failed run is represented as passing.

Independent read-only reviewer `workspace_final_review` found missing whole-statement citations and stale chat request statuses after Changes mutations. Both corrected and covered by browser regressions; final narrow review found no remaining blocker. A visual review caught a stale working-preview message after commit; it is cleared on the new revision and explicitly tested. Reviews do not substitute for runtime evidence.

## Files and skills

UI: SourceReferences, referenceText, ChatComposer, DecisionQueue, DiffView, wordDiff, FeatureWorkspace, WorkspaceShell, RevisionTimeline, App, read/edit artifact views, PackagePreview and styles in `apps/web/src/`. Export: `services/api/specbridge/publisher.py`. Tests: publisher/workbench backend regressions, frontend pure tests, Playwright readable-references/approval/history cases. README/media, capture script and `scripts/check_docs.mjs` maintain the independently usable handoff proof.

Applied versioned Superpowers bounded design/TDD/debugging/review/verification, frontend-ui-engineering and codebase-memory (graph unavailable; exact source fallback). One lead implemented/integrated; the reviewer was read-only. No new skill or tool installation.

## Limits

The conversation view presents saved answers and recent change requests from existing collaboration records; earlier answer versions and older requests remain available through history. It is not a new unrestricted AI chatbot. Answers are saved as user input; requests do not rewrite or approve documents automatically. Exact source entailment/contradiction detection and general natural-language AI rewriting remain outside this change. Existing clinical/factual and unfamiliar-human acceptance limits remain. No milestone3 promotion is implied.

Reproduce with the standard backend/static/frontend commands in AGENTS.md, plus `SPECBRIDGE_E2E_API_PORT=18000 SPECBRIDGE_E2E_WEB_PORT=15173 npm run test:e2e`. The [implementation record](../plans/2026-10-19-readable-references.md) contains the approved scope and actual checkpoints.

## Local integration

Integrated reviewed commitsd54c38d/bc53cf0 into the local development branch after a fresh private backup at `.data/backups/readable-ui-20261019T080225Z/preupdate.db`. Final repeated full browser suite55/55 passed38.6s after the last status fix; media capture1/1 passed7.9s and local30second video/GIF rendered. Owner API/web returned200, both projects remained accessible and every database table fingerprint matched the preupdate backup; schema remained4. Read-only Chromium loaded a saved draft, chat composer, feature sidebar and original source quote with0JavaScript errors,0writes and0model calls. Observed listeners: API41073/8000 and Vite41183/5173; process IDs may change on later restarts. Existing private configuration/session token preserved. No database migration, paid test or external publication occurred.
