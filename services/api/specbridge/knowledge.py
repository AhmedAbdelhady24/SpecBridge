"""Project-scoped immutable knowledge and bounded, explicit context retrieval."""

import json
import sqlite3
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, Query
from pydantic import Field, StringConstraints, model_validator

from .models import Model, Source, digest
from .storage import Conflict, NotFound, Store

Small = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Content = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=16384)
]
Entity = Literal[
    "goal",
    "stakeholder",
    "decision",
    "risk",
    "dependency",
    "api_reference",
    "conversation",
]
Unverified = Literal["user_provided", "recommendation", "assumption", "unknown"]
Kind = Literal["user_provided", "verified", "recommendation", "assumption", "unknown"]


class KnowledgeInput(Model):
    entity_type: Entity
    title: Small
    text: Content
    kind: Unverified = "user_provided"
    source_ids: list[str] = Field(default_factory=list, max_length=20)
    archived: bool = False

    @model_validator(mode="after")
    def bounded_utf8(self) -> "KnowledgeInput":
        if len(self.text.encode()) > 30000:
            raise ValueError("Knowledge text exceeds 30000 UTF-8 bytes")
        return self


class KnowledgeEntry(Model):
    id: str
    project_id: str
    version: int
    digest: str
    entity_type: Entity
    title: str
    text: str
    kind: Kind
    source_ids: list[str]
    archived: bool
    verification_note: str | None = None


class KnowledgeEdit(Model):
    expected_digest: str
    entry: KnowledgeInput


class VerifyKnowledge(Model):
    expected_digest: str
    source_ids: list[str] = Field(min_length=1, max_length=20)
    note: Content
    confirm: bool

    @model_validator(mode="after")
    def explicit_confirmation(self) -> "VerifyKnowledge":
        if not self.confirm:
            raise ValueError("Confirmation required")
        return self


class SnapshotRequest(Model):
    version: int = Field(ge=1)
    expected_digest: str


class ContextItem(Model):
    id: str
    resource_type: Literal["knowledge", "source"]
    title: str
    text: str
    kind: Kind
    digest: str
    version: int | None
    source_ids: list[str]
    score: int


class RevisionSummary(Model):
    id: str
    number: int
    digest: str
    title: str


class Knowledge:
    def __init__(self, store: Store):
        self.store = store

    def _get(
        self,
        db: sqlite3.Connection,
        project_id: str,
        entry_id: str,
        version: int | None = None,
    ) -> KnowledgeEntry:
        row = db.execute(
            "SELECT data FROM knowledge WHERE project_id=? AND id=? AND (? IS NULL OR version=?) ORDER BY version DESC LIMIT 1",
            (project_id, entry_id, version, version),
        ).fetchone()
        if row is None:
            raise NotFound("Knowledge not found")
        return KnowledgeEntry.model_validate_json(row[0])

    def _evidence(
        self,
        db: sqlite3.Connection,
        project_id: str,
        ids: list[str],
        *,
        verify: bool = False,
    ) -> None:
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate sources")
        for sid in ids:
            row = db.execute(
                "SELECT data FROM sources WHERE project_id=? AND id=?",
                (project_id, sid),
            ).fetchone()
            if row is None:
                raise NotFound("Source not found")
            if verify and (
                Source.model_validate_json(row[0]).kind != "user_provided"
                or Source.model_validate_json(row[0]).knowledge_ref is not None
            ):
                raise ValueError("Human verification needs original evidence")

    def _save(
        self,
        db: sqlite3.Connection,
        project_id: str,
        entry_id: str,
        version: int,
        data: dict[str, object],
    ) -> KnowledgeEntry:
        value = KnowledgeEntry.model_validate(
            {
                "id": entry_id,
                "project_id": project_id,
                "version": version,
                "digest": digest(
                    {
                        "id": entry_id,
                        "project_id": project_id,
                        "version": version,
                        **data,
                    }
                ),
                **data,
            }
        )
        db.execute(
            "INSERT INTO knowledge VALUES (?,?,?,?,?)",
            (value.id, project_id, version, value.digest, value.model_dump_json()),
        )
        self.store.audit(
            db, project_id, "knowledge_version_created", f"{value.id}@{version}"
        )
        return value

    def create(self, project_id: str, entry: KnowledgeInput) -> KnowledgeEntry:
        with self.store.transaction() as db:
            self.store.require_project(db, project_id)
            self._evidence(db, project_id, entry.source_ids)
            return self._save(
                db,
                project_id,
                "KN-" + str(uuid4()),
                1,
                {**entry.model_dump(), "verification_note": None},
            )

    def edit(
        self, project_id: str, entry_id: str, request: KnowledgeEdit
    ) -> KnowledgeEntry:
        with self.store.transaction() as db:
            old = self._get(db, project_id, entry_id)
            if old.digest != request.expected_digest:
                raise Conflict("Knowledge changed; reload before editing")
            self._evidence(db, project_id, request.entry.source_ids)
            return self._save(
                db,
                project_id,
                entry_id,
                old.version + 1,
                {**request.entry.model_dump(), "verification_note": None},
            )

    def verify(
        self, project_id: str, entry_id: str, request: VerifyKnowledge
    ) -> KnowledgeEntry:
        with self.store.transaction() as db:
            old = self._get(db, project_id, entry_id)
            if old.digest != request.expected_digest:
                raise Conflict("Knowledge changed; reload before verification")
            self._evidence(db, project_id, request.source_ids, verify=True)
            data = old.model_dump(exclude={"id", "project_id", "version", "digest"})
            data.update(
                kind="verified",
                source_ids=request.source_ids,
                verification_note=request.note,
            )
            value = self._save(db, project_id, entry_id, old.version + 1, data)
            self.store.audit(
                db, project_id, "knowledge_verified", f"{entry_id}@{value.version}"
            )
            return value

    def history(
        self, project_id: str, entry_id: str, before: int, limit: int
    ) -> list[KnowledgeEntry]:
        with self.store.transaction() as db:
            self._get(db, project_id, entry_id)
            return [
                KnowledgeEntry.model_validate_json(r[0])
                for r in db.execute(
                    "SELECT data FROM knowledge WHERE project_id=? AND id=? AND version<? ORDER BY version DESC LIMIT ?",
                    (project_id, entry_id, before, limit),
                )
            ]

    def entries(
        self,
        project_id: str,
        query: str,
        entity_type: Entity | None,
        limit: int,
        include_archived: bool = False,
    ) -> list[KnowledgeEntry]:
        with self.store.transaction() as db:
            self.store.require_project(db, project_id)
            return [
                KnowledgeEntry.model_validate_json(r[0])
                for r in db.execute(
                    """SELECT k.data FROM knowledge k WHERE k.project_id=? AND k.version=(SELECT MAX(v.version) FROM knowledge v WHERE v.id=k.id AND v.project_id=k.project_id) AND (? OR json_extract(k.data,'$.archived')=0) AND (? IS NULL OR json_extract(k.data,'$.entity_type')=?) AND (?='' OR instr(lower(json_extract(k.data,'$.title')),lower(?))>0 OR instr(lower(json_extract(k.data,'$.text')),lower(?))>0) ORDER BY CASE WHEN ?<>'' AND instr(lower(json_extract(k.data,'$.title')),lower(?))>0 THEN 0 ELSE 1 END,k.id LIMIT ?""",
                    (
                        project_id,
                        include_archived,
                        entity_type,
                        entity_type,
                        query,
                        query,
                        query,
                        query,
                        query,
                        limit,
                    ),
                )
            ]

    def context(
        self, project_id: str, query: str, limit: int, budget_bytes: int
    ) -> list[ContextItem]:
        entries = self.entries(project_id, query, None, limit)
        items = [
            ContextItem(
                id=e.id,
                resource_type="knowledge",
                title=e.title,
                text=e.text,
                kind=e.kind,
                digest=e.digest,
                version=e.version,
                source_ids=e.source_ids,
                score=2 if query and query.lower() in e.title.lower() else 1,
            )
            for e in entries
        ]
        with self.store.transaction() as db:
            rows = db.execute(
                "SELECT data FROM sources WHERE project_id=? AND json_extract(data,'$.knowledge_ref') IS NULL AND (?='' OR instr(lower(json_extract(data,'$.text')),lower(?))>0) ORDER BY id LIMIT ?",
                (project_id, query, query, limit),
            )
            for row in rows:
                s = Source.model_validate_json(row[0])
                items.append(
                    ContextItem(
                        id=s.id,
                        resource_type="source",
                        title="Source evidence",
                        text=s.text,
                        kind=s.kind,
                        digest=s.digest,
                        version=None,
                        source_ids=[s.id],
                        score=1,
                    )
                )
        total = 0
        selected = []
        for item in sorted(items, key=lambda i: (-i.score, i.resource_type, i.id)):
            size = len(item.model_dump_json().encode())
            if total + size <= budget_bytes:
                total += size
                selected.append(item)
                if len(selected) == limit:
                    break
        return selected

    def snapshot(
        self, project_id: str, entry_id: str, request: SnapshotRequest
    ) -> Source:
        with self.store.transaction() as db:
            e = self._get(db, project_id, entry_id, request.version)
            if e.digest != request.expected_digest:
                raise Conflict("Knowledge snapshot changed")
            sid = f"knowledge-{e.id}-v{e.version}"
            row = db.execute(
                "SELECT data FROM sources WHERE id=? AND project_id=?",
                (sid, project_id),
            ).fetchone()
            if row is not None:
                return Source.model_validate_json(row[0])
            text = f"Workspace entry: {e.title}\nClassification: {e.kind}\n{e.text}"
            if len(text.encode()) > 32768:
                raise ValueError("Knowledge context exceeds source limit")
            snapshot = Source(
                id=sid,
                project_id=project_id,
                text=text,
                kind=e.kind,
                knowledge_ref=f"{e.id}@{e.version}",
                digest=digest({"entry_digest": e.digest, "text": text, "kind": e.kind}),
            )
            db.execute(
                "INSERT INTO sources VALUES (?,?,?)",
                (sid, project_id, snapshot.model_dump_json()),
            )
            self.store.audit(
                db, project_id, "knowledge_context_selected", f"{e.id}@{e.version}"
            )
            return snapshot


def register_knowledge_routes(app: FastAPI, store: Store) -> None:
    knowledge = Knowledge(store)

    @app.post("/api/projects/{project_id}/knowledge", status_code=201)
    def create(project_id: str, body: KnowledgeInput) -> KnowledgeEntry:
        return knowledge.create(project_id, body)

    @app.get("/api/projects/{project_id}/knowledge")
    def entries(
        project_id: str,
        query: str = Query(default="", max_length=200),
        entity_type: Entity | None = None,
        include_archived: bool = False,
        limit: int = Query(default=20, ge=1, le=50),
    ) -> list[KnowledgeEntry]:
        return knowledge.entries(
            project_id, query.strip(), entity_type, limit, include_archived
        )

    @app.post("/api/projects/{project_id}/knowledge/{entry_id}/edits", status_code=201)
    def edit(project_id: str, entry_id: str, body: KnowledgeEdit) -> KnowledgeEntry:
        return knowledge.edit(project_id, entry_id, body)

    @app.post("/api/projects/{project_id}/knowledge/{entry_id}/verify", status_code=201)
    def verify(project_id: str, entry_id: str, body: VerifyKnowledge) -> KnowledgeEntry:
        return knowledge.verify(project_id, entry_id, body)

    @app.get("/api/projects/{project_id}/knowledge/{entry_id}/history")
    def history(
        project_id: str,
        entry_id: str,
        before: int = Query(default=2147483647, ge=1),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> list[KnowledgeEntry]:
        return knowledge.history(project_id, entry_id, before, limit)

    @app.post(
        "/api/projects/{project_id}/knowledge/{entry_id}/sources", status_code=201
    )
    def snapshot(project_id: str, entry_id: str, body: SnapshotRequest) -> Source:
        return knowledge.snapshot(project_id, entry_id, body)

    @app.get("/api/projects/{project_id}/context")
    def context(
        project_id: str,
        query: str = Query(default="", max_length=200),
        limit: int = Query(default=20, ge=1, le=50),
        budget_bytes: int = Query(default=32768, ge=1, le=65536),
    ) -> list[ContextItem]:
        return knowledge.context(project_id, query.strip(), limit, budget_bytes)

    @app.get("/api/projects/{project_id}/revisions")
    def revisions(
        project_id: str,
        before: int = Query(default=2147483647, ge=1),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> list[RevisionSummary]:
        with store.transaction() as db:
            store.require_project(db, project_id)
            return [
                RevisionSummary(
                    id=r["id"],
                    number=r["number"],
                    digest=r["digest"],
                    title=json.loads(r["data"])["artifact"]["title"],
                )
                for r in db.execute(
                    "SELECT id,number,digest,data FROM revisions WHERE project_id=? AND number<? ORDER BY number DESC LIMIT ?",
                    (project_id, before, limit),
                )
            ]
