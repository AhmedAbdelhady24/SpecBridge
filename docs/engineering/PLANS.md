# Engineering plans

Substantial changes have one self-contained plan in `docs/plans/`. The active implementation plan is [2026-10-15-first-slice-implementation.md](../plans/2026-10-15-first-slice-implementation.md); the [roadmap](../plans/bootstrap-and-first-slice.md) tracks milestone status. The first-slice design and implementation plan were approved on 2026-10-15. Technical execution is verified; see the [results](../evaluations/first-slice-results.md) for remaining qualification.

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
