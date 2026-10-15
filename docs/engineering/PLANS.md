# Engineering plans

Substantial changes have one self-contained plan in `docs/plans/`. The active plan is [bootstrap-and-first-slice.md](../plans/bootstrap-and-first-slice.md).

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
