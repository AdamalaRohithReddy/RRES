"""Citizen Profile Tool (Mock MySQL Interface for Milestone 3).

NOTE: This is a controlled development mock representing citizen profile data.
It simulates the interface of a relational citizen database (e.g. MySQL) that
will be connected in a future milestone.
"""
from typing import Dict, Any, Optional
from src.tools.base import BaseTool


# Controlled mock citizen records for local development and testing
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
    """Tool allowing the agent to retrieve a citizen's profile attributes.

    Interface adheres to repository pattern so it can be swapped with MySQL in future milestones.
    """

    @property
    def name(self) -> str:
        return "get_citizen_profile"

    @property
    def description(self) -> str:
        return (
            "Retrieve citizen demographic and socio-economic profile information (such as age, state of residence, "
            "occupation, and annual income) for personalized scheme assessment. "
            "(NOTE: Returns development mock data from development profile repository)."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "citizen_id": {
                    "type": "string",
                    "description": "Unique citizen identifier (e.g. 'demo-user', 'senior-citizen', or 'rural-farmer'). Defaults to 'demo-user'.",
                    "default": "demo-user"
                }
            },
            "required": []
        }

    def execute(self, citizen_id: Optional[str] = "demo-user", **kwargs) -> Dict[str, Any]:
        """Fetch citizen profile from mock repository."""
        cid = (citizen_id or "demo-user").strip()

        profile = MOCK_CITIZEN_RECORDS.get(cid)
        if not profile:
            # Fallback to default demo-user if unknown ID
            profile = MOCK_CITIZEN_RECORDS.get("demo-user")

        return {
            "status": "success",
            "citizen_id": cid,
            "profile": profile,
            "data_source": "MOCK_DEVELOPMENT_DATABASE",
            "notice": "DEMO MOCK DATA: Simulated citizen profile for development testing. Not connected to live production MySQL.",
            "is_mock": True,
        }
