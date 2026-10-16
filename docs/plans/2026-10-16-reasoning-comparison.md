# Controlled reasoning-enabled comparison and roadmap refresh

Status: experiment verified; semantic acceptance remains open. User requested continuing the plan and an account of remaining phases. The next qualified experiment follows the repeated-failure architecture review: change inference configuration, not add another checklist.

Source verification: current official DeepSeek Chat Completions reference documents reasoning_effort none/low/high/max, with low enabling thinking; thinking-mode guide documents low/high/max. Search results provided official content; direct opens timed out. References: https://api-docs.deepseek.com/api/create-chat-completion/ and https://api-docs.deepseek.com/guides/thinking_mode/. No SDK/install/alternate provider needed: existing compatible adapter accepts low.

Scope and live authorization: the user's continuing-plan instruction follows explicit autonomous testing and the recommendation for a controlled configuration comparison. Run one full five-case round using existing DeepSeek endpoint/model/key, active committed skill 1.2.0, JSON-object mode and the same frozen source/acceptance pack. Preserve the user's no-client-cap diagnostic selection. Change only reasoning_effort none → low in the Python process after local .env loading. No persistent .env/prompt change. At most five new calls, one per case, zero retries, existing 60s/256KiB transport bounds; provider defaults apply and cost is unknown. This is not blanket permission for additional rounds, a new provider or publication.

Acceptance:
- [x] Preview/body comparison proves only reasoning_effort differs from the previous no-client-cap request; all sources, prompt, schema and case criteria unchanged.
- [x] Exactly five calls or recorded failures, no retries/repair. Save artifacts and sanitized usage without provider reasoning content, credentials or envelopes. Count completion usage as provider-reported, not assumed final-answer-only tokens.
- [x] Replay backend validation and independently grade frozen criteria. Preserve every failure; do not force a passing qualification.
- [x] Refresh original roadmap to current M0–M6 evidence, with current gate and later foundations distinguished. No invented completion percentage or schedule.
- [x] Record actual verification, scope, remaining decisions and next task; commit locally.

Lead owns previews/test execution/evidence/roadmap. One read-only explorer audits milestone/source status; one read-only semantic reviewer grades actual output when available. No implementation agents or shared file edits necessary. The qualification observer records optional nonnegative reasoning-token counts and a presence boolean, never reasoning text; tests must cover missing/invalid counts and no text persistence. No dependency, application API, database or runtime skill changes.

Reproduce safely: invoke existing runner via `uv run --env-file .env python`, set SPECBRIDGE_LLM_REASONING_EFFORT=low within that process before prepare/execute, pass omit_output_cap=True, then bind exact prepared hash to a new output directory. Do not print or store reasoning_content. No additional paid trial after this round without a concrete next scope.


Actual result: five HTTP200/stop single-attempt replies, all backend-valid, two frozen semantic passes. Nonzero reasoning usage returned for all five; no reasoning text persisted. Totals16920 input +7827 completion =24747, including3962 reported reasoning tokens; summed45.92s; cost unknown. This consumed five calls (35 project total). Sources and criteria unchanged; only reasoning_effort changed on wire. [Full evidence and remaining gaps](../evaluations/reasoning-low-comparison.md). Independent reviewer agreed with lead grading and found no material observer issue; read-only milestone explorer supplied source-based M0–M6 status. No live configuration/prompt was promoted.

Next: examine behavior/unknown-consistency generation design against preserved failures before another concrete live experiment. Unfamiliar-human handoff and full M1 semantic acceptance remain open. Later phases and actual foundations are in roadmap-status-2026-10-16.md; no calendar date/percentage inferred.

Final local verification: `.venv/bin/python -m pytest -q` passed 153 tests and 176 bootstrap subtests in 1.39s; Ruff lint passed; Ruff format check passed (25 files); mypy passed (10 application sources); `git diff --check` passed. Six new observer cases failed before implementation and passed afterward. No remaining local test failure or generated application contract change. UI/exporter code did not change; no redundant browser/install/audit round was claimed.
