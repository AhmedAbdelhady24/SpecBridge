# Five-case retest without a client output cap

Status: retest verified; semantic acceptance failed. User explicitly requested “remove the tokens cap and try again” after autonomous qualification failed. This authorizes one new full-pack round (five synthetic calls), omitting max_tokens/max_completion_tokens, no retries. Provider defaults, the existing 60-second deadline and 256 KiB response bound still apply; dollar cost unknown. No reasoning/model/prompt/criteria change.

Scope: add explicit --omit-output-cap diagnostic mode only to scripts/qualify_provider.py with offline regressions. Existing application provider configuration/guards remain as committed; no .env edits or runtime skill changes. Lead owns runner/tests/evidence; independent read-only reviewer grades actual output. No concurrent implementation writers or new dependencies/services.

Acceptance:
- [x] Preview and actual outgoing bodies omit both token-limit fields rather than sending null/0. Normal runner mode retains its cap. All other request fields match the active baseline exactly.
- [x] Diagnostic mode is bound to the preview hash and full execution selection; mismatched mode/configuration fails before network/output. One attempt per case; failure is preserved, never retried/repaired.
- [x] Offline regressions pass before five live calls to the current DeepSeek endpoint/model, active committed skill 1.2.0, reasoning none and frozen original/supplemental acceptance.
- [x] Retain all drafts/rejections/usage, deterministic replay, independent and lead semantic review. Never infer acceptance from valid JSON or omit failed cases.

Reproduce preview: `PYTHONPATH=services/api uv run --env-file .env python scripts/qualify_provider.py --omit-output-cap`. Execution adds `--execute HASH --output NEW_DIRECTORY`. Stop after one five-call round, without silently changing the model or prompt in an experiment intended to change only client cap omission. Retain prior failed rounds unchanged.


Actual execution: exactly five requests without either token-limit field; other body fields match capped skill1.2.0 baseline byte-value-for-value. All HTTP200/stop and backend-valid; two semantic passes, three failures on unchanged criteria. Responses used323–1114 output tokens, total16795 input +3502 output =20297 tokens, summed17.28s. No retries or extra calls;30 project hosted attempts now recorded. [Complete drafts/results and limits](../evaluations/no-client-cap-retest.md). Independent read-only reviewer agreed with lead grading and found no material code issue. Runtime cap configuration/.env/skill remain unchanged; diagnostic omission is explicit, not a normal application mode.

Next: investigate semantic behavior/decision consistency with these negative fixtures. Do not repeat calls or infer automatic acceptance from schema validity. User-approved cap-omission trial is consumed.

Final verification: `.venv/bin/python -m pytest -q` → 147 tests and 153 bootstrap subtests passed in 1.28s; Ruff lint passed; Ruff format check passed (25 files); mypy passed (10 application sources); `git diff --check` passed. All five saved drafts passed deterministic replay. No failing local check is hidden; live-semantic acceptance remains failed.
