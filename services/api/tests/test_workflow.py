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
