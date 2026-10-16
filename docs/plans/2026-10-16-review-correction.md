# Human-controlled correction of incomplete handoffs

Status: verified for the scoped correction mechanics. User's continued engineering/autopilot instruction covers this bounded improvement to the existing review flow. No paid/model call or external publication in this task. Generator qualification and unfamiliar-human acceptance remain open.

## Evidence, design and decision

Saved model trials fail on missing observable behavior, missing decision questions and inconsistent criteria. Current ArtifactEditor maps existing questions/criteria but cannot append/remove them, and renders evidence labels read-only. Editing a user_provided excerpt can therefore fail backend source policy without a way to label the changed wording honestly. The API already supports immutable corrected revisions and recalculates findings; the frontend cannot express the needed correction.

Options: add a keyword-based semantic gate (would pretend to prove semantics); add another model reviewer (new cost/error source without acceptance evidence); or make the existing human correction boundary usable. Choose the last. This does not qualify the generator or count corrected output as a raw-model pass.

Design: existing editor gains add/remove controls for open questions (0..100) and each story's criteria (1..30), with blank new fields requiring user text. Evidence classification can be selected explicitly; never offer verified, and do not offer unknown for requirements. Source IDs stay visible/read-only; backend validates source excerpts and all provenance/authorization as before. Native form validation blocks blank additions before save. Every edit keeps the existing dirty-state behavior: invalidate local review/candidate, create a new immutable revision, require fresh review and exact package approval. No schema/database/provider/dependency change or silent relabel/repair.

## Ownership and execution

Lead owns this plan, tests/e2e and documentation, integration/verification. A bounded worker may own apps/web/src/ArtifactEditor.tsx and App.tsx (style only if necessary) in an isolated Git worktree; no other writers touch those files. Read-only discovery explains existing fixture browser setup. Review worker diff before integration; preserve failures/logs. Use existing Superpowers bounded design/TDD/verification; inherited user authorization permits proceeding without another design approval request.

## Acceptance and checks

- [x] Four browser tests first demonstrated missing add/remove/classification controls; traces preserved locally.
- [x] User can append distinct questions/criteria without replacing existing entries, edit/remove them, and save/reload the corrected revision. Add actions respect API cardinalities; last required criterion cannot be removed. New empty fields cannot be submitted. Whitespace-only strings retain the existing backend behavior.
- [x] Evidence labels explicitly distinguish exact user excerpt from recommendation/assumption/unknown, with verified never selectable and unknown excluded for requirements. No automatic reclassification on typing.
- [x] A human correction preserves stable IDs, uses existing backend finding recomputation and invalidates previous package/review until fresh exact approval. Browser security/origin/project/reload regressions remain green.
- [x] Backend/static/web tests, browser suite, diff and standalone package verification pass; docs distinguish supervised correction from generator/human acceptance. No new dependencies or live calls.

Actual results: 14 browser tests, 153 backend tests and 176 bootstrap subtests passed; web type/lint/2 unit tests/build, Python lint/format/type checks passed. Standalone package install/build/dev/preview checks passed in 15.56 seconds. Lead reviewed and integrated the isolated worker commit, and independent read-only review found no material issues. See [verification and limits](../evaluations/review-correction.md).

Reproduce: usual local fixture Playwright runner `npm run test:e2e`; tests use temporary data and explicit fixture provider. UI type/lint/unit/build and backend regressions are listed in AGENTS.md. No .env or user database change. Existing API write/approval semantics are unchanged. Next task after this slice: actual unfamiliar-human correction/handoff acceptance and separate generation/decision-consistency design work; later milestones remain open.
