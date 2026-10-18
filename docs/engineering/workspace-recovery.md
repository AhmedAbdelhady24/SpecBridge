# Workspace knowledge and recovery

Select a project and open **Project knowledge**. Save goals, stakeholders, decisions, risks, dependencies, API references or conversation notes with an evidence label. Source IDs must belong to that project. Save edits as new versions; stale edits require reloading rather than overwriting another change. Archiving removes an entry from active context search; include archived records in the list to inspect or restore it.

Search matches literal substrings in current titles/content and original sources, not semantic similarity. A title match ranks first. Results default to20, with a server maximum50 and a context budget up to65,536 bytes. Empty query browses current context. Refine the query for a smaller selection. Histories use `before`/`limit` for API pagination. The knowledge panel provides continuation controls for current records, knowledge versions, and artifact revisions beyond the first 20. The full project dashboard remains Milestone 5 scope.

Selecting context captures the displayed knowledge version and classification. It appears beside the feature idea before generation; remove it there if unwanted. Historical snapshots stay unchanged when the record is edited or archived. Nothing is sent to an LLM until the existing generation-destination acknowledgment and Generate action. Ordinary knowledge actions, search, history and recovery use no LLM calls.

Human verification needs a saved claim, a note, original supporting source IDs and explicit confirmation. Changing content/title/type/classification/archive state disables verification until saved. Changing evidence or the note clears confirmation. Verification records your review of that version; it never approves a PRD/package. Editing a verified record creates an unverified version. Original evidence can support verification; generated knowledge snapshots cannot.

## Back up a workspace

Run from the repository root with its locked environment. Choose a new output path; existing files are refused. The source may be an active SQLite workspace: SQLite copies a consistent committed snapshot. Protect the backup because it contains project evidence and approved document packages.

```sh
uv run python scripts/backup_workspace.py backup --database .data/specbridge.db --output /tmp/specbridge-private-backup.db
```

The command checks supported schema, database integrity and foreign keys, creates the destination as 0600, then validates the copy. A failed copy is removed; an existing destination is never removed or replaced. Schema 1 backups are supported and migrate transactionally when opened by the current application.

## Restore into a new workspace

Stop the application before switching its data directory. Create a private, separate destination directory; retain the existing workspace until you have checked recovery.

```sh
mkdir -m 700 .recovered-data
uv run python scripts/backup_workspace.py restore --database /tmp/specbridge-private-backup.db --output .recovered-data/specbridge.db
```

Start the usual API command from README with `SPECBRIDGE_DATA_DIR=.recovered-data`. A fresh local session token is created or supplied using the existing private-token process. Provider keys remain in your private environment configuration; database backup/restore does not copy `.env` or session-token files. Do not copy confidential backups into Git, shared directories or public hosting.

## Reproduce recovery checks without real data

```sh
uv run python scripts/verify_workspace_recovery.py
uv run pytest -q services/api/tests/test_knowledge.py services/api/tests/test_workspace_backup.py
```

The verifier creates temporary fixture workspaces, invokes both CLI operations, reconnects through the API, checks seven knowledge types/two immutable goal versions and resumes a saved workflow to human review. It makes no model/network call. Optional `--output NEW.json` saves sanitized evidence and refuses overwrite. Migration regressions additionally compare all nine preexisting tables, approved package bytes and workflow state before/after schema 1→2.
