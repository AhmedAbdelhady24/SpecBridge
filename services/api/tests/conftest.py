import pytest


@pytest.fixture
def artifact_dict():
    return {
        "title": "Report export",
        "purpose": "Let customers use their reports",
        "scope": [
            {"text": "Export saved reports", "source_ids": [], "kind": "recommendation"}
        ],
        "non_goals": [],
        "requirements": [
            {
                "id": "REQ-1",
                "text": "Export a saved report",
                "source_ids": [],
                "kind": "recommendation",
            }
        ],
        "stories": [
            {
                "id": "STORY-1",
                "text": "As a customer I can export my report",
                "requirement_ids": ["REQ-1"],
                "acceptance_criteria": [
                    "Given a saved report, when export is selected, then a file is downloaded"
                ],
                "source_ids": [],
                "kind": "recommendation",
            }
        ],
        "edge_cases": [],
        "dependencies": [],
        "risks": [],
        "success_metrics": [],
        "open_questions": ["Which file format?"],
    }
