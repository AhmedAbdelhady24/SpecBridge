# Review correction verification

The review UI now lets an operator append/remove open questions and story acceptance criteria, and explicitly select evidence classifications. Corrections save as immutable revisions with stable requirement/story IDs. Editing invalidates the current review/package; a fresh review and approval of the exact new package are required.

This closes a usability blocker found while examining the saved failed model trials. It does not improve or qualify the generator: the latest frozen live comparison remains 2/5 semantic passes. Browser-driven correction is not evidence of acceptance by an unfamiliar human engineer.

## Scope and evidence

Changed production files: `apps/web/src/ArtifactEditor.tsx` and `apps/web/src/App.tsx`. Added five cases in `tests/e2e/feature-handoff.spec.ts`; no backend, schema, dependencies, runtime skill or provider settings changed.

Questions support 0–100 entries; each story retains 1–30 criteria. New blank fields require input before submission. Evidence labels never offer `verified`, and requirements cannot select `unknown`. Typing does not silently reclassify source text: the real backend continues to reject changed wording falsely labeled as an exact user excerpt. Source references remain visible and read-only.

Four new browser tests first failed against the original UI because the required controls were absent. Their traces were preserved locally in `.cache/review-correction-red/test-results/`. A fifth test imports the recorded synthetic notification-preferences draft from the reasoning comparison into a temporary fixture project, adds the missing observable delivery criteria, and verifies stable IDs and unchanged generation attempts/history. It makes no new model call and does not relabel the original model result as passing.

## Verification

| Check | Actual result |
| --- | --- |
| `npm run test:e2e` | 14/14 passed in 11.9 seconds, including five correction cases and the existing security/review regressions |
| `.venv/bin/python -m pytest -q` | 153 tests and 176 bootstrap subtests passed |
| Ruff lint/format | Passed; 25 Python files already formatted |
| mypy | Passed for 10 source files |
| Web typecheck/lint/test/build | Passed; 2 unit tests; production build succeeded |
| Standalone `verify_handoff.py` | Fresh install/build and dev/preview website checks passed in 15.56 seconds; evidence in `/tmp/specbridge-review-correction-20261016` |
| Review and `git diff --check` | Lead diff review and independent read-only review found no material issues; whitespace check passed |

The `uv run` invocation initially failed because sandbox access to the shared uv cache was denied. Running the same checks through the existing locked environment's `.venv/bin/` executables succeeded without dependency changes. Native `required` rejects empty fields; whitespace-only strings remain accepted under the existing backend minimum-length contract. This is not semantic validation.

## Delegation and boundaries

The isolated `codex/review-correction` worktree delivered the two UI files in commit `35116c5`; the lead inspected the diff and integrated it as `5d30703`. A read-only discovery agent identified the fixture setup and reviewed the resulting flow. The lead owns the browser tests, combined verification and documentation. Used installed versioned Superpowers design, TDD, worktree and verification guidance. No paid requests, real project data edits or external publication occurred.

Next: conduct an unfamiliar-engineer correction/handoff exercise and address generation/decision consistency separately. Milestone 1 acceptance remains open; milestones 2–6 remain.
