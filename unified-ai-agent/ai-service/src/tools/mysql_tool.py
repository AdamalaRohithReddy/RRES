"""Citizen Profile Tool (Real MySQL Integration for Milestone 7).

Retrieves citizen demographic and socio-economic profile information from the
relational database using parameterized SQLAlchemy ORM queries.
Implements strict identifier validation and safe error handling without silent mock fallback.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError

from src.config.settings import get_settings
from src.database.repositories.citizen_repo import CitizenRepository, validate_citizen_id
from src.tools.base import BaseTool

logger = logging.getLogger(__name__)

# Controlled mock citizen records for explicit development/test fallback only
MOCK_CITIZEN_RECORDS: Dict[str, Dict[str, Any]] = {
    "demo-user": {
        "citizen_id": "demo-user",
        "name": "Ramesh Kumar",
        "age": 28,
        "gender": "Male",
        "state": "Telangana",
        "district": "Hyderabad",
        "annual_income": 240000,
        "occupation": "Tech Startup Founder",
        "has_dpiit_recognition": True,
        "business_incorporated_years": 1,
        "category": "General",
        "is_taxpayer": False,
    },
    "senior-citizen": {
        "citizen_id": "senior-citizen",
        "name": "Lakshmi Devi",
        "age": 65,
        "gender": "Female",
        "state": "Telangana",
        "district": "Warangal",
        "annual_income": 150000,
        "occupation": "Retired / Domestic Worker",
        "category": "General",
        "is_taxpayer": False,
    },
    "rural-farmer": {
        "citizen_id": "rural-farmer",
        "name": "Suresh Patel",
        "age": 42,
        "gender": "Male",
        "state": "Gujarat",
        "annual_income": 180000,
        "occupation": "Smallholder Farmer",
        "landholding_acres": 2.5,
        "category": "OBC",
        "is_taxpayer": False,
    },
}


class CitizenProfileTool(BaseTool):
    """Tool allowing the agent to retrieve a citizen's profile attributes from MySQL."""

    def __init__(self, repository: Optional[CitizenRepository] = None):
        self._repo = repository or CitizenRepository()

    @property
    def name(self) -> str:
        return "get_citizen_profile"

    @property
    def description(self) -> str:
        return (
            "Retrieve citizen demographic and socio-economic profile information (such as age, state of residence, "
            "occupation, and annual income) for personalized scheme assessment from the official citizen database."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "citizen_id": {
                    "type": "string",
                    "description": "Unique citizen identifier (e.g. 'demo-user', 'senior-citizen', or 'rural-farmer'). Defaults to 'demo-user'.",
                    "default": "demo-user",
                }
            },
            "required": [],
        }

    def execute(self, citizen_id: Optional[str] = "demo-user", **kwargs) -> Dict[str, Any]:
        """Fetch citizen profile from MySQL repository or structured unavailable notice."""
        settings = get_settings()
        raw_id = citizen_id or "demo-user"

        # 1. Strict regex validation for citizen_id
        try:
            cid = validate_citizen_id(raw_id)
        except ValueError as val_err:
            return {
                "status": "invalid_input",
                "citizen_id": str(raw_id),
                "profile": None,
                "data_source": "MYSQL_DATABASE",
                "error": str(val_err),
                "is_mock": False,
            }

        # 2. Query relational database via ORM repository
        try:
            profile = self._repo.get_citizen_with_profile(cid)
            if profile:
                return {
                    "status": "success",
                    "citizen_id": cid,
                    "profile": profile,
                    "data_source": "MYSQL_DATABASE",
                    "notice": "Official citizen profile data retrieved from relational database.",
                    "is_mock": False,
                }

            # Citizen ID not found in database
            if settings.allow_mock_fallback and cid in MOCK_CITIZEN_RECORDS:
                logger.info(f"Citizen '{cid}' not in database; fallback enabled: using mock data.")
                mock_prof = MOCK_CITIZEN_RECORDS[cid]
                return {
                    "status": "success",
                    "citizen_id": cid,
                    "profile": mock_prof,
                    "data_source": "MOCK_DEVELOPMENT_DATABASE",
                    "notice": "DEMO MOCK DATA: Simulated citizen profile for development testing.",
                    "is_mock": True,
                }

            return {
                "status": "not_found",
                "citizen_id": cid,
                "profile": None,
                "data_source": "MYSQL_DATABASE",
                "notice": f"No citizen profile found for identifier '{cid}'.",
                "is_mock": False,
            }

        except (SQLAlchemyError, Exception) as exc:
            logger.error(f"Database error while retrieving citizen '{cid}': {exc}")

            # Safety check: if mock fallback is explicitly allowed (dev only)
            if settings.allow_mock_fallback:
                logger.warning("Database unavailable, falling back to mock citizen records.")
                mock_prof = MOCK_CITIZEN_RECORDS.get(cid) or MOCK_CITIZEN_RECORDS.get("demo-user")
                return {
                    "status": "success",
                    "citizen_id": cid,
                    "profile": mock_prof,
                    "data_source": "MOCK_DEVELOPMENT_DATABASE",
                    "notice": "DEMO MOCK DATA: Fallback citizen profile due to database unavailability.",
                    "is_mock": True,
                }

            # Production default: fail-safe structured unavailable response
            return {
                "status": "service_unavailable",
                "citizen_id": cid,
                "profile": None,
                "data_source": "MYSQL_DATABASE",
                "error": "Citizen profile database service is temporarily unavailable.",
                "is_mock": False,
            }
