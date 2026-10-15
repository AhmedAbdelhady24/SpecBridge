# ADR 0001: Local modular monolith and independent documentation exports

Status: **accepted by the user on 2026-10-15** following review of this ADR and the written first-slice design. Implementation remains pending plan review and validation.

## Context

The workspace is empty. The first useful result is a reviewed feature handoff that a developer can run without SpecBridge or model credentials. Source reviews found no reference app already supplying revision-bound approval, durable product knowledge and safe standalone docs publication together. See the [comparison](../engineering/reference-research.md).

## Options

| Approach | Benefit | Material shortfall |
| --- | --- | --- |
| Skills-native execution in Codex | Smallest immediate authoring workflow | Depends on the assistant; no independent product UI, approval authority or durable application records |
| Extend a reference PM app | Reuses a chat/intake shell | Requires replacing provider coupling, session persistence, permissions and publication; two candidates lack a distribution license |
| Small dedicated modular monolith | Explicit domain and security boundaries; standalone application | Requires a small API, UI and persistence layer |

Select the third option, with reusable PM methods as instructions rather than an autonomous software team.

## Decision

- Python 3.12, FastAPI, Pydantic v2; one backend owns all domain changes. Lock compatible versions after approval.
- React and TypeScript with Vite for a local review UI. Next.js was evaluated; no SSR or server-component requirement currently justifies its second application-server responsibility. This is an approved deviation from the suggested stack.
- SQLite with explicit transactions and a schema-version table; keep persistence behind repository functions. PostgreSQL is a future migration, not a second database to support now.
- A deterministic workflow with persisted stages and immutable artifact revisions. No LangGraph in the first slice; revisit when branching/recovery complexity exceeds a small explicit state machine. Durable execution itself does not require an agent framework.
- Configurable provider boundary with a deterministic fixture provider for tests and an explicitly configured OpenAI-compatible HTTP provider. No Codex runtime dependency and no provider SDK orchestration framework. Provider use requires an explicit configured destination; no fallback to an unapproved cloud endpoint.
- Agent Skills-compatible frontmatter parsed with safe YAML and strict metadata/path checks. No executable runtime tools by default. Built-in runtime skill authorship/licensing must be resolved before bundling; noncommercial and unlicensed references are excluded.
- Astro Starlight for portable static documentation source, including a lockfile. Build a committed, pinned template; never generate executable config or package scripts from model output.
- Local loopback only initially, with request-origin/host protection and local session authorization for mutations. External access requires real authentication and project authorization.

## First-slice scope

Feature intake, skill selection, schema-validated PRD and stories, deterministic findings, persisted human review of an exact revision, portable ZIP export, and independently built/navigable local docs. One thin UI is sufficient. Mock integrations have no external write capability.

Skip autonomous agent teams, vector storage, MCP servers, hosting, multi-user collaboration and real Jira/GitHub writes until their milestone needs them. Meeting, status and prioritization are later workflow modules, not forgotten requirements.

## Consequences and verification

Separate API and browser dev processes remain necessary. A Vite proxy can provide a single browser origin; production assets should be served by the API. Starlight is an export/build dependency, not a live backend service. No application build chain exists yet.

Approval binds the artifact revision and a preview digest covering template version/digest, generated paths/content hashes and asset hashes. Export serves the immutable candidate bytes reviewed; edits or template changes require new approval. Preview and export use fixed templates, inert data and no remote assets, with fresh output directories. Later repository regeneration must compare manifests/hashes and produce a conflict preview before writing.

Acceptance is defined in the [first-slice design](../architecture/first-slice.md) and [evaluation plan](../evaluations/acceptance.md). The user's explicit approval settles this decision; passing product checks are still required before any completion claim.
