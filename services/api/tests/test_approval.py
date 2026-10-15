from io import BytesIO
from zipfile import ZipFile

import pytest
from specbridge.models import Artifact
from specbridge.publication import Publication
from specbridge.publisher import TEMPLATE_FILES
from specbridge.storage import Conflict, NotFound, Store


@pytest.fixture
def publication(tmp_path, artifact_dict):
    template = tmp_path / "template"
    for name in TEMPLATE_FILES:
        path = template / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}" if name.endswith("json") else "static template")
    store = Store(tmp_path / "db")
    project = store.create_project("Reports")
    revision = store.save_revision(
        project.id, Artifact.model_validate(artifact_dict), None
    )
    return Publication(store, template), store, project, revision


def test_review_then_exact_approval_and_download(publication):
    service, store, project, revision = publication
    candidate = service.prepare(project.id, revision.id)
    assert candidate.id == service.prepare(project.id, revision.id).id
    with pytest.raises(Conflict):
        service.download(project.id, candidate.id)
    with pytest.raises(Conflict):
        service.approve(project.id, candidate.id, candidate.digest)
    service.review(
        project.id, revision.id, "reviewed", "Unknowns explicitly accepted for handoff"
    )
    service.approve(project.id, candidate.id, candidate.digest)
    assert service.approve(project.id, candidate.id, candidate.digest).approved
    first = service.download(project.id, candidate.id)
    assert first == service.download(project.id, candidate.id)
    with ZipFile(BytesIO(first)) as archive:
        assert archive.testzip() is None
    other = store.create_project("Other")
    with pytest.raises(NotFound):
        service.download(other.id, candidate.id)


def test_revision_template_and_rejection_invalidate(publication):
    service, store, project, revision = publication
    candidate = service.prepare(project.id, revision.id)
    service.review(project.id, revision.id, "reviewed", "Reviewed")
    service.approve(project.id, candidate.id, candidate.digest)
    service.review(project.id, revision.id, "rejected", "Need clarification")
    with pytest.raises(Conflict):
        service.prepare(project.id, revision.id)
    with pytest.raises(Conflict):
        service.download(project.id, candidate.id)
    service.review(project.id, revision.id, "reviewed", "Clarified")
    (service.template_root / "package.json").write_text('{"changed": true}')
    with pytest.raises(Conflict):
        service.download(project.id, candidate.id)
    new = service.prepare(project.id, revision.id)
    service.approve(project.id, new.id, new.digest)
    changed = revision.artifact.model_copy(deep=True)
    changed.title = "Different content"
    store.save_revision(project.id, changed, revision.digest)
    with pytest.raises(Conflict):
        service.download(project.id, new.id)


def test_stored_package_corruption_is_detected(publication):
    service, store, project, revision = publication
    candidate = service.prepare(project.id, revision.id)
    service.review(project.id, revision.id, "reviewed", "Checked")
    service.approve(project.id, candidate.id, candidate.digest)
    with store.transaction() as db:
        db.execute(
            "UPDATE candidates SET zip=CAST(zip || X'00' AS BLOB) WHERE id=?",
            (candidate.id,),
        )
    with pytest.raises(Conflict):
        service.download(project.id, candidate.id)


@pytest.mark.parametrize("action", ["approve", "download"])
def test_template_change_while_waiting_for_transaction(
    publication, monkeypatch, action
):
    from contextlib import contextmanager

    service, store, project, revision = publication
    candidate = service.prepare(project.id, revision.id)
    service.review(project.id, revision.id, "reviewed", "Checked")
    service.approve(project.id, candidate.id, candidate.digest)
    original = store.transaction

    @contextmanager
    def delayed_transaction():
        (service.template_root / "package.json").write_text('{"changed": true}')
        with original() as db:
            yield db

    monkeypatch.setattr(store, "transaction", delayed_transaction)
    with pytest.raises(Conflict):
        if action == "approve":
            service.approve(project.id, candidate.id, candidate.digest)
        else:
            service.download(project.id, candidate.id)
