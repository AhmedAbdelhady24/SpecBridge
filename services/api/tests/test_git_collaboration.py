import hashlib
import subprocess

import pytest
from specbridge.git_collaboration import (
    GitService,
    GitTarget,
    MockGitHubAdapter,
    StaleHeadError,
    extract_candidate_docs_files,
    three_way_compare,
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@pytest.fixture
def base_files():
    return {
        "README.md": b"# My Project Docs\nInitial overview.",
        "src/content/docs/requirements.md": b"# Requirements\nREQ-1: Export CSV",
        "src/content/docs/stories.md": b"# Stories\nSTORY-1: Export as CSV",
        "manifest.json": b'{"files": {}}',
    }


def test_three_way_clean_update(base_files):
    local_files = dict(base_files)
    incoming_files = dict(base_files)
    incoming_files["src/content/docs/requirements.md"] = (
        b"# Requirements\nREQ-1: Export CSV\nREQ-2: Filter columns"
    )

    diff = three_way_compare(
        base_files=base_files,
        local_files=local_files,
        incoming_files=incoming_files,
        managed_paths=set(base_files.keys()),
    )

    assert not diff.has_conflicts
    changes_by_path = {c.path: c for c in diff.changes}
    assert "src/content/docs/requirements.md" in changes_by_path
    req_change = changes_by_path["src/content/docs/requirements.md"]
    assert req_change.status == "modified"
    assert req_change.is_managed is True
    assert req_change.conflict_reason is None


def test_three_way_preserves_unmanaged_developer_files(base_files):
    local_files = dict(base_files)
    # Developer added their own code files
    local_files["src/app.py"] = b"print('hello')"
    local_files["Makefile"] = b"build:\n\techo 'done'"

    incoming_files = dict(base_files)
    incoming_files["src/content/docs/requirements.md"] = b"# Requirements v2"

    diff = three_way_compare(
        base_files=base_files,
        local_files=local_files,
        incoming_files=incoming_files,
        managed_paths=set(base_files.keys()),
    )

    assert not diff.has_conflicts
    changes_by_path = {c.path: c for c in diff.changes}
    # Unmanaged files are not modified by incoming
    assert changes_by_path["src/app.py"].status == "unmodified"
    assert changes_by_path["src/app.py"].is_managed is False
    assert changes_by_path["Makefile"].status == "unmodified"
    assert changes_by_path["Makefile"].is_managed is False


def test_three_way_conflict_on_concurrent_modification(base_files):
    local_files = dict(base_files)
    # Developer edited requirements directly in repo
    local_files["src/content/docs/requirements.md"] = (
        b"# Requirements\nDeveloper manual note: do not use CSV."
    )

    # Incoming generated revision also modified requirements
    incoming_files = dict(base_files)
    incoming_files["src/content/docs/requirements.md"] = (
        b"# Requirements\nREQ-1: Export CSV and JSON."
    )

    diff = three_way_compare(
        base_files=base_files,
        local_files=local_files,
        incoming_files=incoming_files,
        managed_paths=set(base_files.keys()),
    )

    assert diff.has_conflicts is True
    changes_by_path = {c.path: c for c in diff.changes}
    req_change = changes_by_path["src/content/docs/requirements.md"]
    assert req_change.status == "conflict"
    assert req_change.conflict_reason == "concurrent_modification"


def test_three_way_developer_deletion_conflict(base_files):
    local_files = dict(base_files)
    # Developer intentionally deleted stories.md
    del local_files["src/content/docs/stories.md"]

    # Incoming package updated stories.md
    incoming_files = dict(base_files)
    incoming_files["src/content/docs/stories.md"] = b"# Stories\nUpdated stories."

    diff = three_way_compare(
        base_files=base_files,
        local_files=local_files,
        incoming_files=incoming_files,
        managed_paths=set(base_files.keys()),
    )

    assert diff.has_conflicts is True
    changes_by_path = {c.path: c for c in diff.changes}
    story_change = changes_by_path["src/content/docs/stories.md"]
    assert story_change.status == "conflict"
    assert story_change.conflict_reason == "developer_deleted_file"


@pytest.fixture
def local_git_repo(tmp_path):
    repo_dir = tmp_path / "target_repo"
    repo_dir.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test Dev"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "dev@example.com"], cwd=repo_dir, check=True
    )

    # Initial commit with developer code and base docs
    (repo_dir / "src").mkdir()
    (repo_dir / "src/app.py").write_text("print('core app')")
    docs_dir = repo_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "README.md").write_text("# Project Docs\nInitial docs.")
    (docs_dir / "requirements.md").write_text("# Reqs\nREQ-1: Basic auth.")

    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    return repo_dir


def test_git_service_local_preview_and_clean_publish(local_git_repo, tmp_path):
    service = GitService()
    target = GitTarget(
        project_id="proj-1",
        target_type="local",
        repo_path=str(local_git_repo),
        base_branch="main",
        docs_path="docs",
    )

    # Base snapshot recorded when docs were first established
    base_manifest = {
        "README.md": _sha256((local_git_repo / "docs/README.md").read_bytes()),
        "requirements.md": _sha256(
            (local_git_repo / "docs/requirements.md").read_bytes()
        ),
    }

    # Incoming new revision files
    incoming_files = {
        "README.md": (local_git_repo / "docs/README.md").read_bytes(),
        "requirements.md": b"# Reqs\nREQ-1: Basic auth.\nREQ-2: OAuth2 login.",
        "stories.md": b"# Stories\nSTORY-1: Login via GitHub.",
    }

    preview = service.prepare_preview(
        target=target,
        base_revision_id="rev-1",
        base_digest="digest-1",
        base_manifest=base_manifest,
        incoming_revision_id="rev-2",
        incoming_digest="digest-2",
        incoming_files=incoming_files,
        proposed_branch="specbridge/rev-2-oauth2",
    )

    assert not preview.diff.has_conflicts
    assert preview.changeset_digest is not None
    assert preview.proposed_branch == "specbridge/rev-2-oauth2"

    # Now publish with exact changeset digest approval
    receipt = service.publish(
        preview=preview,
        approval_digest=preview.changeset_digest,
        commit_message="docs: update requirements with OAuth2 (SpecBridge rev-2)",
    )

    assert receipt.status == "published"
    assert receipt.branch_name == "specbridge/rev-2-oauth2"
    assert receipt.commit_sha is not None

    # Verify branch was created in local repo and contains incoming files
    check_branch = subprocess.run(
        ["git", "rev-parse", "--verify", "specbridge/rev-2-oauth2"],
        cwd=local_git_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    assert check_branch.stdout.strip() == receipt.commit_sha

    # Verify app.py was preserved untouched on the branch
    app_content = subprocess.run(
        ["git", "show", "specbridge/rev-2-oauth2:src/app.py"],
        cwd=local_git_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    assert app_content.stdout == "print('core app')"

    # Verify updated docs on the branch
    reqs_content = subprocess.run(
        ["git", "show", "specbridge/rev-2-oauth2:docs/requirements.md"],
        cwd=local_git_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "REQ-2: OAuth2 login." in reqs_content.stdout


def test_git_service_rejects_unapproved_or_tampered_digest(local_git_repo):
    service = GitService()
    target = GitTarget(
        project_id="proj-1",
        target_type="local",
        repo_path=str(local_git_repo),
        base_branch="main",
        docs_path="docs",
    )
    base_manifest = {
        "README.md": _sha256((local_git_repo / "docs/README.md").read_bytes()),
    }
    incoming_files = {
        "README.md": b"# Changed Title",
    }
    preview = service.prepare_preview(
        target=target,
        base_revision_id="rev-1",
        base_digest="digest-1",
        base_manifest=base_manifest,
        incoming_revision_id="rev-2",
        incoming_digest="digest-2",
        incoming_files=incoming_files,
        proposed_branch="specbridge/rev-2-test",
    )

    with pytest.raises(ValueError, match="approval_digest_mismatch"):
        service.publish(
            preview=preview,
            approval_digest="wrong-or-tampered-digest",
            commit_message="docs: bad approval",
        )


def test_git_service_detects_stale_head(local_git_repo):
    service = GitService()
    target = GitTarget(
        project_id="proj-1",
        target_type="local",
        repo_path=str(local_git_repo),
        base_branch="main",
        docs_path="docs",
    )
    base_manifest = {
        "README.md": _sha256((local_git_repo / "docs/README.md").read_bytes()),
    }
    incoming_files = {
        "README.md": b"# Changed Title",
    }
    preview = service.prepare_preview(
        target=target,
        base_revision_id="rev-1",
        base_digest="digest-1",
        base_manifest=base_manifest,
        incoming_revision_id="rev-2",
        incoming_digest="digest-2",
        incoming_files=incoming_files,
        proposed_branch="specbridge/rev-2-stale",
    )

    # Another commit lands on main while preview was pending
    (local_git_repo / "src/other.py").write_text("print('concurrent developer commit')")
    subprocess.run(["git", "add", "."], cwd=local_git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "developer pushed to main"],
        cwd=local_git_repo,
        check=True,
    )

    with pytest.raises(StaleHeadError):
        service.publish(
            preview=preview,
            approval_digest=preview.changeset_digest,
            commit_message="docs: attempt write on stale head",
        )


def test_git_service_idempotent_publish(local_git_repo):
    service = GitService()
    target = GitTarget(
        project_id="proj-1",
        target_type="local",
        repo_path=str(local_git_repo),
        base_branch="main",
        docs_path="docs",
    )
    base_manifest = {
        "README.md": _sha256((local_git_repo / "docs/README.md").read_bytes()),
    }
    incoming_files = {
        "README.md": b"# Same content",
    }
    preview = service.prepare_preview(
        target=target,
        base_revision_id="rev-1",
        base_digest="digest-1",
        base_manifest=base_manifest,
        incoming_revision_id="rev-2",
        incoming_digest="digest-2",
        incoming_files=incoming_files,
        proposed_branch="specbridge/rev-2-idempotent",
    )

    receipt1 = service.publish(
        preview=preview,
        approval_digest=preview.changeset_digest,
        commit_message="docs: first publish",
    )
    assert receipt1.status == "published"

    # Repeated request with same preview and digest returns same receipt
    receipt2 = service.publish(
        preview=preview,
        approval_digest=preview.changeset_digest,
        commit_message="docs: second publish retry",
    )
    assert receipt2.status == "already_published"
    assert receipt2.commit_sha == receipt1.commit_sha


def test_mock_github_adapter_pr_creation():
    adapter = MockGitHubAdapter()
    adapter.create_repository("owner/repo", default_branch="main")
    adapter.seed_branch_files(
        repo="owner/repo",
        branch="main",
        files={"docs/README.md": b"# Original Docs"},
    )

    target = GitTarget(
        project_id="proj-gh",
        target_type="github_mock",
        remote_url="https://github.com/owner/repo.git",
        base_branch="main",
        docs_path="docs",
    )

    service = GitService(remote_adapter=adapter)
    preview = service.prepare_preview(
        target=target,
        base_revision_id="rev-1",
        base_digest="digest-1",
        base_manifest={"README.md": _sha256(b"# Original Docs")},
        incoming_revision_id="rev-2",
        incoming_digest="digest-2",
        incoming_files={"README.md": b"# Updated Docs by PM"},
        proposed_branch="specbridge/rev-2-gh",
    )

    receipt = service.publish(
        preview=preview,
        approval_digest=preview.changeset_digest,
        commit_message="docs: update via GitHub PR",
        pr_title="docs: update requirements from SpecBridge",
        pr_body="Detailed PR summary and provenance.",
    )

    assert receipt.status == "published"
    assert receipt.pr_number == 1
    assert receipt.pr_url == "https://github.com/owner/repo/pull/1"

    # Audit log was created in adapter
    audits = adapter.get_audit_log("owner/repo")
    assert len(audits) >= 1
    assert audits[-1]["action"] == "create_pull_request"
    assert audits[-1]["pr_number"] == 1


def test_prepare_candidate_preview_auto_detects_snapshot_roundtrip(local_git_repo):
    service = GitService()
    target = GitTarget(
        project_id="proj-auto",
        target_type="local",
        repo_path=str(local_git_repo),
        base_branch="main",
        docs_path="docs",
    )

    # Initial preview & publish (Rev-1)
    rev1_files = {
        "README.md": b"# Docs v1",
        "requirements.md": b"# Reqs v1\nREQ-1: Auth",
    }
    preview1 = service.prepare_candidate_preview(
        target=target,
        incoming_revision_id="rev-1",
        incoming_digest="digest-rev1",
        incoming_files=rev1_files,
        proposed_branch="specbridge/rev-1",
    )
    assert not preview1.diff.has_conflicts
    assert preview1.diff.base_revision_id is None

    receipt1 = service.publish(
        preview=preview1,
        approval_digest=preview1.changeset_digest,
        commit_message="docs: publish rev-1",
    )
    assert receipt1.status == "published"

    # Merge rev-1 branch into main so main now has the base snapshot
    subprocess.run(
        ["git", "checkout", "main"], cwd=local_git_repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "merge", "specbridge/rev-1"],
        cwd=local_git_repo,
        check=True,
        capture_output=True,
    )

    # Now preview Rev-2 without passing base_manifest manually
    rev2_files = {
        "README.md": b"# Docs v1",
        "requirements.md": b"# Reqs v1\nREQ-1: Auth\nREQ-2: Roles",
        "stories.md": b"# Stories\nSTORY-1: Admin roles",
    }
    preview2 = service.prepare_candidate_preview(
        target=target,
        incoming_revision_id="rev-2",
        incoming_digest="digest-rev2",
        incoming_files=rev2_files,
        proposed_branch="specbridge/rev-2",
    )

    assert not preview2.diff.has_conflicts
    assert preview2.diff.base_revision_id == "rev-1"
    assert preview2.diff.base_digest == "digest-rev1"
    changes_by_path = {c.path: c for c in preview2.diff.changes}
    assert changes_by_path["requirements.md"].status == "modified"
    assert changes_by_path["stories.md"].status == "added"
    assert changes_by_path["README.md"].status == "unmodified"

    receipt2 = service.publish(
        preview=preview2,
        approval_digest=preview2.changeset_digest,
        commit_message="docs: publish rev-2",
    )
    assert receipt2.status == "published"


def test_extract_candidate_docs_files():
    from io import BytesIO
    from zipfile import ZipFile

    buf = BytesIO()
    with ZipFile(buf, "w") as z:
        z.writestr("src/content/docs/index.md", "# Welcome")
        z.writestr("src/content/docs/requirements.md", "# Reqs")
        z.writestr("revision.json", '{"revision_id": "r1"}')
        z.writestr("astro.config.mjs", "export default {}")

    raw_zip = buf.getvalue()
    manifest = {
        "src/content/docs/index.md": "sha1",
        "src/content/docs/requirements.md": "sha2",
        "revision.json": "sha3",
        "astro.config.mjs": "sha4",
    }

    docs = extract_candidate_docs_files(raw_zip, manifest)
    assert "requirements.md" in docs
    assert docs["requirements.md"] == b"# Reqs"
    assert "README.md" in docs  # mapped from index.md
    assert docs["README.md"] == b"# Welcome"
    assert "revision.json" in docs
    # Unrelated template files are excluded from docs payload
    assert "astro.config.mjs" not in docs
