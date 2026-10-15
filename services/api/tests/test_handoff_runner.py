from io import BytesIO
from zipfile import ZipFile

import pytest

from scripts.verify_handoff import extract_package


def archive_bytes(name):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(name, "content")
    return buffer.getvalue()


@pytest.mark.parametrize(
    "name",
    ["../escape", "/absolute", "folder/../../escape", "folder\\escape", "C:/escape"],
)
def test_archive_paths_cannot_escape(tmp_path, name):
    with pytest.raises(ValueError):
        extract_package(archive_bytes(name), tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_extract_refuses_existing_directory(tmp_path):
    with pytest.raises(FileExistsError):
        extract_package(archive_bytes("index.md"), tmp_path)
    output = tmp_path / "new"
    extract_package(archive_bytes("index.md"), output)
    assert (output / "index.md").read_text() == "content"
