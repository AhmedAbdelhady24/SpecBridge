import hashlib
import json
import sqlite3
from io import BytesIO
from pathlib import Path
from typing import Literal
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from .models import Candidate, Review, Run, canonical, digest
from .publisher import hashes, render_package, template_digest
from .storage import Conflict, NotFound, Store


class Publication:
    def __init__(self, store: Store, template_root: Path):
        self.store = store
        self.template_root = template_root

    def reviews(self, project_id: str, revision_id: str) -> list[Review]:
        self.store.get_revision(project_id, revision_id)
        with self.store.transaction() as db:
            return [
                Review(**dict(row))
                for row in db.execute(
                    "SELECT * FROM reviews WHERE project_id=? AND revision_id=? ORDER BY rowid",
                    (project_id, revision_id),
                )
            ]

    def review(
        self,
        project_id: str,
        revision_id: str,
        disposition: Literal["reviewed", "rejected"],
        notes: str,
    ) -> Review:
        self.store.get_revision(project_id, revision_id)
        review = Review(
            id=str(uuid4()),
            project_id=project_id,
            revision_id=revision_id,
            disposition=disposition,
            notes=notes,
        )
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO reviews VALUES (?,?,?,?,?)",
                (review.id, project_id, revision_id, disposition, notes),
            )
            db.execute(
                "DELETE FROM approvals WHERE candidate_id IN (SELECT id FROM candidates WHERE project_id=? AND revision_id=?)",
                (project_id, revision_id),
            )
            self.store.audit(db, project_id, "human_" + disposition, revision_id)
        return review

    def prepare(self, project_id: str, revision_id: str) -> Candidate:
        revision = self.store.get_revision(project_id, revision_id)
        provenance = {
            **revision.provenance,
            "revision_id": revision.id,
            "revision_number": str(revision.number),
            "artifact_digest": revision.digest,
        }
        ids = sorted(
            {
                key
                for statement in revision.artifact.statements()
                for key in statement.source_ids
            }
        )
        if ids:
            provenance["source_texts"] = canonical(
                {
                    source.id: source.text
                    for source in self.store.sources(project_id, ids)
                }
            )
        package = render_package(revision.artifact, provenance, self.template_root)
        with self.store.transaction() as db:
            self._current(db, project_id, revision_id)
            existing = db.execute(
                "SELECT id FROM candidates WHERE digest=? AND project_id=?",
                (package.digest, project_id),
            ).fetchone()
            candidate_id = existing[0] if existing else str(uuid4())
            if not existing:
                db.execute(
                    "INSERT INTO candidates(id,project_id,revision_id,digest,template_digest,manifest,zip) VALUES (?,?,?,?,?,?,?)",
                    (
                        candidate_id,
                        project_id,
                        revision_id,
                        package.digest,
                        package.template_digest,
                        canonical(package.manifest),
                        package.zip_bytes,
                    ),
                )
                self.store.audit(db, project_id, "candidate_prepared", candidate_id)
            return self._candidate(db, project_id, candidate_id)[0]

    @staticmethod
    def _current(db: sqlite3.Connection, project_id: str, revision_id: str) -> None:
        row = db.execute(
            "SELECT id FROM revisions WHERE project_id=? ORDER BY number DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        if not row or row[0] != revision_id:
            raise Conflict("A newer revision exists; prepare and review that revision")

    @staticmethod
    def _candidate(
        db: sqlite3.Connection, project_id: str, candidate_id: str
    ) -> tuple[Candidate, sqlite3.Row]:
        row = db.execute(
            "SELECT * FROM candidates WHERE project_id=? AND id=?",
            (project_id, candidate_id),
        ).fetchone()
        if not row:
            raise NotFound("Candidate not found")
        approval = db.execute(
            "SELECT 1 FROM approvals WHERE candidate_id=? AND digest=?",
            (candidate_id, row["digest"]),
        ).fetchone()
        return Candidate(
            id=row["id"],
            project_id=project_id,
            revision_id=row["revision_id"],
            digest=row["digest"],
            template_digest=row["template_digest"],
            manifest=json.loads(row["manifest"]),
            approved=bool(approval),
        ), row

    @staticmethod
    def _reviewed(db: sqlite3.Connection, candidate: Candidate) -> None:
        row = db.execute(
            "SELECT disposition FROM reviews WHERE project_id=? AND revision_id=? ORDER BY rowid DESC LIMIT 1",
            (candidate.project_id, candidate.revision_id),
        ).fetchone()
        if not row or row[0] != "reviewed":
            raise Conflict("Record human review of this revision before approval")

    @staticmethod
    def _verify(candidate: Candidate, row: sqlite3.Row) -> bytes:
        raw = row["zip"]
        if not isinstance(raw, bytes) or len(raw) > 20 * 1024 * 1024:
            raise Conflict("Stored package integrity check failed")
        try:
            with ZipFile(BytesIO(raw)) as archive:
                infos = archive.infolist()
                if (
                    sum(info.file_size for info in infos) > 20 * 1024 * 1024
                    or len(infos) != len(candidate.manifest)
                    or set(archive.namelist()) != set(candidate.manifest)
                ):
                    raise ValueError("Invalid package entries")
                files = {name: archive.read(name) for name in candidate.manifest}
                if hashes(files) != candidate.manifest:
                    raise ValueError("Package manifest mismatch")
                provenance = json.loads(files["revision.json"])["provenance"]
                expected = digest(
                    {
                        "template": candidate.template_digest,
                        "files": candidate.manifest,
                        "provenance": provenance,
                        "zip": hashlib.sha256(raw).hexdigest(),
                    }
                )
                if expected != candidate.digest:
                    raise ValueError("Package digest mismatch")
                return raw
        except (
            BadZipFile,
            ValueError,
            KeyError,
            TypeError,
            RuntimeError,
            RecursionError,
        ):
            raise Conflict("Stored package integrity check failed") from None

    def approve(
        self, project_id: str, candidate_id: str, expected_digest: str
    ) -> Candidate:
        with self.store.transaction() as db:
            active = template_digest(self.template_root)
            candidate, row = self._candidate(db, project_id, candidate_id)
            self._current(db, project_id, candidate.revision_id)
            self._reviewed(db, candidate)
            if (
                expected_digest != candidate.digest
                or active != candidate.template_digest
            ):
                raise Conflict("Package preview changed; prepare and review again")
            self._verify(candidate, row)
            if not candidate.approved:
                db.execute(
                    "INSERT INTO approvals VALUES (?,?)",
                    (candidate_id, expected_digest),
                )
                self.store.audit(db, project_id, "human_approved", candidate_id)
            return candidate.model_copy(update={"approved": True})

    def download(self, project_id: str, candidate_id: str) -> bytes:
        with self.store.transaction() as db:
            active = template_digest(self.template_root)
            candidate, row = self._candidate(db, project_id, candidate_id)
            self._current(db, project_id, candidate.revision_id)
            self._reviewed(db, candidate)
            if not candidate.approved or active != candidate.template_digest:
                raise Conflict("Approve the current package before downloading")
            raw = self._verify(candidate, row)
            for item in db.execute(
                "SELECT id,data FROM runs WHERE project_id=?", (project_id,)
            ).fetchall():
                run = Run.model_validate_json(item["data"])
                if (
                    run.revision_id == candidate.revision_id
                    and run.status != "published"
                ):
                    run.stage = "publish"
                    run.status = "published"
                    run.history = [*run.history, "human_review", "publish"]
                    db.execute(
                        "UPDATE runs SET data=? WHERE id=?",
                        (run.model_dump_json(), run.id),
                    )
            self.store.audit(db, project_id, "package_downloaded", candidate_id)
            return raw
