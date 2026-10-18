# Focused requirements workspace: verification

Date:19 October2026. Scope: approved focused workspace plan, isolated branch `codex/focused-workspace` from baseline755462e. No owner rollout, model call, paid test, remote push or external publication occurred.

## Delivered behavior

| User task | Implemented behavior and evidence |
| --- | --- |
| Answer while reading | Desktop task/document panes and mobile Task/Draft switch; complete readable draft remains available. Answer versions persist separately from Artifact snapshots. |
| Amend deliberately | Explicit target and manual text; new requirements require human story/criteria. Working previews remain separate until atomic commit. Section edits retain the surrounding readable document. |
| Recover and reconcile | Authenticated durable previews, optimistic versions, explicit stale-copy inspection, discard and same-key commit receipt replay. Local unacknowledged text stays in memory; no browser persistence. |
| Understand changes | Feature-scoped timeline, explicit known parents, nullable legacy metadata, before/after field/evidence/link differences and requested-change history. Resolutions bind to immutable revisions. |
| Use project background | Plain labels, direct Use in next draft selection of an immutable version; later background edits cannot alter the selected source snapshot. |
| Review handoff | Review beside document, then exact verified stored package content, inert preview/source/secondary manifest, explicit digest approval and approved ZIP. Frozen decisions export with the revision. |
| Preserve boundaries | No provider use for answers/previews/history/commits; project/run authority, stale versions, cross-feature IDs and replay/tampering failures tested. |

## Actual checks

- Backend:367 passed and291 subtests,4.23s. Includes migration preservation/rollback, feature isolation, duplicate question identity, stale answer/head/copy/request versions, atomic receipts, source/coverage validation, frozen decisions, candidate integrity and hostile-text boundaries.
- Bootstrap:2 tests passed. Ruff check and format passed across49 files; mypy passed17 source files. Frontend typing/lint,4 unit tests and production build passed.
- OpenAPI and TypeScript regenerated twice with identical SHA256 outputs: `72b52ceee457146b36d2248c413f7e95eac278227090263bc6a40033e6f9f584` and `01f1f05465881f60fad6471b82d798f42e1158dc2a197926222e62f0c867cd1d` respectively.
- Browser: final combined49/49 passed in33.5s after all review fixes. Fixture provider, fresh temporary database and ports18000/15173; owner ports8000/5173 unchanged. Desktop1440, tablet768 and mobile390 widths are exercised.
- Recovery runner passed: seven knowledge types/two immutable versions, checkpoint resumption, saved answer/preview recovery, idempotent commit retry and persistent copy version after discard; backup0600. No provider/network request.
- Standalone handoff runner passed in16.41s at a fresh temporary destination: answer→commit→frozen decisions→compatibility edit→reviewed package→locked install/build/dev/preview/browser. SpecBridge session closes before website verification. Hostile markup remains inert and the decision page retains original question/answer.
- Owner migration rehearsal passed twice using **copies only**: schema2→4, all preexisting table rows unchanged and preupgrade restoration equivalent. Saved reproducible runner: `scripts/verify_workspace_migration.py`. Owner database was opened read-only for backup and never upgraded.
- Python pip-audit: no known vulnerabilities. Full npm audit, including optional packages, for root, apps/web, packages/docs-template and docs/media lockfiles:0 vulnerabilities each. No new runtime dependencies.
- README capture:1 passed in7.2s, including independent generated site build/preview. Refreshed intake/review/approval/documentation PNGs. Hyperframes strict check:0 errors/warnings/layout issues,32/32 sampled contrast checks. Local30-second MP4/GIF rebuilt. No narration, hosted rendering, private screenshots or model calls.

## Review and failures fixed

Independent read-only feature-isolation and final-workspace reviews inspected source, contracts, migrations and tests. Lead integrated and verified changes; reviews themselves do not establish runtime evidence.

- Legacy in-flight base digests and false inferred root numbering: corrected without historical rewriting.
- Copy version reset after discard, duplicate-question identity on reopening, frozen decision loss on compatibility edits: regression-tested and fixed. Ambiguous compound duplicate changes reject422 while retaining the preview.
- Late save response replacing another project: reproduced as a real browser crash before the fix. Navigation epochs/project guards discard stale UI effects. Added project and same-project feature regressions.
- Unpreviewed amendment loss: navigation protection plus explicit preview/discard gate on save. Pending wording is retained after rejection.
-401 in workbench routes: reconnect remains available with mounted local text; commit receipt retained until final revision read/parent update succeeds. Safe replay after postcommit401 is tested.
- Delayed answer history: keyed by question identity, so answers cannot appear under another question.
- Earlier run failures included obsolete edit endpoint test waits, review-tab focus timing, missing DecisionSnapshot import and a missing script import ordering check plus a new race-test selector using a nonexistent navigation label. Corrected checks were rerun; failed attempts were not counted as passing.
- Browser startup requires local socket permissions in this managed environment; sandbox bind failure was environmental and the actual suite ran with approved fixture-only permissions.

## Reproduce

Use locked root/UI dependencies and cached Playwright Chromium as in README:

```sh
uv run pytest -q
python3 -m unittest discover -s tests -v
uv run ruff check services/api scripts
uv run ruff format --check services/api scripts
uv run mypy services/api/specbridge
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web test
npm --prefix apps/web run build
SPECBRIDGE_E2E_API_PORT=18000 SPECBRIDGE_E2E_WEB_PORT=15173 npm run test:e2e
uv run python scripts/verify_workspace_recovery.py
handoff_check_root=$(mktemp -d /tmp/specbridge-focused.XXXXXX)
uv run python scripts/verify_handoff.py --output "$handoff_check_root/handoff"
git diff --check
```

For backup/rehearsal/rollback see [upgrade procedure](../engineering/focused-workspace-upgrade.md). Screenshots/video sources and reproduction are linked in README.

## Limits and next action

The owner app still runs its prior code/schema. Upgrade/restart requires the separately reserved owner approval. Live-provider semantic quality was not retested or changed. Human answers and manual amendments are user input/proposals; no automatic contradiction detection or AI rewrite is claimed. Unknown historical parents/timestamps/authors remain unknown. Unacknowledged tab-memory text cannot survive browser closure; acknowledged private previews recover from the backend. SQLite remains local single-owner, not encrypted multi-user storage. Full assistive-technology certification and an unfamiliar engineer's acceptance remain separate. No overall milestone is promoted solely by these checks.


## Files, skills and reviewers

Backend ownership spans `services/api/specbridge/{migrations,storage,feature_history,workbench,workbench_models,workbench_routes,working_copy,workflow,publication,publisher,main}.py` and their regression tests. Frontend changes are in `apps/web/src/`, including FeatureWorkspace, DecisionQueue, WorkspaceShell, RevisionTimeline, artifactDiff, section editors and PackagePreview. Generated contracts/types, recovery/handoff/migration scripts, Playwright fixture helpers/scenarios, README media, architecture/security/upgrade documentation and this plan record complete the changeset. No runtime dependency was added.

Applied installed skills: versioned Superpowers design/planning/execution/TDD/systematic-debugging/review/verification/worktrees, frontend-ui-engineering and codebase-memory (graph unavailable; exact source fallback). Skills informed engineering only; runtime PM skill permissions remain unchanged.

Read-only subagents `feature_isolation_review` and `workspace_final_review` inspected backend boundaries and combined changes. Their actionable findings were fixed with tests. No independent implementation worker shared edit ownership. The lead owns integration and actual command results. Review reports are not substituted for test evidence.
