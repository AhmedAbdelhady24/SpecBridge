# First Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** A local operator turns a feature idea into a persisted PRD and stories, reviews an exact revision, and downloads an independently runnable Starlight documentation package.

**Architecture:** One FastAPI backend owns project data, skill access, workflow transitions, immutable revisions and approvals. A thin React/Vite UI renders structured data; SQLite persists domain state. A fixed Starlight template renders an approved snapshot without an application or model dependency.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, stdlib sqlite3/zipfile, PyYAML safe loading, httpx; React, TypeScript, Vite; Astro Starlight; pytest, Ruff, mypy, Playwright, npm and uv lockfiles.

**Spec:** [Approved first-slice design](../architecture/first-slice.md), [accepted ADR 0001](../decisions/0001-local-modular-monolith.md), [security requirements](../security/threat-model.md), [acceptance contract](../evaluations/acceptance.md).

**Status — 2026-10-16:** Implementation was authorized after plan review. Tasks 1–8 technical deliverables are implemented and integrated. The lead has verified backend, browser, frontend and static checks; final independent-package rerun and reporting are being closed. Fixture-backed API/browser and independent-package verification exist. Full Milestone 1 semantic, live-provider and unfamiliar-human acceptance remains pending. See [first-slice results](../evaluations/first-slice-results.md) for actual commands, results and limits; this plan does not certify final checks.

The detailed checklists below preserve the original test-first execution targets. Their unchecked markers are historical planning text, not a claim that current code is absent. Use the execution status here and the linked results to resume; do not repeat completed implementation because an original checklist marker remains unchecked.

| Tasks | Current implementation / remaining boundary |
| --- | --- |
| 1–2 | Secure loopback API, SQLite contracts/revisions and generated OpenAPI exist. |
| 3–4 | Original runtime skill, fixture/compatible adapters, checkpoint/retry workflow exist; compatible transport is mock-tested only. |
| 5–6 | Fixed Starlight renderer/template, immutable candidate approval/download exist. |
| 7 | React intake, evidence recovery, labeled revision editing, review and package UI exist. |
| 8 | Browser/security/standalone runner and CI definitions exist. Integrated API/browser/static checks pass; the lead records final independent-package verification and audit results. Hosted CI and unfamiliar-human acceptance remain unverified. |

**Execution method:** Preserve the user's lead-agent orchestration with bounded independent workers. The lead implements the shared backend contract and integrates; UI and template work use isolated Git worktrees after contracts pass. Maximum two implementation workers at once. Review each deliverable before integration and run combined checks afterward. This is not authorization for cloud calls or external publication.

## Global constraints

- Python 3.12 and Node 22.23.1 are the development targets. Resolve compatible releases and commit exact `uv.lock` and `package-lock.json` files; no global tool/config changes.
- Single local operator; loopback binding, host/origin protection and local session authorization. External/multi-user access remains out of scope.
- Runtime PM skills are data, separate from development skills, with no shell or unrestricted filesystem access.
- No confidential data leaves the machine until the operator configures a provider and explicitly generates using that destination.
- Fixture-provider output is labeled test/demo output, never real AI validation.
- Each generated claim can cite source IDs; recommendations, assumptions and unknowns are explicit. Source presence is not factual verification.
- Stable requirement/story IDs are persisted, never renumbered by the model on edits.
- Publication authorization cannot arrive from a prompt, source, model response, or imported skill.
- Export reads the same stored candidate bytes and rechecks the digest; template, asset or content changes require another preview and approval.
- Never compile imported/model content as MDX or accept model-supplied file paths, plugins or npm commands.
- Clean extracted documentation supports `npm ci`, `npm run dev`, `npm run build`, `npm run preview`, without SpecBridge or model credentials. Registry access for install is allowed; offline installation is not promised.
- No upstream noncommercial/unlicensed code imports; no real integration writes, hosting, MCP service, vector store, LangGraph, or second database.

## Review focus

1. An edit or template/asset change between review and download must invalidate the old candidate approval (Task 6).
2. A process stopping after a provider call but before result persistence must not report completion or retry silently; the operator must see the potentially billable retry (Task 4).
3. Model text containing frontmatter, MDX, raw HTML, unsafe URLs or remote images must stay inert in both preview and exported pages (Tasks 5 and 7).
4. A foreign browser origin, unauthorized local request or another project's object ID must not disclose data or mutate state (Tasks 1 and 2).
5. A model error or sensitive input must not leak credentials into errors, logs or exported artifacts (Tasks 3 and 8).

## Repository state and file ownership

Research baseline: commit `3742827` on `codex/phase-zero`. This plan and its approval-status updates follow that commit. At plan-writing time the branch contained engineering documents and two bootstrap integrity tests only. The scope below created the first application versions; current callers/tests now require coordinated updates. The original research baseline remains historical evidence.

| Owner | Created/changed paths and responsibility |
| --- | --- |
| Lead/backend | `pyproject.toml`, `uv.lock`, `services/api/specbridge/{__init__,main,models,storage,skills,providers,workflow,publisher}.py`, `services/api/tests/`, `scripts/export_openapi.py`, `.github/workflows/ci.yml` |
| Lead/runtime skill | `skills/runtime/feature-handoff/{SKILL.md,references/output-contract.md}`, `skills/runtime/feature-handoff/provenance.json`; original instructions only, with system skill-creator review |
| Template worker | `packages/docs-template/` fixed package/config/content skeleton and its lockfile; no API or UI edits |
| UI worker | `apps/web/` including generated `src/api/schema.d.ts`, API client and components; no backend edits |
| Lead/QA | `tests/e2e/`, `tests/fixtures/`, `scripts/verify_handoff.py`, root `package.json`/`package-lock.json` for Playwright, documentation and integration review |

No generic plugin system, ORM, background queue, design system or shared contracts service. Split a module only when its responsibility needs a real boundary. Use stdlib facilities before adding dependencies for a few lines.

## Contract agreed before parallel implementation

JSON requests and responses use strict Pydantic models with unknown fields rejected. Bounds: intake 32 KiB UTF-8, at most 20 selected sources totaling 64 KiB, provider response 256 KiB, skill body/reference 128 KiB each, at most 100 requirements/stories each, candidate ZIP 20 MiB. Reject oversized inputs; never silently truncate requirements. These are initial safety bounds, not measured performance promises.

Canonical artifact fields: `title`, `purpose`, `scope`, `non_goals`, `requirements`, `stories`, `edge_cases`, `dependencies`, `risks`, `success_metrics`, `open_questions`. Lists of factual statements carry `source_ids` and a kind (`user_provided`, `verified`, `recommendation`, `assumption`, `unknown`). Generation cannot self-assign `verified`; only an explicit user evidence-review action can mark a source verified. Each requirement has an immutable server ID and text; each story has an immutable server ID, linked requirement IDs and nonempty acceptance criteria. Persist generation-local key → server ID mapping before saving a revision. Edits retain existing IDs; removed IDs are never reused. New IDs are assigned by the backend and links are remapped in the same transaction.

SQLite schema version 1: `projects`, `sources`, `runs`, `checkpoints`, `revisions`, `reviews`, `candidates`, `approvals`, `audit`. UUID object IDs; foreign keys enabled on every connection. Unique `(project_id, revision_number)`, `(run_id, stage)` and candidate manifest digest. Store candidate ZIP bytes and canonical manifest in SQLite initially so approval cannot race a mutable filesystem package. Each write uses a transaction; workflow transitions additionally check the expected prior stage. One active workflow execution per run; retries use a persisted execution lease/attempt ID and cannot double-commit a stage.

| HTTP contract, all under `/api` | Result / failures |
| --- | --- |
| `GET /health` | Public minimal liveness; no configuration/secret data |
| `GET /config` | Authorized provider mode/model/destination only, never key |
| `POST /projects`, `GET /projects` | Create/list local projects |
| `POST /projects/{p}/sources` | Bounded immutable text with user-provided provenance |
| `GET /skills?intent=...` | Registry metadata only; content/reference paths not exposed as arbitrary file endpoints |
| `POST /projects/{p}/runs` | Selected source IDs, intent, skill ID, explicitly acknowledged configured destination; create checkpointed run, no generation yet |
| `POST /projects/{p}/runs/{r}/advance` | One next stage per call, optional explicit retry acknowledgment; returns durable run state; concurrent advance rejected |
| `GET /projects/{p}/runs/{r}` | Recorded stage, attempts, errors, artifact revision and missing information |
| `GET /projects/{p}/revisions/{v}` | Artifact, findings, sources, provenance and revision digest |
| `POST /projects/{p}/revisions/{v}/edits` | Expected latest digest + edited body → new immutable revision; conflict returns 409 |
| `POST /projects/{p}/revisions/{v}/reviews` | Human conflict notes and review disposition; never implicitly approves |
| `POST /projects/{p}/revisions/{v}/candidates` | Prepare preview manifest from fixed template; structural errors return 422 |
| `POST /projects/{p}/candidates/{c}/approve` | Explicit manifest digest and expected current revision → approval; stale/rejected/invalid candidate returns 409 |
| `GET /projects/{p}/candidates/{c}/download` | Authorized, approved, still-current candidate → identical ZIP bytes; otherwise 409 |

All project/object lookups use both project ID and object ID; wrong-project and absent objects both return 404. Body/schema errors return 422, missing/invalid local token 401, hostile Origin/Host 403, concurrent/stale state 409, bounded provider failure 502/504 with sanitized error code. No credential-bearing exception text in responses. Fixed error shape: `{ "error": { "code": "...", "message": "..." } }`; validation details identify fields without echoing sensitive values.

Local auth: generate a random bearer token at initial startup in `.data/session-token` with owner-only permissions, or accept it from an environment variable. Never print it. The local operator enters it into a password field; browser retains it in memory for the tab, not a URL or persistent browser storage. Protect reads as well as mutations except health. Allow only configured loopback hosts and the exact UI origin; reject wildcard binds and browser `Origin: null`. CORS is not an auth mechanism. Dev proxy forwards `/api` on the same browser origin; production assets are served by the backend. Missing Origin is allowed for authorized CLI requests; foreign Origin is rejected even with a valid token.

## Task 1: Secure runnable API boundary and reproducible backend tooling

**Files:** Create root `pyproject.toml`, `uv.lock`, `services/api/specbridge/{__init__,main}.py`, `services/api/tests/{conftest,test_boundary}.py`; update `.github/workflows/ci.yml` and `AGENTS.md` commands.

**Interfaces:** `create_app(*, data_dir: Path, token: str, allowed_origin: str) -> FastAPI`; factory injection isolates tests from real user data. `/health` and the auth/error boundary precede domain routes. Use `services/api` as Python package search root.

- [ ] Resolve project-local FastAPI/Pydantic v2/httpx/PyYAML/uvicorn and pytest/Ruff/mypy/pip-audit. Inspect metadata/licenses, commit `uv.lock`; no installers from skill repos. Use `uv sync --locked` after the initial resolution. Configure pytest test paths and mypy scope to `services/api`; retain the stdlib bootstrap command.
- [ ] Write the failing boundary tests before the app factory:

```python
def test_reads_require_token(client):
    assert client.get('/api/health').status_code == 200
    assert client.get('/api/config').status_code == 401

def test_foreign_origin_is_denied(authorized_client):
    response = authorized_client.get('/api/config', headers={'Origin': 'https://evil.example'})
    assert response.status_code == 403
```

- [ ] Run `uv run pytest services/api/tests/test_boundary.py -q`; confirm import/behavior failures, not a broken interpreter. Implement factory, fixed error format, auth/host/origin rules, startup token handling and loopback launch. Add tests for missing Origin + valid token, null Origin, foreign Host, token-file permissions and startup refusal to expose a nonloopback bind.
- [ ] Run the boundary tests, `uv run ruff check services/api`, `uv run ruff format --check services/api`, `uv run mypy services/api/specbridge`, and bootstrap tests. Expected exit 0. Commit `feat: add local API security boundary` after diff review.

## Task 2: Project-scoped persistence and immutable artifact contracts

**Files:** Create `services/api/specbridge/{models,storage}.py`, `services/api/tests/{test_storage,test_contracts}.py`; extend `main.py`; create `scripts/export_openapi.py` and `packages/contracts/openapi.json`.

**Interfaces:** `Store(path: Path)`, `Store.create_project(name: str) -> Project`, `Store.add_source(project_id: str, text: str) -> Source`, `Store.save_revision(project_id: str, artifact: Artifact, expected_digest: str | None) -> Revision`, `Store.get_revision(project_id: str, revision_id: str) -> Revision`. `Artifact`, `Project`, `Source`, `Revision`, `Finding` are Pydantic models in `models.py`; expose the HTTP contract above. Define `NotFound` and `Conflict` domain exceptions in `storage.py`, mapped by the API; never expose raw SQLite messages. Test fixtures in `services/api/tests/conftest.py` provide authenticated clients, two isolated projects, canonical artifact data and temp Stores. HTTP test helpers expose resource URLs and their decoded body/digest, not product model properties.

- [ ] Write failing round-trip/immutability tests using `tmp_path` SQLite files and API clients:

```python
def test_revision_lookup_is_project_scoped(store, two_projects, saved_revision):
    with pytest.raises(NotFound):
        store.get_revision(two_projects[1].id, saved_revision.id)

def test_stale_edit_does_not_replace_history(client, revision):
    response = client.post(revision.edits_url, json={'expected_digest': 'stale', 'artifact': revision.body})
    assert response.status_code == 409
    assert client.get(revision.url).json()['digest'] == revision.digest
```

- [ ] Run `uv run pytest services/api/tests/test_storage.py services/api/tests/test_contracts.py -q`; expect missing domain behavior. Implement strict schemas, schema version 1 initialization, transactions, foreign keys, SHA-256 canonical JSON digests, server ID allocation/remapping, optimistic concurrency and audit records.
- [ ] Add restart round-trip, duplicate IDs, missing acceptance criteria, dangling requirement/source IDs, generation trying to mark facts verified, removed-ID reuse, new requirement/story mapping, revision-number concurrency and rollback-on-failed-write tests. A failed migration must leave the old schema intact; refuse unknown future schema versions instead of resetting data.
- [ ] Export deterministic OpenAPI JSON with `uv run python scripts/export_openapi.py`; repeat and compare unchanged output. Run storage/contract tests and Task 1 tests; commit `feat: persist traceable immutable project artifacts`.

## Task 3: Safe skill registry and configurable provider boundary

**Files:** Create `services/api/specbridge/{skills,providers}.py`, `services/api/tests/{test_skills,test_providers}.py`, `skills/runtime/feature-handoff/{SKILL.md,references/output-contract.md,provenance.json}`, `tests/fixtures/feature-idea.txt`, `tests/fixtures/provider-output.json`, `.env.example`; update `docs/engineering/skill-inventory.md`.

**Interfaces:** `SkillRegistry(root: Path).search(intent: str) -> list[SkillMetadata]`, `.load(name: str) -> Skill`, `.reference(name: str, relative_path: str) -> str`; `Skill` includes body, content/provenance digest and explicit empty tool permission list. Define `InvalidSkill` in `skills.py`. `Provider.generate(*, skill: Skill, sources: list[Source]) -> GenerationDraft`; `FixtureProvider` and `CompatibleProvider` implement it, raising `ProviderFailure` from `providers.py` for bounded sanitized failures. `GenerationDraft` has the artifact sections above, generation-local requirement/story keys and source IDs; the workflow maps keys to canonical server IDs once. Fixture constructors `skill_fixture()` and `source_fixtures()` plus the mock transport fixture live in the provider test module; they never contact a real provider.

- [ ] Use system skill-creator to write original, self-contained runtime guidance because reviewed reusable skills lack required output/distribution fit. No upstream text/code copying, companion skill dispatches or executable helpers. Record original authorship, content hash, schema version and intended permissions without inventing a legal distribution license for all original project code. Validate Agent Skills frontmatter; do not load global development skills into the registry.
- [ ] Write failing cases for metadata-only discovery, deterministic name/description intent ranking and progressive reference loading:

```python
def test_skill_cannot_escape_reference_root(registry):
    with pytest.raises(InvalidSkill):
        registry.reference('feature-handoff', '../outside.txt')

def test_provider_does_not_follow_redirects(mock_transport, provider):
    mock_transport.respond(status=302, headers={'Location': 'https://other.example'})
    with pytest.raises(ProviderFailure):
        provider.generate(skill=skill_fixture(), sources=source_fixtures())
    assert mock_transport.request_count == 1
```

- [ ] Run `uv run pytest services/api/tests/test_skills.py services/api/tests/test_providers.py -q`; verify red. Implement YAML safe parsing with duplicate-key rejection, name/directory validation, required provenance/license observation, explicit permission denial, UTF-8/file bounds, absolute/parent/symlink rejection and deterministic routing. Unknown skills fail; no fallback to arbitrary paths.
- [ ] Provider configuration uses environment variables `SPECBRIDGE_PROVIDER` (`fixture` or `compatible`), `SPECBRIDGE_LLM_BASE_URL`, `SPECBRIDGE_LLM_MODEL`, `SPECBRIDGE_LLM_API_KEY`. Compatible mode requires explicit base URL/model, HTTPS unless loopback, no URL credentials/query/fragment, 60-second timeout, response-size limit and no redirects. Use a fixed JSON structured-output request to `/chat/completions`; unsupported provider schema capability fails clearly. No auto-provider fallback, network retries or model-directed tool calls.
- [ ] Add malformed/duplicate YAML, symlink directory/reference, name collision, file-size limit, forbidden permissions, invalid JSON/schema, secret-bearing exceptions, missing provider config, loopback HTTP, remote HTTP rejection and oversized response tests. Fixture results must visibly carry `fixture` provenance and never claim business facts not in sources. Test with `httpx.MockTransport`, never a paid call.
- [ ] Run registry/provider and earlier tests. Update inventory with actual custom-skill verification; commit `feat: add bounded runtime skills and provider adapters`.

## Task 4: Checkpointed workflow and deterministic findings

**Files:** Create `services/api/specbridge/workflow.py`, `services/api/tests/test_workflow.py`; extend `storage.py`, `models.py`, `main.py`, fixtures and OpenAPI artifact.

**Interfaces:** `Workflow(store: Store, registry: SkillRegistry, provider: Provider).start(project_id: str, source_ids: list[str], intent: str, skill_id: str, acknowledged_destination: str) -> Run`; `.advance(project_id: str, run_id: str, *, retry_acknowledged: bool = False) -> Run`. Define `Run` in `models.py` and `RetryAcknowledgmentRequired` in `workflow.py`. `Run` exposes ordered stage/attempt history; human review and publishing remain explicit separate requests. Workflow test fixtures create counting transports, persisted interrupted states and reopened Store instances.

- [ ] Write failing stage/resume tests using a counting provider and a new Store instance on the same temp database:

```python
def test_resume_does_not_repeat_completed_generation(workflow_factory, run_ready_for_validation):
    restarted, counting_provider = workflow_factory(reopen=True)
    restarted.advance(run_ready_for_validation.project_id, run_ready_for_validation.id)
    assert counting_provider.calls == 0

def test_interrupted_call_needs_explicit_retry(restarted_workflow, interrupted_run):
    with pytest.raises(RetryAcknowledgmentRequired):
        restarted_workflow.advance(interrupted_run.project_id, interrupted_run.id)
```

- [ ] Run `uv run pytest services/api/tests/test_workflow.py -q`; confirm red. Implement fixed stages Intake → Context retrieval → Skill selection → Plan → Execute → Validate → Human review → Publish, with atomic stage checkpoint/results, attempt lease, explicit error codes and no stage supplied by the model. Resolve selected sources by project and enforce bounds without truncation.
- [ ] Persist provider result and canonical mapping before marking Execute complete. On restart detect abandoned execution attempts; report potential repeated billing and require acknowledged retry. Do not claim exactly-once provider calls when the process dies before persistence.
- [ ] Add malformed output, duplicate normalized story text, missing sources/AC, same-key conflicts, source-supplied publish instructions, concurrent advance, failed provider, revoked destination acknowledgment and failed transaction cases. Structural errors block candidate creation; semantic findings remain reviewable, not automatic factual judgments. API allows human conflict notes and rejection; rejected revisions cannot publish.
- [ ] Run workflow plus prior tests, regenerate OpenAPI, and commit `feat: checkpoint feature-to-PRD execution`.

## Task 5: Standalone Starlight template and inert documentation renderer

**Files:** Template worker owns `packages/docs-template/{package.json,package-lock.json,astro.config.mjs,tsconfig.json,src/content.config.ts,src/content/docs/index.md,README.md}`. Lead owns `services/api/specbridge/publisher.py`, `services/api/tests/test_publisher.py` and its integration with the agreed template. Worker must not modify the API module.

**Interfaces:** `render_package(artifact: Artifact, provenance: dict[str, str], template_root: Path) -> CandidatePackage`; define `CandidatePackage` in `publisher.py` with `zip_bytes: bytes`, `manifest: dict[str, str]` of fixed paths → SHA-256, `template_digest: str`, `digest: str`. Pass only JSON-serializable nonsecret provenance. Package digest binds artifact digest, template digest and sorted file hashes; manifest serialization is canonical. No process execution inside this function. Define the test-only `assert_safe_package` in `test_publisher.py` to open/test the ZIP, verify confined filenames and hashes, and check that the known malicious fields appear only in escaped rendered form.

- [ ] Create isolated `.worktrees/docs-template` branch after Task 2 contracts pass. Inspect current official Starlight setup and resolved package metadata before choosing compatible exact versions. Use npm lockfile and trusted fixed scripts (`astro dev`, `astro build`, `astro preview`), no model-authored configuration. Preserve necessary upstream notices if any template code is copied.
- [ ] Lead writes failing renderer tests:

```python
def test_package_is_reproducible(artifact, template_root):
    first = render_package(artifact, {}, template_root)
    second = render_package(artifact, {}, template_root)
    assert first.digest == second.digest
    assert first.zip_bytes == second.zip_bytes

def test_model_content_is_inert(malicious_artifact, template_root):
    package = render_package(malicious_artifact, {}, template_root)
    assert_safe_package(package)
```

- [ ] Implement fixed Markdown pages for overview/PRD, requirements/stories/AC, edge cases, risks/dependencies, proposed metrics, questions, provenance/revision and QA scenarios. Absent APIs/decisions/release/Jira/GitHub references display missing/not supplied, not fabricated content. Static filename allowlist and JSON/YAML serializer control frontmatter; raw user/model text is escaped as inert Markdown text, including HTML, Markdown links/images and MDX syntax. Keep human-readable paragraphs and lists; do not wrap the whole document in one code block. No arbitrary reference asset fetching.
- [ ] Use fixed ZIP entry timestamps/permissions/order, reject symlink template files and excess package size, exclude node_modules/build output/dot-env files, and include lockfile, setup instructions, requirement/story/source mapping and revision manifest. Hash assets and all executable template files. Include local Git branch/diff instructions; no remote assumed.
- [ ] Test raw HTML/event handlers, javascript/data URLs, remote images, triple-backtick/frontmatter boundaries, Unicode, MDX import/expressions, filenames resembling `../`, dangling mapping IDs, template edits, reproducibility and ZIP integrity. `assert_safe_package` inspects entries and exact rendered fields; browser/build verification later establishes actual inert rendering.
- [ ] In the template worktree run `npm ci`, `npm run build`; lead runs `uv run pytest services/api/tests/test_publisher.py -q`. Review worker diff, build evidence and exact dependency list before integration. Commit separate template/renderer changes with compatible contracts.

## Task 6: Revision-bound review, approval and immutable ZIP download

**Files:** Lead modifies `models.py`, `storage.py`, `main.py`, `publisher.py`; creates `services/api/tests/test_approval.py`; regenerates OpenAPI.

**Interfaces:** `Store.prepare_candidate(project_id: str, revision_id: str, package: CandidatePackage) -> Candidate`; `.approve_candidate(project_id: str, candidate_id: str, expected_digest: str) -> Approval`; `.download_candidate(project_id: str, candidate_id: str, active_template_digest: str) -> bytes`. Candidate points to its exact revision; approve/download transactionally verify current project revision, review disposition, manifest digest, template digest and stored bytes.

- [ ] Write failing API approval/race tests:

```python
def test_unapproved_candidate_cannot_download(client, candidate):
    assert client.get(candidate.download_url).status_code == 409

def test_template_change_invalidates_approval(client, approved_candidate, mutate_template):
    mutate_template('package.json')
    assert client.get(approved_candidate.download_url).status_code == 409
```

- [ ] Run `uv run pytest services/api/tests/test_approval.py -q`; confirm red. Implement candidate preparation, exact preview/digest, human review/rejection, explicit approve and authenticated download. Keep local review/export idempotent for the same revision/manifest; duplicate approval requests must not create contradictory audit records. Preparing a new revision/template candidate never inherits approval.
- [ ] Add source text requesting approval, wrong-project candidate, wrong/stale digest, edited/deleted requirement, asset change, rejected revision, stored-byte corruption, repeated approval, concurrent edit/export and rollback tests. Validate digest and current revision within the transaction that authorizes the download snapshot; edits that commit afterward do not alter the snapshot already authorized. Expose the approved revision in the download metadata.
- [ ] Run full backend suite and typing/lint checks; review schema/approval diff and commit `feat: enforce human approval of immutable documentation exports`.

## Task 7: Accessible intake, revision review and export UI

**Files:** UI worker owns `apps/web/{package.json,package-lock.json,index.html,vite.config.ts,tsconfig.json,src/main.tsx,src/App.tsx,src/api/client.ts,src/api/schema.d.ts,src/styles.css}`. Lead updates backend static serving and root run instructions only after integration.

**Interfaces:** Generate `schema.d.ts` using pinned `openapi-typescript` from `packages/contracts/openapi.json`. UI requests use the contract table; no duplicated handwritten domain schema. `/api/config` displays fixture/compatible mode and exact destination; generation acknowledges that destination. `vite.config.ts` proxies `/api` to loopback API; production `dist/` can be served by FastAPI.

- [ ] Start isolated `.worktrees/frontend` after Task 4's contract export; use installed frontend/browser guidance progressively. Review selected React guidance before installing any optional skill; the existing skill/tool may suffice. Resolve/lock React/TypeScript/Vite and generated-type tooling; no component framework needed for one screen.
- [ ] Write browser tests in `tests/e2e/feature-handoff.spec.ts` with accessible selectors before UI implementation:

```typescript
test('review is required before download', async ({ page }) => {
  await signInLocal(page);
  await createFeatureDraft(page, 'Allow a customer to export their saved report.');
  await expect(page.getByRole('button', { name: 'Download package' })).toBeDisabled();
  await page.getByRole('button', { name: 'Approve this package' }).click();
  await expect(page.getByRole('button', { name: 'Download package' })).toBeEnabled();
});
```

- [ ] Run the new Playwright case against the fixture API and confirm the missing UI failure. Implement local-token password entry, project selection/creation, text intake, stage advance/progress/retry, structured PRD/story preview, editable fields creating a revision, review notes/reject, manifest preview, explicit approval and download. Reuse standard semantic controls and React text nodes; no HTML/Markdown execution in preview.
- [ ] Add missing-info, known conflict note, provider failure/retry acknowledgment, edit-invalidates-approval, raw HTML/remote image inertness, expired/invalid auth and keyboard-only navigation cases. Define `signInLocal` and `createFeatureDraft` in `tests/e2e/helpers.ts`; they call only public UI/API and use per-run temp data, no embedded credentials. Browser tokens come from the isolated test server fixture.
- [ ] Run `npm --prefix apps/web ci`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run lint`, `npm --prefix apps/web run build` and focused Playwright tests. Verify generated types have no diff after regeneration. Review worker diff and integrate only after green; commit `feat: add local feature handoff review interface`.

## Task 8: Clean developer handoff, attack regressions and combined CI

**Files:** Lead/QA owns `tests/e2e/{feature-handoff.spec.ts,security.spec.ts,helpers.ts}`, `tests/fixtures/{incomplete,contradictory,malicious}.json`, `scripts/verify_handoff.py`, root `package.json`/`package-lock.json`, `playwright.config.ts`, CI updates, `docs/evaluations/first-slice-results.md` and README/onboarding/AGENTS updates.

**Interfaces:** `uv run python scripts/verify_handoff.py --output <new-temp-dir>` drives the fixture API through intake/review/approval/download, extracts only confined ZIP entries, installs/builds the independent docs and checks links/mappings. It never invokes a shell with generated text, overwrites an existing directory, contacts a model or performs external writes. Launch owned local processes with argument lists; poll HTTP health with bounded timeout; drain logs and stop owned process groups in `finally`.

- [ ] Write and run a failing extracted-package browser test: download from real fixture-backed UI, stop SpecBridge, extract to a fresh temp directory and verify expected PRD/story/source mapping plus navigation. The initial failure must identify a missing handoff behavior, not network/browser setup. Test script refuses an existing output directory and malicious ZIP entries.
- [ ] Implement the runner and owned local server fixtures; run `npm ci`, `npm run build` in the extracted project, then exercise both `npm run dev` and `npm run preview` with HTTP/browser checks and bounded process cleanup. The browser checks rendered attack fixtures for executable nodes, external image requests, unsafe hrefs and missing requirement anchors. No SpecBridge/model process is required while viewing docs.
- [ ] Run deterministic backend/security regressions for incomplete input, duplicate stories, missing AC, failed/interrupt/restart cases, cross-project access, unauthorized/stale publication and secret redaction. Curated contradictory/conflicting-API fixtures verify retaining competing sources and human recorded findings; do not report fixture answers as live-model semantic quality.
- [ ] Extend CI with locked installs, bootstrap tests, pytest, Ruff format/lint, mypy, UI lint/typecheck/build, Playwright, clean docs build/links and dependency scans. Use `uv run pip-audit` on the resolved Python environment and `npm audit --audit-level=high` for each package lock; do not suppress a vulnerability to obtain green. Inspect and pin any added GitHub Actions sources; keep contents read-only and no deployment secrets.
- [ ] Run the complete verification commands below from the integrated branch. Record actual exit codes, counts, durations, provider mode/call count, fixture/skill/template hashes and all limitations. Use a fresh independent reviewer for security/contract/diff assessment; address material issues, rerun affected tests, then commit `test: verify independent documentation handoff`.
- [ ] Record automated developer-handoff evidence separately from an actual unfamiliar-human exercise. Mark Milestone 1 verified only when implemented acceptance passes; real-provider quality, hosted CI, containers and human handoff remain explicitly unverified if not run. Do not mark later milestones complete.

## Final commands and expected evidence

These commands now exist. Their presence is not a passing result: use the linked results for actual execution evidence and run affected checks after changes.

```sh
uv sync --locked
python3 -m unittest discover -s tests -v
uv run pytest services/api/tests -q
uv run ruff check services/api scripts
uv run ruff format --check services/api scripts
uv run mypy services/api/specbridge
uv run python scripts/export_openapi.py
npm --prefix apps/web ci
npm --prefix apps/web run generate:types
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web run build
npm ci
npm exec playwright test
uv run python scripts/verify_handoff.py --output /tmp/specbridge-handoff-verification
uv run pip-audit
npm audit --audit-level=high
npm --prefix apps/web audit --audit-level=high
npm --prefix packages/docs-template audit --audit-level=high
git diff --exit-code -- packages/contracts/openapi.json apps/web/src/api/schema.d.ts
git diff --check
```

Expected: each command exits 0; fresh output path for every handoff run; no secret/network-model calls; same approved manifest/file hashes in the downloaded package; navigation/AC/story mapping visible with SpecBridge stopped. Audit failures require a reviewed compatible fix or an explicitly reported unresolved risk, never deletion of the check.

## Recovery, integration and self-review

Preserve worker branches/worktrees/logs on failure; do not rerun unchanged failures indefinitely. Integrate by dependency order after reviewing exact commits and contracts. Tests only use temporary databases; no reset of user `.data/`. Back up real data before future migrations. Restore from the backup only after verifying schema compatibility. No real remote/publication action is part of this plan.

Plan self-review: scope and state stages map to Tasks 1–8; registry/provider failures to Task 3; persistence/ID/source invariants to Task 2; checkpoint recovery to Task 4; inert package/manifest to Task 5; approval authority to Task 6; browser preview to Task 7; independent build, evaluations and CI to Task 8. The five Review Focus cases have explicit owning test targets. Contract names and routes are defined above; source redistribution is excluded. This paragraph records the original planning self-review, not current implementation status.

**Next resumable action:** record final independent-package/combined verification evidence and remaining acceptance gaps in the results report, and conduct an unfamiliar-human handoff plus authorized live-provider/semantic evaluation before closing full Milestone 1. Do not redo approved design/plan gates or implemented Tasks 1–7.

Planning verification on 2026-10-15: `python3 -m unittest discover -s tests -v` passed both bootstrap tests; `git diff --check` passed; the scan for unfinished task markers found none. These checks validate repository-document integrity, not the planned application. No subagents were spawned for plan writing; the planning skill calls for inline self-review. No product dependencies, provider calls, app builds or browser tests were run in this planning step.
