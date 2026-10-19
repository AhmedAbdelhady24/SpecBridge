import hashlib
import html
import json
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .models import Artifact, Statement, canonical, digest
from .workbench_models import DecisionSnapshot

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


def statements(values: list[Statement], sources: dict[str, str] | None = None) -> str:
    sources = sources or {}
    numbers = {key: i + 1 for i, key in enumerate(sources)}
    lines = []
    for value in values:
        citations = ", ".join(
            f"[Source {numbers[key]}](../provenance/#source-{numbers[key]})"
            for key in value.source_ids
            if key in numbers
        )
        lines.append(
            f"- {text(value.text)} — {value.kind}; sources: {citations or 'No source text supplied'}"
        )
    return "\n".join(lines) or "Not supplied."


def page(title: str, body: str) -> bytes:
    return ("---\ntitle: " + canonical(title) + "\n---\n\n" + body + "\n").encode()


@dataclass(frozen=True)
class CandidatePackage:
    zip_bytes: bytes
    manifest: dict[str, str]
    template_digest: str
    digest: str


def render_package(
    artifact: Artifact,
    provenance: dict[str, str],
    template_root: Path,
    *,
    decisions: DecisionSnapshot | None = None,
) -> CandidatePackage:
    files = template_files(template_root)
    template_hash = digest(hashes(files))
    try:
        raw_sources = json.loads(provenance.get("source_texts", "{}"))
    except (ValueError, TypeError):
        raw_sources = {}
    sources = (
        {
            key: value
            for key, value in sorted(raw_sources.items())
            if isinstance(key, str) and isinstance(value, str)
        }
        if isinstance(raw_sources, dict)
        else {}
    )
    source_quotes = "\n\n".join(
        f"## Source {i}\n\n"
        + "\n".join("> " + text(line) for line in value.split("\n"))
        for i, value in enumerate(sources.values(), 1)
    )
    requirement_numbers = {r.id: i for i, r in enumerate(artifact.requirements, 1)}
    pages = {
        "index": (
            artifact.title,
            "## Product overview\n\n"
            + text(artifact.purpose)
            + "\n\n## Scope\n\n"
            + statements(artifact.scope, sources)
            + "\n\n## Non-goals\n\n"
            + statements(artifact.non_goals, sources),
        ),
        "edge-cases": (
            "Edge cases and QA",
            statements(artifact.edge_cases, sources)
            + "\n\n## QA scenarios\n\nTest each story's acceptance criteria, invalid input, retry behavior and unresolved questions. These are proposed checks, not executed QA results.",
        ),
        "risks": (
            "Risks, dependencies and metrics",
            "## Risks\n\n"
            + statements(artifact.risks, sources)
            + "\n\n## Dependencies\n\n"
            + statements(artifact.dependencies, sources)
            + "\n\n## Proposed success metrics\n\n"
            + statements(artifact.success_metrics, sources),
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
                + f"Requirement {i}"
                + "\n\n"
                + statements([requirement], sources)
                + "\n\nStories: "
                + ", ".join(
                    f"[Story {j}: {text(story.text[:120])}](../stories/#story-{j})"
                    for j, story in enumerate(artifact.stories, 1)
                    if requirement.id in story.requirement_ids
                )
                for i, requirement in enumerate(artifact.requirements, 1)
            ),
        ),
        "stories": (
            "User stories and acceptance criteria",
            "\n\n".join(
                "## "
                + f"Story {i}"
                + "\n\n"
                + statements([story], sources)
                + "\n\nRequirements: "
                + ", ".join(
                    f"[Requirement {requirement_numbers[key]}: {text(next(r.text for r in artifact.requirements if r.id == key)[:120])}](../requirements/#requirement-{requirement_numbers[key]})"
                    for key in story.requirement_ids
                    if key in requirement_numbers
                )
                + "\n\n### Acceptance criteria\n\n"
                + "\n".join(
                    "- " + text(criterion) for criterion in story.acceptance_criteria
                )
                for i, story in enumerate(artifact.stories, 1)
            ),
        ),
        "provenance": (
            "Sources and revision history",
            "This is an approved snapshot, not a live project-status report. User input remains user-provided information, not independently verified fact.\n\n"
            + source_quotes
            + "\n\n## Technical revision details\n\n"
            + "\n\n".join(
                f"### {text(key)}\n\n{text(value)}"
                for key, value in sorted(provenance.items())
                if key != "source_texts"
            ),
        ),
    }
    pages["provenance"] = (
        pages["provenance"][0],
        pages["provenance"][1]
        + "\n\n"
        + "\n".join(f"- Source {i}: {text(key)}" for i, key in enumerate(sources, 1))
        + "\n"
        + "\n".join(
            f"- Requirement {i}: {text(r.id)}"
            for i, r in enumerate(artifact.requirements, 1)
        )
        + "\n"
        + "\n".join(
            f"- Story {i}: {text(r.id)}" for i, r in enumerate(artifact.stories, 1)
        ),
    )
    decisions = decisions or DecisionSnapshot()
    decision_lines = [
        "This is recorded decision history, not independently verified fact. Each resolution names its revision; later edits may supersede it. Inspect the current requirements for applicability."
    ]
    for question in decisions.questions:
        decision_lines.append("## " + text(question.text))
        decision_lines.append(
            text(question.latest_answer.text)
            if question.latest_answer
            else "Answer not supplied."
        )
        decision_lines.append(
            "Resolved in revision: "
            + text(question.resolution_revision_id or "unknown")
        )
        decision_lines.append(
            "Targets: " + ", ".join(text(target) for target in question.targets)
        )
    for request in decisions.requests:
        decision_lines.append("## Addressed change request")
        decision_lines.append(text(request.text))
        decision_lines.append(
            "Addressed in revision: "
            + text(request.resolution_revision_id or "unknown")
        )
    if not decisions.questions and not decisions.requests:
        decision_lines.append(
            "No resolved decisions or addressed requests were incorporated in this snapshot."
        )
    pages["decisions"] = (
        "Resolved decisions and review changes",
        "\n\n".join(decision_lines),
    )
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
                "decisions": decisions.model_dump(),
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
