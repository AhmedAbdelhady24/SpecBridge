# Conflict handoff correction and targeted retest

Status: verified targeted correction/retest; broader qualification remains open; user approved “okay lets do that” after the recommendation to strengthen story structure/conditional conflict criteria and retest the two failed cases.

Evidence: previous five-case DeepSeek run produced two invalid conflict drafts, both omitting stories[].id. API draft also changed case/punctuation in exact-excerpt labels. Deletion draft presented alternatives with unconditional criteria and a reversed risk sentence. Prior original outputs remain immutable evidence.

Scope: existing runtime skill/reference/provenance, targeted opt-in runner case selection, offline regression fixtures/tests, evaluation records and skill inventory. No new provider, dependency, persistence migration, public schema, silent repair or loosened validator. Sequential lead ownership; no independent implementation module justifies worktree/delegation overhead here.

Design: retain the supplied JSON Schema and deterministic validation; make all six Story fields explicit (including inherited fields), exact-copy case/punctuation, and decision-conditional criteria concrete using an unrelated non-CSV example. Preserve both supplied alternatives as proposed requirements with source attribution; never claim consensus. Examples are guidance, not semantic validation. Bump runtime skill to 1.2.0 and rehash provenance. Add --case selection to the runner so two-case authorization never reruns the other three cases; exact preview verification includes selection.

Acceptance:
- [x] Tests first: subset selection bounds calls and detects changed selection; old missing-ID drafts still rejected, locally corrected copies exercise excerpt checks without rewriting raw evidence; active request includes a structurally valid complete conflict example and story checklist.
- [x] Implement prompt change and selection only; validate skill/provenance, full backend tests, lint/format/type checks, diff review.
- [x] Preview and run exactly contradictory-deletion and conflicting-api once each using existing DeepSeek endpoint/model/JSON mode, reasoning none, 3072 cap each (6144 maximum output tokens total; inputs additional), no retries. Dollars unknown. This user instruction authorizes those two tests, not automatic paid repetitions.
- [x] Review output against original prewritten criteria, retain failures, source/schema/skill/request hashes and actual usage; no artifact approval/publication. Document broader qualification limits and next task.

Reproduce: `PYTHONPATH=services/api uv run --env-file .env python scripts/qualify_provider.py --case contradictory-deletion --case conflicting-api` previews exact requests. Live execution additionally needs `--execute HASH --output NEW_PATH` and explicit operator authorization. Stop after two calls regardless of outcomes. Existing full-pack and prior case evidence stay readable; prompt changes invalidate stale previews. No .env change.


Actual outcome: both live requests validated; original narrow criteria satisfied on lead and independent review. Deletion 715 output tokens / 4.44 s; API 1069 / 6.64 s. Total 8514 tokens, no retries/truncation. No additional live calls. Complete outputs and remaining cursor/retention ambiguities are in [the evaluation](../evaluations/conflict-handoff-fix.md). The independent read-only reviewer reported no material code/prompt issue and 98 targeted tests passed, then reviewed actual outputs against original criteria. Other three cases have not been rerun under skill 1.2.0; no broad qualification or human approval claim.

Next resumable action: obtain the missing request/retention decisions and human semantic review, then carry one reviewed real-model draft through the existing review → exact ZIP approval → independent website build path. Any further live run needs its own concrete scope; no automatic repeat after these two calls.

Final verification: `.venv/bin/python -m pytest -q` → 144 passed, 124 bootstrap subtests passed (1.32 s); Ruff lint passed; Ruff formatting passed (25 files); mypy passed (10 application files); system skill-creator quick_validate returned “Skill is valid!”; `git diff --check` passed. A first lint run found two test-format issues (regex alias and import order), fixed before live execution and final checks. No failing check remains. Independent reviewer did no writes or live calls. Original evaluation files remain unchanged.
