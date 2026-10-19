"""Unfamiliar engineer handoff evaluation runner.

Simulates an unfamiliar engineer receiving the exported documentation package:
1. Independent installation and validation without SpecBridge running or LLM credentials.
2. Browsing and tracing requirements, stories, acceptance criteria, and edge cases.
3. Creating a Git branch, modifying specifications, reviewing the diff, and verifying clean build.
"""

import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))

from fastapi.testclient import TestClient
from specbridge.main import create_app


def run():
    print(
        "[1/5] Setting up isolated fixture workspace and generating approved package..."
    )
    with TemporaryDirectory() as tmp_str:
        tmp_path = Path(tmp_str)
        client = TestClient(
            create_app(
                data_dir=tmp_path / "api_data",
                token="eval-token",
                allowed_origin="http://127.0.0.1:5173",
            ),
            base_url="http://127.0.0.1:8000",
            headers={"Authorization": "Bearer eval-token"},
        )
        config = client.get("/api/config").json()
        project = client.post(
            "/api/projects", json={"name": "HandoffEvalProject"}
        ).json()["id"]
        base = f"/api/projects/{project}"

        source_text = (
            "Patients can view clinician-published care plans after telehealth appointments. "
            "Plans display vital signs, medications, and next steps. "
            "Data must be encrypted in transit and at rest. "
            "Owner: @bask-engineering. Timeline: Q4 2026."
        )
        source = client.post(base + "/sources", json={"text": source_text}).json()["id"]
        run = client.post(
            base + "/runs",
            json={
                "source_ids": [source],
                "skill_id": "feature-handoff",
                "intent": "Generate care plans documentation",
                "acknowledged_destination": config["destination"],
            },
        ).json()

        for _ in range(6):
            run = client.post(base + "/runs/" + run["id"] + "/advance", json={}).json()

        revision_id = run["revision_id"]
        client.post(
            f"{base}/revisions/{revision_id}/reviews",
            json={"disposition": "reviewed", "notes": "Approved for handoff"},
        )
        candidate = client.post(
            f"{base}/revisions/{revision_id}/candidates", json={}
        ).json()
        client.post(
            f"{base}/candidates/{candidate['id']}/approve",
            json={"digest": candidate["digest"]},
        )

        download_resp = client.get(f"{base}/candidates/{candidate['id']}/download")
        assert download_resp.status_code == 200, "Package download failed"
        zip_bytes = download_resp.content

        # Step 1: Unfamiliar engineer receives portable package
        print("[2/5] Extracting portable package into standalone directory...")
        handoff_dir = tmp_path / "engineer_workspace"
        handoff_dir.mkdir()
        with ZipFile(BytesIO(zip_bytes)) as archive:
            archive.extractall(handoff_dir)

        # Execute clean offline install using package-lock.json
        print("Running npm ci --no-fund...")
        subprocess.run(
            ["npm", "ci", "--no-fund"], cwd=handoff_dir, check=True, capture_output=True
        )

        # Initialize local git repository
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=handoff_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Unfamiliar Engineer"],
            cwd=handoff_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "engineer@baskhealth.com"],
            cwd=handoff_dir,
            check=True,
        )
        subprocess.run(
            ["git", "add", "."], cwd=handoff_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial import of SpecBridge handoff package"],
            cwd=handoff_dir,
            check=True,
            capture_output=True,
        )

        # Step 2: Trace requirements and stories
        print("[3/5] Tracing requirements, stories, edge cases, and provenance...")
        reqs_file = handoff_dir / "src/content/docs/requirements.md"
        stories_file = handoff_dir / "src/content/docs/stories.md"
        assert reqs_file.exists(), "requirements.md missing"
        assert stories_file.exists(), "stories.md missing"

        reqs_content = reqs_file.read_text()
        stories_content = stories_file.read_text()

        assert "Requirement 1" in reqs_content
        assert "Story 1" in stories_content
        assert "Source 1" in reqs_content

        # Step 3: Run docs build with SpecBridge completely stopped
        print("[4/5] Executing independent production build (npm run build)...")
        build_proc = subprocess.run(
            ["npm", "run", "build"],
            cwd=handoff_dir,
            check=False,
            capture_output=True,
            text=True,
        )
        assert build_proc.returncode == 0, f"Docs build failed: {build_proc.stderr}"
        dist_dir = handoff_dir / "dist"
        assert (dist_dir / "index.html").exists(), "dist/index.html missing"

        # Step 4: Propose an engineering clarification on a new branch
        print(
            "[5/5] Creating branch, proposing a requirement change, and verifying rebuild..."
        )
        subprocess.run(
            ["git", "checkout", "-b", "feature/patient-summary-clarification"],
            cwd=handoff_dir,
            check=True,
            capture_output=True,
        )

        # Engineer clarifies vital signs retention
        updated_reqs = (
            reqs_content
            + "\n\n## Requirement 2\n\n- Vital signs older than 30 days are archived — proposal; sources: [Source 1](../provenance/#source-1)\n\nStories: [Story 1](../stories/#story-1)\n"
        )
        reqs_file.write_text(updated_reqs)

        diff_proc = subprocess.run(
            ["git", "diff"], cwd=handoff_dir, check=True, capture_output=True, text=True
        )
        assert "+## Requirement 2" in diff_proc.stdout

        subprocess.run(
            ["git", "commit", "-am", "docs: clarify vital signs retention policy"],
            cwd=handoff_dir,
            check=True,
            capture_output=True,
        )

        # Re-build documentation on the branch
        rebuild_proc = subprocess.run(
            ["npm", "run", "build"],
            cwd=handoff_dir,
            check=False,
            capture_output=True,
            text=True,
        )
        assert rebuild_proc.returncode == 0, (
            f"Modified docs rebuild failed: {rebuild_proc.stderr}"
        )

        print("Handoff evaluation passed successfully!")
        return {
            "status": "passed",
            "candidate_id": candidate["id"],
            "revision_id": revision_id,
            "dist_files": len(list(dist_dir.rglob("*"))),
            "branch": "feature/patient-summary-clarification",
            "independent_build": "passed",
        }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
