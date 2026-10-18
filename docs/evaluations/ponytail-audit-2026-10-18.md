# Ponytail codebase audit and verified repairs

What this repo does: SpecBridge stores product evidence, generates checkpointed requirements, and requires review plus exact-package approval before exporting a standalone documentation site. The audit assumed the documented local, single-owner FastAPI/SQLite application. It did not judge the MVP as an unimplemented multi-user service.

Ponytail5.3.2 was already installed and available. The lead read and applied its primary, audit and review skills; no duplicate installation, dependency, hook or permission change was introduced. [Skill provenance and instruction hashes](../engineering/skill-inventory.md) and [resumable execution record](../plans/2026-10-18-ponytail-audit.md) are maintained.

## Must fix — resolved

1. **Configured credentials could enter model prompts or accepted artifacts.** [Provider boundary](../../services/api/specbridge/providers.py#L52).
   - **What this is:** The configured API credential belongs in the authorization header, separate from selected evidence and generated documents.
   - **Problem:** A source containing the credential was sent to the model; a valid returned Artifact containing it was accepted. Synthetic plain and JSON-escaped cases reproduced this without a real key or network call.
   - **Fix:** Reject credential-bearing payloads before HTTP and inspect decoded output before accepting it. Check the shared request entrypoint as well as normal generation. Do not redact or silently change a reviewed output.
   - **If skipped:** An accidental or reflected configured credential can move into model context or durable/exportable generated documentation. This guard recognizes the configured credential; it is not general secret detection or protection against arbitrary obfuscation.

2. **Rejected evaluation content could still save an escaped credential.** [Retention boundary](../../scripts/qualify_provider.py#L213).
   - **What this is:** The opt-in evaluation harness preserves failed synthetic outputs for diagnosis.
   - **Problem:** Escaping a key character bypassed the raw-byte check. Even when the provider rejected the decoded credential, the harness wrote it to rejected text. Tool-call and malformed-content branches also needed protection.
   - **Fix:** Suppress content retention after a secret rejection and check decoded message/content before any rejected-file write. Eight plain/escaped, valid/malformed and tool-response combinations now pass.
   - **If skipped:** Diagnostic evidence itself can disclose the credential even though no Artifact is accepted.

3. **Deep rejected JSON crashed the diagnostic runner.** [Sanitized failure handling](../../scripts/qualify_provider.py#L270).
   - **What this is:** Rejected content is parsed again to decide whether it is safe to retain.
   - **Problem:** Deeply nested final JSON triggered an uncaught recursion failure, aborting the round without its results record. Independent review reproduced it with one mocked request.
   - **Fix:** Catch recursion failures at this retention boundary and keep sanitized metadata only. The regression verifies one attempt, recorded failure, no rejected content and no crash.
   - **If skipped:** A bounded provider response can interrupt diagnostic evidence collection and obscure the actual result.

## Should fix — resolved

4. **Knowledge browsing and history stopped after twenty items.** [Backend cursor](../../services/api/specbridge/knowledge.py#L240), [UI callers](../../apps/web/src/KnowledgePanel.tsx#L57).
   - **What this is:** Current knowledge, immutable versions and artifact revisions use bounded result pages.
   - **Problem:** The UI requested only the first20, without a continuation control. Item21 and version1 of a21-version record were stored but unreachable through normal browsing.
   - **Fix:** Add an optional bounded current-record cursor preserving title-match priority/id ordering and project scope. Add explicit continuation buttons for all three lists; bind list continuation to submitted search/archive filters. Reuse existing strict history/revision cursors.
   - **If skipped:** Growing projects appear to lose older evidence. The new real-browser test reaches all21records, versions and revisions without duplicates and checks search-filter binding.

No additional material defect was confirmed in the reviewed scope. No speculative framework, forced abstraction removal, dependency replacement or stylistic refactor was justified. Existing transactions, evidence labels, project isolation, generation leases, retry acknowledgment and exact approvals were preserved.

## Actual verification

| Check | Actual result |
| --- | --- |
| Backend/component/security suite | 317 tests passed; bootstrap subtest count recorded in verification JSON |
| Full real-browser suite | 19 passed, including the new21-item regression |
| Web client unit checks | 2 passed |
| Ruff lint and formatting | Passed;38Python files formatted |
| Application mypy | Passed;11sources |
| Web TypeScript/lint/production build | Passed |
| Documentation template build | Passed |
| Fresh standalone documentation handoff | npm ci/build and browser checks in dev/preview passed in15.92s, fixture session closed first |
| Workspace backup/restore/checkpoint recovery | Passed;7knowledge types, immutable history and private0600backup |
| OpenAPI/TypeScript generation | Additive optional after parameter generated; second regeneration produced no further drift |
| Dependency audits | Python57installed dependencies and all3npm lockfiles:0known vulnerabilities |
| Preserved live evidence | Both recorded compiler rounds replay exactly; original successful5/5outputs, prompts, rubric and source pack unchanged |
| Independent repair review | No remaining material finding; reviewer reran31provider-caller tests and16knowledge tests successfully |

The tests were observed failing before their fixes. The initial browser failure reached its test deadline waiting for the absent Load more button; its trace is preserved locally under `.cache/ponytail-red-browser`, outside Git because traces include synthetic session data. A cursor-parameter ordering error caused four intermediate knowledge failures and was corrected. One existing contract test used the same string for model name and API key, correctly triggering the new guard; its key was changed to a distinct synthetic sentinel without weakening the assertion. The later deep-JSON and tool-response failures found during independent review are fixed and retained as executable regressions. No failing check was suppressed.

Astro emits non-failing warnings about optional i18n/custom404 content and an unset public sitemap site; local standalone output builds and serves correctly. No public hostname was invented to silence them. Playwright also reports the existing NO_COLOR/FORCE_COLOR environment warning. These are warnings, not failed checks.

Commands are the repository's documented pytest/unittest, Ruff, mypy, web typecheck/lint/test/build, template build, test:e2e, verify_handoff.py, verify_workspace_recovery.py, export_openapi.py/generate:types, pip-audit and npm audit for each lockfile. The independently extracted package and its detailed logs/result remain at `/tmp/specbridge-ponytail-handoff-20261018`; choose a new path when reproducing. The [machine-readable verification](ponytail-audit-2026-10-18-verification.json) preserves outcomes and scope.

## Coverage and disposition

Read source and connected callers/tests across all application backend modules; React intake, knowledge, review, correction and approval flows; runtime skill metadata/reference confinement; provider and evaluation boundaries; deterministic documentation rendering/template; backup, restore and generation recovery; build, CI and dependency configuration. Two independent read-only reviewers covered backend and web/operations, then reviewed the repairs. Root alone implemented and integrated the changes. Implementation workers were not used, so there were no overlapping writes or unnecessary worktrees.

Changed product files are provider credential checks, current-record paging and knowledge UI continuation controls, plus additive generated contracts. The diagnostic runner and regressions cover the other failures. Dependency manifests/locks, data schema, frozen model evidence and normal provider configuration are unchanged. No private `.env` was read, no real project data was accessed and no paid model request was made during this audit. Skill source was the existing local installed package, not a new upstream download.

Codebase-memory instructions were read, but its graph/index/coverage tools were not exposed. Exact-source/caller reads were used; no graph-completeness or absence-of-all-bugs claim is made. Historical evaluation JSON was preserved and its relevant live rounds replayed, rather than regrading every archived draft. No production-load benchmark, hosted CI, remote branch protection, Claude/local-model qualification, unfamiliar-human handoff or public deployment was performed. The5/5live result is prior evidence, not a fresh model run or proof of broad reliability.

Verdict: all confirmed findings are fixed and applicable checks pass. Continue with runtime integration of the qualified typed-plan candidate and unfamiliar-engineer acceptance. Milestone0/2 status and remaining milestone counts are unchanged.

Not checked: the external/production/human paths above; there is no claim that a finite audit proves zero unknown defects.
