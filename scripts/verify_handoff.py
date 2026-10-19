"""Exercise the public fixture workflow and a fresh independent documentation install."""

import argparse
import json
import os
import secrets
import signal
import socket
import stat
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))

from fastapi.testclient import TestClient
from specbridge.main import create_app


def extract_package(raw: bytes, target: Path) -> None:
    if target.exists():
        raise FileExistsError(
            "Choose a new output directory; existing files are preserved"
        )
    with ZipFile(BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) > 100 or sum(item.file_size for item in infos) > 20 * 1024 * 1024:
            raise ValueError("Archive exceeds the package bounds")
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive names")
        for item in infos:
            name = PurePosixPath(item.filename)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in item.filename
                or ":" in item.filename
                or stat.S_ISLNK(item.external_attr >> 16)
            ):
                raise ValueError("Unsafe archive entry")
        target.mkdir(parents=True, exist_ok=False)
        for item in infos:
            path = target / item.filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(item))


def run_command(args: list[str], directory: Path, log: Path) -> None:
    with log.open("a") as output:
        output.write("\nCOMMAND " + " ".join(args) + "\n")
        output.flush()
        subprocess.run(
            args,
            cwd=directory,
            stdout=output,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=300,
        )


@contextmanager
def serve_docs(directory: Path, mode: str, log: Path) -> Iterator[str]:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    with log.open("a") as output:
        process = subprocess.Popen(
            ["npm", "run", mode, "--", "--ignore-lock", "--port", str(port)],
            cwd=directory,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            for _ in range(300):
                if process.poll() is not None:
                    raise RuntimeError(
                        "Documentation server exited; inspect verification.log"
                    )
                try:
                    with urlopen(url, timeout=1) as response:
                        if response.status == 200:
                            time.sleep(2.0)
                            break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Documentation HTTP readiness timed out")
            yield url
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()


def verify(output: Path) -> None:
    started = time.monotonic()
    if output.exists():
        raise FileExistsError(
            "Choose a new output directory; existing files are preserved"
        )
    with TemporaryDirectory(prefix="specbridge-verifier-") as data:
        # A separate test token is injected through the factory, never read from user data.
        token = secrets.token_urlsafe(32)
        app = create_app(
            data_dir=Path(data), token=token, allowed_origin="http://127.0.0.1:5173"
        )
        with TestClient(
            app,
            base_url="http://127.0.0.1:8000",
            headers={"Authorization": "Bearer " + token},
        ) as client:
            project = client.post(
                "/api/projects", json={"name": "Independent export exercise"}
            ).json()["id"]
            base = f"/api/projects/{project}"
            source = client.post(
                base + "/sources",
                json={
                    "text": "Customers requested CSV export. Owner, delivery date and final API remain unknown."
                },
            ).json()["id"]
            destination = client.get("/api/config").json()["destination"]
            run = client.post(
                base + "/runs",
                json={
                    "source_ids": [source],
                    "skill_id": "feature-handoff",
                    "intent": "Feature PRD",
                    "acknowledged_destination": destination,
                },
            ).json()
            for _ in range(6):
                result = client.post(base + "/runs/" + run["id"] + "/advance", json={})
                result.raise_for_status()
                run = result.json()
            revision_url = base + "/revisions/" + run["revision_id"]
            revision = client.get(revision_url).json()
            # Incorporate a synthetic user answer before export; no model amendment call.
            questions = client.get(base + f"/runs/{run['id']}/questions").json()
            question = questions[0]
            answer = client.post(
                base + f"/runs/{run['id']}/questions/{question['id']}/answers",
                json={
                    "expected_version": question["version"],
                    "text": "Customers requested CSV export.",
                },
            )
            answer.raise_for_status()
            answer = answer.json()
            question = client.get(base + f"/runs/{run['id']}/questions").json()[0]
            resolved_artifact = revision["artifact"]
            resolved_artifact["scope"].append(
                {
                    "text": answer["text"],
                    "source_ids": [answer["source_id"]],
                    "kind": "user_provided",
                }
            )
            resolved_artifact["open_questions"].pop(0)
            working = client.put(
                base + f"/runs/{run['id']}/working-copy",
                json={
                    "expected_version": 0,
                    "base_revision_id": revision["id"],
                    "base_digest": revision["digest"],
                    "artifact": resolved_artifact,
                    "question_changes": [
                        {
                            "question_id": question["id"],
                            "expected_question_version": question["version"],
                            "answer_version": answer["version"],
                            "targets": ["scope"],
                        }
                    ],
                },
            )
            working.raise_for_status()
            from uuid import uuid4

            committed = client.post(
                base + f"/runs/{run['id']}/commits",
                json={
                    "working_copy_version": working.json()["version"],
                    "idempotency_key": str(uuid4()),
                },
            )
            committed.raise_for_status()
            revision_url = base + "/revisions/" + committed.json()["revision_id"]
            revision = client.get(revision_url).json()
            artifact = revision["artifact"]
            artifact["title"] = 'Report export <script id="attack-title">bad()</script>'
            artifact["purpose"] = (
                'Review a saved report export. <script id="attack-body">bad()</script> ![remote](https://evil.invalid/pixel) [link](javascript:bad())\n---\n{import("bad")} — these are inert attack-test strings.'
            )
            revision = client.post(
                revision_url + "/edits",
                json={"expected_digest": revision["digest"], "artifact": artifact},
            ).json()
            revision_url = base + "/revisions/" + revision["id"]
            candidate = client.post(revision_url + "/candidates").json()
            candidate_url = base + "/candidates/" + candidate["id"]
            assert client.get(candidate_url + "/download").status_code == 409
            client.post(
                revision_url + "/reviews",
                json={
                    "disposition": "reviewed",
                    "notes": "DEMO and malicious-content fixture; unresolved questions are explicit.",
                },
            ).raise_for_status()
            client.post(
                candidate_url + "/approve", json={"digest": candidate["digest"]}
            ).raise_for_status()
            download = client.get(candidate_url + "/download")
            download.raise_for_status()
            raw = download.content
    # SpecBridge's application/session is closed before any website installation or view.
    extract_package(raw, output)
    log = output / "verification.log"
    run_command(["npm", "ci", "--no-fund"], output, log)
    run_command(["npm", "run", "build"], output, log)
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".cache/playwright"))
    for mode in ("dev", "preview"):
        with serve_docs(output, mode, log) as url:
            run_command(
                ["node", str(ROOT / "scripts/check_docs.mjs"), url, str(output)],
                ROOT,
                log,
            )
    report = {
        "status": "passed",
        "provider": "fixture",
        "live_model_calls": 0,
        "duration_seconds": round(time.monotonic() - started, 2),
        "candidate_digest": candidate["digest"],
        "template_digest": candidate["template_digest"],
        "manifest": candidate["manifest"],
        "site_modes_checked": ["dev", "preview"],
        "human_handoff": "not performed",
    }
    (output / "verification-result.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "output": str(output),
                "duration_seconds": report["duration_seconds"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="New directory for the independently runnable package and verification logs",
    )
    verify(parser.parse_args().output.resolve())
