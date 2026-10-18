"""Verify migration and restore on private copies; never modify the input database."""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
sys.path.insert(0, str(ROOT))

from specbridge.storage import Store

from scripts.backup_workspace import copy_database


def snapshot(path: Path) -> tuple[int, dict[str, str]]:
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        names = [
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        result = {}
        for name in names:
            quoted = name.replace('"', '""')
            rows = sorted(db.execute(f'SELECT * FROM "{quoted}"').fetchall(), key=repr)
            result[name] = hashlib.sha256(repr(rows).encode()).hexdigest()
        return db.execute("PRAGMA user_version").fetchone()[0], result


def verify(database: Path, output: Path) -> dict[str, object]:
    # Fresh private directory; never overwrite a previous rehearsal or backup.
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    backup = output / "preupgrade.db"
    copy_database(database, backup)
    candidate = output / "migration.db"
    copy_database(backup, candidate)
    old_version, before = snapshot(candidate)
    Store(candidate)
    new_version, after = snapshot(candidate)
    if any(after.get(name) != value for name, value in before.items()):
        raise ValueError("Historical table rows changed during migration")
    restored = output / "restored.db"
    copy_database(backup, restored)
    if snapshot(restored) != (old_version, before):
        raise ValueError("Restored snapshot differs from backup")
    return {
        "old_schema": old_version,
        "new_schema": new_version,
        "historical_tables_unchanged": True,
        "restore_verified": True,
        "backup_mode": oct(os.stat(backup).st_mode & 0o777),
        "input_database_modified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.database, args.output)))


if __name__ == "__main__":
    main()
