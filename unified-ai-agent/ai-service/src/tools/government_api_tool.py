"""Government Scheme Discovery Tool for Agent Orchestrator (Milestone 8)."""

from typing import Any, Dict, Optional

from src.government_api.adapters.myscheme_adapter import MySchemeAdapter
from src.government_api.models import APIResponseStatus
from src.government_api.registry import get_api_registry
from src.tools.base import BaseTool


class GovernmentSchemeDiscoveryTool(BaseTool):
    """Tool allowing the agent to discover official schemes from the national government directory."""

    def __init__(self, adapter: Optional[MySchemeAdapter] = None):
        self._adapter = adapter or MySchemeAdapter()
        # Ensure registered in global registry
        registry = get_api_registry()
        if self._adapter.adapter_id not in registry:
            registry.register(self._adapter)

    @property
    def name(self) -> str:
        return "discover_government_schemes"

    @property
    def description(self) -> str:
        return (
            "Search the official Government of India scheme directory (via API Setu myScheme service) for schemes "
            "matching a citizen's profile, sector, or needs. Returns verified scheme titles, nodal ministries, "
            "official portal URLs, and eligibility tags with authoritative government provenance."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords or topic of assistance (e.g. 'farmer income', 'student scholarship', 'tech startup seed fund').",
                },
                "state": {
                    "type": "string",
                    "description": "Optional state or Union Territory name (e.g. 'Telangana', 'Gujarat').",
                },
                "category": {
                    "type": "string",
                    "description": "Optional target beneficiary category (e.g. 'Farmer', 'Student', 'Entrepreneur').",
                },
            },
            "required": ["query"],
        }

    def execute(self, query: str, state: Optional[str] = None, category: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute scheme discovery via myScheme adapter."""
        clean_query = (query or "").strip()
        if not clean_query:
            return {
                "status": "error",
                "message": "Query parameter cannot be empty.",
            }

        response = self._adapter.execute(
            "search_schemes",
            {"query": clean_query, "state": state, "category": category},
        )

        if response.status == APIResponseStatus.SUCCESS:
            schemes = response.payload.get("schemes", [])
            return {
                "status": "success",
                "total_found": len(schemes),
                "schemes": schemes,
                "data_source": response.data_source.value,
                "verification_status": response.verification_status.value,
                "provider": response.provider,
                "source_url": response.source_url,
                "data_freshness": response.data_freshness.value,
                "retrieved_at": response.retrieved_at,
            }

        return {
            "status": "service_unavailable",
            "message": (
                "The live government scheme directory service is currently unreachable or rate limited. "
                "Consult verified local scheme guidelines using the 'search_government_schemes' tool."
            ),
            "fallback_recommended_tool": "search_government_schemes",
            "data_source": response.data_source.value,
            "verification_status": response.verification_status.value,
            "provider": response.provider,
            "retrieved_at": response.retrieved_at,
            "error_details": response.error_details,
        }
