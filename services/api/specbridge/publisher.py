import hashlib
import html
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .models import Artifact, Statement, canonical, digest

TEMPLATE_FILES = (
    "package.json",
    "package-lock.json",
    "astro.config.mjs",
    "tsconfig.json",
    "src/content.config.ts",
    "src/content/docs/index.md",
    "README.md",
    ".gitignore",
)


def template_files(root: Path) -> dict[str, bytes]:
    if root.is_symlink():
        raise ValueError("Template root cannot be a symlink")
    files = {}
    for name in TEMPLATE_FILES:
        path = root / name
        if (
            any(part.is_symlink() for part in [path, *path.parents])
            or not path.is_file()
        ):
            raise ValueError("Template must contain fixed regular files")
        if path.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("Template file too large")
        files[name] = path.read_bytes()
    return files


def hashes(files: dict[str, bytes]) -> dict[str, str]:
    return {
        name: hashlib.sha256(content).hexdigest()
        for name, content in sorted(files.items())
    }


def template_digest(root: Path) -> str:
    return digest(hashes(template_files(root)))


def text(value: str) -> str:
    return re.sub(
        r"([\\`*{}\[\]()#+\-.!|_>~])", r"\\\1", html.escape(value, quote=False)
    )


def statements(values: list[Statement]) -> str:
    return (
        "\n".join(
            f"- {text(value.text)} — {value.kind}; sources: {', '.join(text(s) for s in value.source_ids) or 'none supplied'}"
            for value in values
        )
        or "Not supplied."
    )


def page(title: str, body: str) -> bytes:
    return ("---\ntitle: " + canonical(title) + "\n---\n\n" + body + "\n").encode()


@dataclass(frozen=True)
class CandidatePackage:
    zip_bytes: bytes
    manifest: dict[str, str]
    template_digest: str
    digest: str


def render_package(
    artifact: Artifact, provenance: dict[str, str], template_root: Path
) -> CandidatePackage:
    files = template_files(template_root)
    template_hash = digest(hashes(files))
    pages = {
        "index": (
            artifact.title,
            "# Product overview\n\n"
            + text(artifact.purpose)
            + "\n\n## Scope\n\n"
            + statements(artifact.scope)
            + "\n\n## Non-goals\n\n"
            + statements(artifact.non_goals),
        ),
        "edge-cases": (
            "Edge cases and QA",
            statements(artifact.edge_cases)
            + "\n\n## QA scenarios\n\nTest each story's acceptance criteria, invalid input, retry behavior and unresolved questions. These are proposed checks, not executed QA results.",
        ),
        "risks": (
            "Risks, dependencies and metrics",
            "## Risks\n\n"
            + statements(artifact.risks)
            + "\n\n## Dependencies\n\n"
            + statements(artifact.dependencies)
            + "\n\n## Proposed success metrics\n\n"
            + statements(artifact.success_metrics),
        ),
        "questions": (
            "Open questions and technical constraints",
            "\n".join("- " + text(question) for question in artifact.open_questions)
            + "\n\n## API contracts, architecture and decisions\n\nNot supplied or approved. Resolve these with the engineering team; this package does not invent API definitions, owners, deadlines or implementation decisions.\n\n## Release and external references\n\nNo release status, Jira or GitHub target was supplied.",
        ),
        "requirements": (
            "Requirements",
            "\n\n".join(
                "## "
                + requirement.id
                + "\n\n"
                + statements([requirement])
                + "\n\nStories: "
                + ", ".join(
                    f"[{story.id}](../stories/#{story.id.lower()})"
                    for story in artifact.stories
                    if requirement.id in story.requirement_ids
                )
                for requirement in artifact.requirements
            ),
        ),
        "stories": (
            "User stories and acceptance criteria",
            "\n\n".join(
                "## "
                + story.id
                + "\n\n"
                + statements([story])
                + "\n\nRequirements: "
                + ", ".join(
                    f"[{key}](../requirements/#{key.lower()})"
                    for key in story.requirement_ids
                )
                + "\n\n### Acceptance criteria\n\n"
                + "\n".join(
                    "- " + text(criterion) for criterion in story.acceptance_criteria
                )
                for story in artifact.stories
            ),
        ),
        "provenance": (
            "Sources and revision history",
            "This is an approved snapshot, not a live project-status report. User input remains user-provided information, not independently verified fact.\n\n"
            + "\n\n".join(
                f"## {text(key)}\n\n{text(value)}"
                for key, value in sorted(provenance.items())
            ),
        ),
    }
    for slug, (title, body) in pages.items():
        files[f"src/content/docs/{slug}.md"] = page(title, body)
    mapping = {
        requirement.id: [
            story.id
            for story in artifact.stories
            if requirement.id in story.requirement_ids
        ]
        for requirement in artifact.requirements
    }
    files["revision.json"] = (
        canonical(
            {
                "artifact": artifact.model_dump(),
                "provenance": provenance,
                "requirement_stories": mapping,
            }
        )
        + "\n"
    ).encode()
    files["manifest.json"] = (
        canonical(
            {
                "template_digest": template_hash,
                "artifact_digest": digest(artifact.model_dump()),
                "files": hashes(files),
            }
        )
        + "\n"
    ).encode()
    manifest = hashes(files)
    if sum(len(content) for content in files.values()) > 20 * 1024 * 1024:
        raise ValueError("Documentation package exceeds the size limit")
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    return CandidatePackage(
        zip_bytes=buffer.getvalue(),
        manifest=manifest,
        template_digest=template_hash,
        digest=digest(
            {
                "template": template_hash,
                "files": manifest,
                "provenance": provenance,
                "zip": hashlib.sha256(buffer.getvalue()).hexdigest(),
            }
        ),
    )
