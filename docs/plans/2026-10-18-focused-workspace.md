# Focused Requirements Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. The lead owns dependent integration; independent review may be delegated with explicit read-only boundaries. Implementation delegation requires an isolated worktree and nonoverlapping ownership.

**Goal:** Let a PM answer questions and review changes beside a complete draft, then export an explicitly approved, understandable documentation package.

**Architecture:** Retain FastAPI/SQLite and React/Vite. Add feature lineage and revision-bound collaboration records beside immutable Artifact snapshots. One backend owns conflicts, validation, working-copy commits, review and exact package approval; the frontend displays saved state and a separate working preview.

**Tech Stack:** Python 3.12, Pydantic, SQLite, React/TypeScript, Node 22.23.1, pytest and existing Playwright. Standalone Starlight export. No new runtime dependency is planned.

**Spec:** [Approved focused requirements workspace](../architecture/review-workspace-design.md).

**Status:** detailed implementation plan prepared; user approved the written design on 18 October 2026. Implementation-plan review remains pending under the writing-plans workflow. No implementation step is complete. Preserve the existing lead-agent execution approach; do not ask the user to select it again. No additional paid test, publication or owner-data migration approval is implied.

## Global Constraints

- Keep original revision IDs, project-wide numbers, artifact JSON and digests unchanged.
- Do not replace Artifact.open_questions with objects or rewrite historical snapshots to introduce IDs.
- Never store tokens, answers, evidence or draft content in browser localStorage.
- No model call occurs when typing, saving an answer, selecting a target, previewing a manual amendment, comparing revisions or saving a revision.
- Approval sends the exact digest shown. Review/approve/download enforcement remains on the backend.
- Generated documentation remains independently runnable with npm ci, npm run dev, npm run build and npm run preview.
- Use existing dependencies; retain security middleware, inert text rendering, locked installs and generated-contract drift checks.
- Work only with isolated fixture databases until backup and disposable migration verification pass. Do not load .env or start the owner API merely to generate contracts or run tests.

## Review Focus

1. Lost save responses/double clicks: retrying the same commit must return the existing revision, while a reused key with different content fails (Task 4).
2. Duplicate or edited question strings: identities must not collapse or silently transfer an answer to a different question (Task 3).
3. Interleaved feature histories and equal artifact digests: feature identity and parent ID, not digest alone, determine the head, conflicts and package eligibility (Tasks 1–2).
4. Reauthentication and stale working copies: recover acknowledged private work without browser storage or automatic overwrite/rebase (Tasks 4–5).
5. Candidate preview drift and malicious document content: display exact stored content safely and reject tampering before approval (Task 7).

## Current evidence and scope

Inspected exact source: storage.save_revision, Workflow.start/advance/list_runs, main edit/review/candidate routes, Publication.prepare/_eligible/_verify/approve/download, knowledge revision/context routes, App/ArtifactWorkspace/ArtifactPreview/ArtifactEditor/KnowledgePanel/EvidencePicker, tests and scripts below. Codebase-memory graph tools are unavailable; source fallback was used. Memory registry lookup yielded no SpecBridge entry. No credential inspection or paid request was needed.

Already implemented: readable drafts, token preservation/help, original evidence picker, meaningful run labels, dirty navigation guards, structural validation, package integrity/approval, SQLite recovery and fixture E2E harness. Preserve those checks rather than repeat the stale audit fixes. Submitted screenshot measurements are external audit evidence, not fresh reproduction.

The approved scope is one connected review-workspace change delivered in eight independently reviewable tasks. GitHub/Jira publication, automatic AI amendment generation, semantic contradiction detection, user accounts, live-model qualification and unrelated milestone acceptance are excluded. Do not promise zero technical debt or broader semantic reliability from these tests.

## Files and responsibilities

| Files | Responsibility |
| --- | --- |
| services/api/specbridge/migrations.py (new), storage.py | Versioned additive schema, immutable revision persistence, feature-local head checks |
| services/api/specbridge/feature_history.py (new) | Proven feature lineage, parent/head lookup, bounded history and comparisons |
| services/api/specbridge/workbench_models.py (new) | Strict typed question, answer, request, working-copy and commit contracts |
| services/api/specbridge/workbench.py (new) | Durable answers/requests, working-copy concurrency and atomic commits |
| services/api/specbridge/workbench_routes.py (new), main.py, models.py | Authenticated scoped API registration and backward-compatible edit integration |
| workflow.py, publication.py, publisher.py | Feature-local generation/publication, exact candidate preview and revision-bound decision export |
| apps/web/src/WorkspaceShell.tsx, DecisionQueue.tsx, RevisionTimeline.tsx, ReviewPanel.tsx, PackagePreview.tsx, artifactDiff.ts (new) | Focused UI modules and deterministic presentation diff |
| App.tsx, ArtifactWorkspace.tsx, ArtifactPreview.tsx, ArtifactEditor.tsx, KnowledgePanel.tsx, styles.css | State integration, section editing, context selection, pane layout and accessibility |
| packages/contracts/openapi.json, apps/web/src/api/schema.d.ts | Generated contracts only; never hand-edit as schema sources |
| scripts/backup_workspace.py, verify_workspace_recovery.py, verify_handoff.py, check_docs.mjs | Schema compatibility, recovery and independently usable export checks |
| Backend test files named below; tests/e2e/workspace.spec.ts (new) | Migration, isolation, persistence, security and browser regression coverage |
| docs/architecture, docs/evaluations, docs/security, README and current plans | Maintained behavior, results and operational instructions |

No worker owns shared integration files concurrently. Native lead execution is preferred because persistence, heads and publication changes are sequential. A reviewer can read the completed feature-isolation diff independently; do not expose .data, tokens or provider settings to it.

## Contracts to establish before UI integration

Use run_id as the feature identifier. All routes below are prefixed with /api/projects/{project_id}/runs/{run_id}; every lookup checks both project and run, never a supplied revision ID alone.

| Route | Input | Result |
| --- | --- | --- |
| GET /history?before=&limit= | Feature revision cursor, default20/max50 | Proven feature lineage entries with legacy reference, actual/unknown metadata and parent |
| GET /compare?base=&head= | Two revision IDs belonging to that feature | Two immutable snapshots and revision-bound decision summaries; frontend computes presentation diff |
| GET /questions | Current queue | Question identity/text/origin, current status, latest answer/version and resolution link |
| POST /questions/{question_id}/answers | expected_version, text | New append-only answer version and user-provided source ID |
| POST /questions/{question_id}/status | expected_version, status, reason | Explicit dismiss/reopen transition; resolving through this route is forbidden |
| GET /change-requests | Active/history list | Persisted requests and their explicit resolution links |
| POST /change-requests | base_revision_id, text, target_ids | New open request |
| POST /change-requests/{request_id}/status | expected_version, status, reason | Dismiss/reopen; addressed status requires a committed revision |
| GET /working-copy | None | Saved record or null; base revision, optimistic version, working Artifact and pending links |
| PUT /working-copy | expected_version, base_revision_id, base_digest, artifact, question_changes, request_changes, change_summary | Saved next version; no artifact revision, review or model call |
| DELETE /working-copy | expected_version | Explicit discard of working copy, not answers/history |
| POST /commits | working_copy_version, idempotency_key | Atomic new revision plus resolution links, or the prior matching receipt |

Keep existing revision reads and edits compatible. Existing /revisions/{id}/edits resolves proven feature association and uses the same guarded commit primitive for that feature; unassociated legacy snapshots remain readable, with an explicit unsupported-association conflict for edits/export. Legacy low-level storage tests can retain the project-local compatibility path for data not associated with a run; it must not become an API bypass.

Candidate read-only preview routes are project/candidate scoped: GET /candidates/{candidate_id}/preview returns integrity-checked file summaries and GET /candidates/{candidate_id}/preview?path=... returns a permitted UTF-8 document. Do not overload /download to bypass approval. Browser preview is not pixel-identical Starlight rendering.

New contracts use strict Pydantic models, bounded IDs/text/lists, 404 for absent/cross-scope IDs, 409 for stale version/head or conflicting idempotency payload, 422 for malformed inputs. Preserve existing fixed error envelopes and never serialize arbitrary exception/provider messages. Requests use explicit expected_version, including version0 for create; no last-writer-wins writes.

## Task 1: Add proven lineage and safe schema migration

**Files:** Create migrations.py, feature_history.py and services/api/tests/test_feature_history.py. Modify storage.py, backup_workspace.py and test_workspace_backup.py. Preserve stored Revision JSON.

**Interfaces produced:** FeatureHistory(store).head(project_id: str, run_id: str, connection=None) -> Revision | None; .list(project_id, run_id, before: int | None = None, limit: int = 20) -> list[FeatureRevision]; .compare(project_id, run_id, base_id: str, head_id: str) -> RevisionComparison. FeatureRevision includes revision_id, run_id, parent_revision_id, feature_number: int | None, legacy_number, created_at: str | None and change_summary: str | None. The before cursor uses immutable legacy_number so incomplete histories can still be paged without fabricated feature numbering. Define typed results in feature_history.py.

- [ ] Write migration tests from a disposable schema-v2 fixture containing two runs, generation provenance, validate checkpoints, ambiguous/missing evidence, candidate approvals and audit times. Record revision data/digests before migration and assert byte equality afterward. Test unsupported versions and an injected migration failure leave no partial schema/version changes.
- [ ] Run `uv run pytest services/api/tests/test_feature_history.py services/api/tests/test_workspace_backup.py -q`; observe new behavior fail before implementation.
- [ ] Add schema-v3 sidecar tables revision_lineage and feature_heads. Keep existing revisions table/snapshot schema. Store explicit project/run association, parent, feature_number, nullable metadata; enforce unique revision association and unique (project_id,run_id,feature_number). Validate parent membership/cycles in transaction. Existing audit creation timestamps may supply actual dates; no backfill timestamp pretending migration time was creation time.

```sql
CREATE TABLE feature_heads (
  project_id TEXT NOT NULL REFERENCES projects(id),
  run_id TEXT PRIMARY KEY REFERENCES runs(id),
  revision_id TEXT NOT NULL REFERENCES revisions(id)
);
```

- [ ] Backfill only consistent provenance.run_id/checkpoint/head evidence with matching project. Proven membership does not prove a parent: leave a gap explicitly represented when old edit links are not provable. Do not infer ancestry from interleaved numbers or equal digests. Unassociated records remain in legacy history. A proven chain receives feature numbering in proven chain order; incomplete chains display legacy references until reconciled.
- [ ] Keep numbered migration application and PRAGMA user_version advancement in the same transaction. Update backup validator to recognize schema3 only when its required tables exist, with existing private-file/nonoverwrite/integrity rules intact.
- [ ] Add and run a failure-path example:

```python
def test_lineage_rejects_other_project(history_fixture):
    history, first, other, run = history_fixture
    with pytest.raises(NotFound):
        history.head(other.id, run.id)
```

Define history_fixture in the new test module using Store.create_project and inserted fixture runs; it returns (FeatureHistory, first_project, other_project, first_run). No provider or owner database is used.
- [ ] Rerun focused tests, inspect snapshot equality, foreign keys, migration repeatability and diff; commit only Task1 files with `feat: add immutable feature revision lineage`.

**Acceptance:** Source-proven history survives restart; uncertain ancestry stays uncertain; no historical content/digest/approval is rewritten. A newly inserted run without a head returns None rather than an unrelated project revision.

## Task 2: Enforce feature-local heads throughout editing and publishing

**Files:** storage.py, workflow.py, main.py, publication.py, models.py, feature_history.py; tests/test_feature_history.py, test_workflow.py, test_api_handoff.py, test_approval.py, test_publisher.py and test_storage.py.

**Interfaces:** Extend Store.save_revision with optional keyword-only run_id: str | None, parent_revision_id: str | None and change_summary: str | None. For associated writes require both expected digest and explicit parent ID against that run's head. Existing project-wide number remains immutable legacy metadata. Publication resolves feature head through FeatureHistory, never project-global MAX(number). Keep existing public Revision fields unchanged; feature views carry new metadata.

- [ ] Add a fixture helper `create_run(client, project_id, text)` in test_feature_history.py using existing authenticated TestClient setup and six fixture advance calls. It returns saved run and revision. Add interleaved A/B creation, A edit/B edit and A/B package approve/download tests. Add stale same-feature edits and a same-digest/different-parent case to pin identity, not just content.
- [ ] Run `uv run pytest services/api/tests/test_feature_history.py -q` and retain expected failing assertions before changes.
- [ ] New workflow roots have no feature parent. Generate under the existing lease/skill/source checks; validate commits against that run's current head and updates feature_heads/run.revision_id transactionally. Do not let an unrelated project edit fail the new feature generation.
- [ ] Use the actual feature parent for provenance and current IDs. Retain project-issued ID protection against adoption/reuse from other features. Add SQL-level head compare-and-update within the same transaction as revision insertion, audit and run update.

```python
# Guard inside the transaction; equal digests do not make different parents equivalent.
head = history.head(project_id, run_id, connection=db)
if (head.id if head else None) != parent_revision_id:
    raise Conflict("Feature changed; compare revisions before saving")
```

- [ ] Route compatibility edits through proven feature association. Apply feature-local eligibility to prepare, approve and download; stale feature A package remains ineligible after A changes, while changing B leaves A eligible. Unassociated legacy export returns a clear conflict; no silent assignment.
- [ ] Add history/compare routes with bounded paging and cross-feature/project rejection. Update RunSummary to show actual feature number where proven and explicit legacy fallback otherwise. Generate contracts with `uv run python scripts/export_openapi.py` and `npm --prefix apps/web run generate:types`.
- [ ] Run full backend suite and static checks, inspect authority paths and changed legacy expectations; commit reviewed Task2 files with `fix: isolate feature edits and package eligibility`.

**Acceptance:** Two features coexist independently; same-feature concurrent writes remain safe; IDs/provenance/approval checks cannot escape feature scope. Future tasks consume FeatureHistory rather than duplicating head queries.

## Task 3: Persist question answers and requested changes separately

**Files:** New workbench_models.py, workbench.py, workbench_routes.py, tests/test_workbench.py. Modify migrations.py, main.py, backup_workspace.py and focused backup tests.

**Interfaces:** Workbench(store) owns questions/answers/requests and working state. `questions(project_id,run_id)` returns QuestionView records. `save_answer(project_id,run_id,question_id,expected_version,text)` returns AnswerVersion. `set_question_status(..., expected_version,status,reason)` accepts dismissed/unanswered only. `create_request(project_id,run_id,base_revision_id,text,target_ids)` and `set_request_status(...,expected_version,status,reason)` persist explicit requests. register_workbench_routes(app, store) registers all task contracts without creating a provider.

QuestionView contains id, text, origin_revision_id, origin_index, version, status, latest_answer and resolution_revision_id. AnswerVersion contains question_id, version, text, source_id, created_at. RequestView contains id, base_revision_id, text, target_ids, version, status, resolution_revision_id and dismissal_reason. No author field is fabricated.

- [ ] Add schema-v4 tests for duplicate question strings, amended/reordered questions, answer restart/history, scope leaks, conflicting expected versions and atomic source creation. A question occurrence is linked by (revision_id,index), not text alone. Reconcile unchanged questions only when occurrence mapping is unambiguous or explicitly user-linked. Preserve original question records when removed from subsequent snapshots.
- [ ] Run `uv run pytest services/api/tests/test_workbench.py -q` and record failures for missing contracts.
- [ ] Implement schema4 tables: questions, question_occurrences, question_answers, change_requests, change_request_events, working_copies and commit_receipts. Question occurrence identity and event version are unique; all records require project/run membership. Update backup validator with complete schema4 requirements. Create answer source and answer version in one transaction; exact answer text is user_provided, not verified. Source text must satisfy existing byte limits.
- [ ] Define strict contract statuses: question unresolved/answered/dismissed/resolved, request open/dismissed/addressed. Answer save produces answered; only committed resolution can produce resolved/addressed. Reopen preserves history; reopen of an already incorporated question creates an explicit pending draft change rather than silently rewriting the saved artifact.

```python
def test_duplicate_questions_keep_independent_answers(workbench_case):
    service, project_id, run_id, first, second = workbench_case
    service.save_answer(project_id, run_id, first.id, first.version, "CSV")
    queue = service.questions(project_id, run_id)
    assert next(q for q in queue if q.id == second.id).latest_answer is None
```

Define workbench_case in test_workbench.py with a disposable two-question Artifact and real generated run/lineage fixtures from Task2; return the two separate identities with identical question text.
- [ ] Register authenticated routes under existing middleware. Add history reads for answers and request events; page default20/max50, deterministic cursors. Enforce text max16384 chars and existing source-byte budget; target lists max100 and only known requirement/story IDs or named document sections.
- [ ] Run workbench, boundary, backup and contract tests; regenerate API/TS artifacts and review auth/scope/error responses. Commit `feat: persist feature questions answers and review requests`.

**Acceptance:** Saved answers survive restart without changing Artifact snapshots; duplicates stay independent; answer evidence remains honestly classified; no model invocation or approval is possible through these routes.

## Task 4: Durable working previews and atomic revision commits

**Files:** workbench_models.py, workbench.py, workbench_routes.py, storage.py and tests/test_workbench.py, test_boundary.py, test_workspace_backup.py, test_approval.py.

**Interfaces:** WorkingCopy has version, base_revision_id, base_digest, artifact, question_changes, request_changes, change_summary. Each QuestionChange has question_id, expected_question_version, answer_version, action (resolve/reopen) and targets. RequestChange has request_id and expected_version. `save_working_copy(project_id,run_id,body)` returns WorkingCopy; `discard_working_copy(...,expected_version)` removes only that copy; `commit(project_id,run_id,working_copy_version,idempotency_key)` returns CommitReceipt {revision_id, feature_number, idempotency_key}. Missing copy reads return null. idempotency_key is a client UUID; bind receipt to normalized complete commit payload and scope.

- [ ] Write tests for interrupted/lost response replay, conflicting reuse of a key, two writers, invalid story coverage, stale answer version, stale parent and rollback between artifact insertion/resolution. Assert no dangling source/resolution/head/audit state and no stale package authorization.
- [ ] Run the focused workbench/approval tests and observe missing working-copy behavior fail.
- [ ] Implement PUT/GET/DELETE with compare-and-swap optimistic versions. Validate draft shape with Artifact; allow empty pending answers only in ephemeral UI state, not saved AnswerVersion. Save a working copy without advancing the immutable head. Return base mismatch for stale work; allow reading stale work so the UI can compare and explicitly reconcile.
- [ ] Commit in one Store.transaction: look up receipt; compare request fingerprint; check working version/head/answer/request versions; validate_handoff; save feature revision; write question/request resolution links and revision-bound decision snapshot; update run/head; consume working copy; write receipt/audit. A replay must return the original receipt even after the working copy has been consumed.

```python
first = service.commit(project_id, run_id, copy.version, commit_key)
replayed = service.commit(project_id, run_id, copy.version, commit_key)
assert replayed.revision_id == first.revision_id
assert len(history.list(project_id, run_id)) == previous_count + 1
```

- [ ] Test separate answer saves do not invalidate an unchanged approved artifact/package. Commit of actual new content requires fresh review. Old decisions in package snapshots stay unchanged when later answers are edited. On discard, keep answer history but remove amendments and display that distinction.
- [ ] Update recovery verification to round-trip new records and fail on partial schema4 databases. Run backend/static/contract checks and commit `feat: save recoverable working drafts with atomic commits`.

**Acceptance:** Durable acknowledged previews survive reconnect; no automatic rebase; save failures do not resolve questions; retries are safe and preserve exact approval boundaries.

## Task 5: Two-pane document workspace, answering and section editing

**Files:** New WorkspaceShell.tsx, DecisionQueue.tsx and ReviewPanel.tsx. Modify App.tsx, ArtifactWorkspace.tsx, ArtifactPreview.tsx, ArtifactEditor.tsx, styles.css, tests/e2e/helpers.ts and new tests/e2e/workspace.spec.ts.

**Interfaces:** WorkspaceShell receives project/run selection, task (questions/changes/review), document pane and task pane. DecisionQueue receives typed QuestionView records and explicit save/preview/status callbacks. ReviewPanel receives existing review/package operations; it never approves from local client state. ArtifactWorkspace receives persisted Artifact, working Artifact, diff and selected editable section. App owns orchestration and scoped request cancellation/identity guards, not child persistence duplication.

- [ ] Write fixture E2E tests for desktop answering while complete draft remains readable, section-only editing, mobile Task/Draft switching, unsaved navigation guards, reconnect recovery and stale-copy reconciliation. Start with the existing auth/run helpers, updating selectors to named user actions without weakening assertions. Fixture tests own disposable data and cannot reuse the paid app server.
- [ ] Run new browser scenarios against the old UI and record the expected missing controls/layout failures before implementation.
- [ ] Move project switching into the header; use explicit Create project and New feature actions. Render no blank review form before a revision exists. Keep already implemented auth help/retention and connect error association.
- [ ] Render two panes with independent, labelled scroll regions on desktop and one pane on <=900px. Keep action bars contained in their pane; focus can leave each scroll region. Review notes stay alongside readable draft. Mobile switches preserve selection/scroll and all pending values.
- [ ] Add question answer Save with persisted status. Preview requires user-supplied amendment text and explicit targets; do not turn an answer into generated requirements. Named callbacks are explicit:

```typescript
type PreviewAmendment = {
  questionId: string;
  answerVersion: number;
  targets: string[];
  amendmentText: string;
};
```

The callback changes only the working artifact. Adding a new requirement must also offer an explicit linked story/criteria editor so coverage validation can succeed; never invent these. Existing requirement text can be amended with explicit source/classification handling. Story/criterion edits can target the same preview.
- [ ] Add per-section editing without hiding the rest of the readable document. Show Saved draft / Working preview and explicit unsaved/saved-working-copy states. Persist work through authenticated API with ordered saves and optimistic versions, preserving in-flight edits; errors remain local and visible. Do not store private content in browser storage or auto-trigger generation on input/change/effect.
- [ ] Save as new revision uses a single commit UUID retained until its receipt or definite failure. Failed/disconnected response is reconciled through the same key, never an invented new commit. Show conflicts with compare/reconcile and discard choices; never silently overwrite.
- [ ] Add a fixture API request spy for run creation/advance and a backend provider spy that raises if generate is called on answer/preview/history/edit operations. Verify no paid calls server-side, not merely browser remote traffic.
- [ ] Run workspace browser scenarios, frontend typecheck/lint/unit/build and existing dirty/auth/security scenarios. Inspect screenshots at390/768/1440 and keyboard focus. Commit `feat: add side by side question and draft review workspace`.

**Acceptance:** The complete draft remains accessible while answering/reviewing; proposed text is visually distinct and saved only on deliberate commit; only edited sections show controls; private work survives reauthentication after acknowledged save.

## Task 6: Feature change timeline and simpler project context

**Files:** New RevisionTimeline.tsx and artifactDiff.ts; modify KnowledgePanel.tsx, App.tsx, ArtifactPreview.tsx, styles.css, apps/web/package.json test script if required. New artifactDiff.test.ts; extend tests/e2e/workspace.spec.ts and knowledge.spec.ts.

**Interfaces:** `diffArtifacts(base: Artifact, head: Artifact): ArtifactChange[]` is a pure function; ArtifactChange contains section, itemId: string | null, field, kind (added/removed/modified), before and after values. No JSON-to-HTML rendering. RevisionTimeline fetches feature-scoped history/compare and exposes read-only historical views. Project context uses existing snapshot endpoint and onSelect callback.

- [ ] Write deterministic tests for inserting at the start of a plain list, duplicate list entries, stable-ID reordering, evidence/classification changes and story link/criterion edits. Changes in provenance must not disappear merely because visible text is equal. Extend the existing Node strip-types test runner to include this file without a new test library.

```typescript
const changes = diffArtifacts(base, changed);
assert.equal(changes.filter(c => c.section === "requirements" && c.itemId === id).length, 1);
assert.equal(changes.some(c => c.field === "source_ids"), true);
```

- [ ] Run frontend unit tests before implementation; add sequence comparison for unidentified lists and stable-ID comparison for requirements/stories. Pure moves have a separate reorder description, not false removal/addition of all following clauses. Working preview uses the same function as historical comparison.
- [ ] Render feature timeline with optional human summaries, actual dates only and explicit missing metadata. Let users choose two proven feature revisions; prevent cross-feature IDs through the API. Show request/answer resolution events separately from document diffs. Historical views cannot mutate a revision or inherit present approval.
- [ ] Rename Project knowledge to Project context. Default to title/text and plain-language labels; evidence verification/history/archive are Details. Every record has direct Use in next draft/Remove actions that capture exact existing snapshot endpoint version/digest. Duplicate selection remains deduplicated; update project-scope guards when requests resolve late.
- [ ] Move generation details into confirmation at point of use while preserving exact destination/model, selected snapshots and billable acknowledgment. Browsing/history/context never opens a paid confirmation or advances a run.
- [ ] Run diff unit tests, knowledge/security/browser scenarios and frontend checks. Add backend compare/paging assertions if API integration reveals drift; regenerate only from backend models. Commit `feat: show feature revisions and simplify project context`.

**Acceptance:** Users understand what changed and which feedback remains open; context is directly usable and remains an exact snapshot; no UUID typing or fabricated dates/authors are introduced.

## Task 7: Exact readable package preview and decision export

**Files:** publication.py, publisher.py, main.py, packages/docs-template documentation/config only if navigation needs change; new PackagePreview.tsx; modify ReviewPanel.tsx and styles.css. Tests/test_publisher.py, test_approval.py, test_boundary.py, test_workbench.py, scripts/verify_handoff.py and check_docs.mjs.

**Interfaces:** `Publication.preview(project_id,candidate_id,path: str | None = None)` verifies stored ZIP/manifest/digest before returning allowed document summaries or bounded UTF-8 content. Return candidate digest and template digest with every response. Preview reads do not approve or publish. Publisher accepts a revision-bound decision snapshot from the backend, not current mutable queue state.

- [ ] Add tests for exact stored bytes despite later working edits, altered ZIP/hash rejection, malicious MDX/HTML, external assets, traversal/encoded paths, cross-project IDs, unsupported file types and inflated archives. Preview may be read before approval but cannot expose arbitrary template code or enable unapproved ZIP download.
- [ ] Run publisher/approval/boundary tests red first. Reuse Publication._verify and fixed template rules, allow only known documentation text files and safe page titles. Bound archive total at existing20MiB and individual returned document at128KiB; reject invalid UTF-8. No extraction onto disk or dynamic code evaluation.
- [ ] Render exact content with inert React text and a conservative renderer for the known generated Markdown subset. Reject/escape unsupported HTML/MDX; never dangerouslySetInnerHTML. Expose raw document text fallback so no content is silently omitted. No external links/assets fetched automatically. If a new parser becomes necessary, stop for dependency review rather than silently install it.
- [ ] Include revision-bound resolved decisions and original question text in a dedicated exported documentation page; renderer receives the frozen commit snapshot. Later answer edits cannot alter an existing candidate. Add a clear unincorporated-answer warning to the workspace without claiming its old package content changed.
- [ ] Technical details exposes copyable manifest/digests and Package integrity checked only after successful comparison. Approval posts the currently displayed exact digest; stale working content cannot be presented as package preview. Preparing/updating a package never authorizes it.
- [ ] Run standalone handoff install/build/browser verification into a fresh temporary path. Confirm `npm ci`, `npm run build` and preview work with no LLM/API; retain generated setup instructions for dev/build/preview. Update template digest expectations intentionally and rerun stale-template approval tests.
- [ ] Run backend/static/frontend/browser checks and commit `feat: preview exact handoff content and exported decisions`.

**Acceptance:** A PM reads the actual candidate content before approving; package integrity and semantic approval remain distinct; resolved decisions travel with the reviewed revision and site runs independently.

## Task 8: Combined acceptance, recovery and operational handoff

**Files:** Existing tests, scripts/verify_workspace_recovery.py, docs/evaluations/focused-workspace.md (new), docs/security/threat-model.md, docs/architecture/first-slice.md, README.md, current plan/PLANS.md. Refresh existing media captures only after the UI is stable. Update roadmap/board only for verified scope, not milestone promotion.

- [ ] Create an isolated end-to-end scenario: choose project, select exact context directly, open fixture feature, save a question answer, preview a requirement/story amendment beside full draft, reconnect/recover, save one revision, inspect diff/request status, record review, preview exact docs, approve/download and build the independent site. Keep explicit assertions at every state transition.
- [ ] Run a second feature in the same project and prove its generation/edit/export does not stale the first. Inject stale answers, stale head, failed save, lost response, restored backup and malicious document text; verify recovery and authority rules.
- [ ] Review complete diff and contracts, migrations, byte-preservation results, limits, approval enforcement and untested claims. Use a read-only independent reviewer where available; give it bounded source paths and no private data. Fix findings and rerun affected regressions before combined final verification.
- [ ] Run actual commands, saving exit status and concise results:

```sh
python3 -m unittest discover -s tests -v
uv run pytest -q
uv run ruff check services/api scripts
uv run ruff format --check services/api scripts
uv run mypy services/api/specbridge
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web test
npm --prefix apps/web run build
npm run test:e2e
uv run python scripts/verify_workspace_recovery.py
handoff_check_root=$(mktemp -d /tmp/specbridge-focused.XXXXXX)
uv run python scripts/verify_handoff.py --output "$handoff_check_root/handoff"
git diff --check
```

The temporary parent exists but its handoff child does not; the existing handoff runner refuses overwrite. Contract generation twice must produce identical outputs; compare against the first generated files, not against prechange HEAD before committing intentional schema additions. Run existing locked Python/npm audits across every lockfile; record findings, never suppress them.
- [ ] Document each command/result, screenshot paths, failures fixed and remaining limitations. Manual unfamiliar-human acceptance and full assistive-technology certification remain separate. No new paid semantic qualification is claimed.
- [ ] Verify backup and migration against a disposable copy of owner schema before proposing the concrete app upgrade. Owner API must be stopped during upgrade/restore; never kill unknown processes. Root E2E requires exclusive ports8000/5173, fixture provider and temporary data. Preserve/restart only known owned dev processes after tests with original configuration; starting owner API on upgraded code is itself a migration and requires the separately recorded upgrade decision.
- [ ] Record restore commands using existing backup CLI, fresh destination paths and owner-only permissions. Rollback of schema3/4 uses verified preupgrade backup plus matching code and a stopped API; do not silently discard subsequent writes or run old code against new tables. Preserve failed-work evidence.
- [ ] Commit maintained documentation/media and report implemented behavior, files, skills, reviews, actual checks, discoveries, decisions and next task. Do not push or publish.

## Plan self-review and execution handoff

Coverage: feature isolation/migration Tasks1–2; answers/requests Task3; preview persistence/idempotency Task4; side-view, editing, review and responsive navigation Task5; timeline/diff/context Task6; exact docs/decision export Task7; full acceptance/recovery/security/docs Task8. Review Focus cases each have explicit owning tests above. No implementation, test pass or milestone completion is asserted by this plan.

The approved design is preserved. Next action is user review of this detailed execution plan, then Task1 using superpowers:executing-plans and the established lead-agent approach. Backend contracts precede UI integration, independent review precedes final claims, and live provider calls remain outside this work.
