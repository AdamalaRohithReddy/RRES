"""Application Status Tool (Mock External Government API for Milestone 3).

NOTE: This is a controlled development mock representing external government
scheme application tracking services. It will be replaced with real portal APIs
in a future milestone.
"""
from typing import Dict, Any
from src.tools.base import BaseTool


MOCK_APPLICATIONS: Dict[str, Dict[str, Any]] = {
    "DEMO-001": {
        "application_id": "DEMO-001",
        "scheme_name": "Startup India Seed Fund Scheme",
        "status": "Under Evaluation by Incubator Seed Management Committee (ISMC)",
        "submitted_date": "2026-08-15",
        "last_updated": "2026-09-24",
        "incubator_preference": "T-Hub Hyderabad",
        "milestone_stage": "Proof of Concept Validation",
        "next_step": "Awaiting final interview schedule notification by email.",
    },
    "DEMO-002": {
        "application_id": "DEMO-002",
        "scheme_name": "Atal Pension Yojana",
        "status": "Active / Enrolled",
        "submitted_date": "2025-11-10",
        "last_updated": "2026-09-01",
        "pran_status": "Generated",
        "next_step": "Maintain sufficient balance for monthly auto-debit on 1st of month.",
    },
    "DEMO-003": {
        "application_id": "DEMO-003",
        "scheme_name": "Startup India Seed Fund Scheme",
        "status": "Rejected by Incubator Preference 1; Forwarded to Incubator Preference 2",
        "submitted_date": "2026-07-20",
        "last_updated": "2026-09-18",
        "next_step": "Under review by secondary incubator ISMC.",
    },
}


class ApplicationStatusTool(BaseTool):
    """Tool allowing the agent to check scheme application tracking status."""

    @property
    def name(self) -> str:
        return "get_application_status"

    @property
    def description(self) -> str:
        return (
            "Check the progress, verification stage, and status of an existing scheme application by its reference ID. "
            "(NOTE: Returns development mock data from simulated external service)."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "string",
                    "description": "The application reference number (e.g. 'DEMO-001' or 'DEMO-002')."
                }
            },
            "required": ["application_id"]
        }

    def execute(self, application_id: str, **kwargs) -> Dict[str, Any]:
        """Fetch application tracking record from mock external API."""
        app_id = application_id.strip() if application_id else "DEMO-001"

        record = MOCK_APPLICATIONS.get(app_id)
        if not record:
            # If unknown application ID, return default DEMO-001 with note
            record = {
                "application_id": app_id,
                "status": "Pending Verification",
                "submitted_date": "2026-09-01",
                "last_updated": "2026-09-24",
                "scheme_name": "Government Social Support Scheme",
                "next_step": "Under initial document scrutiny by administrative officer.",
            }

        return {
            "status": "success",
            "application_id": app_id,
            "record": record,
            "data_source": "MOCK_EXTERNAL_API",
            "notice": "DEMO MOCK DATA: Simulated application tracking record. Not connected to production government portal API.",
            "is_mock": True,
        }
