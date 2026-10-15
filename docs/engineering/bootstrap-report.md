# Phase Zero bootstrap report

Date: 2026-10-15. Status: **research/bootstrap delivered; Milestone 0 remains open pending design/planning review and product dependency validation. No application implemented.**

## Delivered

- Local repository on `codex/phase-zero`, with no remote or external publication.
- [Environment audit](environment-audit.md): actual tool versions, permissions, Docker limitation, native delegation and missing proofs.
- [Skill inventory](skill-inventory.md) and [pinned source inventory](sources.json): no new skill installation required for this phase.
- [Comparison of five product references and three engineering-skill sources](reference-research.md), based on source files rather than README summaries alone.
- Concise root `AGENTS.md`, [planning conventions](PLANS.md), [resumable roadmap](../plans/bootstrap-and-first-slice.md), [proposed ADR](../decisions/0001-local-modular-monolith.md) and [first-slice design](../architecture/first-slice.md).
- [Security requirements](../security/threat-model.md) and [acceptance/evaluation contract](../evaluations/acceptance.md).
- Dependency-free bootstrap tests and a minimal GitHub Actions workflow. This is a documentation/inventory integrity baseline, not the product testing suite.

Changed paths: root `.gitignore`, `.python-version`, `.node-version`, `README.md`, `AGENTS.md`; `.github/workflows/ci.yml`; `tests/test_bootstrap.py`; the files linked above under `docs/engineering/`, `docs/architecture/`, `docs/decisions/`, `docs/plans/`, `docs/security/` and `docs/evaluations/`.

## Skills and delegation

Used using-superpowers, brainstorming, dispatching-parallel-agents, skill-installer guidance, git-workflow-and-versioning, requesting-code-review and verification-before-completion. Writing-plans was inspected; the current roadmap is not an approved detailed implementation plan. No custom skill was created; skill-creator remains available for a justified runtime gap.

Three bounded native research agents completed independent read-only tasks:

| Agent | Result | Independent review outcome |
| --- | --- | --- |
| pm_research | Dean/Julian source, permissions, tests, license and skill compatibility review | Corrected license/NOTICE phrasing; no blocking source-record inaccuracies |
| app_research | Three PM applications, persistence/approval/security/testing review | Added full template/file/asset approval binding, inert preview requirements and explicit semantic-review limits; corrected intake/delegation wording |
| skill_source_review | Superpowers/Vercel/Anthropic source, scripts, permissions and discovery review | Confirmed version/license/discovery distinctions; identified no-op CI whitespace check, changed to committed-HEAD check |

Agents did not modify the workspace or execute repository programs. The lead integrated the findings and corrected a recorded source path after checking the fetched tree. No implementation branches were merged. Future implementation workers require worktree isolation.

## Verification executed

| Command/check | Actual result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` before source inventory | Expected red: missing `sources.json` caused two local-link failures and one inventory error |
| Report portability regression | Local-link check rejected a machine-absolute skill link in this report; replaced it with an explanatory code path, preserving portable repository links |
| Same command after inventory | 2 tests passed, 0 failures/errors on default Python 3.9.6 |
| Same unittest suite using installed managed Python 3.12.13 | 2 tests passed, 0 failures/errors |
| Source-path check against temporary downloaded snapshots | Recorded paths checked where snapshots were mapped; incorrect agent source subdirectory corrected |
| `git diff --cached --check` | Passed after staging all 18 bootstrap files; no whitespace errors |
| Native delegation | 3 research tasks and 3 follow-up reviews returned actual reports |
| Skill discovery | Local CLI enabled list + exposed session catalog + readable Superpowers entries; remote catalog lookup warned/fell back |
| Docker daemon check | Failed: expected socket absent. Containers not exercised |

The unittest suite checks local inline Markdown targets and inventory structure/required source coverage. It does not authenticate upstream commits, check remote URLs, parse CI YAML, measure output quality, or exercise an application. Source revisions were independently fetched during research, not inferred from passing tests.

CI uses official `actions/checkout` v4.3.1 at `34e114876b0b11c390a56381ad16ebd13914f8d5` and `actions/setup-python` v6 at `ece7cb06caefa5fff74198d8649806c4678c61a1`; refs were checked against official remotes. Manifests and selected authentication/setup sources were inspected, not the entire bundled JavaScript dependency trees. Contents permission is read-only; checkout credential persistence is disabled; no secrets, deployment or PR writes. Direct SHA pinning follows [GitHub's documented fallback](https://docs.github.com/en/actions/reference/security/secure-use); no workflow dependency lockfile was introduced. Hosted execution and broader supply-chain auditing are unverified. CI's committed-HEAD whitespace check is a bootstrap check, not a repository-wide linter.

## Decisions and issues

Propose FastAPI/Pydantic + SQLite, a thin React/TypeScript/Vite frontend, deterministic checkpointed stages, a configurable provider adapter and portable Starlight export. Next.js and LangGraph are deferred because the first slice has no SSR or complex orchestration requirement. None of these product dependencies has been installed or locked yet.

Do not import Dean's noncommercial/share-alike skills into a commercial runtime without suitable permission. Do not copy the two unlicensed app repositories. Julian's MIT original material is a possible reference with its NOTICE retained, but its market PRD does not cover the engineering handoff alone. Runtime skills remain unbundled; local development skills are not automatically distributable assets.

Observed app hazards were unrestricted `eval`, unconstrained model filenames, agent permission bypasses, unpinned MCP launch and prompt-only approvals. Proposed SpecBridge controls avoid those patterns, but no control is implemented or verified yet.

## Remaining gate and next action

Review the [first-slice design](../architecture/first-slice.md) and [ADR](../decisions/0001-local-modular-monolith.md), especially the Vite choice, single-local-operator boundary, configured provider behavior and immutable candidate-package approval. The requested outcome and milestone sequence are retained in the roadmap.

The installed Superpowers brainstorming skill at `~/.codex/plugins/cache/claude-plugins-official/superpowers/6.4.1/skills/brainstorming/SKILL.md` explicitly says: “Architectural: the human partner reviews and approves the written spec,” then requires written-plan review/execution selection before implementation. This is the reason application scaffolding and product dependency installation have not begun. The bootstrap files fulfill the separately requested Phase Zero engineering deliverables; they do not constitute design approval. This machine-local skill path is evidence for the current session, not a repository dependency.

After design approval, prepare the detailed implementation plan under the installed planning workflow, then resolve/lock dependencies and implement the first slice through test-first tasks. Record any user-approved process exception explicitly rather than inventing approval.

Not checked: application tests/builds, LLM/provider quality, real integrations, live browser flow, containers, hosted CI, branch protection and human developer handoff. Primary remaining risks are unverified runtime compatibility and proposed controls that still require implementation.
