from pathlib import Path

from fastapi.testclient import TestClient
from specbridge.main import create_app


def test_project_source_contract_and_sanitized_validation(tmp_path: Path):
    client = TestClient(
        create_app(
            data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    project = client.post("/api/projects", json={"name": "Reports"})
    assert project.status_code == 201
    project_id = project.json()["id"]
    source = client.post(
        f"/api/projects/{project_id}/sources",
        json={"text": "Customers requested export"},
    )
    assert source.status_code == 201
    assert source.json()["kind"] == "user_provided"
    invalid = client.post(
        "/api/projects",
        json={"name": "SECRET_SENTINEL", "unexpected": "SECRET_SENTINEL"},
    )
    assert invalid.status_code == 422
    assert "SECRET_SENTINEL" not in invalid.text
    assert client.get("/api/projects").json() == [project.json()]
