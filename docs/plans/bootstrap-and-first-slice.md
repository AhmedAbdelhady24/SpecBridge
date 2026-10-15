# Bootstrap and first-slice roadmap

Status: Phase Zero research/bootstrap delivered; first-slice design approved on 2026-10-15. Product implementation awaits written-plan review. See the [detailed implementation plan](2026-10-15-first-slice-implementation.md).

## Outcome and existing state

Start from an empty local directory, build an independent local product, and prove feature idea → PM skill → PRD/stories → human review → portable documentation → local website. See [design](../architecture/first-slice.md), [ADR](../decisions/0001-local-modular-monolith.md), [audit](../engineering/environment-audit.md), and [acceptance](../evaluations/acceptance.md).

Current installed skills are sufficient for engineering bootstrap. No product dependencies, third-party source, provider calls or real integrations have been installed/run. Python 3.12 and Node 22 targets are available; Docker daemon is unavailable. Upstream noncommercial/unlicensed code is excluded.

## Milestones and gates

- [x] Inspect empty repository, tool versions, permissions and native delegation.
- [x] Inspect official skill sources, licenses and relevant executable helpers without running them.
- [x] Delegate/review five reference repositories with exact source revisions.
- [x] Record inventory and propose the smallest sustainable architecture.
- [x] Finish bootstrap checks, independent review and actual verification report.
- [x] Obtain review/approval of the concrete first-slice design and ADR 0001.
- [x] Write and self-review the detailed first-slice implementation plan.
- [ ] Obtain review of the written implementation plan; preserve the user's bounded-delegation execution method.
- [ ] Resolve/lock product dependencies and validate compatibility; Milestone 0 cannot be called complete before the required readiness checks.
- [ ] Milestone 1: implement and verify the complete local handoff slice.
- [ ] Milestone 2: extend persistent project knowledge, retrieval, decisions and artifact versioning beyond the first slice.
- [ ] Milestone 3: reviewable Git changesets, repository/PR previews, conflict detection and authorized destination support.
- [ ] Milestone 4: meeting actions, deterministic prioritization, source-grounded status and Jira adapter.
- [ ] Milestone 5: dashboard, conversational workspace, skill explorer, artifact/approval center and history.
- [ ] Milestone 6: production security, broader evaluations, containers, operations and onboarding.

The first slice necessarily includes minimal persistence, checkpoints and revisioning from Milestone 2. That overlap does not mean all of Milestone 2 is complete.

## First-slice work packages after approval

| Order | Ownership / planned paths | Dependency and acceptance |
| --- | --- | --- |
| 1 | Lead: root Python/Node manifests, lockfiles, CI | Install project-local tooling; import/version check; minimal API and UI builds. Pin and audit direct dependencies; do not change global configuration. |
| 2 | Backend: `services/api/` models, storage and API tests | Agree OpenAPI contracts and schema migration before parallel UI. Round-trip SQLite, unique IDs, immutable revisions and project isolation. |
| 3 | Backend: registry, providers, workflow modules and tests | Safe YAML/path validation; explicit provider config; fixture and failing transports; stage restart and invalid output cases. Runtime skill content must have distribution rights and full provenance. |
| 4 | Frontend worker in isolated worktree: `apps/web/` only | Stable contracts from package 2; accessible intake/review forms, error/retry states, explicit destination and approval/download flow. |
| 5 | Publisher worker in isolated worktree: `packages/docs-template/` and publisher tests | Agreed artifact schema; audited pinned Starlight template, lockfile, inert content rendering, complete ZIP and manifest. |
| 6 | Lead: API publisher integration and approval checks | Exact revision + preview digest, stale approval rejection, concurrency/failure cases. Do not duplicate backend ownership with workers. |
| 7 | QA/review: `tests/` browser/evaluations plus docs | End-to-end review/export, clean extracted install/build, security fixtures, checkpoint recovery and diff review. Lead runs combined suite after integration. |

The [detailed implementation plan](2026-10-15-first-slice-implementation.md) expands these into test-first tasks with owned paths, contracts, commands and expected results according to [PLANS.md](../engineering/PLANS.md). User review of that plan remains pending; no product implementation has started.

Use at most two independent implementation workers after contracts stabilize; the root remains accountable for integration. Research agents required no worktrees because they only inspected public sources. Preserve failure logs/worktrees. Review returned changes and run regression checks before integration; no auto-merge.

## Verification and rollback

Bootstrap commands are `python3 -m unittest discover -s tests -v` and `git diff --check`. Product acceptance requires separate API, browser, security, typing/lint, package audit and docs build checks. See the final bootstrap verification report for actual results.

Use temporary databases/output directories in tests; never delete user projects to reset a test. Migration changes require backup/restore verification. Export to fresh paths initially; Git publishing stays preview-only until explicit target/payload authorization. Local Git commits are safe points, not deployment approvals.

## Resume here

Review the detailed implementation plan next; design/ADR approval is already recorded. Do not request that design approval again, restart repository research, or reinstall already available skills. Do not describe Milestone 0 or the product as complete from bootstrap tests.
