# Focused requirements workspace

Status: design approved by the user on 18 October 2026: “im the human partner and this plan is approved”. This is a source-checked refinement of the user-supplied UX report, not an implementation or acceptance claim. The user subsequently confirmed the detailed implementation plan. Implementation is verified in an isolated branch; see [results](../evaluations/focused-workspace.md). No paid call, publication or owner-database migration is authorized here. Execution details are in [the implementation plan](../plans/2026-10-18-focused-workspace.md).

## Outcome

A product manager can open a feature, read the complete specification while answering questions or reviewing changes, understand what is proposed versus saved, and approve a comprehensible handoff. Project context is optional background explicitly selected for generation. The main view offers one understandable next action.

Preserve the existing editorial identity, backend approval authority, immutable artifacts, evidence rules and independently runnable Starlight ZIP. Keep the current React/FastAPI modular monolith. No new workflow framework, provider or external integration is needed.

## Evidence and corrections to the audit

Source inspection used App, ArtifactWorkspace, ArtifactPreview, ArtifactEditor, KnowledgePanel, EvidencePicker, models, storage, workflow, publication, knowledge routes, Playwright configuration and helpers. The codebase-memory skill was consulted; graph tools are unavailable, so exact source reads were used. The submitted screenshots and browser measurements were not independently replayed in this design review.

| Finding | Current source evidence and disposition |
| --- | --- |
| JF-01 authentication | App already preserves the token after 401, shows `.data/session-token` help and an inline invalid-field message. Retain and regression-test; the audit's reset claim is stale. Never suggest startup logs contain a token without evidence. |
| JF-02 project/feature navigation | Project selection and creation share the intake panel. Move switching to the header, creation behind an explicit action, and feature selection into project navigation. |
| JF-03 selecting context | Current records expose Edit and History; selection requires separate context search. Add a direct, reversible Use in next draft action capturing an exact version. |
| JF-04 evidence | EvidencePicker already supports original-source snippets, checkboxes, search and paging. Reuse it; no new UUID picker or mandatory modal. Improve classification labels and defaults. |
| JF-05 destination | New feature intake already collapses when a run is open. Further simplify destination presentation and show an explicit confirmation immediately before generation. |
| JF-06 editing | Read mode and collapsed edit sections already exist. Add section-level editing and test action-bar containment; overlap measurements remain audit-reported, not newly reproduced. |
| JF-07 questions | Artifact.open_questions is list[str]; preview has no answer interaction. Add durable question/answer records outside immutable Artifact snapshots. |
| JF-08 lineage | Revision numbering, optimistic writes, workflow base_digest and publication eligibility are project-wide. This needs backend feature isolation before a trustworthy feature timeline. Provenance already records originating run_id on generated revisions. |
| JF-09 review | Review controls remain below the document. Place review notes beside the complete draft. |
| JF-10 package | Candidate API exposes hashes/manifest, not readable file content. Add an authenticated, integrity-checked read-only content preview tied to the exact candidate. |

Do not copy the wireframe's illustrative clinical rules, response-time targets, context excerpts or verification badges into the product as facts. A digest proves a comparison against a stored value, not factual correctness or trusted authorship.

## Interaction design

Header: project switcher, feature switcher, New feature, and Project context. Project creation is a secondary explicit action. No draft controls appear before a feature exists.

Desktop: a narrower task pane beside the complete readable specification. Task navigation is Questions, Changes, Review & export. Selecting a task does not replace the document. Allow the task pane and document to scroll without losing the visible save controls or keyboard access. Do not add a third permanently visible settings column.

Tablet/mobile: one visible pane at a time, using Task / Draft controls and clear task navigation. Preserve selected question, scroll position and pending work across switches. Native headings, labelled controls, focus management, visible focus, count/status announcements and no horizontal scrolling at 390/768/1440px are acceptance requirements.

The document defaults to Saved draft. Once an amendment exists, Working preview shows additions/removals with text labels as well as color. A clear label states that the saved revision is unchanged. Section Edit opens only that section. Save as new revision and Discard amendments remain reachable and inside the pane bounds. Discarding amendments does not delete separately saved answers; say so explicitly.

Keep technical provenance, raw IDs, pipeline details, template hashes and full manifests in Details. Generation confirmation still shows the actual destination, model, selected evidence and billable nature. A small badge alone is insufficient destination disclosure.

## Questions, answers and requested changes

Questions have explicit identities scoped to a feature. Store the question's originating revision, original text and occurrence; identical strings appearing twice must not collapse. Do not replace Artifact.open_questions with objects or rewrite historical snapshots to introduce IDs. Add an API view for the question queue and append-only answer versions. Carry identities forward only when an explicit link or unambiguous unchanged occurrence is known; uncertain matches require review.

User sequence:

1. Select a question; see original wording and any known links. If there is no reliable link, say No section linked and let the user choose targets.
2. Type and Save answer. This records user-provided input and retains history; it does not update or approve the specification. Show saving/saved/failure feedback.
3. Select one or more target clauses or a new clause. Enter the exact amendment text. Preview amendment changes only the working copy. A reply is not automatically a well-formed requirement or acceptance criterion.
4. Inspect the complete draft and its diff. Users may adjust or remove amendments. Requirement/story relationships and evidence constraints still apply.
5. Save as new revision, optionally with a human change summary. Validate and write the artifact, explicit question-to-change links and requested resolutions atomically. A failed save leaves the saved artifact and resolution state unchanged.

Track answer state separately from resolution: Unanswered, Answer saved, and Resolved in revision N. Dismissal requires a reason and can be reopened. An answered question is not automatically resolved. When resolution removes a question from the new artifact's open-question list, preserve its original wording, answer history and resolution link outside the artifact. Reopening is explicit and must make any required artifact amendment reviewable.

New amendment evidence uses the saved answer as a user-provided source. Exact-excerpt rules remain enforced. Rephrased user text is not silently relabelled verified or quoted evidence. Do not auto-generate linked stories, clinical policy, owners, metrics or deadlines.

Requested changes are separate persistent review items linked to a base revision and optional question/requirement/story. Record their text, status and explicit resolution revision. A save or an answer must not automatically mark every request addressed. Review dispositions and exact package approval remain separate authoritative records. Reviewer identity is not invented for the current local-session model.

No model call occurs when typing, saving an answer, selecting a target, previewing a manual amendment, comparing revisions or saving a revision. Optional AI-assisted amendments are a later bounded addition with explicit payload/destination confirmation; they are not necessary to deliver this design. Do not claim automatic semantic contradiction detection. Show linked project context and let the user record conflicts; deterministic stale-version/reference checks can run automatically.

## Feature isolation and historical compatibility

Use an existing run as the feature identity for this scope; introducing a separate feature service is unnecessary. Add lineage metadata beside existing revision snapshots: project/run association, parent revision, feature revision number, actual creation time when known and optional human summary. Keep original revision IDs, project-wide numbers, artifact JSON and digests unchanged. Display feature revision numbers only for proven associations. Preserve project-wide numbers as legacy references in Details.

Migration is versioned and transactional, tested on disposable copies. Existing generated revision provenance.run_id and validate checkpoints can prove associations; verify project membership and agreement before accepting them. Current run.revision_id links identify heads. Never infer a parent from adjacency, title similarity or project-wide numbering. Ambiguous/unassociated legacy revisions remain readable in a labelled legacy history. Missing authors, dates and summaries remain unknown. Parent associations cannot cross project/feature boundaries or form cycles.

This is not merely a nullable-column migration. Change the backend's latest-head and concurrency rules consistently across:

- workflow initialization and generation checkpoint commit;
- revision creation, editing and requirement/story ID preservation;
- candidate preparation, approval and download eligibility;
- feature history, comparisons, question resolution and review requests.

Saving feature B must not stale feature A. Concurrent edits of feature A must still fail with a conflict. New requirements receive new IDs; existing IDs cannot be reused after removal, and unrelated features cannot adopt each other's identified items. Provenance is taken from the actual parent, never the latest unrelated project revision. Historical access must not become a bypass to publish an unassociated legacy artifact.

Diffs compare selected saved revisions within the same proven feature. Match requirements/stories by stable IDs, showing edits to text, links, criteria, evidence and classification. For unidentified lists, present deterministic sequence changes; do not claim that an insertion changed every later item or infer semantic equivalence. Default to parent comparison. Include question/answer resolutions and human requests in the history presentation without modifying old snapshots.

## Persistence, recovery and review boundaries

Use an authenticated server-side working-copy record per feature, with base revision ID/digest and an optimistic version. Recover saved working copies after reauthentication; token stays in tab memory. Never store tokens, answers, evidence or draft content in browser localStorage. Use explicit status text to distinguish pending local keystrokes from acknowledged persistence. Failed persistence remains visible and navigation requires a deliberate discard while work is unsaved.

Opening stale work offers a read-only comparison and explicit reconciliation onto the current feature head. Never silently rebase, discard or resubmit. Double-submit protection and idempotent commit handling must prevent duplicate revisions if a response is lost. Changes to questions/answers cannot claim to invalidate the content of an already approved package unless a new artifact/package is actually created; disclose decisions not yet incorporated. Any saved artifact revision requires fresh review and a fresh exact-package approval. Old approvals remain historical and cannot authorize the new head.

Project context defaults to a title and text with plain-language classification, and exposes verification/evidence/history as Details. A direct Use in next draft toggle captures a versioned snapshot. Saving/editing context does not automatically select it or amend existing drafts. Selecting context while reading an existing run must explicitly say it is for the next generation. Updating a context record does not silently upgrade an already selected snapshot.

## Exact documentation preview

Preview content from the prepared candidate's stored ZIP after integrity verification. Do not regenerate preview from the current working artifact. Permit only bounded, known documentation files in that candidate; reject arbitrary paths, cross-project IDs, oversized/decompression-heavy archives and invalid manifests. Render inert text/Markdown safely; no model-authored HTML, MDX evaluation, scripts or external image fetches. Reuse existing dependencies where adequate; review any new parser separately.

The preview is a readable view of exact packaged content, not a claim of pixel-identical Starlight rendering. Include a file navigator and a Technical details view with copyable hashes. Do not call a hash alone Tamper-Evident or Provenance Verified. Show Package integrity checked only after an actual server comparison. Approval sends the exact digest shown. Review/approve/download enforcement remains on the backend.

For standalone handoff, include the explicitly resolved decisions and original questions associated with that revision, with clear status and provenance. Do not include later answers, unsaved drafts or private unselected context. This extends package generation and template regression coverage; it is not a new hosting target. Retain local Starlight ZIP export. GitHub/Jira writes remain later milestones.

## Delivery choices and dependency order

Recommended: an additive backend model plus the two-pane UI, delivered as one coherent user journey in reviewable changes. A visual-only rearrangement is smaller but leaves the question and lineage loops broken. Replacing Artifact schemas and rewriting history is broader and threatens existing hashes, fixtures, provider prompts and exports.

1. Establish feature isolation and historical compatibility before implementing a feature timeline. Include migration, API contracts, conflict handling and package eligibility tests.
2. Add durable answers, requested changes, working previews and atomic revision commits. Preserve Artifact compatibility. Regenerate OpenAPI/TypeScript from backend models, never edit generated schemas as the source of truth.
3. Build the two-pane workspace, section editing, direct context selection and understandable task states against those contracts.
4. Add saved-revision comparison and integrity-checked documentation preview; update portable exports and run the combined acceptance journey.

This order differs from the submitted PR sequence because the UI must not imply persistence, correct lineage or safe preview semantics before they exist. No new external integration, automatic semantic detector, collaboration identity system or AI amendment generator is in this scope.

## Independently verifiable acceptance

- All currently passing authentication, evidence, dirty-state, review and package regressions remain meaningful; update selectors deliberately when layout changes.
- Start two features in one project, alternate edits, and prepare/download each current head independently. Stale edits within one feature fail. Cross-feature/project associations and comparisons fail.
- Migrate disposable historical databases with proven, missing, duplicated and conflicting provenance; original artifact bytes/digests and approvals remain unchanged. Unsupported versions fail without partial writes. Backup/recovery and failure injection cover new records.
- Answer two identical questions independently. Reload/reconnect and recover each saved answer. Editing an answer preserves history, does not silently resolve a question, and does not rewrite the saved artifact.
- Preview an amendment affecting a requirement and its story/criteria, discard it, and verify the saved revision is unchanged. Save a valid amendment once; resolution links and the new revision appear together. Invalid artifact, stale base and interrupted/double submission cannot partially resolve or duplicate work.
- Requested changes persist and resolve only through explicit user action; recording an answer and accepting a review are distinct. Newly saved content requires fresh package review/approval.
- With the complete draft visible, answer a question, inspect its preview and record review notes on desktop. Mobile switching preserves pending work and selected position. Verify focus order, error association, live announcements and pane/action-bar bounds at390/768/1440px.
- Directly select context from its saved record, remove it, and inspect the captured version. Subsequent edits to that record cannot silently change selected evidence. Generation acknowledgment stays explicit at point of use.
- Package preview reflects exact stored candidate files; malicious content remains inert; tampering, traversal, oversized files and cross-project requests fail. Built Starlight export contains only revision-bound, intended decisions and works independently.
- Prove no paid calls with a backend provider spy that fails if generation is invoked during answer/edit/preview/history/package operations, plus a network-denied fixture harness. Browser-only monitoring of api.deepseek.com cannot observe backend egress and is insufficient. Separately assert no workflow advance/generation request originates from those UI actions.
- Run backend unit/integration/security checks, frontend typing/lint/unit/build, fixture Playwright, generated-contract drift checks, standalone documentation build and workspace recovery. Record actual outcomes; existing audit snippets are pseudocode, not executable acceptance evidence.

## Review state and next action

This review changed documentation only and did not read credentials, invoke a provider, migrate the owner's database, change application code or accept a milestone. No fresh browser, backend or build pass is claimed by this design review.

The user approved the corrected design, including immutable Artifact compatibility, feature-local concurrency, durable answer/preview semantics and no automatic paid amendments. Next: review the implementation plan under docs/plans, then execute in dependency order using the preserved lead-agent approach. Before any owner-database upgrade, verify a backup and review the migration on a disposable copy; never run old write-capable binaries on an upgraded database as a rollback shortcut.
