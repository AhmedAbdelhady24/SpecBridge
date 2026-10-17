# Skill inventory and adoption decisions

Baseline inspected 2026-10-15; implementation update 2026-10-16 below. Historical inventory observations are preserved. The scope is skills relevant to this project; this is not an audit of every globally installed plugin. Source identifiers are machine-readable in [sources.json](sources.json).

## Development skills already available at bootstrap

Canonical Superpowers source: `obra/superpowers`, installed 6.4.1 at revision `5bf4e78011075bcfc0dc295f0724994cd123ee71`, under `~/.codex/plugins/cache/claude-plugins-official/superpowers/6.4.1/skills/`. This is a development dependency of the assistant, not an application dependency. MIT. The native manifest declares Interactive/Read/Write and `hooks: {}`. Skills do not independently grant permissions; the host and user authorization govern tool use.

| Skill | Purpose | Permissions when applicable | Verification status |
| --- | --- | --- | --- |
| using-superpowers | Progressive skill selection | Read local guidance | Read; exposed in session catalog |
| brainstorming | Clarify/design before implementation | Read/write design docs; human design review | Read; applied to proposed design; product implementation gate pending |
| writing-plans | Self-contained implementation tasks | Read/write plans | Inspected; detailed plan follows design approval |
| test-driven-development | Red/green behavior checks | Project test commands and file writes | Entry exists/catalog; product TDD not exercised yet |
| systematic-debugging | Reproduce/isolate failures | Read source/logs; scoped tests | Entry exists/catalog; no application failure investigated |
| dispatching-parallel-agents | Independent bounded research | Native spawn/message tools | Read; three read-only research tasks completed |
| subagent-driven-development | Isolated task implementation and review | Worktrees, edits, tests, agent tools | Source reviewed; not exercised for implementation |
| using-git-worktrees | Isolate changes | Local Git/filesystem writes | Entry exists/catalog; not needed for read-only researchers |
| requesting-code-review | Independent review before integration | Read diffs, scoped verification and review agents | Entry exists/catalog; bootstrap review recorded separately |
| receiving-code-review | Verify feedback before edits | Source/tests and scoped edits | Entry exists/catalog; no product feedback cycle yet |
| verification-before-completion | Evidence before completion claims | Actual verification commands | Read; applies to bootstrap report |
| finishing-a-development-branch | Finish verified branch deliberately | Git; external writes separately authorized | Entry exists/catalog; branch not published |

Other existing capabilities: system `skill-installer` (installer guidance read; no installation), system `skill-creator` (available; no custom skill created), local `plain-english-prd` and `inputs-to-ticket` (available development authoring guidance; redistribution license not established). No version/provenance is inferred for unversioned local skills.

There are 14 overlapping unprefixed Superpowers skill copies under `~/.agents/skills`; 6 match and 8 differ from plugin copies. Preserve them pending separate review. Prefer the versioned plugin for this repository; do not add another installation or modify global configuration.

## Requested external sources

| Skill(s) | Source / reviewed revision | License / permissions / dependencies | Decision and verification |
| --- | --- | --- | --- |
| prd-development | deanpeters/Product-Manager-Skills / `1b5a524ebb95e9497fa3f25002d8b8ec528d4444` | CC BY-NC-SA 4.0; instructions reference many companion skills | Source/template reviewed; excluded from product imports without suitable permission |
| user-story | Same Dean revision | Same license; optional stdlib argparse/sys printer, no network/file writes in that script | SKILL/script reviewed statically; no install/execution |
| epic-breakdown-advisor | Same Dean revision | Same license; prose, workshop-facilitation reference | Reviewed; no install; engineering vertical-slice planning already available |
| context-engineering-advisor | Same Dean revision | Same license; prose, not an implementation of retrieval/memory | Reviewed; no install |
| agent-orchestration-advisor | Same Dean revision | Same license; prose, not a runtime orchestrator | Reviewed; no install; unsupported evaluation claims not adopted |
| pm-prd (alternative) | julianoczkowski/product-manager / `b408a093a5d0171937ce5f9035c2e3b073689e97` | MIT original content + NOTICE framework/trademark caveat; Read/Write/Edit/Bash/Glob/Grep requested, shared references | Reviewed, optional/deferred; does not cover detailed engineering AC alone |
| react-best-practices | vercel-labs/agent-skills / `063bee94c3f4df8453406c830b0a7df0f2860278` | README/SKILL state MIT; no standalone license file found; Markdown/metadata, no selected-folder scripts | Deferred until frontend; rule bodies not fully audited |
| web-design-guidelines | Same Vercel revision | README states MIT; skill has no license field; fetches mutable remote guideline document | Deferred; review/pin secondary document before adoption |
| webapp-testing | anthropics/skills / `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Apache 2.0 per-skill license; Python Playwright/browser for examples; helper accepts shell commands | SKILL/helper reviewed, not executed; defer to browser phase or reuse existing Playwright tools |
| mcp-builder | Same Anthropic revision | Apache 2.0; evaluator needs anthropic/mcp libraries, cloud credentials and tool access | SKILL/evaluator/connections reviewed; defer until custom MCP need; evaluator not authorized |

Keep all licenses/notices and modification notices required by their terms if later vendoring. Do not run `npx skills add` or a third-party install hook merely to copy reviewed Markdown. No new execution permission or untrusted installation code has been requested or run.

## Runtime PM skills are separate

The bootstrap initially bundled no runtime skill. Implementation now includes original `skills/runtime/feature-handoff/SKILL.md` version 1.2.0, a progressively loaded `references/output-contract.md`, and `provenance.json` with content hashes, version/schema metadata, original authorship and licensing observations. This guidance fits the strict Artifact contract without importing reviewed noncommercial or unlicensed material. No separate distribution license is asserted for original project content.

The application loads only its project runtime registry, never global Codex development skills or their tools. The runtime permission allowlist is empty; skills are prompt data and cannot execute shell commands or access arbitrary files. Tests exercise strict metadata/YAML validation, provenance hashes, confined reference loading and traversal/symlink rejection. This is local registry/fixture and mocked-provider evidence, not live-provider output quality.

Required runtime metadata includes name/description, compatible version/provenance, license and explicit permission allowlist. Safe YAML parsing and supporting reference confinement are application requirements, not guaranteed by SKILL.md itself. [Agent Skills specification](https://agentskills.io/specification) defines the interoperable format; host-specific tool declarations are not a sandbox.

## Discoverability and permissions

Installed Superpowers is both listed enabled by `codex plugin list --json` and present in this session's skill catalog, with readable entrypoints. That establishes discoverability, not full behavior validation. Remote plugin catalog lookup failed independently of local enumeration. Deferred skills are deliberately not discoverable because none were installed. After any future project-scope install, verify files/frontmatter/references and refresh the Codex session before claiming native discovery.

Minimum Phase Zero installation decision: **install nothing**. That historical decision was retained; no duplicate collection or optional remote skill was installed.

## Implementation adoption update — 2026-10-16

The installed versioned Superpowers guidance was applied progressively to execution, tests, debugging, review and verification. UI/template workers used isolated Git worktrees with owned paths; the lead integrated changes. Actual test/command evidence belongs in the [first-slice results](../evaluations/first-slice-results.md), not the historical verification-status table above.

Frontend work reused installed frontend-design and frontend-ui-engineering guidance and standard React controls. The optional Vercel skills and mutable remote design guidelines remain deferred. Browser checks use the project-owned Playwright suite; the reviewed third-party webapp-testing helper was not imported. System skill-creator guidance informed the original runtime skill; its application validation is in `services/api/tests/test_skills.py`. Development authoring skills are not shipped inside exported documentation.

The 1.1.0 update injects the active output contract during generation with snapshot-bound reference hashes, precise evidence labels and complete requirement links. Agent Skills quick validation, registry/provenance tests and outgoing-request tests passed. [Rule-change evidence and limits](../evaluations/handoff-rules-results.md). No additional runtime permission or third-party content was introduced.

The 1.2.0 update makes all six Story fields explicit, reinforces case/punctuation-preserving excerpts and adds a complete conditional-conflict example. Permissions remain empty and provenance hashes were refreshed. Structural/example and old-failure regressions pass; two targeted live retests passed; broader quality remains open. See [the correction and limits](../evaluations/conflict-handoff-fix.md).

Autonomous qualification tested experimental 1.3.0/1.3.1 guidance but neither passed the full frozen pack. Both are archived as evaluation evidence and excluded from the runtime registry. The active skill/provenance is restored to committed 1.2.0, still unqualified against the stronger semantic pack. [Results and disposition](../evaluations/autopilot-qualification.md).

## Evaluation-only source analysis — 2026-10-17

Original `skills/experiments/source-analysis/SKILL.md` version0.1.0 (schema1) is explicitly discoverable by the separate staged qualification harness, never the production runtime registry. Its provenance pins SKILL.md SHA256 `4e7908a594583d7a2b96e4dfdb485a0fc02c6585754faa75d0e16e3fb50f83a5`; original authorship, no copied third-party text and no separate distribution license asserted. Permission allowlist is empty, with no executable script, dependency, shell or filesystem grant. System skill-creator guided this bounded ledger workflow because the existing Artifact authoring skill does not supply a separate analysis contract. Agent Skills quick validation, registry discovery/provenance, mock stage-boundary and secret-guard tests pass. Integrated revisions21482bc/4f13dab. The approved ten-call live round completed but final handoffs remained2/5 semantically accepted; the skill is not promoted and runtime adoption remains unverified; [execution scope and evidence](../plans/2026-10-17-staged-generation.md).

## Typed handoff-plan experiment — 2026-10-17

Original `skills/experiments/handoff-plan/SKILL.md` version0.1.0 uses empty tool permissions and hashed provenance, no third-party text or new dependency. System skill-creator validation and explicit experimental registry discovery pass. One provisional typed plan is assembled deterministically into an Artifact, preserving recorded outcomes/questions and conditional alternatives.24component/runner checks pass, including the actual notification analysis; this is not live semantic qualification. No separate original-content redistribution license is asserted. [Scope, integrated implementation and pending paid preview](../plans/2026-10-17-compiled-handoff.md). Production runtime skill remains1.2.0.
