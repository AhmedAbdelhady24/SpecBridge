# Evidence and requirement-coverage rules

User requested clearer injected rules after the live CSV draft added a motivation and omitted REQ-2 from story links. Scope is the existing skill/provider/workflow/storage/publication flow; no new model, framework, schema field, database migration or paid call.

Design: version the original runtime skill and its output contract. Load that contract only for the active generation, with its bytes checked against the same skill snapshot. Inject evidence policy, output roles, contrasting examples and a final coverage check. `user_provided` is reserved for an exact source excerpt with each cited source containing the whole statement; paraphrases/synthesized stories use recommendation/assumption as applicable. Omit unstated story motivations. Unknowns remain questions/dependencies, not invented commitments. Every requirement must appear in a story's explicit requirement_ids.

Deterministic boundary: one shared handoff validator enforces source IDs, no self-verification, conservative excerpt labeling and complete requirement coverage for generated output/new revision writes/publication eligibility. It cannot prove semantic entailment of recommendations or that an acceptance criterion implements the linked requirement. Preserve old snapshots as readable history; publication of a nonconforming old snapshot requires an explicit corrected revision and fresh review. Never rewrite the saved raw model draft.

Owned reach: runtime SKILL/reference/provenance; skills.py progressive preparation; workflow.py active loading; shared model validation, provider/store/publication callers; focused tests; skill inventory/evaluation/execution records. Public JSON shape remains unchanged, so no generated type change is expected.

- [x] Reproduce missing contract in actual outgoing request and both policy holes in provider/storage/publication tests.
- [x] Inject the contract from the checked skill snapshot, strengthen rules/examples, bump skill version and rehash provenance.
- [x] Share policy checks across write/generation/publication boundaries, retain legacy reads, and test explicit correction.
- [x] Run complete backend, typing/lint, browser and independent export checks; review diff and document limits. No live call without separate authorization.

Success: request contains the active contract; unsupported text cannot be labeled user-provided; uncovered requirement cannot pass new-write/export eligibility; direct excerpt/proposed story plus complete links passes. Tampered references fail before a provider call. Stored old artifacts remain readable. Semantic-generation effectiveness remains unqualified until a separately authorized live evaluation.

Verified:130 pytest tests plus bootstrap subtests; strict typing/lint; skill validation;9 browser cases; clean independent export checks. Independent bounded review found no material issue. [Actual results and semantic limits](../evaluations/handoff-rules-results.md). No live model call made; one revised synthetic request prepared for separate approval.
