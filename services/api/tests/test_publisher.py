import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from specbridge.models import Artifact
from specbridge.publisher import TEMPLATE_FILES, render_package, template_digest


@pytest.fixture
def template(tmp_path):
    for name in TEMPLATE_FILES:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("{}" if name.endswith("json") else "fixed template\n")
    return tmp_path


def test_reproducible_safe_complete_zip(artifact_dict, template):
    artifact_dict["purpose"] = (
        '<script>alert(1)</script> ![steal](https://evil.example/img) {import("bad")}'
    )
    artifact_dict["title"] = "---\n<script>Bad</script>"
    artifact = Artifact.model_validate(artifact_dict)
    first = render_package(artifact, {"revision_id": "rev-1"}, template)
    second = render_package(artifact, {"revision_id": "rev-1"}, template)
    assert first.zip_bytes == second.zip_bytes
    assert first.digest == second.digest
    with ZipFile(BytesIO(first.zip_bytes)) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert "package-lock.json" in names
        assert "src/content/docs/requirements.md" in names
        assert all(
            not Path(name).is_absolute() and ".." not in Path(name).parts
            for name in names
        )
        markdown = archive.read("src/content/docs/index.md").decode()
        assert (
            json.loads(markdown.splitlines()[1].removeprefix("title: "))
            == artifact.title
        )
        assert "<script>" not in markdown.split("---\n", 2)[2]
        assert "![steal]" not in markdown
        assert "&lt;script&gt;" in markdown
        assert "\n# Product overview" not in markdown
        assert (
            json.loads(archive.read("revision.json"))["artifact"]["title"]
            == artifact.title
        )
    (template / "package.json").write_text('{"changed": true}')
    assert template_digest(template) != first.template_digest


def test_template_symlink_rejected(artifact_dict, template, tmp_path):
    target = template / "package.json"
    target.unlink()
    target.symlink_to("/etc/hosts")
    with pytest.raises(ValueError):
        render_package(Artifact.model_validate(artifact_dict), {}, template)


def test_exported_template_has_no_vulnerable_selector_parser(artifact_dict):
    root = Path(__file__).resolve().parents[3] / "packages/docs-template"
    package = render_package(Artifact.model_validate(artifact_dict), {}, root)
    with ZipFile(BytesIO(package.zip_bytes)) as archive:
        lock = json.loads(archive.read("package-lock.json"))
        parsers = [
            item["version"]
            for path, item in lock["packages"].items()
            if path.endswith("node_modules/postcss-selector-parser")
        ]
        assert parsers
        assert all(
            tuple(map(int, version.split("."))) >= (7, 1, 6) for version in parsers
        )


def test_readable_quotes_and_links_preserve_technical_mapping(artifact_dict, template):
    source_id = "source-opaque-uuid"
    source = 'Original spec: Export saved reports. <img src="https://evil.example">'
    artifact_dict["requirements"][0]["source_ids"] = [source_id]
    package = render_package(
        Artifact.model_validate(artifact_dict),
        {"source_texts": json.dumps({source_id: source})},
        template,
    )
    with ZipFile(BytesIO(package.zip_bytes)) as archive:
        requirements = archive.read("src/content/docs/requirements.md").decode()
        provenance = archive.read("src/content/docs/provenance.md").decode()
        assert "## Requirement 1" in requirements
        assert "[Story 1:" in requirements
        assert "../stories/#story-1" in requirements
        assert "[Source 1](../provenance/#source-1)" in requirements
        assert source_id not in requirements
        assert "Original spec: Export saved reports" in provenance
        assert "<img" not in provenance
        assert "&lt;img" in provenance
        assert json.loads(archive.read("revision.json"))["artifact"]["requirements"][0][
            "source_ids"
        ] == [source_id]
