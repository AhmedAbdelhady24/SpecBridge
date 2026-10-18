from __future__ import annotations

import json
import sqlite3
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from .models import Artifact, Finding, Run, RunSummary, canonical, digest
from .storage import Conflict, NotFound, Store

if TYPE_CHECKING:
    from .providers import Provider
    from .skills import SkillRegistry


STAGES = (
    "intake",
    "context_retrieval",
    "skill_selection",
    "plan",
    "execute",
    "validate",
    "human_review",
    "publish",
)
LEASE_SECONDS = 120
HEARTBEAT_SECONDS = 30


class RetryAcknowledgmentRequired(Conflict):
    pass


class Workflow:
    def __init__(self, store: Store, registry: SkillRegistry, provider: Provider):
        self.store = store
        self.registry = registry
        self.provider = provider

    def start(
        self,
        project_id: str,
        source_ids: list[str],
        intent: str,
        skill_id: str,
        acknowledged_destination: str,
    ) -> Run:
        self.store.sources(project_id, source_ids)
        self.registry.load(skill_id)
        if self.provider.destination != acknowledged_destination:
            raise Conflict("Acknowledge the currently configured provider destination")
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT digest FROM revisions WHERE project_id=? ORDER BY number DESC LIMIT 1",
                (project_id,),
            ).fetchone()
            run = Run(
                id=str(uuid4()),
                project_id=project_id,
                source_ids=source_ids,
                skill_id=skill_id,
                intent=intent,
                destination=acknowledged_destination,
                stage="intake",
                base_digest=row[0] if row else None,
            )
            db.execute(
                "INSERT INTO runs(id,project_id,data) VALUES (?,?,?)",
                (run.id, project_id, run.model_dump_json()),
            )
            self.store.audit(db, project_id, "workflow_created", run.id)
            return run

    def get(self, project_id: str, run_id: str) -> Run:
        with self.store.transaction() as db:
            run, row = self._row(db, project_id, run_id)
            if run.status == "running" and row["lease_until"] < time.time():
                return run.model_copy(
                    update={
                        "status": "failed",
                        "error": "interrupted_retry_may_repeat_billing",
                    }
                )
            return run

    def list_runs(self, project_id: str) -> list[RunSummary]:
        with self.store.transaction() as db:
            self.store.require_project(db, project_id)
            ids = [
                row[0]
                for row in db.execute(
                    "SELECT id FROM runs WHERE project_id=? ORDER BY rowid DESC",
                    (project_id,),
                )
            ]
            revisions = {
                row["id"]: (row["title"], row["number"])
                for row in db.execute(
                    "SELECT DISTINCT r.id,r.number,json_extract(r.data,'$.artifact.title') AS title "
                    "FROM revisions r JOIN runs w "
                    "ON r.id=json_extract(w.data,'$.revision_id') AND w.project_id=r.project_id "
                    "WHERE r.project_id=?",
                    (project_id,),
                )
            }
            creation_times = {
                row["subject"]: row["at"]
                for row in db.execute(
                    "SELECT a.subject,a.at FROM audit a JOIN "
                    "(SELECT min(id) AS first_id FROM audit "
                    "WHERE project_id=? AND action='workflow_created' GROUP BY subject) first "
                    "ON a.id=first.first_id",
                    (project_id,),
                )
            }
        summaries = []
        for run_id in ids:
            # Keep the existing expired-lease presentation and its lack of writes.
            run = self.get(project_id, run_id)
            title, revision_number = revisions.get(run.revision_id, (run.intent, None))
            created = creation_times.get(run_id)
            created_at = None
            if created:
                # SQLite CURRENT_TIMESTAMP records UTC without a timezone suffix.
                created_at = (
                    datetime.fromisoformat(created)
                    .replace(tzinfo=UTC)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
            summaries.append(
                RunSummary(
                    **run.model_dump(),
                    title=title,
                    revision_number=revision_number,
                    created_at=created_at,
                )
            )
        return summaries

    @staticmethod
    def _row(
        db: sqlite3.Connection, project_id: str, run_id: str
    ) -> tuple[Run, sqlite3.Row]:
        row = db.execute(
            "SELECT * FROM runs WHERE project_id=? AND id=?", (project_id, run_id)
        ).fetchone()
        if not row:
            raise NotFound("Workflow not found")
        return Run.model_validate_json(row["data"]), row

    def _renew_lease(self, run_id: str, lease: str) -> bool:
        with self.store.transaction() as db:
            now = time.time()
            return (
                db.execute(
                    "UPDATE runs SET lease_until=? WHERE id=? AND lease=? AND lease_until>?",
                    (now + LEASE_SECONDS, run_id, lease, now),
                ).rowcount
                == 1
            )

    @contextmanager
    def _maintain_lease(self, run_id: str, lease: str) -> Iterator[None]:
        stop = threading.Event()
        failed = threading.Event()

        def renew() -> None:
            while not stop.wait(HEARTBEAT_SECONDS):
                try:
                    if self._renew_lease(run_id, lease):
                        continue
                except Exception:  # noqa: BLE001 -- Fail closed without retaining secret exception text.
                    failed.set()
                    return
                failed.set()
                return

        heartbeat = threading.Thread(
            target=renew, name=f"specbridge-lease-{run_id}", daemon=True
        )
        heartbeat.start()
        try:
            yield
        finally:
            stop.set()
            heartbeat.join()
        if failed.is_set():
            raise Conflict("Workflow lease renewal failed; this result was discarded")

    def advance(
        self, project_id: str, run_id: str, *, retry_acknowledged: bool = False
    ) -> Run:
        lease = str(uuid4())
        with self.store.transaction() as db:
            run, row = self._row(db, project_id, run_id)
            if run.stage == "execute" and run.destination != self.provider.destination:
                raise Conflict("Provider destination changed; create a new run")
            if run.stage in ("human_review", "publish"):
                raise Conflict("Review and publication require explicit user actions")
            if row["lease"] and row["lease_until"] > time.time():
                raise Conflict("A workflow stage is already running")
            if (run.status == "failed" or row["lease"]) and not retry_acknowledged:
                raise RetryAcknowledgmentRequired(
                    "Retry may repeat a billable provider call; acknowledge explicitly"
                )
            if run.attempts >= 3 and run.stage == "execute":
                raise Conflict("Provider attempt limit reached; create a new run")
            run.status = "running"
            run.error = None
            if run.stage == "execute":
                run.attempts += 1
            db.execute(
                "UPDATE runs SET data=?,lease=?,lease_until=? WHERE id=?",
                (run.model_dump_json(), lease, time.time() + LEASE_SECONDS, run.id),
            )

        try:
            sources = self.store.sources(project_id, run.source_ids)
            payload: object = {}
            if run.stage == "context_retrieval":
                payload = {s.id: s.digest for s in sources}
            elif run.stage == "skill_selection":
                skill = self.registry.load(run.skill_id)
                payload = {"skill": skill.name, "digest": skill.digest}
            elif run.stage == "plan":
                payload = {
                    "stages": list(STAGES),
                    "provider": self.provider.model,
                    "destination": run.destination,
                }
            elif run.stage == "execute":
                skill = self.registry.load(run.skill_id, with_output_contract=True)
                with self.store.transaction() as db:
                    selected = db.execute(
                        "SELECT data FROM checkpoints WHERE run_id=? AND stage='skill_selection'",
                        (run.id,),
                    ).fetchone()
                    if not selected or selected[0] != canonical(
                        {"skill": skill.name, "digest": skill.digest}
                    ):
                        raise Conflict("Runtime skill changed; create a new run")
                generation_provenance = {
                    "skill": skill.name,
                    "skill_digest": skill.digest,
                    "skill_instructions_digest": digest(skill.body),
                    "provider": self.provider.mode,
                    "model": self.provider.model,
                    "destination": self.provider.destination,
                    "sources": canonical({s.id: s.digest for s in sources}),
                    "run_id": run.id,
                }
                with self._maintain_lease(run.id, lease):
                    artifact = self.provider.generate(skill=skill, sources=sources)
                selected_ids = {s.id for s in sources}
                if any(
                    set(item.source_ids) - selected_ids
                    for item in artifact.statements()
                ):
                    raise ValueError("Output cites context not selected for this run")
                payload = {
                    "artifact": artifact.model_dump(),
                    "provenance": generation_provenance,
                }
            with self.store.transaction() as db:
                _, current_row = self._row(db, project_id, run_id)
                if (
                    current_row["lease"] != lease
                    or current_row["lease_until"] <= time.time()
                ):
                    raise Conflict("Workflow lease changed; this result was discarded")
                if run.stage == "validate":
                    draft = db.execute(
                        "SELECT data FROM checkpoints WHERE run_id=? AND stage='execute'",
                        (run.id,),
                    ).fetchone()
                    if not draft:
                        raise Conflict("Generation checkpoint is missing")
                    checkpoint = json.loads(draft[0])
                    artifact = Artifact.model_validate(checkpoint["artifact"])
                    findings = self.findings(artifact)
                    revision = self.store.save_revision(
                        project_id,
                        artifact,
                        run.base_digest,
                        provenance=checkpoint["provenance"],
                        findings=findings,
                        connection=db,
                    )
                    run.revision_id = revision.id
                    payload = {"revision_id": revision.id}
                db.execute(
                    "INSERT INTO checkpoints VALUES (?,?,?)",
                    (run.id, run.stage, canonical(payload)),
                )
                run.history.append(run.stage)
                run.stage = STAGES[STAGES.index(run.stage) + 1]
                run.status = "review" if run.stage == "human_review" else "ready"
                db.execute(
                    "UPDATE runs SET data=?,lease=NULL,lease_until=NULL WHERE id=?",
                    (run.model_dump_json(), run.id),
                )
                return run
        except Exception:  # noqa: BLE001 -- Persist failures without potentially secret exception text.
            with self.store.transaction() as db:
                _, current_row = self._row(db, project_id, run_id)
                if current_row["lease"] != lease:
                    raise Conflict("Workflow result lost its lease") from None
                run.status = "failed"
                run.error = (
                    "generation_failed" if run.stage == "execute" else "stage_failed"
                )
                db.execute(
                    "UPDATE runs SET data=?,lease=NULL,lease_until=NULL WHERE id=?",
                    (run.model_dump_json(), run.id),
                )
                self.store.audit(db, project_id, run.error, run.id)
                return run

    @staticmethod
    def findings(artifact: Artifact) -> list[Finding]:
        findings = []
        normalized = [
            " ".join(story.text.casefold().split()) for story in artifact.stories
        ]
        if len(set(normalized)) != len(normalized):
            findings.append(
                Finding(
                    code="duplicate_story",
                    message="Some stories have identical normalized text; review before approving",
                )
            )
        if artifact.open_questions:
            findings.append(
                Finding(
                    code="open_questions",
                    message="Unresolved questions remain; review them explicitly",
                )
            )
        if not artifact.scope:
            findings.append(
                Finding(
                    code="missing_scope",
                    message="Define scope before engineering handoff",
                )
            )
        return findings
