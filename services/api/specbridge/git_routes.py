"""Git collaboration routes for targets, previews, publish receipts, and audits."""

from typing import Any, Literal

from fastapi import FastAPI

from .git_collaboration import (
    GitPublishPreview,
    GitPublishReceipt,
    GitService,
    GitTarget,
    StaleHeadError,
    extract_candidate_docs_files,
)
from .models import Model
from .publication import Publication
from .storage import Conflict, NotFound, Store


class GitTargetInput(Model):
    target_type: Literal["local", "github_mock"] = "local"
    repo_path: str | None = None
    remote_url: str | None = None
    base_branch: str = "main"
    docs_path: str = "docs"


class GitPreviewInput(Model):
    candidate_id: str
    proposed_branch: str | None = None


class GitPublishInput(Model):
    candidate_id: str
    approval_digest: str
    proposed_branch: str
    commit_message: str | None = None
    pr_title: str | None = None
    pr_body: str | None = None


def register_git_routes(
    app: FastAPI,
    store: Store,
    publication: Publication,
    git_service: GitService | None = None,
) -> None:
    service = git_service or GitService()

    @app.post("/api/projects/{project_id}/git/targets", status_code=200)
    def save_target(project_id: str, body: GitTargetInput) -> GitTarget:
        target = GitTarget(
            project_id=project_id,
            target_type=body.target_type,
            repo_path=body.repo_path,
            remote_url=body.remote_url,
            base_branch=body.base_branch,
            docs_path=body.docs_path,
        )
        return store.save_git_target(target)

    @app.get("/api/projects/{project_id}/git/targets")
    def get_target(project_id: str) -> GitTarget:
        target = store.get_git_target(project_id)
        if not target:
            raise NotFound("Git target not configured for this project")
        return target

    @app.post("/api/projects/{project_id}/git/preview")
    def preview(project_id: str, body: GitPreviewInput) -> GitPublishPreview:
        target = store.get_git_target(project_id)
        if not target:
            raise Conflict(
                "Configure a Git destination target before generating a preview"
            )

        with store.transaction() as db:
            candidate, row = publication._candidate(db, project_id, body.candidate_id)
            if not candidate.approved:
                raise Conflict(
                    "Candidate package must be approved before Git collaboration"
                )
            raw_zip = publication._verify(candidate, row)

        incoming_files = extract_candidate_docs_files(raw_zip, candidate.manifest)
        try:
            return service.prepare_candidate_preview(
                target=target,
                incoming_revision_id=candidate.revision_id,
                incoming_digest=candidate.digest,
                incoming_files=incoming_files,
                proposed_branch=body.proposed_branch,
            )
        except (ValueError, FileNotFoundError) as err:
            raise Conflict(str(err)) from err

    @app.post("/api/projects/{project_id}/git/publish", status_code=201)
    def publish(project_id: str, body: GitPublishInput) -> GitPublishReceipt:
        target = store.get_git_target(project_id)
        if not target:
            raise Conflict("Configure a Git destination target before publishing")

        with store.transaction() as db:
            candidate, row = publication._candidate(db, project_id, body.candidate_id)
            if not candidate.approved:
                raise Conflict(
                    "Candidate package must be approved before Git collaboration"
                )
            raw_zip = publication._verify(candidate, row)

        incoming_files = extract_candidate_docs_files(raw_zip, candidate.manifest)
        try:
            preview_obj = service.prepare_candidate_preview(
                target=target,
                incoming_revision_id=candidate.revision_id,
                incoming_digest=candidate.digest,
                incoming_files=incoming_files,
                proposed_branch=body.proposed_branch,
            )
        except (ValueError, FileNotFoundError) as err:
            raise Conflict(str(err)) from err

        if preview_obj.changeset_digest != body.approval_digest:
            raise Conflict(
                "approval_digest_mismatch: changeset has changed since preview"
            )

        if preview_obj.diff.has_conflicts:
            raise Conflict("cannot_publish_unresolved_conflicts")

        try:
            receipt = service.publish(
                preview=preview_obj,
                approval_digest=body.approval_digest,
                commit_message=body.commit_message,
                pr_title=body.pr_title,
                pr_body=body.pr_body,
            )
        except StaleHeadError as err:
            raise Conflict(f"stale_head: {err}") from err

        store.record_git_audit(
            project_id=project_id,
            action="publish",
            receipt=receipt,
            extra_data={
                "candidate_id": candidate.id,
                "revision_id": candidate.revision_id,
                "proposed_branch": body.proposed_branch,
            },
        )
        return receipt

    @app.get("/api/projects/{project_id}/git/audits")
    def list_audits(project_id: str) -> list[dict[str, Any]]:
        return store.list_git_audits(project_id)
