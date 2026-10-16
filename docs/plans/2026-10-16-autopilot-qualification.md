# Autonomous full-pack qualification

Status: test execution verified; live acceptance not achieved. User explicitly requested autopilot check/test/fix until all cases pass. This supersedes earlier one-shot live-call scopes for this bounded task, not external publishing or artifact approval requirements.

Scope is the five existing synthetic provider scenarios plus applicable repository regression/security/browser/build checks. Before live execution freeze the original criteria and supplemental checks addressing previously recorded semantic gaps. Preserve all prior evidence and all failed rounds; do not weaken validators, edit generated drafts into passing samples or drop hard cases. Unknown business decisions remain questions; they cannot be invented in order to pass.

Success: one complete full-pack round on the same active skill passes backend validation, source/link checks and lead plus independent review against frozen criteria, and repository checks pass. This is a sample-pack result, not guaranteed reliability, unfamiliar-engineer acceptance or permission to publish.

Live bounds stated before execution: existing https://api.deepseek.com / deepseek-flash, JSON-object mode, reasoning none, 3072 output tokens each. Maximum three rounds of five calls (15 calls, 46080 output tokens, input additional); no transport retries or silent automatic repair. Stop on the first fully passing round. Diagnose each failed round before another one, change only a justified cause, and keep exact request previews/hashes. Cost unknown. Do not expand model/provider or send real project data.

Ownership: lead owns runtime prompt/provenance, tests and evaluation records; any implementation stays in lead checkout. Independent read-only QA owns frontend/build/browser execution; independent read-only reviewer assesses saved drafts against frozen source criteria. No concurrent source writers or implementation worktrees necessary. Use Superpowers debugging/TDD/verification and system skill-creator progressively when a prompt edit is supported by failures.

- [x] Freeze five-case acceptance supplement and run full baseline once under skill 1.2.0.
- [x] Diagnose structural/semantic failures, implement minimal evidence-based correction with offline regressions if needed, rehash/version skill.
- [ ] Run full pack on final active skill and independently review actual outputs; retain failures and counts.
- [x] Verify backend, frontend, contract drift, fixture browser checks, standalone export/build, dependency scans and diff.
- [x] Record final pass/fail matrix, limitations, exact commands, call/token totals, reviewer outcomes; commit small local changes. No remote writes.

Reproduce: preview with `PYTHONPATH=services/api uv run --env-file .env python scripts/qualify_provider.py`; execution adds `--execute HASH --output NEW_DIRECTORY` only within authorized round budget. Frozen supplemental criteria are tests/fixtures/provider-qualification/acceptance.json; these are evaluator rules, not extra facts sent to the model. Full raw synthetic outputs and sanitized metadata go under docs/evaluations/autopilot-qualification-2026-10-16/round-N/. Runtime source files remain data with an empty tool allowlist.

Next resumable action: run round 1 without speculative prompt changes, inspect saved artifacts against the supplement and original criteria. If three distinct rounds still fail, stop honestly with findings rather than report a fabricated pass.


Execution outcome: all three full rounds ran once (15 calls), with unchanged criteria. Backend-valid/semantic-pass counts: round 1 = 5/2, round 2 = 5/3, round 3 = 4/2, each out of five. The full-pack acceptance checkbox remains unfulfilled. Do not resume another paid round automatically under this exhausted plan.

The independent semantic reviewer agreed with lead failures. A repeated-failure architecture advisor recommended stopping additive prompt edits, archiving experiments and restoring committed skill 1.2.0; the lead did so. Both experimental skill snapshots/provenance match saved request hashes. Restoration is containment, not qualification. The actual REQ-4 default omission is now a saved offline regression; both semantic contradictions remain negative fixtures. No runtime validator was weakened and no actual output edited.

Read-only web QA passed type/lint/2 unit tests/build and all 9 E2E cases (5.3s). Lead passed backend/static/contract drift, fresh standalone handoff (15.99s, npm ci/build/dev/preview and browser navigation/inertness), Python audit (57 dependencies, 0 known vulnerabilities), and all 3 npm audits (0 advisories). Generated contracts/types have no diff. Active skill validation passed; no dependency, public schema, database or environment setting changed.

[Full results, archived experiments, known failures and limits](../evaluations/autopilot-qualification.md). Next is a controlled configuration comparison with verified API support and an explicit new live scope. The user has not been asked to accept a defective handoff; no model output has been approved or published.

Final local commands: `.venv/bin/python -m pytest -q` passed145 tests and144 bootstrap subtests in1.22s; Ruff lint/format passed (25 files); mypy passed (10 sources); Agent Skills validation passed; `git diff --check` passed. Backend replay matched all15 recorded response statuses, including round3 invalid_artifact. All repository checks pass while model acceptance remains failed.
