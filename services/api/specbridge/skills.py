"""A bounded, data-only registry; global development skills are never searched."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, ValidationError

from specbridge.models import Model, digest

LIMIT = 128 * 1024
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class InvalidSkill(ValueError):
    def __init__(self) -> None:
        super().__init__("invalid_skill")


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise InvalidSkill()
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


class SkillMetadata(Model):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=1024)
    version: str
    schema_version: int
    tool_allowlist: list[str]


class Details(Model):
    version: str
    schema_version: int
    tool_allowlist: list[str]


class Frontmatter(Model):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=1024)
    metadata: Details


class Provenance(Model):
    schema_version: int
    version: str
    authorship: str = Field(min_length=1)
    license_observation: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    tool_allowlist: list[str]
    files: dict[str, str]


@dataclass(frozen=True)
class Skill:
    metadata: SkillMetadata
    body: str
    digest: str
    provenance: dict[str, Any]
    references: dict[str, str]

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def tool_allowlist(self) -> list[str]:
        return self.metadata.tool_allowlist


class SkillRegistry:
    def __init__(self, root: Path):
        self.root = root.absolute()

    def _file(self, name: str, relative: str) -> Path:
        if not NAME.fullmatch(name) or len(name) > 64:
            raise InvalidSkill()
        parts = relative.split("/")
        if not parts or any(p in ("", ".", "..") for p in parts):
            raise InvalidSkill()
        path = self.root
        # Reject symlinks in the root itself and every ancestor/component.
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise InvalidSkill()
        for component in [name, *parts]:
            path = path / component
            if path.is_symlink():
                raise InvalidSkill()
        if not path.is_file():
            raise InvalidSkill()
        return path

    def _read(self, name: str, relative: str) -> str:
        try:
            with self._file(name, relative).open("rb") as stream:
                data = stream.read(LIMIT + 1)
            if len(data) > LIMIT:
                raise InvalidSkill()
            return data.decode("utf-8")
        except (OSError, UnicodeError) as error:
            raise InvalidSkill() from error

    def load(self, name: str) -> Skill:
        try:
            raw = self._read(name, "SKILL.md")
            if not raw.startswith("---\n"):
                raise InvalidSkill()
            header, body = raw[4:].split("\n---\n", 1)
            front = Frontmatter.model_validate(yaml.load(header, Loader=UniqueLoader))
            provenance = Provenance.model_validate_json(
                self._read(name, "provenance.json")
            )
            details = front.metadata
            if (
                front.name != name
                or details.schema_version != 1
                or provenance.schema_version != 1
                or details.version != provenance.version
                or details.tool_allowlist
                or provenance.tool_allowlist
                or not body.strip()
            ):
                raise InvalidSkill()
            if "SKILL.md" not in provenance.files:
                raise InvalidSkill()
            references = {}
            for relative, expected in provenance.files.items():
                if relative != "SKILL.md" and not relative.startswith("references/"):
                    raise InvalidSkill()
                content = raw if relative == "SKILL.md" else self._read(name, relative)
                if hashlib.sha256(content.encode()).hexdigest() != expected:
                    raise InvalidSkill()
                if relative != "SKILL.md":
                    references[relative] = expected
            metadata = SkillMetadata(
                name=front.name, description=front.description, **details.model_dump()
            )
            return Skill(
                metadata,
                body,
                digest(provenance.model_dump()),
                provenance.model_dump(),
                references,
            )
        except (ValueError, TypeError, yaml.YAMLError, ValidationError) as error:
            raise InvalidSkill() from error

    def search(self, intent: str) -> list[SkillMetadata]:
        words = set(re.findall(r"[a-z0-9]+", intent.lower()))
        try:
            entries = sorted(self.root.iterdir())
        except OSError as error:
            raise InvalidSkill() from error
        metadata = [self.load(p.name).metadata for p in entries if p.is_dir()]

        def rank(item: SkillMetadata) -> tuple[int, str]:
            name = set(item.name.split("-"))
            description = set(re.findall(r"[a-z0-9]+", item.description.lower()))
            return (-(3 * len(words & name) + len(words & description)), item.name)

        return sorted(metadata, key=rank)

    def reference(self, name: str, relative_path: str) -> str:
        skill = self.load(name)
        if relative_path not in skill.references:
            raise InvalidSkill()
        content = self._read(name, relative_path)
        if (
            hashlib.sha256(content.encode()).hexdigest()
            != skill.references[relative_path]
        ):
            raise InvalidSkill()
        return content
