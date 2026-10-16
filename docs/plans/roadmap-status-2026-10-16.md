# SpecBridge phase status — 2026-10-16

Milestone 0 is delivered locally. Milestone 1's technical vertical slice is implemented and locally verified, but product acceptance remains open. **Five later milestones (2–6), plus the current Milestone 1 gate, remain.** They are not equal amounts of work, so milestone count is not a completion percentage.

This checkpoint is based on a fresh read-only audit of source, not directory names alone. See the [original roadmap](bootstrap-and-first-slice.md) for scope and the [latest provider comparison](2026-10-16-reasoning-comparison.md) for current evidence. That five-case reasoning-enabled run passed 5/5 backend and 2/5 semantic checks; the M1 gate remains open.

| Phase | Verified or existing foundation | Remaining deliverables |
| --- | --- | --- |
| 0 — Codex readiness | Local environment audit, source/license research, skills inventory, accepted architecture, AGENTS/plans, locked tools and automated CI/test definitions. | Delivered locally. Hosted CI execution and remote protections are not established. |
| 1 — First complete vertical slice | Local feature evidence → skill → PRD/stories → revision → review → exact ZIP approval → standalone Starlight website, with real-browser and clean-package checks. Live DeepSeek transport has been exercised. | Full frozen semantic suite passing on a selected configuration, useful model-artifact review, and actual unfamiliar-engineer handoff. Structural JSON validity alone is insufficient. |
| 2 — Persistent knowledge | SQLite projects/sources, hashes/citations, immutable revisions, stable requirement/story IDs, concurrency protection, checkpoints/leases/history, review/audit provenance. | Goals/stakeholders/decisions/knowledge entities, useful contextual retrieval beyond selected source IDs, revision/decision navigation, expanded-model backup/migration verification. |
| 3 — Git collaboration | Portable ZIP, deterministic managed files, manifests/hashes, revision/source mapping and exact package approval. | Existing/dedicated repository destinations, Git changesets/PR previews, safe regeneration, developer-edit conflicts/three-way comparison, authorized retry-safe external writes and audit. |
| 4 — Delivery automation | Reusable skill/provider/workflow and evidence boundaries. | Meeting actions, deterministic prioritization, source-grounded delivery reporting, mock adapters then Jira integration with exact-payload approval/idempotency. |
| 5 — Full product interface | Session/project selection, intake, evidence/editor, review/rejection, package approval/download and basic run recovery. | Dashboard, conversational workspace, actual skill explorer, artifact/version management, consolidated approval center and searchable history. Current first-result skill selection is not a full explorer. |
| 6 — Production hardening | Backend/security/contract tests, fixture browser checks, strict typing/lint/builds, pinned least-privilege CI definition, audits, threat model and local onboarding. | Containers/Compose, supported deployment/operations, real authentication/project authorization before nonlocal/multi-user use, backup/recovery, hosted CI proof and broader security/performance/cost/human acceptance. |

## Evidence and dependency order

Audit inspected models/storage/workflow/main/publication/publisher, actual React UI, CI definition and current evaluations. The [first-slice results](../evaluations/first-slice-results.md) are historical technical evidence, superseded for live-model status by [autonomous qualification](../evaluations/autopilot-qualification.md), [no-client-cap retest](../evaluations/no-client-cap-retest.md) and the new reasoning comparison.

Work order remains: close the M1 semantic/human handoff gate, expand M2 knowledge, build M3 against stable artifact/provenance contracts, add M4 workflows/integrations, expand M5 around stable operations, and finish M6 operational acceptance. Security, tests and documentation continue within each phase; authentication must precede any external/multi-user exposure. No remote publication is implied.

No credible calendar completion estimate or percentage is inferred from file counts. The current uncertainty is model usefulness and acceptance, not whether the backend/UI/export files exist. Per-request application usage persistence, native Claude and local serving remain provider-plan work; diagnostic runner usage records do not implement product metering.
