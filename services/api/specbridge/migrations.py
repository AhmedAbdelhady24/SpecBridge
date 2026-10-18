"""Additive metadata migrations; historical revision JSON is never rewritten."""

import json
import sqlite3

BASE_TABLES = {
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


WORKBENCH_TABLES = {
    "questions",
    "question_occurrences",
    "question_answers",
    "question_events",
    "change_requests",
    "change_request_events",
    "working_copies",
    "commit_receipts",
    "revision_decisions",
    "working_versions",
}


def migrate_workbench(db: sqlite3.Connection) -> None:
    db.execute(
        "CREATE TABLE working_versions (run_id TEXT PRIMARY KEY REFERENCES runs(id),version INTEGER NOT NULL)"
    )
    db.execute(
        "CREATE TABLE questions (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), run_id TEXT NOT NULL REFERENCES runs(id), data TEXT NOT NULL)"
    )
    db.execute(
        "CREATE TABLE question_occurrences (revision_id TEXT NOT NULL REFERENCES revisions(id), position INTEGER NOT NULL, question_id TEXT NOT NULL REFERENCES questions(id), PRIMARY KEY(revision_id,position))"
    )
    db.execute(
        "CREATE TABLE question_answers (question_id TEXT NOT NULL REFERENCES questions(id), version INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY(question_id,version))"
    )
    db.execute(
        "CREATE TABLE question_events (question_id TEXT NOT NULL REFERENCES questions(id), version INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY(question_id,version))"
    )
    db.execute(
        "CREATE TABLE change_requests (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), run_id TEXT NOT NULL REFERENCES runs(id), data TEXT NOT NULL)"
    )
    db.execute(
        "CREATE TABLE change_request_events (request_id TEXT NOT NULL REFERENCES change_requests(id), version INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY(request_id,version))"
    )
    db.execute(
        "CREATE TABLE working_copies (run_id TEXT PRIMARY KEY REFERENCES runs(id),project_id TEXT NOT NULL REFERENCES projects(id),version INTEGER NOT NULL,data TEXT NOT NULL)"
    )
    db.execute(
        "CREATE TABLE commit_receipts (run_id TEXT NOT NULL REFERENCES runs(id),key TEXT NOT NULL,fingerprint TEXT NOT NULL,data TEXT NOT NULL,PRIMARY KEY(run_id,key))"
    )
    db.execute(
        "CREATE TABLE revision_decisions (revision_id TEXT PRIMARY KEY REFERENCES revisions(id),data TEXT NOT NULL)"
    )
    for row in db.execute(
        "SELECT r.id,r.project_id,r.data,l.run_id,l.parent_revision_id FROM revisions r JOIN revision_lineage l ON l.revision_id=r.id ORDER BY r.number"
    ).fetchall():
        sync_questions(
            db,
            row["project_id"],
            row["run_id"],
            row["id"],
            json.loads(row["data"])["artifact"]["open_questions"],
            row["parent_revision_id"],
        )
    db.execute("PRAGMA user_version=4")


def sync_questions(
    db: sqlite3.Connection,
    project_id: str,
    run_id: str,
    revision_id: str,
    texts: list[str],
    parent_id: str | None,
    excluded_question_ids: list[str] | None = None,
    reopened_question_ids: list[str] | None = None,
) -> None:
    from uuid import uuid4

    from .workbench_models import QuestionView

    previous = (
        [
            (r["position"], r["question_id"], json.loads(r["data"])["text"])
            for r in db.execute(
                "SELECT o.position,o.question_id,q.data FROM question_occurrences o JOIN questions q ON q.id=o.question_id WHERE o.revision_id=? ORDER BY o.position",
                (parent_id,),
            )
        ]
        if parent_id
        else []
    )
    previous = [p for p in previous if p[1] not in (excluded_question_ids or [])]
    for reopen_id in reopened_question_ids or []:
        row = db.execute(
            "SELECT data FROM questions WHERE id=? AND project_id=? AND run_id=?",
            (reopen_id, project_id, run_id),
        ).fetchone()
        if row is None or any(item[1] == reopen_id for item in previous):
            raise ValueError("Reopened question identity is not valid for this feature")
        previous.append((len(previous), reopen_id, json.loads(row[0])["text"]))
    old_texts = [p[2] for p in previous]
    if (
        (excluded_question_ids or reopened_question_ids)
        and texts != old_texts
        and any(old_texts.count(text) > 1 and text in texts for text in old_texts)
    ):
        raise ValueError(
            "Save duplicate-question resolutions separately from other question-list edits"
        )
    for index, text in enumerate(texts):
        question_id = None
        if texts == old_texts:
            question_id = previous[index][1]
        elif texts.count(text) == 1 and old_texts.count(text) == 1:
            question_id = previous[old_texts.index(text)][1]
        if question_id is None:
            question_id = str(uuid4())
            question = QuestionView(
                id=question_id,
                text=text,
                origin_revision_id=revision_id,
                origin_index=index,
            )
            db.execute(
                "INSERT INTO questions VALUES (?,?,?,?)",
                (question_id, project_id, run_id, question.model_dump_json()),
            )
        db.execute(
            "INSERT INTO question_occurrences VALUES (?,?,?)",
            (revision_id, index, question_id),
        )
