"""Git collaboration domain models and schemas."""

from typing import Literal

from pydantic import Field

from .models import Model


class GitTarget(Model):
    project_id: str
    target_type: Literal["local", "github_mock"] = "local"
    repo_path: str | None = None
    remote_url: str | None = None
    base_branch: str = "main"
    docs_path: str = "docs"


FileChangeType = Literal["added", "modified", "deleted", "unmodified", "conflict"]


class FileComparison(Model):
    path: str
    status: FileChangeType
    base_sha: str | None = None
    local_sha: str | None = None
    incoming_sha: str | None = None
    diff: str | None = None
    conflict_reason: str | None = None
    is_managed: bool = True


class ThreeWayDiff(Model):
    base_revision_id: str | None = None
    base_digest: str | None = None
    incoming_revision_id: str
    incoming_digest: str
    target_head_sha: str = ""
    changes: list[FileComparison] = Field(default_factory=list)
    has_conflicts: bool = False
    changeset_digest: str = ""


class GitPublishPreview(Model):
    target: GitTarget
    proposed_branch: str
    diff: ThreeWayDiff
    commit_message: str
    pr_title: str
    pr_body: str
    incoming_files: dict[str, bytes] = Field(default_factory=dict)
    changeset_digest: str


class GitPublishReceipt(Model):
    id: str
    project_id: str
    branch_name: str
    commit_sha: str
    pr_url: str | None = None
    pr_number: int | None = None
    changeset_digest: str
    timestamp: str
    status: Literal["published", "already_published"]


class StaleHeadError(Exception):
    """Raised when target branch HEAD moved after preview generation."""
