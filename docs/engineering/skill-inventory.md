# Skill inventory and adoption decisions

Inspected 2026-10-15. The scope is skills relevant to this project; this is not an audit of every globally installed plugin. Source identifiers are machine-readable in [sources.json](sources.json).

## Development skills already available

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

No runtime skills have been bundled. Global Codex skills and their tools must never be exposed automatically through the application registry. An original minimal runtime handoff skill may be justified if available skills cannot meet engineering-output and redistribution requirements; create it only after that gap is explicitly established, using system skill-creator and Agent Skills specification validation.

Required runtime metadata includes name/description, compatible version/provenance, license and explicit permission allowlist. Safe YAML parsing and supporting reference confinement are application requirements, not guaranteed by SKILL.md itself. [Agent Skills specification](https://agentskills.io/specification) defines the interoperable format; host-specific tool declarations are not a sandbox.

## Discoverability and permissions

Installed Superpowers is both listed enabled by `codex plugin list --json` and present in this session's skill catalog, with readable entrypoints. That establishes discoverability, not full behavior validation. Remote plugin catalog lookup failed independently of local enumeration. Deferred skills are deliberately not discoverable because none were installed. After any future project-scope install, verify files/frontmatter/references and refresh the Codex session before claiming native discovery.

Minimum Phase Zero installation decision: **install nothing**. Existing development capabilities are sufficient. Future missing skills are staged at their actual point of use; runtime redistribution/licensing needs a separate review.
