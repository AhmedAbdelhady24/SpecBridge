# Handoff evidence and coverage rules — 2026-10-16

Implemented and verified locally. A subsequent authorized [live targeted check](deepseek-handoff-rules-live.md) passed on the CSV case; broader semantic qualification remains open. The user asked to resolve the unsupported story motivation and missing headers requirement link by giving the model clearer rules and structure. The implementation itself made no model call; the later explicitly authorized live check is recorded separately.

## Root cause and change

The existing skill linked to an output contract, but Workflow supplied only the entrypoint body. The runtime model had no filesystem tool and never received the reference. Evidence labels were broad, and validation rejected dangling requirement IDs without checking that every requirement was covered by a story.

The original [runtime skill](../../skills/runtime/feature-handoff/SKILL.md) is now version 1.1.0. Its [output contract](../../skills/runtime/feature-handoff/references/output-contract.md) defines section roles, evidence labels, contrasting examples, explicit links and a final consistency check. Workflow loads this reference only for active generation. Reference bytes are checked against the same loaded skill snapshot; metadata discovery remains progressive. The selection digest detects changed skills, and the execution checkpoint records the digest of the actual composed skill instructions.

The prompt now requires:

1. `user_provided` text is a verbatim excerpt present in every cited source. Added wording or paraphrasing is a recommendation/assumption as applicable. A citation does not make a whole synthesized sentence factual.
2. Constructed user stories are normally recommendations. Omit an unstated motivation rather than invent a plausible “so that” benefit.
3. Every requirement has at least one explicit story link. Criteria covering export and headers require both IDs. Each linked behavior should have observable criteria.
4. Unknown values remain open questions/dependencies. Do not create unknown requirements phrased as commitments.
5. No generated self-verification or approval. The provider request schema excludes `verified`, and requirement kinds also exclude `unknown`; local validation enforces the policy even in JSON-object mode.

`models.validate_handoff` is the shared deterministic policy used by provider output, new revision writes and publication eligibility. It checks excerpts, source IDs, coverage and prohibited kinds. Publication rechecks eligibility for prepare/approve/download, so existing candidate approvals cannot bypass the rules. Old snapshots remain readable and unchanged; a nonconforming artifact requires an explicit corrected revision and fresh human review. Existing exported ZIPs are not rewritten.

## Concrete example and tests

The [original live draft](deepseek-complete-csv-draft.json) remains the historical output. The [corrected CSV example](handoff-corrected-csv-example.json) is a lead-authored illustration of the desired structure, not a newly generated response or a human-approved specification. It omits the external-tools motivation, labels the constructed story a recommendation, links REQ-1/REQ-2, quotes direct requests exactly, and keeps unknown limits/permissions as questions rather than requirements.

Regression tests first reproduced the missing injected contract, unsupported user-provided statement, missing requirement coverage, unknown commitment and legacy-publication bypass. They now pass. A public API run with mocked transport checks the complete reference in the actual outbound request. Tests also check a reference/provenance change during loading, tampering before generation, valid excerpts/proposed stories, old snapshot readability and explicit correction. The original draft fails the new policy while the corrected example passes.

Actual checks:

- Full pytest suite: 130 tests plus bootstrap link/source subtests passed.
- Ruff lint/format, strict mypy: passed; OpenAPI/types regenerated without drift.
- System skill-creator `quick_validate.py`: skill valid; registry/provenance tests passed.
- Local browser review/approval/security suite: 9/9 passed in 5.1 seconds.
- Fresh independent fixture export install/build/dev/preview/CSS/browser checks: passed in 15.11 seconds. [Exact package evidence](handoff-rules-verification.json); logs/screenshots in `/tmp/specbridge-handoff-rules-20261016-1`.
- Independent bounded backend review found no material issue. It inspected the code/tests and did not rerun the lead's suites or access credentials.

Changed paths: runtime skill/reference/provenance; backend models, skills, workflow, provider, storage and publication modules; focused provider/storage/approval/skill/workflow tests; current skill inventory, README and engineering records. Public JSON fields and database schema are unchanged. No dependency or permission was added.

Used system skill-creator guidance, TDD, debugging and verification methods. The lead implemented and ran checks; `backend_contract_review` independently reviewed boundaries and compatibility. Decision: use a conservative exact-excerpt meaning for user_provided rather than add a second LLM judge or introduce new evidence fields. Paraphrases must be labeled as synthesis. This can reject otherwise reasonable user-provided paraphrases; that tradeoff is explicit in the prompt and documentation.

## What this does not prove

Excerpt matching is not semantic entailment: a quote can omit context. Coverage checks validate IDs, not whether a criterion truly implements a requirement. A recommendation may still be weak or unsupported despite its honest label. Prompt examples are not evidence that a fresh generation follows them. Human semantic review remains required.

A revised request is prepared in ignored `.cache/deepseek-handoff-rules-preview.json`: same synthetic brief, DeepSeek `deepseek-flash`, skill 1.1.0/contract injected, thinking disabled, 3072 output tokens and no retries. No new source data, credential or external write is included. The user subsequently authorized this one request, and it completed with 610 output tokens. The [live check](deepseek-handoff-rules-live.md) records that targeted success and its generalization limits. Additional paid evaluation remains separately budgeted.
