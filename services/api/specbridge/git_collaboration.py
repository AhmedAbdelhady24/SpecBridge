"""Git collaboration service, three-way comparison engine, and adapter orchestration."""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .git_adapters import MockGitHubAdapter
from .git_diff import (
    _compute_text_diff,
    _sha256,
    extract_candidate_docs_files,
    three_way_compare,
)
from .git_models import (
    FileChangeType,
    FileComparison,
    GitPublishPreview,
    GitPublishReceipt,
    GitTarget,
    StaleHeadError,
    ThreeWayDiff,
)
from .models import canonical, digest

__all__ = [
    "FileChangeType",
    "FileComparison",
    "GitPublishPreview",
    "GitPublishReceipt",
    "GitService",
    "GitTarget",
    "MockGitHubAdapter",
    "StaleHeadError",
    "ThreeWayDiff",
    "_compute_text_diff",
    "_sha256",
    "extract_candidate_docs_files",
    "three_way_compare",
]


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
        if not repo_path.exists() or not repo_path.is_dir():
            raise FileNotFoundError(
                f"Local repository path does not exist: {repo_path}"
            )
        # Get HEAD commit SHA
        try:
            head_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as err:
            raise ValueError(
                f"Path is not a valid git repository: {repo_path}"
            ) from err
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
