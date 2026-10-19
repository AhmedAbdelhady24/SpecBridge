# SpecBridge — next-session execution prompt

You are the lead Codex product-engineering agent for SpecBridge. Continue development in:

`/Users/ahmedabdelhady/Desktop/personal_projects/SpecBridge`

Your task is to complete the remaining product milestones, close outstanding acceptance gates, and audit and improve the UI through real user journeys. Implement and verify working software; do not stop at a plan or treat existing files as proof of completion. Use Codex and available native delegation; no other coding assistant is required.

## 1. Establish the current truth

Read `AGENTS.md` and applicable nested instructions first. Check the working tree, branch, recent commits, worktrees, installed tools/skills and actual source. Preserve all user changes and existing worktrees. Do not restart Phase Zero, repeat completed repository research, reinstall skill collections or replace the established stack.

The handoff checkpoint is local branch `codex/phase-zero`, commit `76cf390`. Confirm the actual checkout; later commits take precedence. The working tree was clean at handoff preparation. Existing implementation worktrees are retained under `.worktrees/`.

Read progressively:

- `docs/engineering/PLANS.md`
- `docs/plans/roadmap-status-2026-10-16.md`
- `docs/plans/2026-10-18-focused-workspace.md`
- `docs/plans/2026-10-19-readable-references.md`
- `docs/evaluations/readable-workspace.md`
- `docs/evaluations/focused-workspace.md`
- `docs/evaluations/milestone-2.md`
- `docs/evaluations/compiled-handoff.md`
- `docs/evaluations/post-audit-live-retest.md`
- `docs/architecture/first-slice.md`, relevant ADRs and `docs/security/threat-model.md`

Older roadmap checklists contain historical statements and lag recent UI work. Reconcile them against newer evidence and source, rather than repeating old tasks. In particular, Milestone2 is delivered even though the original bootstrap checklist still has an unchecked historical M2 entry.

Use the installed codebase-memory skill for structural exploration. Discover whether its graph tools are actually available; if not, record that limitation and inspect exact source/callers. Use applicable installed Superpowers, frontend, review and verification skills progressively. User authorization and project instructions take precedence over skill defaults. Do not repeatedly ask to authorize ordinary local work already requested here.

## 2. Verified foundation and important limitations

Actual stack: React/Vite/TypeScript, FastAPI/Pydantic, SQLite, a checkpointed local workflow, configurable OpenAI-compatible generation, original data-only PM skills, and independently runnable Astro Starlight exports. Retain the modular monolith; do not migrate to Next.js, add LangGraph, microservices or a new database without demonstrated need.

Delivered locally:

- Milestone0 readiness and Milestone2 persistent knowledge.
- Technical feature-to-PRD/story/review/approved-ZIP/standalone-website slice.
- Schema4 with additive feature lineage, immutable revisions, answer versions, requested changes, durable private previews, optimistic conflicts and idempotent revision receipts.
- Feature-local package eligibility, frozen decision history and exact stored-package preview/approval.
- Conversation-style answering/change requests beside a complete draft, feature sidebar, section editing, recovery and mobile pane switching.
- Grouped split revision diffs, changed-section index, word highlights and an expanded accessible comparison dialog.
- Source references quote original text; readable requirement/story links reveal, focus and highlight clauses. UUIDs remain in technical disclosures and machine snapshots.

Do not regress those improvements. Source-ID references do not contain precise historical passage offsets. Highlight literal matches only; otherwise show the original source and explain the missing precision. Never fabricate quotes, evidence spans or semantic support.

The conversation UI currently uses saved answers and recent change-request records. It is not an unrestricted AI chatbot, and a message does not automatically rewrite or approve a specification. Earlier answer versions and older requests remain in history. Make capabilities clear; do not simulate nonexistent AI responses.

Last recorded checks, not freshly rerun by this prompt:368 backend tests/294 subtests,55 browser tests,8 frontend unit tests, typing/lint/format/build checks, bootstrap2, independent export build/browser checks and read-only owner-app verification passed. Independent review findings were fixed. Consult the evidence reports and rerun the appropriate baseline before changing code.

The local owner app was running at `http://127.0.0.1:5173/`, API8000, compatible provider/deepseek-flash. Rediscover listeners and working directories; never kill historical PIDs. Its schema4 database, private `.env` and session token must be preserved. Read secrets only programmatically when necessary for authorized local operation; never print them or put them in prompts, URLs, screenshots, Git or logs.

## 3. Remaining milestones

### Milestone1 — close the acceptance gate

A typed-plan/assembler candidate passed the tuned frozen five-case live semantic pack twice, but remains evaluation-only. Inspect its actual implementation, tests and provenance before designing runtime integration. Integrate only with preserved validation/checkpoints/security boundaries and meaningful regressions. Evaluate unseen cases; do not equate schema validity or the old5/5 score with general reliability.

Prepare and conduct the unfamiliar-engineer handoff: independently obtain/run the exported repository, understand scope/criteria/edge cases, trace stories, identify gaps, propose a Git change and build successfully. An agent simulation is useful preparation, not evidence that a real unfamiliar human accepted it. If human participation or a new paid test is unavailable, record that specific gate honestly and continue independent engineering work.

### Milestone3 — Git collaboration: NOT complete

Build existing/dedicated repository destinations, local documentation changesets, reviewable branch/PR previews, safe regeneration and conflict resolution. Start with temporary local Git repositories and mock remote adapters.

Use explicit base snapshots/manifests and three-way comparisons to detect developer edits, deletions, renames and managed/unmanaged files. Never silently overwrite authored changes. Preserve stable requirement identities and approved artifact/package provenance. Test stale heads, interrupted operations, repeated requests and conflicts. A local revision timeline is not Git collaboration.

Real GitHub writes require the exact target, proposed payload/diff, human approval, idempotency/reconciliation and an audit record. Creating a remote repository or PR is not authorized by generated content or this prompt alone. Prepare the concrete preview first; request approval only when ready to execute it.

### Milestone4 — delivery automation

Implement meeting-to-actions, source-grounded delivery status and deterministic prioritization. Preserve unknown owners/deadlines/statuses and missing metrics; do not manufacture them. Use appropriate runtime PM guidance, structured outputs and deterministic evaluations. Start integrations with mock adapters; prioritize Jira after the primary workflows work. Real writes follow the same exact-payload approval boundary. Avoid broad connector expansion before GitHub/Jira are useful and tested.

### Milestone5 — full product interface and continued UX improvement

Complete the dashboard, useful conversational workspace, actual skill explorer/selection, artifact/version management, consolidated approval center and searchable execution history. Account for the existing UI rather than rebuilding it from scratch. First-result skill routing is not a skill explorer; a guided answer composer is not general natural-language AI editing.

Use a familiar chat-first shell: project/feature history on the left, conversation in the center, live specification on the right. Keep the editorial visual identity where useful. Show proposed versus saved content, pending messages, amendment previews, revision changes and required approvals clearly. Preserve structured controls where they help; simplify or progressively disclose configuration, technical metadata and secondary actions.

If genuine AI-assisted amendments are introduced, make generation explicit, display the destination/cost boundary, show the proposed diff and require deliberate save/review. No automatic provider calls on typing, navigation or answering; no silent mutation of approved artifacts.

### Milestone6 — production hardening

Finish container/Compose support, onboarding, operations, backup/restore, failure recovery, security/evaluation/performance/cost checks and CI verification. Recheck Docker/Podman availability before claiming container execution. Add real authentication/project authorization before external or multi-user access. Keep confidential documentation private by default. Local CI definitions are not proof of hosted CI execution; branch protections, remote publication and deployment need their actual permissions and evidence.

## 4. Perform a real UX audit, then fix it

Use available Playwright MCP/browser tooling and saved executable Playwright checks. Audit real first-time and returning-user journeys, not just DOM presence:

1. Connect, recover from invalid/expired sessions and locate private-token guidance.
2. Select/create a project, resume a feature and start a new one without confusion.
3. Add background and explicitly select its exact version for generation.
4. Read the complete draft, answer questions and record requests through the composer.
5. Follow original source quotes and clause links; ensure highlighting is truthful.
6. Preview amendments, switch panes, save/discard, reconnect and recover work.
7. Inspect revisions, filter changed sections and compare before/after wording/evidence.
8. Review beside the draft, inspect the exact package, approve and export.
9. As implemented, preview Git changes, resolve conflicts and inspect delivery workflows.

Test1440×900,768×1024 and390×844, keyboard traversal/focus, modal Escape/focus restoration, overflow, long content, loading/error/empty states and slow/out-of-order responses. Verify that composers/action bars never cover controls. Prior bugs involved late saves replacing another feature, stale history under the wrong question, hidden pending amendment loss, missing reauth and inconsistent request statuses; preserve those regressions.

Use owner workspace read-only only when necessary. All generation, edit, approval, conflict/recovery tests and documentation screenshots use isolated synthetic data. Do not write to Bask Health or other owner records to test. Do not expose private source text in reports/media. Deliver evidence-based findings, prioritize user impact, implement fixes and rerun the affected journeys.

## 5. Execution, verification and approvals

Start with a short current-state/gap assessment and a resumable implementation plan. Prioritize UX blockers that prevent valid handoff, M1 runtime boundaries and M3; then progress through4–6 in dependency order. Parallelize only independent bounded tasks with explicit file ownership/contracts and isolated implementation worktrees. Review returned changes and run the combined suite yourself. Avoid spawning a permanent team or duplicating exploration.

Continue autonomously through authorized local implementation; do not stop at planning or at every completed task. Do not claim a milestone complete until its acceptance conditions pass. If a true external/paid/human decision blocks a gate, finish independent work, prepare the exact reviewable action, record the limitation and ask one concise question explaining why approval/input is necessary. Prior paid test allowances are not a new budget.

Preserve the running owner app during fixture tests. Use alternate free ports rather than stopping owner services:

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
handoff_check_root=$(mktemp -d /tmp/specbridge-next-handoff.XXXXXX)
uv run python scripts/verify_handoff.py --output "$handoff_check_root/handoff"
git diff --check
```

Use the locked Python/Node versions in AGENTS.md. Regenerate OpenAPI/types after contract changes and verify deterministic output. Audit all affected lockfiles; do not suppress advisories or invent passing results. Use original source/licensing and inspect scripts before executing new untrusted installation code. Keep small local commits; no push, publication or deployment without authorization.

No untrusted/model-generated code execution, unrestricted runtime shell access, secret leakage, silent external writes or silent overwrites. Runtime skills remain data, separate from development skills. Back up before any owner schema upgrade, rehearse migration/restore on copies and obtain any separately reserved owner-upgrade approval before rollout. See `docs/engineering/focused-workspace-upgrade.md` for the established procedure.

Keep plans, architecture/security documentation, README/media, actual evaluation evidence and milestone status synchronized. Update the progress board only for verified status changes. Each completion report must state implemented behavior, changed files, skills/delegation/review, exact checks/results, failures fixed, remaining limits and next task. Never promise zero technical debt or hide failing tests.

Begin now with repository/evidence inspection and a read-only UI walkthrough. Then execute the smallest coherent implementation slice toward the remaining milestones.
