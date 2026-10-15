from types import SimpleNamespace

import pytest
from specbridge.models import Artifact
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
    def load(self, name):
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
