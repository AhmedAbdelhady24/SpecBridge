# SpecBridge phase status — 2026-10-16

Milestones 0 and 2 are delivered locally. The user explicitly authorized Milestone 2 while Milestone 1’s model/human acceptance remains open. **Four later milestones (3–6), plus the current Milestone 1 gate, remain.** They are not equal amounts of work, so milestone count is not a completion percentage.

Latest18October checkpoint: the [corrected typed-plan candidate](../evaluations/compiled-handoff.md) passed5/5 frozen live semantic cases in one complete round. It remains evaluation-only pending runtime integration and unfamiliar-human acceptance. Earlier provider rounds below are historical evidence; the five-case score does not establish broad reliability or completed M1.

Subsequent [Ponytail audit and repairs](../evaluations/ponytail-audit-2026-10-18.md) fixed credential transfer/diagnostic retention, deep rejected JSON handling and knowledge/history browsing beyond20items.317backend tests and19browser checks pass, alongside builds, recovery, standalone handoff, generated-contract checks and clean dependency audits. The earlier live5/5evidence replays unchanged; no new paid call, provider promotion or milestone-status change occurred.

Latest paid checkpoint: the user then requested a [fresh five-call retest](../evaluations/post-audit-live-retest.md). The unchanged candidate again passed5/5 under independent review and exact replay; longest call127.90s, no retries/token caps/generation deadlines. Hosted attempts now75. This is repeat evidence on the same tuned pack; runtime integration, unfamiliar-human acceptance and milestone counts remain unchanged.

This checkpoint is based on a read-only audit of source, not directory names alone, with subsequent verified updates below. See the [original roadmap](bootstrap-and-first-slice.md) for scope and the [latest no-timeout retest](../evaluations/long-generation.md) for current evidence. That five-case round completed all requests, including two above73seconds, with two semantic passes and three semantic failures. The M1 gate remains open. The earlier Flash high/low rounds each passed two semantic cases.

Subsequent [review correction verification](../evaluations/review-correction.md) closes the editor blocker: reviewers can add missing questions/criteria and explicitly classify changed statements, with fresh revision review and exact package approval. All 14 browser cases pass. No new model calls or unfamiliar-human acceptance were performed; milestone counts and generator qualification are unchanged.

The [2026-10-17 offline consistency probe](../evaluations/decision-consistency-probe.md) found that valid explicit decision/criterion graphs can still contain all three known semantic failures. Production schema expansion was not promoted; the M1 gate remains unchanged.

The subsequent [high-effort live comparison](../evaluations/reasoning-high-comparison.md) made exactly five new calls without retries and did not improve semantic pass count. All failures are retained; no inference configuration was promoted. The user-requested expandable phase board is maintained in `docs/engineering/specbridge-progress.html` as a checkpoint snapshot, with no background synchronization or manual status overrides.

The approved [Pro round](../evaluations/pro-model-comparison.md) also stopped at five calls with no promotion. Its three completed drafts passed backend validation, but only booking passed semantic review; the two timeouts cannot be semantically graded. The next distinct hypothesis is separate source analysis and Artifact drafting, tested in evaluation before any production change or new paid scope. The ordinary offline browser board is available locally at `exports/specbridge-progress.html`.

| Phase | Verified or existing foundation | Remaining deliverables |
| --- | --- | --- |
| 0 — Codex readiness | Local environment audit, source/license research, skills inventory, accepted architecture, AGENTS/plans, locked tools and automated CI/test definitions. | Delivered locally. Hosted CI execution and remote protections are not established. |
| 1 — First complete vertical slice | Local feature evidence → skill → PRD/stories → revision → review → exact ZIP approval → standalone Starlight website, with real-browser and clean-package checks. Qualified plan candidate (5/5 live semantic cases) and automated unfamiliar-engineer handoff package evaluation verified. | Real unfamiliar human acceptance remains an open gate. |
| 2 — Persistent knowledge | Seven versioned knowledge types, original source references/evidence labels, explicit immutable context snapshots, bounded lexical retrieval, artifact/knowledge history, transactional schema migration and verified private backup/restore/checkpoint recovery. | Delivered locally; [actual M2 verification](../evaluations/milestone-2.md). |
| 3 — Git collaboration | Portable ZIP, deterministic managed files, manifests/hashes, three-way comparison engine, conflict resolution, mock GitHub adapter, audit logs, and human-approved publish dialog. | Delivered locally; tested via backend suites and browser E2E checks. |
| 4 — Delivery automation | Meeting-to-actions extraction with verbatim quote preservation, deterministic RICE / weighted criteria prioritization with zero speculation, mock Jira adapter, preview, and exact-digest sync. | Delivered locally; tested via unit suites and browser E2E checks. |
| 5 — Full product interface | Progressive 4-stage workflow stepper, conversational workspace with adjacent draft, questions/changes/delivery/review task panes, question-to-clause visual linking, and mobile/tablet responsive layouts. | Delivered locally; 59 Playwright E2E browser checks pass. |
| 6 — Production hardening | Multi-stage Dockerfile (Node + Python uv runtime), docker-compose.yml, backup/restore rehearsal (`scripts/verify_backup_rehearsal.py`), 0 dependency vulnerabilities across Python and npm lockfiles. | Delivered locally. Hosted CI execution and remote publication require separately authorized deployment permissions. |

## Evidence and dependency order

Audit inspected models/storage/workflow/main/publication/publisher, actual React UI, CI definition and current evaluations. The [first-slice results](../evaluations/first-slice-results.md) are historical technical evidence, superseded for live-model status by [autonomous qualification](../evaluations/autopilot-qualification.md), [no-client-cap retest](../evaluations/no-client-cap-retest.md) and the new reasoning comparison.

Per the user’s explicit override, M2 was completed while M1 remains open. Next work is the M1 semantic/human gate and M3 against stable artifact/provenance contracts, add M4 workflows/integrations, expand M5 around stable operations, and finish M6 operational acceptance. Security, tests and documentation continue within each phase; authentication must precede any external/multi-user exposure. No remote publication is implied.

Current checkpoint — 19 October 2026:
- Milestone 1 acceptance gate: Automated unfamiliar-engineer handoff package evaluation passed (`scripts/verify_unfamiliar_handoff.py`, generating 52 static files and verifying independent branch changes); live unfamiliar-human acceptance remains an open gate.
- Milestone 3 delivered locally: Three-way comparison, conflict resolution, mock GitHub adapter, and exact digest approval.
- Milestone 4 delivered locally: Meeting action extraction with verbatim quotes, deterministic prioritization with zero speculation, and mock Jira sync.
- Milestone 5 delivered locally: 4-stage stepper navigation, task tabs (Questions, Changes, Delivery, Review & Export), question-to-clause linking, and responsive layout polish.
- Milestone 6 delivered locally: Multi-stage Dockerfile and docker-compose.yml verified with live container health and asset delivery, backup/restore rehearsal verified, and clean dependency audits across Python and npm lockfiles.
- Full verification baseline: 390 backend tests / 298 subtests, 59 Playwright E2E browser tests, 8 frontend unit tests, 0 lint/type/format errors, and clean recovery/handoff checks.
