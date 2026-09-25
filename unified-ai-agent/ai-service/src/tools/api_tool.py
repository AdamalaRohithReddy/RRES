"""Application Status Tool (Real MySQL Integration for Milestone 7).

Retrieves scheme application tracking information from the relational database
using parameterized SQLAlchemy ORM queries and provides audit history.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError

from src.config.settings import get_settings
from src.database.repositories.application_repo import ApplicationRepository, validate_application_id
from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

# Controlled mock applications for explicit development fallback only
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
    """Tool allowing the agent to check scheme application tracking status from MySQL."""

    def __init__(self, repository: Optional[ApplicationRepository] = None):
        self._repo = repository or ApplicationRepository()

    @property
    def name(self) -> str:
        return "get_application_status"

    @property
    def description(self) -> str:
        return (
            "Check the progress, verification stage, and status of an existing scheme application by its reference ID "
            "from the official application tracking database."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "application_id": {
                    "type": "string",
                    "description": "The application reference number (e.g. 'DEMO-001' or 'DEMO-002').",
                }
            },
            "required": ["application_id"],
        }

    def execute(self, application_id: str, **kwargs) -> Dict[str, Any]:
        """Fetch application tracking record from MySQL repository or structured unavailable notice."""
        settings = get_settings()
        raw_id = application_id or "DEMO-001"

        # 1. Strict regex validation for application_id
        try:
            app_id = validate_application_id(raw_id)
        except ValueError as val_err:
            return {
                "status": "invalid_input",
                "application_id": str(raw_id),
                "record": None,
                "data_source": "MYSQL_DATABASE",
                "error": str(val_err),
                "is_mock": False,
            }

        # 2. Query relational database via ORM repository
        try:
            record = self._repo.get_application(app_id)
            if record:
                return {
                    "status": "success",
                    "application_id": app_id,
                    "record": record,
                    "data_source": "MYSQL_DATABASE",
                    "notice": "Official application tracking record retrieved from relational database.",
                    "is_mock": False,
                }

            # Application not found in database
            if settings.allow_mock_fallback and app_id in MOCK_APPLICATIONS:
                logger.info(f"Application '{app_id}' not in DB; fallback enabled: using mock data.")
                return {
                    "status": "success",
                    "application_id": app_id,
                    "record": MOCK_APPLICATIONS[app_id],
                    "data_source": "MOCK_EXTERNAL_API",
                    "notice": "DEMO MOCK DATA: Simulated application tracking record.",
                    "is_mock": True,
                }

            return {
                "status": "not_found",
                "application_id": app_id,
                "record": None,
                "data_source": "MYSQL_DATABASE",
                "notice": f"No application record found for reference '{app_id}'.",
                "is_mock": False,
            }

        except (SQLAlchemyError, Exception) as exc:
            logger.error(f"Database error while retrieving application '{app_id}': {exc}")

            if settings.allow_mock_fallback:
                logger.warning("Database unavailable, falling back to mock application records.")
                mock_rec = MOCK_APPLICATIONS.get(app_id) or {
                    "application_id": app_id,
                    "status": "Pending Verification",
                    "scheme_name": "Government Social Support Scheme",
                }
                return {
                    "status": "success",
                    "application_id": app_id,
                    "record": mock_rec,
                    "data_source": "MOCK_EXTERNAL_API",
                    "notice": "DEMO MOCK DATA: Fallback application tracking record.",
                    "is_mock": True,
                }

            return {
                "status": "service_unavailable",
                "application_id": app_id,
                "record": None,
                "data_source": "MYSQL_DATABASE",
                "error": "Application tracking database service is temporarily unavailable.",
                "is_mock": False,
            }
