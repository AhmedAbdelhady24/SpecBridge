from types import SimpleNamespace

import pytest
from specbridge.models import Artifact, Source
from specbridge.storage import Conflict, Store
from specbridge.workflow import RetryAcknowledgmentRequired, Workflow


class Provider:
    destination = "local test"
    mode = "fixture"
    model = "demo"

    def __init__(self, body):
        self.body = body
        self.calls = 0
        self.fail = False

    def generate(self, *, skill, sources):
        self.calls += 1
        if self.fail:
            raise RuntimeError("SECRET_SENTINEL")
        return Artifact.model_validate(self.body)


class Registry:
    def load(self, name, *, with_output_contract=False):
        return SimpleNamespace(
            name=name, digest="skill-v1", body="Write a careful draft"
        )


def setup(tmp_path, body):
    store = Store(tmp_path / "db")
    project = store.create_project("Reports")
    source = store.add_source(project.id, "Export my saved report")
    provider = Provider(body)
    workflow = Workflow(store, Registry(), provider)
    run = workflow.start(
        project.id, [source.id], "Create a PRD", "feature-handoff", provider.destination
    )
    return store, workflow, provider, run


def test_checkpoint_restart_and_no_repeated_generation(tmp_path, artifact_dict):
    store, workflow, provider, run = setup(tmp_path, artifact_dict)
    for _ in range(5):
        run = workflow.advance(run.project_id, run.id)
    assert provider.calls == 1
    assert run.stage == "validate"
    restarted = Workflow(Store(store.path), Registry(), provider)
    run = restarted.advance(run.project_id, run.id)
    assert run.status == "review"
    assert run.revision_id
    assert provider.calls == 1
    assert len(run.history) == 6
    with pytest.raises(Conflict):
        restarted.advance(run.project_id, run.id)


def test_failure_redaction_and_acknowledged_retry(tmp_path, artifact_dict):
    _store, workflow, provider, run = setup(tmp_path, artifact_dict)
    for _ in range(4):
        run = workflow.advance(run.project_id, run.id)
    provider.fail = True
    failed = workflow.advance(run.project_id, run.id)
    assert failed.status == "failed"
    assert "SECRET_SENTINEL" not in failed.model_dump_json()
    with pytest.raises(RetryAcknowledgmentRequired):
        workflow.advance(run.project_id, run.id)
    provider.fail = False
    assert (
        workflow.advance(run.project_id, run.id, retry_acknowledged=True).stage
        == "validate"
    )


def test_interrupted_lease_and_changed_destination(tmp_path, artifact_dict):
    store, workflow, provider, run = setup(tmp_path, artifact_dict)
    with store.transaction() as db:
        running = run.model_copy(update={"stage": "execute", "status": "running"})
        db.execute(
            "UPDATE runs SET data=?,lease='old',lease_until=0 WHERE id=?",
            (running.model_dump_json(), run.id),
        )
    with pytest.raises(RetryAcknowledgmentRequired):
        workflow.advance(run.project_id, run.id)
    provider.destination = "https://changed.example"
    with pytest.raises(Conflict):
        workflow.advance(run.project_id, run.id, retry_acknowledged=True)


def test_generation_provenance_survives_config_change(tmp_path, artifact_dict):
    store, workflow, provider, run = setup(tmp_path, artifact_dict)
    for _ in range(5):
        run = workflow.advance(run.project_id, run.id)
    provider.model = "different-model"
    run = workflow.advance(run.project_id, run.id)
    assert (
        store.get_revision(run.project_id, run.revision_id).provenance["model"]
        == "demo"
    )


def test_active_output_contract_is_in_actual_model_request(tmp_path):
    import json
    from pathlib import Path

    import httpx
    from fastapi.testclient import TestClient
    from specbridge.main import create_app
    from specbridge.providers import CompatibleProvider, FixtureProvider
    from specbridge.skills import SkillRegistry

    root = Path(__file__).resolve().parents[3] / "skills/runtime"
    registry = SkillRegistry(root)
    contract = registry.reference("feature-handoff", "references/output-contract.md")
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        sources = [
            Source(id=row["id"], project_id="synthetic", text=row["text"], digest="d")
            for row in json.loads(body["messages"][1]["content"])
        ]
        artifact = FixtureProvider().generate(
            skill=registry.load("feature-handoff"), sources=sources
        )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": artifact.model_dump_json()},
                    }
                ]
            },
        )

    provider = CompatibleProvider(
        base_url="https://test.example",
        model="test",
        api_key="test",
        transport=httpx.MockTransport(handler),
    )
    with TestClient(
        create_app(
            data_dir=tmp_path,
            token="test",
            allowed_origin="http://127.0.0.1:5173",
            provider=provider,
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    ) as client:
        project = client.post("/api/projects", json={"name": "Contract test"}).json()[
            "id"
        ]
        base = f"/api/projects/{project}"
        source = client.post(
            base + "/sources", json={"text": "Export saved reports as CSV."}
        ).json()["id"]
        run = client.post(
            base + "/runs",
            json={
                "source_ids": [source],
                "skill_id": "feature-handoff",
                "intent": "PRD",
                "acknowledged_destination": provider.destination,
            },
        ).json()
        for _ in range(5):
            run = client.post(base + "/runs/" + run["id"] + "/advance", json={}).json()
        assert len(requests) == 1
        assert contract in requests[0]["messages"][0]["content"]


def test_tampered_contract_fails_before_a_provider_call(tmp_path, artifact_dict):
    import shutil
    from pathlib import Path

    from specbridge.skills import SkillRegistry

    root = tmp_path / "runtime"
    shutil.copytree(Path(__file__).resolve().parents[3] / "skills/runtime", root)
    store = Store(tmp_path / "db")
    project = store.create_project("Tamper test")
    source = store.add_source(project.id, "Export CSV")
    provider = Provider(artifact_dict)
    workflow = Workflow(store, SkillRegistry(root), provider)
    run = workflow.start(
        project.id, [source.id], "PRD", "feature-handoff", provider.destination
    )
    for _ in range(4):
        run = workflow.advance(project.id, run.id)
    (root / "feature-handoff/references/output-contract.md").write_text(
        "Tampered contract"
    )
    run = workflow.advance(project.id, run.id)
    assert run.status == "failed" and provider.calls == 0


def blocked_generation(tmp_path, artifact_dict, monkeypatch, *, fail=False):
    import threading

    import specbridge.workflow as module

    now = [1000.0]
    monkeypatch.setattr(module, "time", SimpleNamespace(time=lambda: now[0]))
    monkeypatch.setattr(module, "HEARTBEAT_SECONDS", 0.005, raising=False)
    store, workflow, provider, run = setup(tmp_path, artifact_dict)
    for _ in range(4):
        run = workflow.advance(run.project_id, run.id)
    started, release = threading.Event(), threading.Event()

    def generate(*, skill, sources):
        provider.calls += 1
        started.set()
        assert release.wait(5), "Test did not release its blocked provider"
        if fail:
            raise RuntimeError("SECRET_HEARTBEAT_SENTINEL")
        return Artifact.model_validate(artifact_dict)

    provider.generate = generate
    return store, workflow, provider, run, now, started, release


def assert_heartbeat_stopped(run):
    import threading

    assert not any(
        t.name == f"specbridge-lease-{run.id}" for t in threading.enumerate()
    )


def test_long_generation_renews_lease_and_prevents_duplicate_call(
    tmp_path, artifact_dict, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    store, workflow, provider, run, now, started, release = blocked_generation(
        tmp_path, artifact_dict, monkeypatch
    )
    renewed = Event()
    original = getattr(workflow, "_renew_lease", lambda *args: False)

    def renew(*args):
        result = original(*args)
        renewed.set()
        return result

    monkeypatch.setattr(workflow, "_renew_lease", renew, raising=False)
    with ThreadPoolExecutor() as pool:
        future = pool.submit(workflow.advance, run.project_id, run.id)
        try:
            assert started.wait(1)
            now[0] = 1100.0
            assert renewed.wait(1), "A running provider must renew its lease"
            renewed.clear()
            now[0] = 1150.0  # Beyond the original lease, within the renewed lease.
            assert renewed.wait(1)
            other = Workflow(Store(store.path), Registry(), provider)
            assert other.get(run.project_id, run.id).status == "running"
            with pytest.raises(Conflict, match="already running"):
                other.advance(run.project_id, run.id, retry_acknowledged=True)
            assert provider.calls == 1
        finally:
            release.set()
        assert future.result(timeout=2).stage == "validate"
    assert_heartbeat_stopped(run)
    with store.transaction() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM checkpoints WHERE run_id=? AND stage='execute'",
                (run.id,),
            ).fetchone()[0]
            == 1
        )


def test_expired_owner_cannot_renew_or_checkpoint(tmp_path, artifact_dict, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    import specbridge.workflow as module

    store, workflow, _provider, run, now, started, release = blocked_generation(
        tmp_path, artifact_dict, monkeypatch
    )
    monkeypatch.setattr(module, "HEARTBEAT_SECONDS", 3600, raising=False)
    with ThreadPoolExecutor() as pool:
        future = pool.submit(workflow.advance, run.project_id, run.id)
        try:
            assert started.wait(1)
            now[0] = 1200.0
            with store.transaction() as db:
                token, expiry = db.execute(
                    "SELECT lease,lease_until FROM runs WHERE id=?", (run.id,)
                ).fetchone()
            assert expiry == 1120.0
            assert hasattr(workflow, "_renew_lease"), "Lease renewal must be explicit"
            assert workflow._renew_lease(run.id, token) is False
            with store.transaction() as db:
                assert (
                    db.execute(
                        "SELECT lease_until FROM runs WHERE id=?", (run.id,)
                    ).fetchone()[0]
                    == expiry
                )
        finally:
            release.set()
        assert future.result(timeout=2).status == "failed"
    assert_heartbeat_stopped(run)
    with store.transaction() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM checkpoints WHERE run_id=? AND stage='execute'",
                (run.id,),
            ).fetchone()[0]
            == 0
        )


def test_replaced_lease_cannot_be_overwritten(tmp_path, artifact_dict, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    store, workflow, _provider, run, _now, started, release = blocked_generation(
        tmp_path, artifact_dict, monkeypatch
    )
    with ThreadPoolExecutor() as pool:
        future = pool.submit(workflow.advance, run.project_id, run.id)
        try:
            assert started.wait(1)
            with store.transaction() as db:
                db.execute(
                    "UPDATE runs SET lease='replacement',lease_until=2000 WHERE id=?",
                    (run.id,),
                )
        finally:
            release.set()
        with pytest.raises(Conflict, match="lease"):
            future.result(timeout=2)
    assert_heartbeat_stopped(run)
    with store.transaction() as db:
        assert (
            db.execute("SELECT lease FROM runs WHERE id=?", (run.id,)).fetchone()[0]
            == "replacement"
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM checkpoints WHERE run_id=? AND stage='execute'",
                (run.id,),
            ).fetchone()[0]
            == 0
        )


def test_heartbeat_failure_discards_result_and_redacts_error(
    tmp_path, artifact_dict, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    store, workflow, _provider, run, _now, started, release = blocked_generation(
        tmp_path, artifact_dict, monkeypatch
    )
    attempted = Event()

    def broken_renew(*args):
        attempted.set()
        raise RuntimeError("SECRET_HEARTBEAT_SENTINEL")

    monkeypatch.setattr(workflow, "_renew_lease", broken_renew, raising=False)
    with ThreadPoolExecutor() as pool:
        future = pool.submit(workflow.advance, run.project_id, run.id)
        try:
            assert started.wait(1)
            assert attempted.wait(1), "Heartbeat did not run"
        finally:
            release.set()
        failed = future.result(timeout=2)
    assert failed.status == "failed" and failed.error == "generation_failed"
    assert "SECRET_HEARTBEAT_SENTINEL" not in failed.model_dump_json()
    assert_heartbeat_stopped(run)
    with pytest.raises(RetryAcknowledgmentRequired):
        workflow.advance(run.project_id, run.id)
    with store.transaction() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM checkpoints WHERE run_id=? AND stage='execute'",
                (run.id,),
            ).fetchone()[0]
            == 0
        )


def test_provider_failure_stops_heartbeat(tmp_path, artifact_dict, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    _store, workflow, _provider, run, _now, started, release = blocked_generation(
        tmp_path, artifact_dict, monkeypatch, fail=True
    )
    renewed = Event()
    original = getattr(workflow, "_renew_lease", lambda *args: False)

    def renew(*args):
        result = original(*args)
        renewed.set()
        return result

    monkeypatch.setattr(workflow, "_renew_lease", renew, raising=False)
    with ThreadPoolExecutor() as pool:
        future = pool.submit(workflow.advance, run.project_id, run.id)
        try:
            assert started.wait(1)
            assert renewed.wait(1)
        finally:
            release.set()
        assert future.result(timeout=2).status == "failed"
    assert_heartbeat_stopped(run)


def test_abandoned_execute_requires_acknowledged_recovery(tmp_path, artifact_dict):
    store, workflow, provider, run = setup(tmp_path, artifact_dict)
    for _ in range(4):
        run = workflow.advance(run.project_id, run.id)
    with store.transaction() as db:
        stale = run.model_copy(update={"status": "running"})
        db.execute(
            "UPDATE runs SET data=?,lease='abandoned',lease_until=0 WHERE id=?",
            (stale.model_dump_json(), run.id),
        )
    assert workflow.get(run.project_id, run.id).status == "failed"
    with pytest.raises(RetryAcknowledgmentRequired):
        workflow.advance(run.project_id, run.id)
    assert (
        workflow.advance(run.project_id, run.id, retry_acknowledged=True).stage
        == "validate"
    )
    assert provider.calls == 1


def test_renewal_checks_expiry_after_acquiring_database(
    tmp_path, artifact_dict, monkeypatch
):
    from contextlib import contextmanager

    import specbridge.workflow as module

    now = [1000.0]
    monkeypatch.setattr(module, "time", SimpleNamespace(time=lambda: now[0]))
    store, workflow, _provider, run = setup(tmp_path, artifact_dict)
    with store.transaction() as db:
        db.execute(
            "UPDATE runs SET lease='test',lease_until=1050 WHERE id=?", (run.id,)
        )
    original = store.transaction

    @contextmanager
    def delayed_transaction():
        now[0] = 1100.0  # Simulate waiting for SQLite's writer lock.
        with original() as db:
            yield db

    monkeypatch.setattr(store, "transaction", delayed_transaction)
    assert workflow._renew_lease(run.id, "test") is False
