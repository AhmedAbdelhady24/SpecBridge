"""Delivery automation domain model, deterministic prioritization, meeting actions, and Jira adapters."""

import re
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field

from .models import Model, digest


class ActionItem(Model):
    id: str
    description: str
    owner: str | None = None
    deadline: str | None = None
    status: Literal["not_started", "in_progress", "blocked", "done", "unknown"] = (
        "not_started"
    )
    source_id: str
    source_quote: str
    requirement_id: str | None = None


class MeetingActionsResult(Model):
    meeting_title: str
    date: str | None = None
    actions: list[ActionItem] = Field(default_factory=list)
    unassigned_count: int = 0
    digest: str = ""


class PriorityScore(Model):
    item_id: str
    title: str
    reach: float | None = None
    impact: float | None = None
    urgency: float | None = None
    effort: float | None = None
    confidence: float | None = None
    score: float | None = None
    rank: int = 0
    missing_metrics: list[str] = Field(default_factory=list)


class PrioritizationRequest(Model):
    method: Literal["rice", "weighted_criteria"] = "rice"
    items: list[dict[str, Any]] = Field(default_factory=list)


class PrioritizationResult(Model):
    method: str
    ranked_items: list[PriorityScore] = Field(default_factory=list)
    unranked_items: list[PriorityScore] = Field(default_factory=list)


class JiraTarget(Model):
    project_key: str
    instance_url: str
    issue_type_mapping: dict[str, str] = Field(
        default_factory=lambda: {
            "requirement": "Story",
            "story": "Sub-task",
            "action": "Task",
        }
    )


class DeliverySyncPreview(Model):
    target: JiraTarget
    items_to_create: list[dict[str, Any]] = Field(default_factory=list)
    items_to_update: list[dict[str, Any]] = Field(default_factory=list)
    changeset_digest: str = ""


class DeliverySyncReceipt(Model):
    id: str
    project_id: str
    created_issues: list[dict[str, Any]] = Field(default_factory=list)
    changeset_digest: str
    timestamp: str
    status: Literal["synced", "already_synced"] = "synced"


def prioritize_items(req: PrioritizationRequest) -> PrioritizationResult:
    ranked: list[PriorityScore] = []
    unranked: list[PriorityScore] = []

    for item in req.items:
        item_id = str(item.get("item_id") or item.get("id") or "")
        title = str(item.get("title") or item_id)
        reach = float(item["reach"]) if item.get("reach") is not None else None
        impact = float(item["impact"]) if item.get("impact") is not None else None
        urgency = float(item["urgency"]) if item.get("urgency") is not None else None
        effort = float(item["effort"]) if item.get("effort") is not None else None
        confidence = (
            float(item["confidence"]) if item.get("confidence") is not None else None
        )

        missing: list[str] = []

        if req.method == "rice":
            if reach is None or reach <= 0:
                missing.append("reach")
            if impact is None or impact <= 0:
                missing.append("impact")
            if confidence is None or confidence <= 0:
                missing.append("confidence")
            if effort is None or effort <= 0:
                missing.append("effort")

            score = None
            if (
                reach is not None
                and impact is not None
                and confidence is not None
                and effort is not None
                and effort > 0
            ):
                score = round((reach * impact * confidence) / effort, 2)
        else:
            # Weighted criteria
            if impact is None:
                missing.append("impact")
            if urgency is None:
                missing.append("urgency")
            if effort is None:
                missing.append("effort")

            score = None
            if impact is not None and urgency is not None and effort is not None:
                inv_effort = max(0.0, 6.0 - effort)
                score = round(0.4 * impact + 0.4 * urgency + 0.2 * inv_effort, 2)

        ps = PriorityScore(
            item_id=item_id,
            title=title,
            reach=reach,
            impact=impact,
            urgency=urgency,
            effort=effort,
            confidence=confidence,
            score=score,
            missing_metrics=sorted(missing),
        )

        if score is not None:
            ranked.append(ps)
        else:
            unranked.append(ps)

    # Sort deterministically: score descending, then item_id ascending
    ranked.sort(key=lambda x: (-1.0 * (x.score or 0.0), x.item_id))
    unranked.sort(key=lambda x: x.item_id)

    for i, ranked_item in enumerate(ranked, 1):
        ranked_item.rank = i

    return PrioritizationResult(
        method=req.method,
        ranked_items=ranked,
        unranked_items=unranked,
    )


def extract_meeting_actions(
    text: str, source_id: str, meeting_title: str = "Team Sync"
) -> MeetingActionsResult:
    lines = text.splitlines()
    actions: list[ActionItem] = []
    unassigned = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower()
        if not lower.startswith(
            ("- action", "* action", "action:", "todo:", "- [ ]", "* [ ]")
        ):
            continue

        # Extract owner if specified
        owner: str | None = None
        owner_match = re.search(
            r"(?:owner|assigned(?:\s*to)?):\s*@?([a-zA-Z0-9_-]+)",
            stripped,
            re.IGNORECASE,
        )
        if owner_match:
            owner = owner_match.group(1).strip()
        elif "@" in stripped:
            at_match = re.search(r"@([a-zA-Z0-9_-]+)", stripped)
            if at_match:
                owner = at_match.group(1).strip()

        if not owner:
            unassigned += 1

        # Extract deadline if specified
        deadline: str | None = None
        due_match = re.search(
            r"(?:due|by):\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", stripped, re.IGNORECASE
        )
        if due_match:
            deadline = due_match.group(1).strip()

        # Clean description
        desc = stripped.lstrip("-* ").strip()
        if desc.lower().startswith("action:"):
            desc = desc[7:].strip()
        elif desc.lower().startswith("todo:"):
            desc = desc[5:].strip()
        elif desc.lower().startswith("[ ]"):
            desc = desc[3:].strip()

        action = ActionItem(
            id=f"ACT-{uuid4().hex[:8]}",
            description=desc,
            owner=owner,
            deadline=deadline,
            status="not_started",
            source_id=source_id,
            source_quote=line,  # exact verbatim substring
        )
        actions.append(action)

    result_data = {
        "title": meeting_title,
        "actions": [a.model_dump() for a in actions],
        "source_id": source_id,
    }

    return MeetingActionsResult(
        meeting_title=meeting_title,
        actions=actions,
        unassigned_count=unassigned,
        digest=digest(result_data),
    )


class MockJiraAdapter:
    """In-memory mock adapter for Jira issue tracking and audit logs."""

    def __init__(self) -> None:
        self.issues: dict[str, list[dict[str, Any]]] = {}
        self.audit_log: dict[str, list[dict[str, Any]]] = {}

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Story",
        priority: str = "Medium",
        assignee: str | None = None,
    ) -> dict[str, Any]:
        key = project_key.upper()
        if key not in self.issues:
            self.issues[key] = []
            self.audit_log[key] = []

        issue_num = len(self.issues[key]) + 1
        issue_key = f"{key}-{issue_num}"
        issue_record = {
            "id": str(uuid4()),
            "key": issue_key,
            "summary": summary,
            "description": description,
            "issue_type": issue_type,
            "priority": priority,
            "assignee": assignee,
            "status": "To Do",
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.issues[key].append(issue_record)
        self.audit_log[key].append(
            {
                "action": "create_issue",
                "issue_key": issue_key,
                "summary": summary,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        return issue_record

    def list_issues(self, project_key: str) -> list[dict[str, Any]]:
        return list(self.issues.get(project_key.upper(), []))

    def get_audit_log(self, project_key: str) -> list[dict[str, Any]]:
        return list(self.audit_log.get(project_key.upper(), []))


class DeliveryService:
    """Coordinates delivery automation, Jira issue previews, synchronization, and audits."""

    def __init__(self, jira_adapter: MockJiraAdapter | None = None) -> None:
        self.jira_adapter = jira_adapter or MockJiraAdapter()
        self.synced_receipts: dict[str, DeliverySyncReceipt] = {}

    def prepare_jira_sync_preview(
        self,
        project_id: str,
        target: JiraTarget,
        items: list[dict[str, Any]],
    ) -> DeliverySyncPreview:
        items_to_create: list[dict[str, Any]] = []

        for item in items:
            item_type = item.get("type", "requirement")
            mapped_type = target.issue_type_mapping.get(item_type, "Story")
            summary = item.get("title") or item.get("description", "")[:120]
            description = item.get("description", "")
            priority = item.get("priority", "Medium")
            assignee = item.get("assignee")

            items_to_create.append(
                {
                    "source_item_id": item.get("id"),
                    "summary": summary,
                    "description": description,
                    "issue_type": mapped_type,
                    "priority": priority,
                    "assignee": assignee,
                }
            )

        preview_data = {
            "project_id": project_id,
            "target": target.model_dump(),
            "items_to_create": items_to_create,
        }
        changeset_digest = digest(preview_data)

        return DeliverySyncPreview(
            target=target,
            items_to_create=items_to_create,
            items_to_update=[],
            changeset_digest=changeset_digest,
        )

    def sync_jira(
        self,
        preview: DeliverySyncPreview,
        approval_digest: str,
    ) -> DeliverySyncReceipt:
        if approval_digest != preview.changeset_digest:
            raise ValueError("approval_digest_mismatch")

        if preview.changeset_digest in self.synced_receipts:
            existing = self.synced_receipts[preview.changeset_digest]
            return DeliverySyncReceipt(
                id=existing.id,
                project_id=existing.project_id,
                created_issues=existing.created_issues,
                changeset_digest=existing.changeset_digest,
                timestamp=existing.timestamp,
                status="already_synced",
            )

        created_records: list[dict[str, Any]] = []
        for item in preview.items_to_create:
            issue = self.jira_adapter.create_issue(
                project_key=preview.target.project_key,
                summary=item["summary"],
                description=item["description"],
                issue_type=item["issue_type"],
                priority=item["priority"],
                assignee=item["assignee"],
            )
            created_records.append(
                {
                    "key": issue["key"],
                    "summary": issue["summary"],
                    "issue_type": issue["issue_type"],
                    "assignee": issue["assignee"],
                    "source_item_id": item.get("source_item_id"),
                }
            )

        receipt = DeliverySyncReceipt(
            id=str(uuid4()),
            project_id=preview.target.project_key,
            created_issues=created_records,
            changeset_digest=preview.changeset_digest,
            timestamp=datetime.now(UTC).isoformat(),
            status="synced",
        )
        self.synced_receipts[preview.changeset_digest] = receipt
        return receipt
