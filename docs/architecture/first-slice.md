# First vertical slice: reviewable feature handoff

Status: **approved on 2026-10-15; technical first slice implemented and verified on 2026-10-16**. See [actual results and qualification limits](../evaluations/first-slice-results.md). Design approval does not authorize external publication.

## Intent and scope

The user requested an independent, configurable-provider product that converts ideas into engineering-ready, validated artifacts. Success means an unfamiliar engineer can understand scope, acceptance criteria, dependencies and missing information, then run the generated docs without an LLM.

The first slice handles text intake for one feature within a project, a PRD with linked user stories, human review, and a complete Starlight source ZIP. A thin browser interface covers intake, findings, revision editing, approval and download. It does not attempt the final dashboard or external publication.

Approved initial boundaries: single local operator; manual text sources first; no confidential data leaves the machine until the operator configures a provider and explicitly generates using that destination. The fixture provider is labeled test/demo output, never presented as real AI validation.

## Modules and contracts

| Module / planned location | Owns | Must not own |
| --- | --- | --- |
| API / `services/api/` | Request validation, workflow transitions, project-scoped access | Model-directed shell commands |
| Skills / API registry module | Metadata discovery/search, progressive references, provenance | Development tools, arbitrary imported scripts |
| Workflow / API service module | Stage results, checkpoints, bounded retries, validation findings | Silent approval or publishing |
| Storage / API repository module | SQLite transactions, projects, sources, immutable revisions, audit | Provider credentials or logs of full prompts |
| Provider / API adapter module | Bounded structured generation to configured endpoint | Choosing credentials/destinations from retrieved content |
| Publisher / API export module | Fixed template + approved snapshot → bytes and manifest | Executing generated MDX, installing packages, overwriting existing repos |
| Web / `apps/web/` | Accessible forms, preview, review and download | Authoritative permission decisions |
| Export template / `packages/docs-template/` | Pinned Astro/Starlight source and lockfile | Secrets, telemetry, API dependency |

Pydantic/OpenAPI is the contract source. Generate/check a TypeScript schema artifact when the API exists; do not hand-maintain parallel incompatible schemas. No separate contracts service is necessary.

## State and provenance

Persist projects, sources, workflow runs, stage checkpoints, artifact revisions, review findings, approvals and export records. Every record is project-scoped. Sources distinguish user information from independently verified material. Each generated claim can cite source IDs; recommendations, assumptions and unknowns are explicit. Source presence is not factual verification.

Stable requirement/story IDs are persisted, never renumbered by the model on edits. A revision is immutable with a monotonic project-local revision number and content digest. Revisions retain source and skill digests plus provider/model identifiers. Credentials stay in environment/configuration outside artifact data.

Required PRD structure: purpose, scope/non-goals, requirements with stable IDs, linked user stories and testable acceptance criteria, edge cases, dependencies, risks, proposed success metrics without fabricated baselines, and open questions. Missing owners/deadlines remain null/unknown. Unsupported API definitions remain open questions, never “approved contracts”.

## Workflow and failure behavior

| Stage | Input → output | Error/recovery |
| --- | --- | --- |
| Intake | Bounded text + project → immutable source | Invalid/oversized input rejected before provider call |
| Context retrieval | Project + source IDs → bounded relevant excerpts | Missing/cross-project source rejected; never load entire history |
| Skill selection | Intent + approved registry → skill ID/digest | Unknown/incompatible skill fails clearly; no arbitrary path fallback |
| Plan | Inputs + skill metadata → recorded fixed workflow steps | Instructions cannot add tools or skip approval |
| Execute | Skill body + selected context → candidate structured artifact | Timeout/invalid output stored as failed stage; bounded explicit retry |
| Validate | Candidate + sources → deterministic checks and findings | Invalid IDs/references/schema block progression; semantic uncertainty remains visible |
| Human review | Exact revision + findings → recorded review/approval/rejection | Approval requires explicit local user action; editing invalidates prior approval |
| Publish | Approved revision + preview digest → export + manifest | Recheck digest transactionally; reject stale/rejected/unapproved artifacts |

Commit each successful stage and its outputs atomically. Interrupted running stages become resumable with an explicit retry decision. Resume completed stages without repeating them; a provider call interrupted before its result was persisted may need another billable request and must be reported. No automatic retry of ambiguous external writes.

Deterministic checks cover schema, unique/linked IDs, source existence, duplicate story text and explicit missing fields. Human reviewers can record contradictions; generation or optional LLM critique can suggest conflicts for review. Curated, human-reviewed cases evaluate known conflicts and their recorded disposition, not a universal semantic detector. Do not claim deterministic semantic truth or perfect prompt-injection detection. LLM critique is advisory data, never the authority to approve.

## Review and export

Show the precise PRD/story revision, findings, provider destination, and proposed output paths. Prepare an immutable candidate package before approval. Its preview digest binds the artifact revision, template version/digest, sorted file paths, generated file hashes and asset hashes. Persist approval of that digest. Export reads the same stored candidate bytes and rechecks the digest; template, asset or content changes require another preview and approval. Publication authorization cannot arrive from a prompt, source, model response, or imported skill. Selecting a new revision requires another review.

The ZIP contains a fixed Starlight project, `package.json`, `package-lock.json`, configuration, content, any referenced local assets, requirement/story mapping, revision manifest, setup instructions, and a clean Git collaboration guide. No credentials or private absolute paths. Apply inert rendering to browser preview as well as export: fixed serialized frontmatter, plain Markdown, escaped raw HTML/scripts/template syntax, safe URL schemes and no remotely loaded images/assets. Never compile imported/model content as MDX or accept model-supplied file paths, plugins or npm commands.

Required commands from a clean extracted directory: `npm ci`, `npm run dev`, `npm run build`, `npm run preview`. No SpecBridge process or LLM credentials are required. Dependencies initially need registry access; offline installation is not promised.

For the first slice, generation creates a new package rather than updating an existing developer repo. Later Git changesets use a managed-file manifest, base hashes and conflict previews. Existing authored files must never be silently replaced.

## Success criteria

The [acceptance scenarios](../evaluations/acceptance.md) are the test contract. First-slice completion requires API/integration tests, browser review/download tests, attack fixtures, interruption/restart tests, and an actual clean ZIP install/build/navigation test. No live-provider quality claim is allowed from fixture execution alone.

Performance is recorded as actual duration, provider call count and reported token/cost data where available. Do not fabricate prices or latency budgets. Set budgets from measured local baselines before widening scope.


## Focused workspace extension (19 October 2026)

The [approved workspace design](review-workspace-design.md) adds schema3 feature lineage and schema4 collaboration sidecars. Historical Artifact JSON, IDs, legacy numbers and digests remain immutable. Proven run associations own feature heads; parent links are explicit and unknown legacy metadata stays unknown. Equal digests do not imply feature identity.

`feature_history.py` owns scoped history/comparison. `workbench.py` owns question identities, versioned answers and requested changes. `working_copy.py` owns compare-and-swap private previews and atomic, idempotent revision commits. Commit receipts survive lost responses; changes resolve only in the same transaction as the new feature revision. `revision_decisions` freezes incorporated decisions for history and export. Existing compatibility edits inherit that snapshot.

React presents a task pane beside a complete document on desktop, with Task/Draft switching on narrow screens. Answers, unpreviewed wording, working previews and saved revisions are separate states. Section editors retain the rest of the readable document. Scope guards reject late responses after navigation; reauthentication retains mounted local work. Project context captures exact versions only on explicit selection. Private content is not written to browser storage.

Prepared package previews read verified stored ZIP bytes. Only fixed bounded documentation paths can be returned; rendering uses inert React text and a conservative Markdown subset, with exact source available. Approval remains backend-owned and digest-bound. See [verification and limitations](../evaluations/focused-workspace.md).
