from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from specbridge.main import create_app, local_token


@pytest.fixture
def client(tmp_path: Path):
    return TestClient(
        create_app(
            data_dir=tmp_path,
            token="test-token",
            allowed_origin="http://127.0.0.1:5173",
        ),
        base_url="http://127.0.0.1:8000",
    )


def test_reads_require_token(client):
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/config").status_code == 401
    assert (
        client.get(
            "/api/config", headers={"Authorization": "Bearer test-token"}
        ).status_code
        == 200
    )


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://evil.example"},
        {"Origin": "null"},
        {"Host": "evil.example"},
        {"Host": "127.0.0.1.evil.example"},
    ],
)
def test_foreign_browser_denied(client, headers):
    headers["Authorization"] = "Bearer test-token"
    assert client.get("/api/config", headers=headers).status_code == 403


def test_token_is_private_and_stable(tmp_path):
    assert local_token(tmp_path) == local_token(tmp_path)
    assert (tmp_path / "session-token").stat().st_mode & 0o777 == 0o600


def test_nonlocal_origin_refused(tmp_path):
    with pytest.raises(ValueError):
        create_app(
            data_dir=tmp_path, token="test", allowed_origin="http://0.0.0.0:5173"
        )
