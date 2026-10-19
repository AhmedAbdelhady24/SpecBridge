import pytest
from specbridge.delivery import (
    DeliveryService,
    JiraTarget,
    MockJiraAdapter,
    PrioritizationRequest,
    extract_meeting_actions,
    prioritize_items,
)


def test_deterministic_prioritization_rice():
    items = [
        {
            "item_id": "REQ-1",
            "title": "CSV Export",
            "reach": 500,
            "impact": 3,
            "confidence": 0.8,
            "effort": 2,
        },
        {
            "item_id": "REQ-2",
            "title": "Dark Mode",
            "reach": 200,
            "impact": 1,
            "confidence": 0.9,
            "effort": 1,
        },
        {
            "item_id": "REQ-3",
            "title": "SSO Login",
            "reach": 1000,
            "impact": 5,
            "confidence": 1.0,
            "effort": 4,
        },
        {
            "item_id": "REQ-4",
            "title": "Vague Idea",
            "reach": 100,
            "impact": None,
            "confidence": 0.5,
            "effort": 2,
        },
    ]

    req = PrioritizationRequest(method="rice", items=items)
    result = prioritize_items(req)

    assert result.method == "rice"
    # REQ-3: (1000 * 5 * 1.0) / 4 = 1250.0
    # REQ-1: (500 * 3 * 0.8) / 2 = 600.0
    # REQ-2: (200 * 1 * 0.9) / 1 = 180.0
    assert len(result.ranked_items) == 3
    assert result.ranked_items[0].item_id == "REQ-3"
    assert result.ranked_items[0].score == 1250.0
    assert result.ranked_items[0].rank == 1

    assert result.ranked_items[1].item_id == "REQ-1"
    assert result.ranked_items[1].score == 600.0
    assert result.ranked_items[1].rank == 2

    assert result.ranked_items[2].item_id == "REQ-2"
    assert result.ranked_items[2].score == 180.0
    assert result.ranked_items[2].rank == 3

    # REQ-4 had missing impact: preserved as unranked, never guessed
    assert len(result.unranked_items) == 1
    assert result.unranked_items[0].item_id == "REQ-4"
    assert "impact" in result.unranked_items[0].missing_metrics
    assert result.unranked_items[0].score is None


def test_prioritization_is_strictly_deterministic():
    items = [
        {
            "item_id": "B",
            "title": "Item B",
            "reach": 100,
            "impact": 2,
            "confidence": 0.5,
            "effort": 1,
        },
        {
            "item_id": "A",
            "title": "Item A",
            "reach": 100,
            "impact": 2,
            "confidence": 0.5,
            "effort": 1,
        },
    ]
    req = PrioritizationRequest(method="rice", items=items)
    r1 = prioritize_items(req)
    r2 = prioritize_items(req)
    assert [x.item_id for x in r1.ranked_items] == [x.item_id for x in r2.ranked_items]
    # Tied score resolved deterministically by item_id
    assert r1.ranked_items[0].item_id == "A"
    assert r1.ranked_items[1].item_id == "B"


def test_meeting_actions_extraction_preserves_unknowns():
    notes = (
        "Meeting Transcript - Q4 Planning\n"
        "Date: 2026-10-18\n"
        "- Action: Set up production monitoring (Owner: @sarah, Due: 2026-10-31)\n"
        "- Action: Review FHIR mapping specification\n"
        "- Action: Audit session timeout edge cases (Owner: @david)\n"
    )
    result = extract_meeting_actions(
        notes, source_id="src-meeting-1", meeting_title="Q4 Planning"
    )
    assert result.meeting_title == "Q4 Planning"
    assert len(result.actions) == 3

    # Action 1: Owner and deadline present
    a1 = result.actions[0]
    assert "Set up production monitoring" in a1.description
    assert a1.owner == "sarah"
    assert a1.deadline == "2026-10-31"
    assert a1.source_quote in notes  # exact verbatim quote

    # Action 2: Missing owner and deadline -> explicitly None, not fabricated
    a2 = result.actions[1]
    assert "Review FHIR mapping specification" in a2.description
    assert a2.owner is None
    assert a2.deadline is None
    assert a2.source_quote in notes

    # Action 3: Owner present, deadline missing
    a3 = result.actions[2]
    assert a3.owner == "david"
    assert a3.deadline is None

    assert result.unassigned_count == 1
    assert result.digest is not None


def test_mock_jira_adapter_and_delivery_service():
    adapter = MockJiraAdapter()
    service = DeliveryService(jira_adapter=adapter)

    target = JiraTarget(
        project_key="SPEC",
        instance_url="https://acme.atlassian.net",
    )

    items = [
        {
            "id": "REQ-101",
            "title": "OAuth2 Login",
            "description": "Users can authenticate via Google/GitHub OAuth2.",
            "type": "requirement",
            "priority": "High",
        },
        {
            "id": "ACT-201",
            "title": "Configure staging secrets",
            "description": "Store secrets in KMS.",
            "type": "action",
            "priority": "Medium",
            "assignee": "sarah",
        },
    ]

    preview = service.prepare_jira_sync_preview(
        project_id="proj-delivery-1",
        target=target,
        items=items,
    )

    assert len(preview.items_to_create) == 2
    assert preview.changeset_digest is not None

    # Mismatched approval digest fails
    with pytest.raises(ValueError, match="approval_digest_mismatch"):
        service.sync_jira(preview, approval_digest="wrong-digest")

    # Valid approval digest succeeds
    receipt = service.sync_jira(preview, approval_digest=preview.changeset_digest)
    assert receipt.status == "synced"
    assert len(receipt.created_issues) == 2
    assert receipt.created_issues[0]["key"] == "SPEC-1"
    assert receipt.created_issues[0]["issue_type"] == "Story"
    assert receipt.created_issues[1]["key"] == "SPEC-2"
    assert receipt.created_issues[1]["issue_type"] == "Task"
    assert receipt.created_issues[1]["assignee"] == "sarah"

    # Idempotent re-sync
    receipt2 = service.sync_jira(preview, approval_digest=preview.changeset_digest)
    assert receipt2.status == "already_synced"
    assert receipt2.id == receipt.id

    # Audit log in adapter
    audit = adapter.get_audit_log("SPEC")
    assert len(audit) == 2
    assert audit[0]["action"] == "create_issue"
