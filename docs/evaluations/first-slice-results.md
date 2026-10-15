# First-slice verification — 2026-10-16

The technical vertical slice works locally: feature evidence → runtime skill → structured DEMO draft → persisted requirements/stories → human review → exact package approval → standalone documentation website. **Milestone 1 product qualification remains pending**: no live model generation or unfamiliar-human engineering handoff was performed. The fixture produces generic illustrative recommendations, not source-specific AI analysis. No remote publication occurred.

## Implementation and boundaries

- FastAPI/Pydantic owns local authorization, project-scoped sources, deterministic workflow stages, checkpoints, immutable revisions, canonical requirement/story IDs and audit records in SQLite.
- Runtime skill metadata/body/references load progressively with confined paths, bounded safe YAML and explicit empty tool permissions. Intent search proposes a skill; the operator chooses it. The original `feature-handoff` 1.0.0 skill is independent of Codex development tooling.
- Provider selection is environment-configured. Fixture mode makes zero network/model calls. Compatible mode sends bounded structured-output requests to an explicit operator-selected destination, with no redirects, ambient proxy credentials, runtime tools or automatic retry. Its transport is mock-qualified only. A 60-second total HTTP deadline cancels slow headers/body reads before the 120-second workflow lease expires.
- React/TypeScript provides local sign-in, project/run recovery, inert source evidence and artifact editing, findings, human review/rejection, package preview/approval and download. Credentials stay in memory.
- The fixed Astro Starlight template exports plain Markdown, source mappings, revision metadata and a hashed manifest. Only the exact stored bytes approved by the operator can download. Edits, rejection, changed template and corrupted ZIPs invalidate authorization. Export never regenerates into an authored repository.

The accepted modular-monolith ADR avoids LangGraph, separate runtime agents, vector databases, MCP services and microservices because this slice needs deterministic transitions, not those dependencies. Vite replaces the proposed Next.js layer: backend-owned state and a local static client need no second server framework. SQLite is local-only; a PostgreSQL migration has not been implemented.

## Changed paths

| Paths | Delivered responsibility |
| --- | --- |
| `services/api/specbridge/`, `services/api/tests/` | Domain models, persistence, authorization, runtime skills/providers, workflow, publication and regression tests |
| `apps/web/`, `packages/contracts/` | Accessible React client and generated API contract/types |
| `skills/runtime/feature-handoff/` | Original runtime instructions, reference contract and provenance/licensing status |
| `packages/docs-template/` | Locked independently runnable static documentation source |
| `tests/e2e/`, `playwright.config.ts`, `scripts/` | Browser acceptance, schema export, independent clean-package verifier |
| `pyproject.toml`, `uv.lock`, npm manifests/locks, version files, `.env.example` | Reproducible toolchain and explicit provider configuration |
| `.github/workflows/ci.yml`, `AGENTS.md`, `docs/`, `README.md` | Read-only CI definition, maintained instructions, research, design and verification evidence |

## Actual verification

Final code checks ran after all three final review fixes. Documentation link counts may change as maintained documentation grows.

| Command/check | Actual result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | 98 tests passed, plus 65 bootstrap link/source subtests |
| `.venv/bin/ruff check services/api scripts` | Passed |
| `.venv/bin/ruff format --check services/api scripts` | 23 files already formatted |
| `.venv/bin/mypy services/api/specbridge` | 10 source files passed strict checking |
| `.venv/bin/python scripts/export_openapi.py` + `npm --prefix apps/web run generate:types` | Regenerated contract/types without drift |
| Web `typecheck`, `lint`, `test`, `build` | Passed; 2 client tests; Vite production build succeeded |
| `PLAYWRIGHT_BROWSERS_PATH=.cache/playwright npm exec playwright test` | 9/9 passed in 4.7 seconds via the documented `npm run test:e2e` runner |
| `.venv/bin/python scripts/verify_handoff.py --output /tmp/specbridge-handoff-20261016-final` | Fresh install/build, dev and preview HTTP/browser checks passed in 15.39 seconds |
| Python dependency audit | 57 installed distributions, zero known advisories |
| Root/web npm audits | Zero known advisories |
| Documentation npm audit | Ten moderate dependency entries for one underlying advisory; zero high/critical |
| `git diff --check`, local documentation integrity | Passed before final commit |

A post-build static-serving smoke check also passed: the API served the UI and both assets while project data still required authorization.

The independent verifier closes the application/session before installing the ZIP in a fresh directory. Chromium checks seven routes, stable requirement/story links, literal attack strings, no injected executable DOM and zero remote asset requests in both server modes. It uses deliberately malicious title/body strings, so this output is a security fixture, not a real approved feature specification. Exact candidate/template/file hashes, duration and zero live model calls are committed in [the verification record](first-slice-verification.json). Generated logs and screenshots remain in the local output directory. Repeat with a **new** output directory to preserve earlier evidence.

Browser cases cover exact preview/approval, edits invalidating old approval, reload recovery with original evidence, inert HTML/images, keyboard/narrow viewport use, invalid authorization, acknowledged failure retry, human rejection, foreign origin/host rejection and project scoping. Backend cases also cover malformed/deep skill/output parsing, traversal/symlinks, source byte limits, strict schemas, source citations, stable IDs, concurrent storage writers, rollback, checkpoint restart, provenance changes, template approval races, stale/corrupted packages and slow provider cancellation. These are deterministic structural/security checks, not semantic model evaluations or a comprehensive accessibility audit.

## Failures found and corrected

- Valid 32KiB source input was rejected by a shared 16k character constraint. HTTP and persistence byte-boundary tests now cover ASCII and multibyte inputs.
- Skill discovery eagerly loaded references. Metadata, instructions and reference loading are now separate and bounded. Strict provider schemas require nested fields while retaining backend defaults; deep parser errors are sanitized.
- Generation provenance could drift after a model configuration change. The generation checkpoint now retains the original model/skill metadata.
- Template authorization sampled its digest before opening the transaction. A controlled race regression now verifies sampling inside the authorization transaction. Artifact citation limits now match exportable context bounds.
- Initial real browser checks failed six cases because implicit labels included populated textarea/select values. Explicit labels fixed the actual accessibility relationship; selectors were not weakened. Source text recovery after reload and rejected-revision package preparation were corrected too.
- The clean website check found two H1 headings and timed out on Astro 7's daemonizing CLI behavior. The redundant heading was removed; the verifier uses the supported `--ignore-lock` flag, HTTP readiness and process-group cleanup. Earlier failed output directories were retained, and the owned initial daemon was stopped.
- Final independent review found three Important defects. Each reproduced with a failing test before the fix: edits lost findings; revision/audit insertion could commit before the run-pointer update; inactivity timeouts allowed indefinitely slow HTTP responses. Edits now recompute findings, save all related state atomically, and the provider uses a cancellable total deadline. All four new regression cases and the combined suite pass. No Critical findings were reported.

## Skills, delegation and review

Used installed Superpowers design/planning, isolated worktrees, TDD, systematic debugging, parallel/subagent execution, review and verification methods; system skill-creator for the original runtime skill; installed frontend/browser and documentation guidance. [Skill inventory](../engineering/skill-inventory.md) records source revisions, licensing, permissions and discoverability. No duplicate collection or third-party installation hook was needed.

Independent research agents `pm_research` and `app_research` reviewed actual source, licensing and reuse options; source records and comparisons are maintained in the engineering research documents. `runtime_skills_provider` delivered the skill registry/adapter in an isolated branch and fixed review findings. `docs_template` delivered and independently built the fixed site template. `frontend_handoff` delivered the UI and accessibility fixes, then refreshed handoff docs. `browser_acceptance` supplied executable browser cases. `backend_contract_review` reviewed boundaries/contracts and regression gaps. A separate `final_security_review` inspected the combined implementation and produced the three findings above. The lead reviewed/integrated changes, fixed shared backend issues and ran combined checks. Branches/worktrees and failed-run evidence were preserved. Agent reports alone were never treated as feature verification.

Ruling: retain compatible locked Starlight dependencies with the moderate [GHSA-rj75-hqrm-r3gf](https://github.com/advisories/GHSA-rj75-hqrm-r3gf) exposed, rather than force an incompatible dependency override. The affected selector parser is build-time tooling and CSS/configuration are fixed trusted source. If that boundary changes or the assessment is wrong, attacker-controlled selectors can exhaust build CPU. Reassess when a compatible patch exists. There are no deferred Minor findings from final review.

## Remaining acceptance and next task

The next task is bounded live-provider qualification using an explicitly chosen endpoint/model, approved nonconfidential feature fixtures and call/cost limits, followed by an unfamiliar engineer's handoff exercise. Compare outputs against human-reviewed references, including curated contradictory stakeholder/API cases, for completeness, contradiction handling, acceptance-criteria quality and unsupported claims. Record failures rather than treating schema-valid output as correct.

No hosted CI run, container/daemon deployment, real Git/Jira/Confluence/Drive/Slack writes, Git regeneration/conflict workflow, production authentication, later product workflows or later milestones were verified. No remote repository or branch protection was configured. Local SQLite is not encrypted and the single local token is not multi-user authorization. Remote cancellation cannot guarantee provider-side computation/billing stops. Local timings are fixture observations, not production latency/cost benchmarks.
