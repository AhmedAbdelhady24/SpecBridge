"""Delivery automation routes for meeting action extraction, prioritization, and Jira sync."""

from typing import Any

from fastapi import FastAPI

from .delivery import (
    DeliveryService,
    DeliverySyncPreview,
    DeliverySyncReceipt,
    JiraTarget,
    MeetingActionsResult,
    PrioritizationRequest,
    PrioritizationResult,
    extract_meeting_actions,
    prioritize_items,
)
from .models import Model
from .storage import Conflict, Store


class MeetingExtractInput(Model):
    text: str
    source_id: str
    meeting_title: str = "Team Sync"


class JiraPreviewInput(Model):
    target: JiraTarget
    items: list[dict[str, Any]]


class JiraSyncInput(Model):
    preview: DeliverySyncPreview
    approval_digest: str


def register_delivery_routes(
    app: FastAPI,
    store: Store,
    delivery_service: DeliveryService | None = None,
) -> None:
    service = delivery_service or DeliveryService()

    @app.post("/api/projects/{project_id}/delivery/meetings/extract")
    def extract_actions(
        project_id: str, body: MeetingExtractInput
    ) -> MeetingActionsResult:
        with store.transaction() as db:
            store.require_project(db, project_id)
        if not body.text.strip():
            raise Conflict("Meeting text cannot be empty")
        return extract_meeting_actions(body.text, body.source_id, body.meeting_title)

    @app.post("/api/projects/{project_id}/delivery/prioritize")
    def prioritize(
        project_id: str, body: PrioritizationRequest
    ) -> PrioritizationResult:
        with store.transaction() as db:
            store.require_project(db, project_id)
        return prioritize_items(body)

    @app.post("/api/projects/{project_id}/delivery/jira/preview")
    def preview_jira(project_id: str, body: JiraPreviewInput) -> DeliverySyncPreview:
        with store.transaction() as db:
            store.require_project(db, project_id)
        return service.prepare_jira_sync_preview(
            project_id=project_id, target=body.target, items=body.items
        )

    @app.post("/api/projects/{project_id}/delivery/jira/sync", status_code=201)
    def sync_jira(project_id: str, body: JiraSyncInput) -> DeliverySyncReceipt:
        with store.transaction() as db:
            store.require_project(db, project_id)
        try:
            receipt = service.sync_jira(
                preview=body.preview, approval_digest=body.approval_digest
            )
        except ValueError as err:
            raise Conflict(str(err)) from err

        with store.transaction() as db:
            store.audit(db, project_id, "jira_sync", receipt.id)

        return receipt
