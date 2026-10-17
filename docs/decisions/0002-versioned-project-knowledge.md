# ADR 0002: Versioned project knowledge and explicit context snapshots

Status: accepted for the user-authorized Milestone 2 on 2026-10-17. This extends the existing modular monolith; it does not qualify the model or close Milestone 1 acceptance.

The application already persists original sources, artifact revisions, workflow checkpoints and exact publication approvals. Milestone 2 adds goals, stakeholders, decisions, risks, dependencies, API references and conversation notes without introducing a retrieval service or autonomous agent.

Store knowledge as append-only SQLite versions keyed by stable entry ID and version, scoped to a project. Digest-based optimistic concurrency includes entry identity and version, preventing stale writes even after content is reverted. A transactional schema 1→2 migration adds only the knowledge table/index; existing rows and package bytes remain untouched. Unknown future schemas are refused.

Use bounded deterministic substring search over current entries and original sources. Titles rank above content matches; ties use stable resource/ID ordering. This is lexical retrieval, not semantic search. Entry bodies are bounded to30,000 UTF-8 bytes and16,384 characters; query/result/context limits are explicit. Archived current entries and historical knowledge-source snapshots are excluded from active retrieval. Historical versions remain addressable. API history lists are paginated with `before` and `limit`; the initial UI presents a bounded recent history.

Context enters a generation only after deliberate selection. Capture an immutable Source with its entry/version reference, version digest and evidence kind. Later knowledge edits never mutate that snapshot or an existing run. Original sources remain immutable. A generated user_provided excerpt may cite only user_provided evidence; assumptions/recommendations/unknowns and human-verification records cannot silently acquire that label. Retrieved content is always inert context, never a tool grant.

Creation/editing cannot set verified. A separate local authenticated action requires original source evidence, a note, an exact saved digest and strict boolean confirmation. The UI blocks verification while substantive edits are unsaved and clears confirmation when the reviewed payload changes. Every edit removes earlier verification; history retains the prior judgment. Verification records a human judgment; it does not establish world truth, approve an artifact or authorize publication. Knowledge snapshots cannot bootstrap verification evidence.

Backups use SQLite's consistent backup API into new private 0600 files, with supported-schema, integrity and foreign-key checks. Restore requires a new destination and never overwrites an active workspace. Session tokens and provider keys are not copied by this database-only operation. A fixture recovery command exercises backup/restore, all seven knowledge categories, version history, context labels and resuming a checkpoint to human review.

Keep SQLite behind the existing Store transaction boundary. PostgreSQL remains a future deliberate port; vector databases, embeddings, LangGraph and new services are not justified by this milestone. Local session/origin boundaries continue to apply; real multi-user authorization remains required before external access.
