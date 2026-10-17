"""Private SQLite workspace backup/restore into a new path; never overwrite."""

import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path


def validate_database(db: sqlite3.Connection) -> None:
    if db.execute("PRAGMA user_version").fetchone()[0] not in (1, 2):
        raise ValueError("Unsupported workspace schema")
    required = {
        "projects",
        "sources",
        "revisions",
        "runs",
        "checkpoints",
        "reviews",
        "candidates",
        "approvals",
        "audit",
    }
    tables = {
        r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    if not required <= tables or (
        db.execute("PRAGMA user_version").fetchone()[0] == 2
        and "knowledge" not in tables
    ):
        raise ValueError("Incomplete workspace schema")
    if (
        db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]
        or db.execute("PRAGMA foreign_key_check").fetchall()
    ):
        raise ValueError("Workspace integrity check failed")


def copy_database(source: Path, output: Path) -> None:
    if source.is_symlink():
        raise ValueError("Workspace must be a regular file, not a symlink")
    if not source.is_file():
        raise FileNotFoundError("Workspace does not exist")
    with closing(
        sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
    ) as original:
        validate_database(original)
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        try:
            with closing(sqlite3.connect(output)) as destination:
                original.backup(destination)
                validate_database(destination)
        except BaseException:
            output.unlink()
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["backup", "restore"])
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    copy_database(args.database, args.output)
    print("Workspace copied and integrity-checked. Existing data was not overwritten.")


if __name__ == "__main__":
    main()
