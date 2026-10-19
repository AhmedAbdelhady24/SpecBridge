import subprocess

from fastapi.testclient import TestClient
from specbridge.main import create_app


def _setup_approved_candidate(client: TestClient) -> tuple[str, str, str]:
    config = client.get("/api/config").json()
    project = client.post("/api/projects", json={"name": "GitCollabTest"}).json()["id"]
    base = f"/api/projects/{project}"
    source_text = "Users need automated report exports. Requirements must be traceable."
    source = client.post(base + "/sources", json={"text": source_text}).json()["id"]
    run = client.post(
        base + "/runs",
        json={
            "source_ids": [source],
            "skill_id": "feature-handoff",
            "intent": "Create handoff",
            "acknowledged_destination": config["destination"],
        },
    ).json()

    for _ in range(6):
        run = client.post(base + "/runs/" + run["id"] + "/advance", json={}).json()

    revision_id = run["revision_id"]
    # Record human review
    client.post(
        f"{base}/revisions/{revision_id}/reviews",
        json={"disposition": "reviewed", "notes": "LGTM"},
    )
    # Prepare candidate
    candidate = client.post(
        f"{base}/revisions/{revision_id}/candidates", json={}
    ).json()
    # Approve candidate
    client.post(
        f"{base}/candidates/{candidate['id']}/approve",
        json={"digest": candidate["digest"]},
    )

    return project, revision_id, candidate["id"]


def test_git_target_crud_and_validation(tmp_path):
    client = TestClient(
        create_app(
            data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    project = client.post("/api/projects", json={"name": "TargetCRUD"}).json()["id"]

    # Target not yet configured
    resp = client.get(f"/api/projects/{project}/git/targets")
    assert resp.status_code == 404

    # Save target
    save_resp = client.post(
        f"/api/projects/{project}/git/targets",
        json={
            "target_type": "local",
            "repo_path": str(tmp_path / "repo"),
            "base_branch": "main",
            "docs_path": "docs",
        },
    )
    assert save_resp.status_code == 200
    target = save_resp.json()
    assert target["target_type"] == "local"
    assert target["repo_path"] == str(tmp_path / "repo")
    assert target["base_branch"] == "main"
    assert target["docs_path"] == "docs"

    # Get target
    get_resp = client.get(f"/api/projects/{project}/git/targets")
    assert get_resp.status_code == 200
    assert get_resp.json()["repo_path"] == str(tmp_path / "repo")


def test_git_preview_requires_target_and_approval(tmp_path):
    client = TestClient(
        create_app(
            data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    config = client.get("/api/config").json()
    project = client.post("/api/projects", json={"name": "UnapprovedTest"}).json()["id"]
    base = f"/api/projects/{project}"
    source = client.post(
        base + "/sources", json={"text": "Initial requirements"}
    ).json()["id"]
    run = client.post(
        base + "/runs",
        json={
            "source_ids": [source],
            "skill_id": "feature-handoff",
            "intent": "Handoff",
            "acknowledged_destination": config["destination"],
        },
    ).json()
    for _ in range(6):
        run = client.post(base + "/runs/" + run["id"] + "/advance", json={}).json()

    # Prepare candidate without approval
    candidate = client.post(
        f"{base}/revisions/{run['revision_id']}/candidates", json={}
    ).json()

    # 1. Preview without target -> 409
    resp = client.post(f"{base}/git/preview", json={"candidate_id": candidate["id"]})
    assert resp.status_code == 409
    assert "Configure a Git destination" in resp.json()["error"]["message"]

    # Save target
    client.post(
        f"{base}/git/targets",
        json={"target_type": "local", "repo_path": str(tmp_path / "repo")},
    )

    # 2. Preview with unapproved candidate -> 409
    resp2 = client.post(f"{base}/git/preview", json={"candidate_id": candidate["id"]})
    assert resp2.status_code == 409
    assert "approved before Git collaboration" in resp2.json()["error"]["message"]


def test_git_preview_and_publish_local_flow(tmp_path):
    # Setup local git repo
    repo_dir = tmp_path / "local_repo"
    repo_dir.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test PM"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "pm@example.com"], cwd=repo_dir, check=True
    )
    (repo_dir / "docs").mkdir()
    (repo_dir / "docs/README.md").write_text("# Initial Repo Docs\n")
    (repo_dir / "src").mkdir()
    (repo_dir / "src/main.py").write_text("print('core logic')\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    client = TestClient(
        create_app(
            data_dir=tmp_path / "api_data",
            token="test",
            allowed_origin="http://127.0.0.1:5173",
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    project, _revision_id, candidate_id = _setup_approved_candidate(client)
    base = f"/api/projects/{project}"

    # Configure local target
    client.post(
        f"{base}/git/targets",
        json={
            "target_type": "local",
            "repo_path": str(repo_dir),
            "base_branch": "main",
            "docs_path": "docs",
        },
    )

    # Preview
    preview_resp = client.post(
        f"{base}/git/preview",
        json={
            "candidate_id": candidate_id,
            "proposed_branch": "specbridge/feature-export",
        },
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["proposed_branch"] == "specbridge/feature-export"
    assert preview["changeset_digest"] is not None
    assert not preview["diff"]["has_conflicts"]

    # Publish with invalid approval digest -> 409
    bad_pub = client.post(
        f"{base}/git/publish",
        json={
            "candidate_id": candidate_id,
            "approval_digest": "tampered-digest",
            "proposed_branch": "specbridge/feature-export",
        },
    )
    assert bad_pub.status_code == 409
    assert "approval_digest_mismatch" in bad_pub.json()["error"]["message"]

    # Publish with valid approval digest -> 201
    pub_resp = client.post(
        f"{base}/git/publish",
        json={
            "candidate_id": candidate_id,
            "approval_digest": preview["changeset_digest"],
            "proposed_branch": "specbridge/feature-export",
            "commit_message": "docs: sync approved requirements",
        },
    )
    assert pub_resp.status_code == 201
    receipt = pub_resp.json()
    assert receipt["status"] == "published"
    assert receipt["branch_name"] == "specbridge/feature-export"
    assert receipt["commit_sha"] is not None

    # Verify branch in local git repo
    branch_check = subprocess.run(
        ["git", "rev-parse", "--verify", "specbridge/feature-export"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    assert branch_check.stdout.strip() == receipt["commit_sha"]

    # Verify docs and snapshot file were written
    reqs_check = subprocess.run(
        ["git", "show", "specbridge/feature-export:docs/requirements.md"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Requirement 1" in reqs_check.stdout

    # Verify unmanaged developer files in src/ remain untouched
    src_check = subprocess.run(
        ["git", "show", "specbridge/feature-export:src/main.py"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "print('core logic')" in src_check.stdout

    # Audit endpoint returns audit record
    audits_resp = client.get(f"{base}/git/audits")
    assert audits_resp.status_code == 200
    audits = audits_resp.json()
    assert len(audits) >= 1
    assert audits[0]["receipt_id"] == receipt["id"]
    assert audits[0]["changeset_digest"] == preview["changeset_digest"]


def test_git_preview_and_publish_github_mock_flow(tmp_path):
    client = TestClient(
        create_app(
            data_dir=tmp_path / "api_data",
            token="test",
            allowed_origin="http://127.0.0.1:5173",
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    project, _revision_id, candidate_id = _setup_approved_candidate(client)
    base = f"/api/projects/{project}"

    # Configure remote target
    client.post(
        f"{base}/git/targets",
        json={
            "target_type": "github_mock",
            "remote_url": "https://github.com/acme/care-plans.git",
            "base_branch": "main",
            "docs_path": "docs",
        },
    )

    # Preview
    preview_resp = client.post(
        f"{base}/git/preview",
        json={
            "candidate_id": candidate_id,
            "proposed_branch": "specbridge/care-plans-reqs",
        },
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert not preview["diff"]["has_conflicts"]

    # Publish
    pub_resp = client.post(
        f"{base}/git/publish",
        json={
            "candidate_id": candidate_id,
            "approval_digest": preview["changeset_digest"],
            "proposed_branch": "specbridge/care-plans-reqs",
            "pr_title": "docs: import care plans requirements",
            "pr_body": "Automated import from SpecBridge approved candidate.",
        },
    )
    assert pub_resp.status_code == 201
    receipt = pub_resp.json()
    assert receipt["status"] == "published"
    assert receipt["pr_number"] == 1
    assert "https://github.com/acme/care-plans/pull/1" == receipt["pr_url"]
