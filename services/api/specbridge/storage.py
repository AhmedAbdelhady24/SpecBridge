import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from .migrations import (
    BASE_TABLES,
    LINEAGE_TABLES,
    WORKBENCH_TABLES,
    migrate_lineage,
    migrate_workbench,
    require_tables,
    sync_questions,
)
from .models import (
    Artifact,
    Finding,
    Project,
    Revision,
    Source,
    digest,
    validate_handoff,
)


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2, 3, 4):
                raise ValueError(
                    "Unsupported database schema; database was not changed"
                )
            if version >= 1:
                require_tables(
                    db, BASE_TABLES | ({"knowledge"} if version >= 2 else set())
                )
            if version >= 4:
                require_tables(db, WORKBENCH_TABLES)
            if version >= 3:
                require_tables(db, LINEAGE_TABLES)
            db.execute(
                "CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), data TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS revisions (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), number INTEGER NOT NULL, digest TEXT NOT NULL, data TEXT NOT NULL, UNIQUE(project_id, number))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), data TEXT NOT NULL, lease TEXT, lease_until REAL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints (run_id TEXT NOT NULL REFERENCES runs(id), stage TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(run_id, stage))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), revision_id TEXT NOT NULL REFERENCES revisions(id), disposition TEXT NOT NULL, notes TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS candidates (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), revision_id TEXT NOT NULL REFERENCES revisions(id), digest TEXT NOT NULL UNIQUE, template_digest TEXT NOT NULL, manifest TEXT NOT NULL, zip BLOB NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS approvals (candidate_id TEXT PRIMARY KEY REFERENCES candidates(id), digest TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), action TEXT NOT NULL, subject TEXT NOT NULL, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS knowledge (id TEXT NOT NULL, project_id TEXT NOT NULL REFERENCES projects(id), version INTEGER NOT NULL, digest TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(id,version))"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS knowledge_project ON knowledge(project_id,id,version)"
            )
            if version < 3:
                migrate_lineage(db)
            if version < 4:
                migrate_workbench(db)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def create_project(self, name: str) -> Project:
        if not name.strip() or len(name) > 200:
            raise ValueError("Project name must have 1–200 characters")
        project = Project(id=str(uuid4()), name=name.strip())
        with self.transaction() as db:
            db.execute("INSERT INTO projects VALUES (?,?)", (project.id, project.name))
        return project

    def projects(self) -> list[Project]:
        with self.transaction() as db:
            return [
                Project(**dict(row))
                for row in db.execute("SELECT * FROM projects ORDER BY rowid")
            ]

    @staticmethod
    def require_project(db: sqlite3.Connection, project_id: str) -> None:
        if not db.execute(
            "SELECT 1 FROM projects WHERE id=?", (project_id,)
        ).fetchone():
            raise NotFound("Project not found")

    def add_source(self, project_id: str, text: str) -> Source:
        if not text.strip() or len(text.encode()) > 32768:
            raise ValueError("Source must contain 1–32768 UTF-8 bytes")
        source = Source(
            id=str(uuid4()), project_id=project_id, text=text, digest=digest(text)
        )
        with self.transaction() as db:
            self.require_project(db, project_id)
            db.execute(
                "INSERT INTO sources VALUES (?,?,?)",
                (source.id, project_id, source.model_dump_json()),
            )
        return source

    def sources(self, project_id: str, source_ids: list[str]) -> list[Source]:
        if not 1 <= len(source_ids) <= 20 or len(set(source_ids)) != len(source_ids):
            raise ValueError("Select 1–20 distinct sources")
        result = []
        with self.transaction() as db:
            self.require_project(db, project_id)
            for source_id in source_ids:
                row = db.execute(
                    "SELECT data FROM sources WHERE id=? AND project_id=?",
                    (source_id, project_id),
                ).fetchone()
                if not row:
                    raise NotFound("Source not found")
                result.append(Source.model_validate_json(row[0]))
        if sum(len(s.text.encode()) for s in result) > 65536:
            raise ValueError("Selected context exceeds 64 KiB")
        return result

    def get_revision(self, project_id: str, revision_id: str) -> Revision:
        with self.transaction() as db:
            row = db.execute(
                "SELECT data FROM revisions WHERE id=? AND project_id=?",
                (revision_id, project_id),
            ).fetchone()
            if not row:
                raise NotFound("Revision not found")
            return Revision.model_validate_json(row[0])

    def save_revision(
        self,
        project_id: str,
        artifact: Artifact,
        expected_digest: str | None,
        *,
        run_id: str | None = None,
        parent_revision_id: str | None = None,
        change_summary: str | None = None,
        excluded_question_ids: list[str] | None = None,
        reopened_question_ids: list[str] | None = None,
        provenance: dict[str, str] | None = None,
        findings: list[Finding] | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> Revision:
        if connection is None:
            with self.transaction() as db:
                return self.save_revision(
                    project_id,
                    artifact,
                    expected_digest,
                    run_id=run_id,
                    parent_revision_id=parent_revision_id,
                    change_summary=change_summary,
                    excluded_question_ids=excluded_question_ids,
                    reopened_question_ids=reopened_question_ids,
                    provenance=provenance,
                    findings=findings,
                    connection=db,
                )
        db = connection
        self.require_project(db, project_id)
        rows = db.execute(
            "SELECT data FROM revisions WHERE project_id=? ORDER BY number",
            (project_id,),
        ).fetchall()
        history = [Revision.model_validate_json(row[0]) for row in rows]
        latest = history[-1] if history else None
        if run_id is not None:
            from .feature_history import FeatureHistory

            latest = FeatureHistory(self).head(project_id, run_id, connection=db)
            if (latest.id if latest else None) != parent_revision_id:
                raise Conflict("Feature changed; compare revisions before saving")
        elif parent_revision_id is not None:
            raise ValueError("Parent requires feature identity")
        if (latest.digest if latest else None) != expected_digest:
            raise Conflict("Revision changed; reload before editing")
        current_ids = (
            {item.id for item in latest.artifact.identified_items()}
            if latest
            else set()
        )
        issued = {
            item.id for rev in history for item in rev.artifact.identified_items()
        }
        body = deepcopy(artifact)
        mapping = {}
        for item in body.identified_items():
            if item.id in issued and item.id not in current_ids:
                raise Conflict("Removed IDs cannot be reused")
            if item.id not in current_ids:
                mapping[item.id] = item.id.split("-")[0] + "-" + str(uuid4())
                item.id = mapping[item.id]
        for story in body.stories:
            story.requirement_ids = [
                mapping.get(key, key) for key in story.requirement_ids
            ]
        cited: dict[str, Source] = {}
        for statement in body.statements():
            for source_id in statement.source_ids:
                row = db.execute(
                    "SELECT data FROM sources WHERE id=? AND project_id=?",
                    (source_id, project_id),
                ).fetchone()
                if not row:
                    raise NotFound("Source not found")
                cited[source_id] = Source.model_validate_json(row[0])
        validate_handoff(body, list(cited.values()))
        revision = Revision(
            id=str(uuid4()),
            project_id=project_id,
            number=len(history) + 1,
            digest=digest(body.model_dump()),
            artifact=body,
            provenance=provenance
            if provenance is not None
            else (latest.provenance if latest else {}),
            findings=findings or [],
        )
        db.execute(
            "INSERT INTO revisions VALUES (?,?,?,?,?)",
            (
                revision.id,
                project_id,
                revision.number,
                revision.digest,
                revision.model_dump_json(),
            ),
        )
        if run_id is not None:
            parent_number = (
                db.execute(
                    "SELECT feature_number FROM revision_lineage WHERE revision_id=? AND project_id=? AND run_id=?",
                    (parent_revision_id, project_id, run_id),
                ).fetchone()
                if parent_revision_id
                else None
            )
            feature_number = (
                1
                if parent_revision_id is None
                else (
                    parent_number[0] + 1
                    if parent_number and parent_number[0] is not None
                    else None
                )
            )
            db.execute(
                "INSERT INTO revision_lineage VALUES (?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%SZ','now'),?)",
                (
                    revision.id,
                    project_id,
                    run_id,
                    parent_revision_id,
                    feature_number,
                    change_summary,
                ),
            )
            db.execute(
                "INSERT INTO feature_heads VALUES (?,?,?) ON CONFLICT(run_id) DO UPDATE SET revision_id=excluded.revision_id",
                (project_id, run_id, revision.id),
            )
        if run_id is not None:
            sync_questions(
                db,
                project_id,
                run_id,
                revision.id,
                body.open_questions,
                parent_revision_id,
                excluded_question_ids,
                reopened_question_ids,
            )
        if run_id is not None and parent_revision_id is not None:
            db.execute(
                "INSERT INTO revision_decisions SELECT ?,data FROM revision_decisions WHERE revision_id=?",
                (revision.id, parent_revision_id),
            )
        self.audit(db, project_id, "revision_created", revision.id)
        return revision

    @staticmethod
    def audit(
        db: sqlite3.Connection, project_id: str, action: str, subject: str
    ) -> None:
        db.execute(
            "INSERT INTO audit(project_id,action,subject) VALUES (?,?,?)",
            (project_id, action, subject),
        )
