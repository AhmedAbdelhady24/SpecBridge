# Long model requests and semantic follow-through

Status: timeout/lease repair and five-call latency retest verified; semantic follow-through remains open. User explicitly requested fixing the outstanding issues and avoiding request timeout because higher effort may take longer. This authorizes a bounded repair/retest; do not treat lack of final output as a semantic failure or promise that removing timeout fixes semantic content.

## Evidence and design

providers.py hard-codes a 60-second whole-request deadline; workflow.py leases generation for120 seconds without renewal. The Pro notification/injection responses exceeded60 seconds; three completed drafts retained decision gaps/contradictions. Removing only HTTP timeout could expire a healthy workflow lease and permit a duplicate billable attempt. Existing source/approval policy is sound and must remain unchanged.

Use an explicit environment setting `SPECBRIDGE_LLM_TIMEOUT_SECONDS=none` for no generation total/read deadline, with validated finite positive seconds supported and60 seconds retained when unset. Keep finite connection establishment, response byte bounds, no automatic retry, source policy and private key handling. Apply none to the user's local configuration without exposing/changing the key. Record the execution timeout in evaluation previews so approval fingerprints bind transport settings as well as exact request bodies.

Renew an executing workflow's owned lease while provider generation runs. Use compare-and-set renewal, stop/join the heartbeat on completion/failure, reject results if renewal failed or ownership changed, retain explicit retry acknowledgement and interrupted-process recovery. No database migration, public contract, new dependency or job framework. A stopped process stops renewal; a healthy long request remains single-owned. Unlimited waiting can require an operator to stop a genuinely stalled process; do not misrepresent it as guaranteed eventual provider completion.

Ownership: isolated worker owns providers.py and its test file only; lead owns workflow.py/tests, evaluation runner/tests, .env.example/README, plans/evidence and integration. Read-only review inspects lease/failure guarantees. Workers must not revert concurrent changes. Review/integrate provider commit before running combined verification. Use installed versioned Superpowers debugging/TDD/worktree/verification methods.

## Acceptance

- [x] Failing tests first: unlimited delayed headers/body complete; configured deadlines still cancel; invalid timeout values rejected; byte limits/secrets/retry behavior preserved.
- [x] Long-running workflow renews lease, rejects concurrent advance after the original lease duration, stops heartbeat afterward, refuses stale ownership/heartbeat failure, and interrupted work still needs retry acknowledgement.
- [x] Evaluation preview binds timeout; mismatch aborts before a request, uncapped output remains uncapped, no private configuration printed.
- [x] Backend/static/contract/browser checks pass and source/diff review complete. Documentation and board describe actual limits.
- [x] Run one full five-case Pro/skill1.2/high round without client token cap or generation timeout; zero retries, same sources/evaluator. This is a latency-control retest, not automatic semantic qualification. Preserve every final result and usage; do not persist reasoning text.
- [ ] Independently grade semantic results; address any remaining gaps through a separately identified generation strategy, not fabricated facts, repaired benchmark outputs or weaker evaluation. No configuration/prompt promotion without evidence.

Initial live scope: at most five new calls at the already approved DeepSeek endpoint/model using the existing private key, synthetic pack only, no retries, no client output cap and no generation deadline as requested. Cost unknown; connection and response-size bounds remain. No new provider/model or external publication. Do not silently expand into repeated rounds. If content still fails, prepare an evaluation-only two-stage source-analysis/drafting strategy with original evidence at both stages; its additional call scope must be explicit before execution.

Reproduce using existing qualification runner with process-local Pro/high and new timeout none after loading .env privately. Use a new output directory and exact preview digest. Run repository commands from AGENTS.md; retain failed worktrees/tests/evidence. Next checkpoint must separate timeout functionality, completed draft validation, semantic grading and unfamiliar-human acceptance.

## Verified checkpoint

Integrated provider change `ce0aedf` and lease/preview change `0d0bf02` after independent review. Final combined backend check after the separate evaluation harness integration: 254 tests and 207 bootstrap subtests passed in1.75s; Ruff lint/format29 files and mypy10 sources passed. Web type/lint/2unit/build,14browser cases, unchanged OpenAPI/types, standalone handoff verifier and Python plus all three npm vulnerability audits passed during this repair. No known vulnerabilities reported. The normal `uv run` wrapper hit a sandbox cache permission error; equivalent commands used the already locked `.venv` directly.

Actual five-call no-timeout round completed all five, including73.39s and73.15s responses. Backend5/5, semantic2/5; all final artifacts and sanitized usage retained in [the evaluation record](../evaluations/long-generation.md). Hosted attempts50. Additional staged paid scope is separately previewed and awaits authorization; no runtime prompt/model promotion or M1 completion.
