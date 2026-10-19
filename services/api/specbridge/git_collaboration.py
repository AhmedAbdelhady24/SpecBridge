"""Git collaboration domain model, three-way comparison engine, local Git operations, and mock remote adapters."""

import difflib
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4
from zipfile import ZipFile

from pydantic import Field

from .models import Model, canonical, digest


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


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


def extract_candidate_docs_files(
    raw_zip: bytes, manifest: dict[str, str]
) -> dict[str, bytes]:
    """Extract markdown documentation and snapshot files from an approved candidate zip."""
    docs_files: dict[str, bytes] = {}
    with ZipFile(BytesIO(raw_zip)) as archive:
        for name in manifest:
            if name.startswith("src/content/docs/"):
                base_name = name.removeprefix("src/content/docs/")
                content = archive.read(name)
                docs_files[base_name] = content
                if base_name == "index.md" and "README.md" not in docs_files:
                    docs_files["README.md"] = content
            elif name in ("README.md", "revision.json"):
                docs_files[name] = archive.read(name)
    return docs_files


def _compute_text_diff(
    old_bytes: bytes | None, new_bytes: bytes | None, filename: str
) -> str | None:
    if old_bytes == new_bytes:
        return None
    old_lines = (
        old_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
        if old_bytes
        else []
    )
    new_lines = (
        new_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
        if new_bytes
        else []
    )
    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
    return "".join(diff_lines) if diff_lines else None


def three_way_compare(
    base_files: dict[str, bytes],
    local_files: dict[str, bytes],
    incoming_files: dict[str, bytes],
    managed_paths: set[str],
    base_revision_id: str | None = None,
    base_digest: str | None = None,
    incoming_revision_id: str = "rev-incoming",
    incoming_digest: str = "digest-incoming",
    target_head_sha: str = "",
) -> ThreeWayDiff:
    """Perform three-way comparison between Base, Local (target branch), and Incoming package."""
    all_paths = sorted(
        set(base_files.keys()) | set(local_files.keys()) | set(incoming_files.keys())
    )
    comparisons: list[FileComparison] = []
    has_conflicts = False

    for path in all_paths:
        base_bytes = base_files.get(path)
        local_bytes = local_files.get(path)
        incoming_bytes = incoming_files.get(path)

        base_sha = _sha256(base_bytes) if base_bytes is not None else None
        local_sha = _sha256(local_bytes) if local_bytes is not None else None
        incoming_sha = _sha256(incoming_bytes) if incoming_bytes is not None else None

        is_managed = (path in managed_paths) or (path in incoming_files)

        # 1. Unmanaged file in local working tree
        if not is_managed:
            comparisons.append(
                FileComparison(
                    path=path,
                    status="unmodified",
                    base_sha=base_sha,
                    local_sha=local_sha,
                    incoming_sha=incoming_sha,
                    diff=None,
                    conflict_reason=None,
                    is_managed=False,
                )
            )
            continue

        # 2. File in base, but deleted by developer locally
        if base_bytes is not None and local_bytes is None:
            if incoming_bytes is not None and incoming_sha != base_sha:
                # Developer deleted file, but incoming modified it
                has_conflicts = True
                comparisons.append(
                    FileComparison(
                        path=path,
                        status="conflict",
                        base_sha=base_sha,
                        local_sha=None,
                        incoming_sha=incoming_sha,
                        diff=_compute_text_diff(base_bytes, incoming_bytes, path),
                        conflict_reason="developer_deleted_file",
                        is_managed=True,
                    )
                )
            else:
                # Both deleted or incoming did not touch it
                comparisons.append(
                    FileComparison(
                        path=path,
                        status="deleted",
                        base_sha=base_sha,
                        local_sha=None,
                        incoming_sha=incoming_sha,
                        diff=None,
                        conflict_reason=None,
                        is_managed=True,
                    )
                )
            continue

        # 3. File not in base (newly added)
        if base_bytes is None:
            if incoming_bytes is not None and local_bytes is None:
                # Clean addition from incoming
                comparisons.append(
                    FileComparison(
                        path=path,
                        status="added",
                        base_sha=None,
                        local_sha=None,
                        incoming_sha=incoming_sha,
                        diff=_compute_text_diff(None, incoming_bytes, path),
                        conflict_reason=None,
                        is_managed=True,
                    )
                )
            elif incoming_bytes is not None and local_bytes is not None:
                if local_sha == incoming_sha:
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="unmodified",
                            base_sha=None,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=None,
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                else:
                    # Developer created file with same path but different content
                    has_conflicts = True
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="conflict",
                            base_sha=None,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=_compute_text_diff(local_bytes, incoming_bytes, path),
                            conflict_reason="concurrent_creation",
                            is_managed=True,
                        )
                    )
            else:
                # Local unmanaged file
                comparisons.append(
                    FileComparison(
                        path=path,
                        status="unmodified",
                        base_sha=None,
                        local_sha=local_sha,
                        incoming_sha=None,
                        diff=None,
                        conflict_reason=None,
                        is_managed=False,
                    )
                )
            continue

        # 4. File in base and in local
        if base_bytes is not None and local_bytes is not None:
            if incoming_bytes is None:
                # Incoming package deleted this file
                if local_sha != base_sha:
                    has_conflicts = True
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="conflict",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=None,
                            diff=_compute_text_diff(local_bytes, None, path),
                            conflict_reason="modified_deleted_conflict",
                            is_managed=True,
                        )
                    )
                else:
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="deleted",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=None,
                            diff=_compute_text_diff(base_bytes, None, path),
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                continue

            # Path is present in base, local, and incoming
            if local_sha == base_sha:
                if incoming_sha == base_sha:
                    # Unmodified by both
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="unmodified",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=None,
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                else:
                    # Clean update from incoming
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="modified",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=_compute_text_diff(local_bytes, incoming_bytes, path),
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
            else:
                # Developer modified local file
                if incoming_sha == base_sha:
                    # Developer's edit preserved untouched
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="unmodified",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=None,
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                elif local_sha == incoming_sha:
                    # Both made identical modification
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="unmodified",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=None,
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                else:
                    # Concurrent conflicting edit!
                    has_conflicts = True
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="conflict",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=_compute_text_diff(local_bytes, incoming_bytes, path),
                            conflict_reason="concurrent_modification",
                            is_managed=True,
                        )
                    )

    # Compute deterministic changeset digest
    summary = {
        "base_revision_id": base_revision_id,
        "base_digest": base_digest,
        "incoming_revision_id": incoming_revision_id,
        "incoming_digest": incoming_digest,
        "target_head_sha": target_head_sha,
        "changes": [c.model_dump() for c in comparisons],
    }
    changeset_digest = digest(summary)

    return ThreeWayDiff(
        base_revision_id=base_revision_id,
        base_digest=base_digest,
        incoming_revision_id=incoming_revision_id,
        incoming_digest=incoming_digest,
        target_head_sha=target_head_sha,
        changes=comparisons,
        has_conflicts=has_conflicts,
        changeset_digest=changeset_digest,
    )


class MockGitHubAdapter:
    """In-memory mock adapter for GitHub pull requests and repository state."""

    def __init__(self) -> None:
        self.repos: dict[str, dict[str, str]] = {}  # repo -> {branch: head_sha}
        self.files: dict[
            str, dict[str, dict[str, bytes]]
        ] = {}  # repo -> {branch: {path: content}}
        self.pull_requests: dict[
            str, list[dict[str, Any]]
        ] = {}  # repo -> list of PR dicts
        self.audit_log: dict[str, list[dict[str, Any]]] = {}

    def _repo_key(self, repo_url_or_name: str) -> str:
        s = repo_url_or_name.strip()
        s = s.removesuffix(".git")
        if "github.com/" in s:
            s = s.split("github.com/")[-1]
        return s

    def create_repository(self, repo: str, default_branch: str = "main") -> None:
        key = self._repo_key(repo)
        self.repos[key] = {default_branch: "sha-0000"}
        self.files[key] = {default_branch: {}}
        self.pull_requests[key] = []
        self.audit_log[key] = []

    def seed_branch_files(
        self, repo: str, branch: str, files: dict[str, bytes]
    ) -> None:
        key = self._repo_key(repo)
        if key not in self.repos:
            self.create_repository(key, default_branch=branch)
        self.files[key][branch] = dict(files)
        # Update head SHA
        content_hash = _sha256(
            canonical({k: _sha256(v) for k, v in sorted(files.items())}).encode()
        )
        self.repos[key][branch] = content_hash

    def get_branch_head(self, repo: str, branch: str) -> str:
        key = self._repo_key(repo)
        if key not in self.repos:
            self.create_repository(key, default_branch=branch)
        if branch not in self.repos[key]:
            self.repos[key][branch] = "sha-0000"
            self.files[key][branch] = {}
        return self.repos[key][branch]

    def get_branch_files(self, repo: str, branch: str) -> dict[str, bytes]:
        key = self._repo_key(repo)
        if key not in self.files or branch not in self.files[key]:
            return {}
        return dict(self.files[key][branch])

    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
        files: dict[str, bytes],
    ) -> dict[str, Any]:
        key = self._repo_key(repo)
        if key not in self.repos:
            self.create_repository(key, default_branch=base_branch)

        commit_sha = _sha256(
            canonical({k: _sha256(v) for k, v in sorted(files.items())}).encode()
        )
        self.repos[key][head_branch] = commit_sha
        self.files[key][head_branch] = dict(files)

        pr_number = len(self.pull_requests[key]) + 1
        pr_record = {
            "number": pr_number,
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "url": f"https://github.com/{key}/pull/{pr_number}",
            "commit_sha": commit_sha,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.pull_requests[key].append(pr_record)
        self.audit_log[key].append(
            {
                "action": "create_pull_request",
                "pr_number": pr_number,
                "head": head_branch,
                "commit_sha": commit_sha,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        return pr_record

    def get_audit_log(self, repo: str) -> list[dict[str, Any]]:
        key = self._repo_key(repo)
        return list(self.audit_log.get(key, []))


class GitService:
    """Manages Git target comparisons, previews, local git branch creation and remote PRs."""

    def __init__(self, remote_adapter: MockGitHubAdapter | None = None):
        self.remote_adapter = remote_adapter or MockGitHubAdapter()
        self.published_receipts: dict[
            str, GitPublishReceipt
        ] = {}  # changeset_digest -> receipt

    def _read_local_repo_files(
        self, repo_path: Path, docs_path: str
    ) -> tuple[str, dict[str, bytes]]:
        # Get HEAD commit SHA
        head_proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        head_sha = head_proc.stdout.strip()

        # Read files in docs_path
        target_dir = repo_path / docs_path
        files: dict[str, bytes] = {}
        if target_dir.exists():
            for item in target_dir.rglob("*"):
                if item.is_file() and not any(
                    p.name.startswith(".") for p in item.parents
                ):
                    rel = str(item.relative_to(target_dir))
                    files[rel] = item.read_bytes()
        return head_sha, files

    def prepare_candidate_preview(
        self,
        target: GitTarget,
        incoming_revision_id: str,
        incoming_digest: str,
        incoming_files: dict[str, bytes],
        proposed_branch: str | None = None,
    ) -> GitPublishPreview:
        """Inspect target branch for previous SpecBridge snapshot and prepare three-way preview."""
        base_manifest: dict[str, str] = {}
        base_revision_id: str | None = None
        base_digest: str | None = None

        if target.target_type == "local":
            if not target.repo_path:
                raise ValueError("local_target_requires_repo_path")
            repo_path = Path(target.repo_path)
            docs_dir = repo_path / target.docs_path
            snapshot_path = docs_dir / ".specbridge-snapshot.json"
            if snapshot_path.exists():
                try:
                    snapshot = json.loads(snapshot_path.read_text())
                    base_manifest = snapshot.get("manifest", {})
                    base_revision_id = snapshot.get("revision_id")
                    base_digest = snapshot.get("revision_digest")
                except (json.JSONDecodeError, OSError):
                    pass
        else:
            if not target.remote_url:
                raise ValueError("remote_target_requires_remote_url")
            prefix = (
                f"{target.docs_path}/"
                if target.docs_path and target.docs_path != "."
                else ""
            )
            all_files = self.remote_adapter.get_branch_files(
                target.remote_url, target.base_branch
            )
            snap_raw = all_files.get(f"{prefix}.specbridge-snapshot.json")
            if snap_raw:
                try:
                    snapshot = json.loads(snap_raw.decode("utf-8"))
                    base_manifest = snapshot.get("manifest", {})
                    base_revision_id = snapshot.get("revision_id")
                    base_digest = snapshot.get("revision_digest")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

        branch = proposed_branch or f"specbridge/{incoming_revision_id}"
        return self.prepare_preview(
            target=target,
            base_revision_id=base_revision_id,
            base_digest=base_digest,
            base_manifest=base_manifest,
            incoming_revision_id=incoming_revision_id,
            incoming_digest=incoming_digest,
            incoming_files=incoming_files,
            proposed_branch=branch,
        )

    def prepare_preview(
        self,
        target: GitTarget,
        base_revision_id: str | None,
        base_digest: str | None,
        base_manifest: dict[str, str],
        incoming_revision_id: str,
        incoming_digest: str,
        incoming_files: dict[str, bytes],
        proposed_branch: str,
    ) -> GitPublishPreview:
        """Create a full reviewable three-way diff preview for Git collaboration."""
        if target.target_type == "local":
            if not target.repo_path:
                raise ValueError("local_target_requires_repo_path")
            repo_path = Path(target.repo_path)
            head_sha, local_files = self._read_local_repo_files(
                repo_path, target.docs_path
            )
        else:
            if not target.remote_url:
                raise ValueError("remote_target_requires_remote_url")
            head_sha = self.remote_adapter.get_branch_head(
                target.remote_url, target.base_branch
            )
            all_branch_files = self.remote_adapter.get_branch_files(
                target.remote_url, target.base_branch
            )
            prefix = (
                f"{target.docs_path}/"
                if target.docs_path and target.docs_path != "."
                else ""
            )
            local_files = {
                (k[len(prefix) :] if prefix and k.startswith(prefix) else k): v
                for k, v in all_branch_files.items()
                if not prefix or k.startswith(prefix)
            }

        # If no base_manifest supplied (initial publish), adopt existing files that intersect with incoming
        effective_base_manifest = dict(base_manifest)
        if not effective_base_manifest:
            effective_base_manifest = {
                path: _sha256(local_files[path])
                for path in local_files
                if path in incoming_files
            }

        # Build base_files representation from effective_base_manifest & local_files
        base_files: dict[str, bytes] = {}
        for path, sha in effective_base_manifest.items():
            if path in local_files and _sha256(local_files[path]) == sha:
                base_files[path] = local_files[path]
            elif path in incoming_files and _sha256(incoming_files[path]) == sha:
                base_files[path] = incoming_files[path]
            else:
                # If neither local nor incoming has exact base, record placeholder to detect deletion/diff
                base_files[path] = b""

        diff = three_way_compare(
            base_files=base_files,
            local_files=local_files,
            incoming_files=incoming_files,
            managed_paths=set(effective_base_manifest.keys()),
            base_revision_id=base_revision_id,
            base_digest=base_digest,
            incoming_revision_id=incoming_revision_id,
            incoming_digest=incoming_digest,
            target_head_sha=head_sha,
        )

        commit_msg = f"docs: update specifications ({incoming_revision_id})"
        pr_title = f"docs: update requirements from SpecBridge ({incoming_revision_id})"
        pr_body = (
            f"Automated documentation update from SpecBridge revision `{incoming_revision_id}`.\n"
            f"Base revision: `{base_revision_id or 'none'}`.\n"
            f"Changeset digest: `{diff.changeset_digest}`."
        )

        preview_summary = {
            "target": target.model_dump(),
            "proposed_branch": proposed_branch,
            "diff_digest": diff.changeset_digest,
            "has_conflicts": diff.has_conflicts,
        }
        changeset_digest = digest(preview_summary)

        return GitPublishPreview(
            target=target,
            proposed_branch=proposed_branch,
            diff=diff,
            commit_message=commit_msg,
            pr_title=pr_title,
            pr_body=pr_body,
            incoming_files=incoming_files,
            changeset_digest=changeset_digest,
        )

    def publish(
        self,
        preview: GitPublishPreview,
        approval_digest: str,
        commit_message: str | None = None,
        pr_title: str | None = None,
        pr_body: str | None = None,
    ) -> GitPublishReceipt:
        """Execute Git publish after explicit human approval matching preview changeset digest."""
        if approval_digest != preview.changeset_digest:
            raise ValueError("approval_digest_mismatch")

        if preview.diff.has_conflicts:
            raise ValueError("cannot_publish_unresolved_conflicts")

        # Idempotency check
        if preview.changeset_digest in self.published_receipts:
            existing = self.published_receipts[preview.changeset_digest]
            return GitPublishReceipt(
                id=existing.id,
                project_id=existing.project_id,
                branch_name=existing.branch_name,
                commit_sha=existing.commit_sha,
                pr_url=existing.pr_url,
                pr_number=existing.pr_number,
                changeset_digest=existing.changeset_digest,
                timestamp=existing.timestamp,
                status="already_published",
            )

        target = preview.target
        msg = commit_message or preview.commit_message

        if target.target_type == "local":
            repo_path = Path(target.repo_path)  # type: ignore[arg-type]

            # Verify target branch hasn't moved (stale head check)
            head_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
            current_head = head_proc.stdout.strip()
            if current_head != preview.diff.target_head_sha:
                raise StaleHeadError(
                    f"Target branch '{target.base_branch}' moved from {preview.diff.target_head_sha} to {current_head}."
                )

            # Create or checkout the proposed branch
            subprocess.run(
                ["git", "checkout", "-B", preview.proposed_branch, target.base_branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            # Apply changes into target docs_path
            docs_dir = repo_path / target.docs_path
            docs_dir.mkdir(parents=True, exist_ok=True)

            for change in preview.diff.changes:
                if not change.is_managed or change.status == "unmodified":
                    continue
                file_path = docs_dir / change.path
                if change.status in ("added", "modified"):
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    content = preview.incoming_files.get(change.path)
                    if content is not None:
                        file_path.write_bytes(content)
                elif change.status == "deleted":
                    if file_path.exists():
                        file_path.unlink()

            # Record snapshot manifest inside the branch
            manifest_path = docs_dir / ".specbridge-snapshot.json"
            snapshot_manifest = {
                change.path: change.incoming_sha
                for change in preview.diff.changes
                if change.is_managed
                and change.status != "deleted"
                and change.incoming_sha
            }
            snapshot_data = {
                "revision_id": preview.diff.incoming_revision_id,
                "revision_digest": preview.diff.incoming_digest,
                "changeset_digest": preview.changeset_digest,
                "manifest": snapshot_manifest,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            manifest_path.write_text(canonical(snapshot_data) + "\n")

            # Stage docs_dir and commit
            subprocess.run(
                ["git", "add", target.docs_path],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            new_sha_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
            commit_sha = new_sha_proc.stdout.strip()

            receipt = GitPublishReceipt(
                id=str(uuid4()),
                project_id=target.project_id,
                branch_name=preview.proposed_branch,
                commit_sha=commit_sha,
                pr_url=None,
                pr_number=None,
                changeset_digest=preview.changeset_digest,
                timestamp=datetime.now(UTC).isoformat(),
                status="published",
            )
        else:
            # Remote mock GitHub adapter
            if not target.remote_url:
                raise ValueError("remote_target_requires_remote_url")
            remote_url = target.remote_url
            current_head = self.remote_adapter.get_branch_head(
                remote_url, target.base_branch
            )
            if current_head != preview.diff.target_head_sha:
                raise StaleHeadError(
                    f"Target branch '{target.base_branch}' moved from {preview.diff.target_head_sha} to {current_head}."
                )

            # Prepare files to write in branch
            files_to_commit = self.remote_adapter.get_branch_files(
                remote_url, target.base_branch
            )
            prefix = (
                f"{target.docs_path}/"
                if target.docs_path and target.docs_path != "."
                else ""
            )

            # Update files
            for change in preview.diff.changes:
                if not change.is_managed or change.status == "unmodified":
                    continue
                full_path = f"{prefix}{change.path}"
                if change.status in ("added", "modified"):
                    content = preview.incoming_files.get(change.path)
                    if content is not None:
                        files_to_commit[full_path] = content
                elif change.status == "deleted":
                    files_to_commit.pop(full_path, None)

            # Record snapshot manifest in branch
            snapshot_manifest = {
                change.path: change.incoming_sha
                for change in preview.diff.changes
                if change.is_managed
                and change.status != "deleted"
                and change.incoming_sha
            }
            snapshot_data = {
                "revision_id": preview.diff.incoming_revision_id,
                "revision_digest": preview.diff.incoming_digest,
                "changeset_digest": preview.changeset_digest,
                "manifest": snapshot_manifest,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            files_to_commit[f"{prefix}.specbridge-snapshot.json"] = (
                canonical(snapshot_data) + "\n"
            ).encode()

            # Create pull request
            pr_record = self.remote_adapter.create_pull_request(
                repo=remote_url,
                title=pr_title or preview.pr_title,
                body=pr_body or preview.pr_body,
                head_branch=preview.proposed_branch,
                base_branch=target.base_branch,
                files=files_to_commit,
            )

            receipt = GitPublishReceipt(
                id=str(uuid4()),
                project_id=target.project_id,
                branch_name=preview.proposed_branch,
                commit_sha=pr_record["commit_sha"],
                pr_url=pr_record["url"],
                pr_number=pr_record["number"],
                changeset_digest=preview.changeset_digest,
                timestamp=datetime.now(UTC).isoformat(),
                status="published",
            )

        self.published_receipts[preview.changeset_digest] = receipt
        return receipt
