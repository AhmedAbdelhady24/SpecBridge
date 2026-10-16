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
