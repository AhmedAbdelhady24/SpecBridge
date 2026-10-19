# Focused workspace: upgrade and rollback

Status: owner rollout authorized by the user ("okay restart the app") and verified on19 October2026. Reviewed branch fast-forwarded into `codex/phase-zero`; owner schema upgraded2→4 after a stopped-write backup. No hosted provider request, remote push or external publication occurred. The procedure below remains the upgrade/rollback reference.

## What changes

FastAPI opens schema2 and transactionally adds schema3 feature lineage plus schema4 question/answer/request/working-copy/receipt sidecars. It preserves original tables, IDs, JSON, legacy revision numbers and digests. Proven associations can receive a feature head; ambiguous lineage remains explicitly unknown. Old candidates may require a fresh review/preparation because the documentation template changed. Private project content stays local.

## Rehearse before rollout

Run from the new code with locked dependencies. Choose a private fresh directory under an existing parent; existing paths are refused:

```sh
migration_parent=$(mktemp -d /tmp/specbridge-migration-check.XXXXXX)
uv run python scripts/verify_workspace_migration.py --database .data/specbridge.db --output "$migration_parent/rehearsal"
```

This reads the owner database through SQLite's consistent backup API, migrates only a copy, compares every preexisting table, restores the preupgrade copy to another new file and verifies it. It prints schema numbers/results, never private rows. Backups are0600 in a0700 directory and remain confidential. On19 October2026, schema2→4, byte-equivalent historical table rows and restoration passed against a disposable copy of the owner workspace.

## Approved rollout sequence

After explicit approval, the lead verifies the current root branch and known owner processes, records the preupgrade commit, then stops only the owned API/Vite gracefully. With writes stopped, create a new private backup using the old compatible backup command:

```sh
uv run python scripts/backup_workspace.py backup --database .data/specbridge.db --output PRIVATE_NEW_BACKUP_PATH
```

`PRIVATE_NEW_BACKUP_PATH` is a placeholder chosen privately at execution, never a shared directory. Record the actual private location for the owner. Integrate the reviewed branch with a fast-forward only; do not reset or overwrite unrelated changes. Preserve the existing private environment/session token. Start the API with its original approved provider configuration, then Vite using the README commands. Opening the database performs the additive migration. Verify schema/integrity plus authenticated project/run/history reads without generating a new paid draft. Confirm the browser shows the new workspace and saved owner projects. Record exact process IDs and health results.

No model call is necessary for rollout verification. Answering questions/editing saves local data only; generation still requires explicit destination acknowledgement.

## Rollback

Stop the upgraded API before restoring. Preserve the upgraded database and any subsequent writes; do not silently discard them. Restore the verified preupgrade backup into a **fresh** destination with the existing CLI:

```sh
uv run python scripts/backup_workspace.py restore --database PRIVATE_NEW_BACKUP_PATH --output NEW_PRIVATE_DIRECTORY/specbridge.db
```

Run the matching recorded preupgrade code with `SPECBRIDGE_DATA_DIR=NEW_PRIVATE_DIRECTORY`, following the existing private token procedure. Never run old code against schema4 or replace a database under an active API. If writes occurred after upgrade, agree how to retain/reconcile them before rollback. Backups do not include `.env` or token files; preserve those separately without logging/copying them into Git.

## Acceptance limits

See [actual verification](../evaluations/focused-workspace.md). Local fixture verification does not establish clinical correctness, live-model quality, unfamiliar-human acceptance or multi-user security. The rollout decision is separate from approving generated product requirements.


## Actual rollout record —19 October2026

Preupgrade code755462e; integrated code0d3a3dd. Verified original owner listeners25540/25548 and their repository working directories, confirmed no running workflow stage, then stopped them gracefully. Private consistent backup: `.data/backups/focused-workspace-20261019T073701Z/preupgrade.db` (0600); baseline table fingerprints retained in that private directory. No credential or private content was printed.

Started the same compatible/deepseek-flash configuration using the existing private `.env` and session token. API listener29194 on127.0.0.1:8000; Vite listener29242 on127.0.0.1:5173 (process IDs can change later). API/config and web returned200. Both projects, five runs and three saved feature histories loaded. Schema4, SQLite integrity/foreign keys and all preexisting table fingerprints passed. Read-only Chromium loaded a saved draft and Questions/Changes panes; zero JavaScript errors, writes or model calls. No full fixture suite was rerun against owner data.
