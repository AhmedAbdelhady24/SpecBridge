# Engineering plans

Approved next design: [focused requirements workspace](../architecture/review-workspace-design.md), a source-checked refinement of the user-supplied UX audit, approved by the user on 18 October 2026. The [detailed implementation plan](../plans/2026-10-18-focused-workspace.md) covers complete-draft side view, persistent question replies, feature-local history/concurrency, direct context selection and exact package content preview. The plan was confirmed, implemented and verified; owner rollout was separately authorized and completed on19 October2026. Preserve the established lead-agent execution approach. Design approval does not supersede verified implementation evidence or authorize paid calls, publication or an owner-database migration.

Substantial changes have one self-contained plan in `docs/plans/`. The current execution record is [readable references and conversation/revision UI](../plans/2026-10-19-readable-references.md), following the [focused workspace implementation](../plans/2026-10-18-focused-workspace.md), following the [approved review-workspace UX repairs](../plans/2026-10-18-review-workspace-ux.md), following [README media](../plans/2026-10-18-readme-media.md), the [fresh post-audit paid retest](../plans/2026-10-18-post-audit-live-retest.md) and [Ponytail audit and repairs](../plans/2026-10-18-ponytail-audit.md). [Milestone2](../plans/2026-10-17-milestone-2.md) and the [first-slice implementation plan](../plans/2026-10-15-first-slice-implementation.md) preserve earlier execution; the [roadmap](../plans/bootstrap-and-first-slice.md) tracks milestone status. The first-slice design and implementation plan were approved on 2026-10-15. Earlier qualification notes below are chronological history, superseded by the latest checkpoint.

Each plan records:

1. User outcome, scope, non-goals and independently verifiable acceptance criteria.
2. Current repository state, inspected sources, assumptions and open decisions.
3. ADRs and contracts: schemas, state transitions, permission boundaries and error behavior.
4. Ordered work packages with exact owned paths, dependencies, tests and expected results.
5. Delegation/worktree strategy and review/integration order.
6. Reproduction commands, dependencies, fixture provenance and rollback/data protection.
7. Checkboxes, actual execution results, unresolved failures and the next resumable action.

Use `proposed`, `approved`, `in progress`, `verified`, or `blocked by <specific decision>` precisely. Never check off an implementation milestone because files exist. Record human approvals with their scope; an architectural approval is not authorization for an external write.

Keep plans near the size of the work. Add detailed implementation tasks after the design is approved; do not invent line numbers in nonexistent files. Update the same plan when scope changes and rewrite stale instructions. Every handoff must be reproducible without this conversation.

Latest provider checkpoint: [autonomous qualification](../plans/2026-10-16-autopilot-qualification.md) completed its bounded tests without achieving full live-semantic acceptance. Keep failed evidence and the recorded live-call limit when resuming; do not treat the earlier targeted retest as full qualification.

Subsequent authorized [no-client-cap retest](../plans/2026-10-16-no-client-cap-retest.md) completed five calls; schema passed but semantic acceptance did not. Its single-round authorization is consumed.

Current continuation: [reasoning-enabled comparison](../plans/2026-10-16-reasoning-comparison.md); [phase checkpoint](../plans/roadmap-status-2026-10-16.md) distinguishes delivered foundations from remaining milestones. Historical no-live statements are not current qualification status.

Latest completed scope: [human review correction](../plans/2026-10-16-review-correction.md), verified with browser/backend/static and standalone-package checks. Next resumable work is unfamiliar-engineer correction/handoff acceptance and separate generation/decision-consistency design; current live-semantic acceptance remains open.

Subsequent [offline decision-consistency probe](../plans/2026-10-17-consistency-probe.md) demonstrated that the three preserved semantic failures survive valid declared graphs. Do not adopt a production decision schema as a quality fix on this evidence. Next is an explicitly scoped generation comparison and actual unfamiliar-human acceptance; no additional paid calls are authorized by the probe.

Latest completed comparison: [high effort](../plans/2026-10-17-reasoning-high-comparison.md), five new calls with 4/5 backend and 2/5 semantic passes. Scope consumed; configuration not promoted. Maintain the requested interactive Kanban checkpoint in `docs/engineering/specbridge-progress.html` alongside roadmap evidence. Next generation hypothesis must address the recorded behavioral/decision failures; unfamiliar-human acceptance remains open.

Latest completed scope: [approved model crossover and accessible board](../plans/2026-10-17-model-crossover.md). Five Pro calls yielded one semantic pass, two semantic failures and two timeouts without assessable drafts. Approval consumed; no configuration promoted. The next task is an evaluation-only source-analysis→Artifact-drafting design with original evidence retained; do not add further paid calls or production orchestration automatically. Keep the canonical phase board and local offline browser export synchronized with this result.

Latest checkpoint: M2 is delivered locally. The [compiled handoff candidate](../plans/2026-10-17-compiled-handoff.md) subsequently passed5/5frozen live cases; runtime adoption and unfamiliar-human acceptance remain open. The user then authorized a whole-codebase Ponytail review and repairs; [actual audit results](../evaluations/ponytail-audit-2026-10-18.md) distinguish fresh automated verification from preserved live evidence. No new paid call, external write or milestone acceptance is implied by this maintenance work.
