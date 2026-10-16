"""A bounded, data-only registry; global development skills are never searched."""

import hashlib
import re
from dataclasses import dataclass, replace
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
    files: dict[str, str] = Field(max_length=33)


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

    def _header(self, name: str) -> str:
        try:
            path = self._file(name, "SKILL.md")
            if path.stat().st_size > LIMIT:
                raise InvalidSkill()
            with path.open("rb") as stream:
                if stream.readline(LIMIT + 1) != b"---\n":
                    raise InvalidSkill()
                header = bytearray()
                while len(header) <= LIMIT:
                    line = stream.readline(LIMIT + 1)
                    if line == b"---\n":
                        return header.decode("utf-8")
                    if not line:
                        break
                    header.extend(line)
            raise InvalidSkill()
        except (OSError, UnicodeError) as error:
            raise InvalidSkill() from error

    def _metadata(self, name: str, header: str) -> tuple[SkillMetadata, Provenance]:
        try:
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
                or "SKILL.md" not in provenance.files
            ):
                raise InvalidSkill()
            for relative, expected in provenance.files.items():
                if (
                    relative != "SKILL.md" and not relative.startswith("references/")
                ) or (
                    len(relative) > 256
                    or any(p in ("", ".", "..") for p in relative.split("/"))
                    or not re.fullmatch(r"[a-f0-9]{64}", expected)
                ):
                    raise InvalidSkill()
            metadata = SkillMetadata(
                name=front.name, description=front.description, **details.model_dump()
            )
            return metadata, provenance
        except (
            ValueError,
            TypeError,
            yaml.YAMLError,
            ValidationError,
            RecursionError,
        ) as error:
            raise InvalidSkill() from error

    def load(self, name: str, *, with_output_contract: bool = False) -> Skill:
        try:
            raw = self._read(name, "SKILL.md")
            if not raw.startswith("---\n"):
                raise InvalidSkill()
            header, body = raw[4:].split("\n---\n", 1)
            metadata, provenance = self._metadata(name, header)
            if (
                not body.strip()
                or hashlib.sha256(raw.encode()).hexdigest()
                != provenance.files["SKILL.md"]
            ):
                raise InvalidSkill()
            skill = Skill(
                metadata,
                body,
                digest(provenance.model_dump()),
                provenance.model_dump(),
                {
                    path: value
                    for path, value in provenance.files.items()
                    if path != "SKILL.md"
                },
            )
            if (
                with_output_contract
                and "references/output-contract.md" in skill.references
            ):
                contract = self._reference(skill, "references/output-contract.md")
                skill = replace(skill, body=skill.body + "\n" + contract)
            return skill
        except (ValueError, TypeError, RecursionError) as error:
            raise InvalidSkill() from error

    def search(self, intent: str) -> list[SkillMetadata]:
        words = set(re.findall(r"[a-z0-9]+", intent.lower()))
        try:
            entries = sorted(self.root.iterdir())
        except OSError as error:
            raise InvalidSkill() from error
        metadata = [
            self._metadata(p.name, self._header(p.name))[0]
            for p in entries
            if p.is_dir()
        ]

        def rank(item: SkillMetadata) -> tuple[int, str]:
            name = set(item.name.split("-"))
            description = set(re.findall(r"[a-z0-9]+", item.description.lower()))
            return (-(3 * len(words & name) + len(words & description)), item.name)

        return sorted(metadata, key=rank)

    def reference(self, name: str, relative_path: str) -> str:
        return self._reference(self.load(name), relative_path)

    def _reference(self, skill: Skill, relative_path: str) -> str:
        if relative_path not in skill.references:
            raise InvalidSkill()
        content = self._read(skill.name, relative_path)
        if (
            hashlib.sha256(content.encode()).hexdigest()
            != skill.references[relative_path]
        ):
            raise InvalidSkill()
        return content
