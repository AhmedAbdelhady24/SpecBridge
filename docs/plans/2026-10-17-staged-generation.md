# Experimental source analysis before handoff drafting

Status: approved live round completed and independently reviewed; hypothesis did not pass semantic acceptance. No promotion or further paid scope. This follows the user's request to fix the remaining quality issues and the no-timeout baseline confirming that all five requests finish but three semantic cases still fail.

## Design and acceptance

Hypothesis: separating source analysis from drafting will make requested behavioral effects and unresolved decisions explicit before the model composes a full Artifact. This is different from another late checklist and does not imply that structure guarantees semantic completeness. Keep the original selected sources at both stages; a generated ledger is untrusted advice and never a new source, approval or permission.

Stage1 uses an original data-only experimental source-analysis skill and a strict bounded ledger of exact source excerpts, proposed observable outcomes and unresolved decisions. Validate real source references, exact excerpts in every citation, unique/valid behavior references and no unknown fields or authority state. Stage2 uses the existing active feature-handoff skill, its unchanged Artifact schema/policy, the original sources and the validated provisional ledger in untrusted user context. No model judge, automatic repair, migration, runtime agents or new dependency.

The candidate lives outside the application runtime registry. `skills/experiments/source-analysis/` is loaded explicitly only by `scripts/qualify_staged.py`; the production registry remains `skills/runtime/`. Provider/transport/secret guards and private configuration are reused. First-stage failure prevents the second call for that case. Never count structural ledger acceptance as semantic acceptance.

Ownership: isolated worker reuses native worktree7bd3 on codex/staged-evaluation from tested timeout commit0d0bf02. Owns new staged script, test file and experimental skill only. Root owns long-request code/evidence/docs, review/integration and live decisions; no overlapping writers. Read-only independent review must inspect the actual candidate before any external execution. Use system skill-creator and installed versioned Superpowers TDD/verification.

- [x] Offline/keyless preview includes exact analysis requests, deterministic drafting template, skill/source/schema/config fingerprints and maximum10/no-retry scope.
- [x] Fresh preview/hash binding fails changed targets/config/instructions before network/output creation; new output path required.
- [x] Tests observe failure before implementation; valid mocked two-stage flow preserves original sources and final validation; invalid ledger/authority/excerpts/refs stop drafting; credentials/reasoning never persist.
- [x] Review actual diff, all applicable tests/static checks and skill validation, integrate isolated commit and inventory as experimental only.
- [x] Prepare a concrete proposed full five-case, at-most-ten-call round under existing Pro/high/none/no-output-cap settings and frozen rubric. Human authorization must precede those additional paid calls. The prior five-call no-timeout allowance is consumed.

Proposed live stopping rule: one analysis and at most one drafting call per case, five unchanged synthetic cases, at most10 calls, zero retries/repairs. The second payload is the approved deterministic template populated only by that case's validated first-stage ledger and original sources; record actual payload/hash and ledger digest before sending. This data dependency is part of the previewed algorithm, not model authority to add destinations or tools. No real project input, model/provider change, runtime promotion or external publication. Cost unknown and generation wait unlimited as requested; connection and byte bounds retained.

Grade both extraction and drafting independently against frozen source/acceptance criteria, preserve failures and separate cause attribution. Even5/5 on this tuned pack is not unseen-case reliability, unfamiliar-human acceptance or approval to ship. If the round fails, record the remaining defects and stop this bounded experiment.

Reproduce through candidate's preview-first CLI with synthetic pack and private environment only for execution. Never copy its model-generated ledger into authoritative project facts. That proposed round is now consumed; use the final execution/disposition below to resume, without modifying the frozen evaluator.

## Verified preparation

Isolated commits739dfa4/b155f94 integrated as21482bc/4f13dab. Independent review passed37 staged cases; root combined check passed254 tests and207 subtests, Ruff lint/format29files and mypy10sources. Rejected parseable final JSON is preserved only after raw/decoded secret guards; malformed/refused/secret responses retain sanitized metadata/hash only. Envelope reasoning is excluded. No production schema, active skill or model was changed.

Concrete [offline preview](../evaluations/staged-preview-2026-10-17/preview.json): `ac18069cb607ce946d44613d09df2df95d58d3eb6ebcb11fcb43ee6ae5902e8f`. DeepSeek Pro/high, JSON-object mode, omitted output caps, timeoutnone, maximum10calls, zero retries. Preview generated without credentials/network. Async authorization was requested after concrete review and then explicitly granted, as recorded below.

## Paid authorization

User explicitly replied “approved for paid test” after the exact ten-call preview request. This authorizes only this round: maximum10calls, original five synthetic cases, same endpoint/Pro/high, no retries, output cap or generation deadline. Execution directory `docs/evaluations/staged-live-2026-10-17` must be new; approved digest remains ac18069cb607ce946d44613d09df2df95d58d3eb6ebcb11fcb43ee6ae5902e8f. No extra round, publication or runtime promotion.

## Actual execution and stopping disposition

Exactly10calls completed, allHTTP200 and structurally validated: five ledgers and five Artifacts, one attempt each, no timeout/retry/repair. Original sources, frozen criteria and exact preview unchanged; actual draft requests equal the approved template populated only with each validated ledger and original sources. Four calls exceeded60seconds; summed duration518.18s. Reported25,622input+47,335completion=72,957tokens; reasoning may be included in completion, no reasoning text retained. Costunknown. Project hosted attempts60.

Lead and independent final-Artifact review: booking and injection pass; notification/deletion/API fail, unchanged2/5. Separate ledger diagnostic: only notification complete; four have unknowns/contract gaps or inconsistency. Notification analysis captures the delivery effect and drafting loses it, so more intermediate prose does not guarantee coverage. Ledger grading is diagnostic, not a new pre-registered benchmark. See [full result](../evaluations/staged-generation.md) and preserved files.

Fresh37 staged checks passed before the round; final full suite/static results recorded in report. No application code, active runtime skill, provider default or schema changed in this execution. The experiment stopped at the announced limit; no promotion, automatic fix or extra model call. Next recommended work is an offline typed coverage-preservation design/regression using these failures, with original-source review still required. Do not start another paid iteration automatically.
