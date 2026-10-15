# Acceptance and evaluation contract

Status: acceptance contract. The [first-slice results](first-slice-results.md) distinguish passing technical checks from live-model, human and future-milestone checks still outstanding.

Use human-reviewed reference fixtures and deterministic assertions. The fixture provider enables repeatable orchestration tests; its outputs are not evidence of LLM quality. Keep live provider evaluation opt-in with explicit destination, approved nonconfidential input, call/token limits and recorded model/skill revisions.

| Scenario | Independently checked result |
| --- | --- |
| Incomplete feature idea | Missing scope/owners/metrics shown as unknowns/questions, not factual completions |
| Contradictory stakeholder requests | In curated known-conflict cases, human review or advisory generation records both sources and unresolved conflict; no silent choice represented as consensus. This does not promise all contradictions are detected. |
| Missing acceptance criteria | Validation finding and review visibility; structural failures block export |
| Duplicate stories | Exact/normalized duplicates detected; unique stable story IDs |
| Unsupported assumptions | Labeled recommendations/assumptions; source traceability does not relabel user input as verified fact |
| Conflicting API specs | Competing source references + unresolved decision; no invented approved API |
| Failed provider/tool call | Persist failure, redact secret, permit explicit bounded retry without losing source |
| Interrupted workflow | Restart from persisted completed stage; no repeated completed side effects |
| Unauthorized publication | No approval, rejected revision, stale digest and source-requested approval all denied |
| Malicious embedded instructions | No shell, credential access, hidden publish, destination change or executable output |
| Unsafe skill references | Absolute/parent/symlink escape, malformed metadata and oversized files rejected |
| Documentation drift | Detect managed-file change and stop with conflict preview; preserve developer edits (Milestone 3) |
| Cross-project access | Context, source and revision lookups reject another project's IDs |
| Approval race/replay | Only bytes matching the approved revision/template/file/asset manifest can export; a template change after preview requires fresh approval |
| Deterministic prioritization | Same supplied inputs/weights → same ranking; absent metrics explicitly missing (Milestone 4) |

## Independent handoff exercise

An engineer unfamiliar with the feature receives only the portable package and its README. Record actual failures and ambiguities while the engineer:

1. Extracts or clones the generated project and runs `npm ci`.
2. Runs `npm run dev` and navigates the PRD, scope, acceptance criteria, edge cases and constraints.
3. Traces requirements to stories and sources, identifies missing information, and sees the approved revision/history manifest.
4. Creates a Git branch, edits a requirement and reviews the diff as a proposed change.
5. Runs `npm run build` and `npm run preview` successfully with SpecBridge stopped and no LLM credentials.

Automated evidence must cover clean extraction, lockfile install, production build, link checks, accessible browser navigation, and exact requirement/story mapping. An automated fresh-reader test cannot be described as an actual human handoff; record the human exercise separately when performed.

## Evaluation report fields

Record fixture/source hashes, skill/provider revisions, command, duration, exit status, assertion counts, failed cases, human-reviewed discrepancies, provider call/token totals where available, and limitations. Product checks cover completeness, AC quality, factual/source traceability, routing, schema validity, recovery, approval enforcement and docs build. No LLM-only self-grading.

Bootstrap checks local Markdown targets and reviewed source identifiers. CI now also defines pytest/integration/contract tests, Ruff, typing, frontend checks, Playwright, package audits and exported-doc builds. These commands passed locally; hosted CI has not run. Bootstrap checks do not replace product tests.
