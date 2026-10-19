from fastapi.testclient import TestClient
from specbridge.main import create_app


def test_delivery_meeting_actions_route(tmp_path):
    client = TestClient(
        create_app(
            data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    project = client.post("/api/projects", json={"name": "DeliveryMeetings"}).json()[
        "id"
    ]
    base = f"/api/projects/{project}"

    # Empty text -> 409
    bad_resp = client.post(
        f"{base}/delivery/meetings/extract",
        json={"text": "   ", "source_id": "src-1"},
    )
    assert bad_resp.status_code == 409

    # Valid transcript
    transcript = (
        "Weekly Standup - 2026-10-19\n"
        "- Action: Deploy Starlight docs template (Owner: @alex, Due: 2026-10-24)\n"
        "- Action: Clarify telemetry data retention policy\n"
    )
    resp = client.post(
        f"{base}/delivery/meetings/extract",
        json={
            "text": transcript,
            "source_id": "src-1",
            "meeting_title": "Sprint 42 Kickoff",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["meeting_title"] == "Sprint 42 Kickoff"
    assert len(data["actions"]) == 2
    assert data["actions"][0]["owner"] == "alex"
    assert data["actions"][0]["deadline"] == "2026-10-24"
    assert data["actions"][1]["owner"] is None
    assert data["actions"][1]["deadline"] is None
    assert data["unassigned_count"] == 1


def test_delivery_prioritization_route(tmp_path):
    client = TestClient(
        create_app(
            data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    project = client.post(
        "/api/projects", json={"name": "DeliveryPrioritization"}
    ).json()["id"]
    base = f"/api/projects/{project}"

    items = [
        {
            "item_id": "REQ-A",
            "title": "OAuth Login",
            "reach": 1000,
            "impact": 4,
            "confidence": 1.0,
            "effort": 2,
        },
        {
            "item_id": "REQ-B",
            "title": "CSV Download",
            "reach": 200,
            "impact": 2,
            "confidence": 0.8,
            "effort": 1,
        },
        {
            "item_id": "REQ-C",
            "title": "Missing Metric",
            "reach": 500,
            "impact": None,
            "confidence": 0.9,
            "effort": 2,
        },
    ]

    resp = client.post(
        f"{base}/delivery/prioritize",
        json={"method": "rice", "items": items},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["ranked_items"]) == 2
    assert data["ranked_items"][0]["item_id"] == "REQ-A"
    assert data["ranked_items"][0]["score"] == 2000.0
    assert len(data["unranked_items"]) == 1
    assert data["unranked_items"][0]["item_id"] == "REQ-C"


def test_delivery_jira_preview_and_sync_route(tmp_path):
    client = TestClient(
        create_app(
            data_dir=tmp_path, token="test", allowed_origin="http://127.0.0.1:5173"
        ),
        base_url="http://127.0.0.1:8000",
        headers={"Authorization": "Bearer test"},
    )
    project = client.post("/api/projects", json={"name": "DeliveryJira"}).json()["id"]
    base = f"/api/projects/{project}"

    target = {
        "project_key": "PROJ",
        "instance_url": "https://company.atlassian.net",
    }
    items = [
        {
            "id": "REQ-1",
            "title": "Patient Portal",
            "description": "Secure access to care plans",
            "type": "requirement",
        },
        {
            "id": "ACT-1",
            "title": "Review HIPAA guidelines",
            "description": "Legal audit",
            "type": "action",
            "assignee": "alex",
        },
    ]

    # Preview
    preview_resp = client.post(
        f"{base}/delivery/jira/preview",
        json={"target": target, "items": items},
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert len(preview["items_to_create"]) == 2
    assert preview["changeset_digest"] is not None

    # Sync with bad digest -> 409
    bad_sync = client.post(
        f"{base}/delivery/jira/sync",
        json={"preview": preview, "approval_digest": "tampered-digest"},
    )
    assert bad_sync.status_code == 409

    # Sync with valid digest -> 201
    good_sync = client.post(
        f"{base}/delivery/jira/sync",
        json={"preview": preview, "approval_digest": preview["changeset_digest"]},
    )
    assert good_sync.status_code == 201
    receipt = good_sync.json()
    assert receipt["status"] == "synced"
    assert len(receipt["created_issues"]) == 2
    assert receipt["created_issues"][0]["key"] == "PROJ-1"
    assert receipt["created_issues"][0]["issue_type"] == "Story"
    assert receipt["created_issues"][1]["key"] == "PROJ-2"
    assert receipt["created_issues"][1]["issue_type"] == "Task"

    # Idempotency
    resync = client.post(
        f"{base}/delivery/jira/sync",
        json={"preview": preview, "approval_digest": preview["changeset_digest"]},
    )
    assert resync.status_code == 201
    assert resync.json()["status"] == "already_synced"
