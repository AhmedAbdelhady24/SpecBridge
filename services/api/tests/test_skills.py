import hashlib
import json
from pathlib import Path

import pytest
from specbridge.skills import InvalidSkill, SkillRegistry

ROOT = Path(__file__).resolve().parents[3] / "skills/runtime"


def copy_skill(tmp_path):
    import shutil

    shutil.copytree(ROOT, tmp_path / "runtime")
    return tmp_path / "runtime"


def rehash(root):
    folder = root / "feature-handoff"
    path = folder / "provenance.json"
    data = json.loads(path.read_text())
    data["files"] = {
        name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
        for name in data["files"]
    }
    path.write_text(json.dumps(data))


def test_discovery_and_progressive_reference():
    registry = SkillRegistry(ROOT)
    metadata = registry.search("feature requirements")
    assert [m.name for m in metadata] == ["feature-handoff"]
    assert not hasattr(metadata[0], "body")
    skill = registry.load("feature-handoff")
    assert skill.tool_allowlist == []
    assert len(skill.digest) == 64
    assert "source_ids" in registry.reference(
        skill.name, "references/output-contract.md"
    )
    assert registry.search("") == metadata


@pytest.mark.parametrize("name", ["../feature-handoff", "/tmp/x", "unknown"])
def test_invalid_name(name):
    with pytest.raises(InvalidSkill):
        SkillRegistry(ROOT).load(name)


@pytest.mark.parametrize(
    "path", ["../SKILL.md", "/etc/passwd", "references/../../x", "provenance.json"]
)
def test_reference_containment(path):
    with pytest.raises(InvalidSkill):
        SkillRegistry(ROOT).reference("feature-handoff", path)


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "unknown", "permissions", "yaml", "large", "name", "version"],
)
def test_reject_bad_metadata(tmp_path, mutation):
    root = copy_skill(tmp_path)
    path = root / "feature-handoff/SKILL.md"
    text = path.read_text()
    replacements = {
        "duplicate": (
            "name: feature-handoff",
            "name: feature-handoff\nname: feature-handoff",
        ),
        "unknown": ("name: feature-handoff", "unexpected: true\nname: feature-handoff"),
        "permissions": ("tool_allowlist: []", "tool_allowlist: [shell]"),
        "yaml": ("name: feature-handoff", "name: [broken"),
        "large": ("# Feature handoff", "x" * 131073),
        "name": ("name: feature-handoff", "name: other"),
        "version": ('version: "1.0.0"', 'version: "9.0.0"'),
    }
    path.write_text(text.replace(*replacements[mutation]))
    rehash(root)
    with pytest.raises(InvalidSkill):
        SkillRegistry(root).load("feature-handoff")


@pytest.mark.parametrize("target", ["directory", "reference"])
def test_symlinks_denied(tmp_path, target):
    root = copy_skill(tmp_path)
    path = root / "feature-handoff"
    if target == "directory":
        path.rename(root / "real")
        path.symlink_to(root / "real", target_is_directory=True)
    else:
        ref = path / "references/output-contract.md"
        ref.unlink()
        ref.symlink_to(ROOT / "feature-handoff/references/output-contract.md")
    with pytest.raises(InvalidSkill):
        SkillRegistry(root).load("feature-handoff")


def test_tamper_denied(tmp_path):
    root = copy_skill(tmp_path)
    (root / "feature-handoff/references/output-contract.md").write_text("changed")
    with pytest.raises(InvalidSkill):
        SkillRegistry(root).load("feature-handoff")


def test_nonregular_skill_file_denied(tmp_path):
    import os

    root = copy_skill(tmp_path)
    path = root / "feature-handoff/SKILL.md"
    path.unlink()
    os.mkfifo(path)
    # The registry must reject the file type before attempting a blocking read.
    with pytest.raises(InvalidSkill):
        SkillRegistry(root)._file("feature-handoff", "SKILL.md")


def test_ranking_is_deterministic(tmp_path):
    import shutil

    root = copy_skill(tmp_path)
    other = root / "risk-review"
    shutil.copytree(root / "feature-handoff", other)
    skill_path = other / "SKILL.md"
    skill_path.write_text(
        skill_path.read_text()
        .replace("name: feature-handoff", "name: risk-review")
        .replace(
            "Turn feature ideas and selected project evidence into traceable requirements and developer stories for a human-reviewed handoff.",
            "Review risk evidence.",
        )
    )
    provenance_path = other / "provenance.json"
    data = json.loads(provenance_path.read_text())
    data["files"]["SKILL.md"] = hashlib.sha256(skill_path.read_bytes()).hexdigest()
    provenance_path.write_text(json.dumps(data))
    registry = SkillRegistry(root)
    assert [m.name for m in registry.search("risk")] == [
        "risk-review",
        "feature-handoff",
    ]
    assert [m.name for m in registry.search("feature")] == [
        "feature-handoff",
        "risk-review",
    ]
    assert [m.name for m in registry.search("")] == ["feature-handoff", "risk-review"]


def test_reference_size_bound(tmp_path):
    root = copy_skill(tmp_path)
    (root / "feature-handoff/references/output-contract.md").write_bytes(b"x" * 131073)
    rehash(root)
    with pytest.raises(InvalidSkill):
        SkillRegistry(root).reference(
            "feature-handoff", "references/output-contract.md"
        )
