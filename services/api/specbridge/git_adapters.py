"""Mock remote adapters for Git repository and pull request simulation."""

from datetime import UTC, datetime
from typing import Any

from .git_diff import _sha256
from .models import canonical


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
