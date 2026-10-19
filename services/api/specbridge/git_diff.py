"""Git comparison engine and documentation file extraction."""

import difflib
import hashlib
from io import BytesIO
from zipfile import ZipFile

from .git_models import FileComparison, ThreeWayDiff
from .models import digest


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def extract_candidate_docs_files(
    raw_zip: bytes, manifest: dict[str, str]
) -> dict[str, bytes]:
    """Extract markdown documentation and snapshot files from an approved candidate zip."""
    docs_files: dict[str, bytes] = {}
    with ZipFile(BytesIO(raw_zip)) as archive:
        for name in manifest:
            if name.startswith("src/content/docs/"):
                base_name = name.removeprefix("src/content/docs/")
                content = archive.read(name)
                docs_files[base_name] = content
                if base_name == "index.md" and "README.md" not in docs_files:
                    docs_files["README.md"] = content
            elif name in ("README.md", "revision.json"):
                docs_files[name] = archive.read(name)
    return docs_files


def _compute_text_diff(
    old_bytes: bytes | None, new_bytes: bytes | None, filename: str
) -> str | None:
    if old_bytes == new_bytes:
        return None
    old_lines = (
        old_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
        if old_bytes
        else []
    )
    new_lines = (
        new_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
        if new_bytes
        else []
    )
    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
    return "".join(diff_lines) if diff_lines else None


def three_way_compare(
    base_files: dict[str, bytes],
    local_files: dict[str, bytes],
    incoming_files: dict[str, bytes],
    managed_paths: set[str],
    base_revision_id: str | None = None,
    base_digest: str | None = None,
    incoming_revision_id: str = "rev-incoming",
    incoming_digest: str = "digest-incoming",
    target_head_sha: str = "",
) -> ThreeWayDiff:
    """Perform three-way comparison between Base, Local (target branch), and Incoming package."""
    all_paths = sorted(
        set(base_files.keys()) | set(local_files.keys()) | set(incoming_files.keys())
    )
    comparisons: list[FileComparison] = []
    has_conflicts = False

    for path in all_paths:
        base_bytes = base_files.get(path)
        local_bytes = local_files.get(path)
        incoming_bytes = incoming_files.get(path)

        base_sha = _sha256(base_bytes) if base_bytes is not None else None
        local_sha = _sha256(local_bytes) if local_bytes is not None else None
        incoming_sha = _sha256(incoming_bytes) if incoming_bytes is not None else None

        is_managed = (path in managed_paths) or (path in incoming_files)

        # 1. Unmanaged file in local working tree
        if not is_managed:
            comparisons.append(
                FileComparison(
                    path=path,
                    status="unmodified",
                    base_sha=base_sha,
                    local_sha=local_sha,
                    incoming_sha=incoming_sha,
                    diff=None,
                    conflict_reason=None,
                    is_managed=False,
                )
            )
            continue

        # 2. File in base, but deleted by developer locally
        if base_bytes is not None and local_bytes is None:
            if incoming_bytes is not None and incoming_sha != base_sha:
                # Developer deleted file, but incoming modified it
                has_conflicts = True
                comparisons.append(
                    FileComparison(
                        path=path,
                        status="conflict",
                        base_sha=base_sha,
                        local_sha=None,
                        incoming_sha=incoming_sha,
                        diff=_compute_text_diff(base_bytes, incoming_bytes, path),
                        conflict_reason="developer_deleted_file",
                        is_managed=True,
                    )
                )
            else:
                # Both deleted or incoming did not touch it
                comparisons.append(
                    FileComparison(
                        path=path,
                        status="deleted",
                        base_sha=base_sha,
                        local_sha=None,
                        incoming_sha=incoming_sha,
                        diff=None,
                        conflict_reason=None,
                        is_managed=True,
                    )
                )
            continue

        # 3. File not in base (newly added)
        if base_bytes is None:
            if incoming_bytes is not None and local_bytes is None:
                # Clean addition from incoming
                comparisons.append(
                    FileComparison(
                        path=path,
                        status="added",
                        base_sha=None,
                        local_sha=None,
                        incoming_sha=incoming_sha,
                        diff=_compute_text_diff(None, incoming_bytes, path),
                        conflict_reason=None,
                        is_managed=True,
                    )
                )
            elif incoming_bytes is not None and local_bytes is not None:
                if local_sha == incoming_sha:
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="unmodified",
                            base_sha=None,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=None,
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                else:
                    # Developer created file with same path but different content
                    has_conflicts = True
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="conflict",
                            base_sha=None,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=_compute_text_diff(local_bytes, incoming_bytes, path),
                            conflict_reason="concurrent_creation",
                            is_managed=True,
                        )
                    )
            else:
                # Local unmanaged file
                comparisons.append(
                    FileComparison(
                        path=path,
                        status="unmodified",
                        base_sha=None,
                        local_sha=local_sha,
                        incoming_sha=None,
                        diff=None,
                        conflict_reason=None,
                        is_managed=False,
                    )
                )
            continue

        # 4. File in base and in local
        if base_bytes is not None and local_bytes is not None:
            if incoming_bytes is None:
                # Incoming package deleted this file
                if local_sha != base_sha:
                    has_conflicts = True
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="conflict",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=None,
                            diff=_compute_text_diff(local_bytes, None, path),
                            conflict_reason="modified_deleted_conflict",
                            is_managed=True,
                        )
                    )
                else:
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="deleted",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=None,
                            diff=_compute_text_diff(base_bytes, None, path),
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                continue

            # Path is present in base, local, and incoming
            if local_sha == base_sha:
                if incoming_sha == base_sha:
                    # Unmodified by both
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="unmodified",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=None,
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                else:
                    # Clean update from incoming
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="modified",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=_compute_text_diff(local_bytes, incoming_bytes, path),
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
            else:
                # Developer modified local file
                if incoming_sha == base_sha:
                    # Developer's edit preserved untouched
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="unmodified",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=None,
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                elif local_sha == incoming_sha:
                    # Both made identical modification
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="unmodified",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=None,
                            conflict_reason=None,
                            is_managed=True,
                        )
                    )
                else:
                    # Concurrent conflicting edit!
                    has_conflicts = True
                    comparisons.append(
                        FileComparison(
                            path=path,
                            status="conflict",
                            base_sha=base_sha,
                            local_sha=local_sha,
                            incoming_sha=incoming_sha,
                            diff=_compute_text_diff(local_bytes, incoming_bytes, path),
                            conflict_reason="concurrent_modification",
                            is_managed=True,
                        )
                    )

    # Compute deterministic changeset digest
    summary = {
        "base_revision_id": base_revision_id,
        "base_digest": base_digest,
        "incoming_revision_id": incoming_revision_id,
        "incoming_digest": incoming_digest,
        "target_head_sha": target_head_sha,
        "changes": [c.model_dump() for c in comparisons],
    }
    changeset_digest = digest(summary)

    return ThreeWayDiff(
        base_revision_id=base_revision_id,
        base_digest=base_digest,
        incoming_revision_id=incoming_revision_id,
        incoming_digest=incoming_digest,
        target_head_sha=target_head_sha,
        changes=comparisons,
        has_conflicts=has_conflicts,
        changeset_digest=changeset_digest,
    )
