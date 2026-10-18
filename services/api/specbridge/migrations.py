"""Additive metadata migrations; historical revision JSON is never rewritten."""

import json
import sqlite3

LINEAGE_TABLES = {"revision_lineage", "feature_heads"}


def require_tables(db: sqlite3.Connection, required: set[str]) -> None:
    actual = {
        row[0]
        for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    if not required <= actual:
        raise ValueError("Incomplete workspace schema")


def migrate_lineage(db: sqlite3.Connection) -> None:
    db.execute("""CREATE TABLE revision_lineage (
        revision_id TEXT PRIMARY KEY REFERENCES revisions(id),
        project_id TEXT NOT NULL REFERENCES projects(id),
        run_id TEXT NOT NULL REFERENCES runs(id),
        parent_revision_id TEXT REFERENCES revisions(id),
        feature_number INTEGER,
        created_at TEXT,
        change_summary TEXT,
        UNIQUE(project_id,run_id,feature_number))""")
    db.execute("""CREATE TABLE feature_heads (
        project_id TEXT NOT NULL REFERENCES projects(id),
        run_id TEXT PRIMARY KEY REFERENCES runs(id),
        revision_id TEXT NOT NULL REFERENCES revisions(id))""")
    runs = {row["id"]: row for row in db.execute("SELECT * FROM runs")}
    revisions = {row["id"]: row for row in db.execute("SELECT * FROM revisions")}
    signals: dict[str, set[str]] = {key: set() for key in revisions}
    for key, row in revisions.items():
        origin = json.loads(row["data"]).get("provenance", {}).get("run_id")
        if origin:
            signals[key].add(origin)
    for run_id, row in runs.items():
        head = json.loads(row["data"]).get("revision_id")
        if head in signals:
            signals[head].add(run_id)
    roots: set[str] = set()
    for row in db.execute("SELECT run_id,data FROM checkpoints WHERE stage='validate'"):
        revision_id = json.loads(row["data"]).get("revision_id")
        if revision_id in signals:
            signals[revision_id].add(row["run_id"])
            roots.add(revision_id)
    proven = {}
    for revision_id, origins in signals.items():
        if len(origins) != 1:
            continue
        run_id = next(iter(origins))
        if (
            run_id not in runs
            or runs[run_id]["project_id"] != revisions[revision_id]["project_id"]
        ):
            continue
        proven[revision_id] = run_id
    for revision_id, run_id in proven.items():
        project_id = revisions[revision_id]["project_id"]
        created = db.execute(
            "SELECT at FROM audit WHERE project_id=? AND action='revision_created' AND subject=? ORDER BY id LIMIT 1",
            (project_id, revision_id),
        ).fetchone()
        db.execute(
            "INSERT INTO revision_lineage VALUES (?,?,?,?,?,?,?)",
            (
                revision_id,
                project_id,
                run_id,
                None,
                1 if revision_id in roots else None,
                created[0] + "Z" if created else None,
                None,
            ),
        )
    for run_id, row in runs.items():
        head = json.loads(row["data"]).get("revision_id")
        if proven.get(head) == run_id:
            db.execute(
                "INSERT INTO feature_heads VALUES (?,?,?)",
                (row["project_id"], run_id, head),
            )
    db.execute("PRAGMA user_version=3")
