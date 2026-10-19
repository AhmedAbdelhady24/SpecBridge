# Readable source and requirement references

Status: user requested implementation on19 October2026. Bounded change to existing reference presentation; no schema/provider/dependency change. Root app remains on verified code while this isolated branch is tested.

Outcome: source references show verbatim original text instead of UUIDs. Requirement/story references use readable labels and quotes, and open/highlight the linked clause. Stored IDs remain unchanged for traceability and can be inspected in technical details. No exact passage exists in historical source-ID-only citations: show the original source and explicitly distinguish matching wording from verified support. Never fabricate a quote/span or infer semantic grounding.

Scope: reusable lazy authenticated source quote view for read/edit UI; stable internal clause anchors with readable labels and accessible highlight/focus; selected evidence labels; portable export readable source quotes and internal requirement/story links. Existing stored packages and revisions remain immutable. No paid call, automatic regeneration or owner-data migration.

Acceptance/checks:
- [x] Failing fixture browser test for quoted source and readable cross-links; exact matching text highlighted after activation, collapsed target revealed.
- [x] Deterministic reference matching tests cover exact spans, no match and Unicode/literal hostile input.
- [x] Missing/stale/cross-project source fetches fail visibly without substituting another source; source loading remains read-only and scoped.
- [x] Generated documentation includes escaped verbatim quotes and readable requirement/story link labels; original technical mapping retained.
- [x] Backend/frontend/static/browser/standalone export checks pass; diff reviewed, docs updated, changes locally integrated. No provider calls.

## User steering: chat-first and revision review

User supplied a split GitHub-style diff screenshot and confirmed "Yes—chat first, draft beside it". Extend this bounded presentation work to a conversation-centered question/reply/request composer over the existing authenticated answer/request APIs, plus grouped split before/after diffs with word highlights and a changed-section index. Existing records remain authoritative; do not invent assistant responses, silently rewrite requirements or introduce new paid model calls. Saved answers/history provide the conversation record; explicit request intent records review feedback. Manual amendment preview/commit/review controls remain available beside it. No new persistence/provider or external integration. Preserve mobile access, navigation loss protection, reauth, immutable snapshots and exact approvals.


## Verification checkpoint

Source quote and composer/split-diff browser cases were run red before implementation; pure matching/word-diff modules likewise failed missing-module tests first. Publisher regression failed on old UUID headings before implementation. Final initial combined run:55browser tests in38.6s,368backend tests/294subtests in4.31s,8frontend units, typing/lint/build, Ruff49files/mypy17sources, bootstrap2, diff check pass. Standalone export install/build/dev/preview/browser passed16.57s. Media capture passed7.8s using synthetic data; screenshots inspected. A screenshot-discovered stale working-copy message after commit was corrected and tested separately before final integration.

Independent read-only reviewer found missing whole-statement source citations in diffs and stale conversation request statuses. Both fixed and regression-tested; reviewer reported no remaining blocker. Other failures fixed: composer overlay intercepted controls (replaced with separate flex footer/scroll thread), old UUID visibility assertions (now explicitly reveal technical details), and a split-word test expecting one contiguous mark (now checks individual words plus exact reconstructed text). No failing result is counted as a pass.

Saved answers and recent requests back the conversation view; prior answer versions and older requests remain in existing history controls. This is a conversation-first interface over the existing manual collaboration workflow, not a new general-purpose AI chat provider. No automatic semantic grounding, AI rewriting, exact span recovery or paid generation is claimed. Database/schema/contracts/dependencies remain unchanged; stored snapshots and previously approved package bytes are not rewritten.

Final repeated browser run after the status fix:55/55 passed in38.6s. Final media capture1/1 passed7.9s; strict Hyperframes0issues/32contrast checks;30second video/GIF rendered locally. No source/dependency/schema contract changes occurred after verification. Local integration and read-only owner-app checks follow without a database migration.
