"""myScheme API Adapter implementing API Setu Service API contract (Milestone 8.2)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.government_api.adapters.base import BaseGovernmentAPIAdapter
from src.government_api.cache import MetadataCache
from src.government_api.client import GovernmentAPIClient
from src.government_api.exceptions import GovernmentAPIError, TimeoutError, RateLimitError
from src.government_api.models import (
    APIResponseStatus,
    DataFreshness,
    GovernmentSource,
    NormalizedGovernmentResponse,
    SourceType,
    VerificationStatus,
)
from src.government_api.provenance import build_government_response
from src.government_api.trust import SOURCE_API_SETU_MYSCHEME, SOURCE_SANDBOX_FIXTURE

logger = logging.getLogger(__name__)


class MySchemeItem(BaseModel):
    """Normalized schema for a scheme discovered through myScheme."""
    scheme_id: str
    scheme_name: str
    nodal_ministry: str
    brief_description: str
    target_beneficiaries: List[str] = Field(default_factory=list)
    eligibility_tags: List[str] = Field(default_factory=list)
    application_url: str
    level: str = "Central"


class MySchemeAdapter(BaseGovernmentAPIAdapter):
    """Adapter implementing the official API Setu myScheme Service API contract."""

    def __init__(
        self,
        client: Optional[GovernmentAPIClient] = None,
        cache: Optional[MetadataCache] = None,
        fixtures_dir: Optional[Path] = None,
    ):
        self._client = client or GovernmentAPIClient()
        self._cache = cache or MetadataCache(default_ttl_seconds=300)
        self._fixtures_dir = fixtures_dir or (Path(__file__).resolve().parent.parent.parent.parent / "tests" / "fixtures" / "government_api")

    @property
    def adapter_id(self) -> str:
        return "myscheme_service"

    @property
    def source(self) -> GovernmentSource:
        return SOURCE_API_SETU_MYSCHEME

    def execute(self, operation: str, params: Dict[str, Any]) -> NormalizedGovernmentResponse:
        """Execute permitted myScheme operations with caching and graceful degradation."""
        self.validate_operation(operation)

        if operation == "search_schemes":
            return self._search_schemes(params)
        elif operation == "get_scheme_details":
            return self._get_scheme_details(params)
        else:
            raise GovernmentAPIError(f"Unsupported operation '{operation}' for myScheme adapter.")

    def _search_schemes(self, params: Dict[str, Any]) -> NormalizedGovernmentResponse:
        """Search government schemes matching query, category, or state."""
        query = (params.get("query") or "").strip().lower()
        state = (params.get("state") or "").strip().lower()
        category = (params.get("category") or "").strip().lower()

        # Check Cache
        cache_key = MetadataCache.generate_key(self.adapter_id, "search_schemes", params)
        cached_result = self._cache.get(cache_key)
        if cached_result:
            return build_government_response(
                status=APIResponseStatus.SUCCESS,
                data_source=cached_result["data_source"],
                verification_status=cached_result["verification_status"],
                provider=self.source.organization,
                api_name="myScheme Service API",
                endpoint_identifier="APISETU_MYSCHEME_SEARCH",
                source_url=self.source.documentation_url,
                payload=cached_result["payload"],
                data_freshness=DataFreshness.CACHED,
            )

        settings = get_settings()

        # Check if actual external API endpoint (production or official sandbox) is enabled
        if settings.gov_api_enabled and settings.apisetu_api_key:
            try:
                headers = {
                    "X-APISETU-CLIENTID": settings.apisetu_client_id or "",
                    "X-APISETU-APIKEY": settings.apisetu_api_key.get_secret_value() if hasattr(settings.apisetu_api_key, "get_secret_value") else str(settings.apisetu_api_key),
                }
                api_url = f"{settings.apisetu_base_url.rstrip('/')}/myscheme/schemes"
                live_payload = self._client.get(api_url, params={"q": query, "state": state, "category": category}, headers=headers)

                # Actual authorized production API vs actual official sandbox endpoint
                ver_tier = (
                    VerificationStatus.PRODUCTION_CONNECTED
                    if settings.gov_api_environment == "production"
                    else VerificationStatus.SANDBOX_VERIFIED
                )

                res = build_government_response(
                    status=APIResponseStatus.SUCCESS,
                    data_source=SourceType.OFFICIAL_GOVERNMENT_API,
                    verification_status=ver_tier,
                    provider=self.source.organization,
                    api_name="myScheme Service API",
                    endpoint_identifier="APISETU_MYSCHEME_SEARCH",
                    source_url=self.source.documentation_url,
                    payload=live_payload,
                    data_freshness=DataFreshness.LIVE,
                )
                self._cache.set(cache_key, {"data_source": res.data_source, "verification_status": res.verification_status, "payload": res.payload})
                return res

            except (TimeoutError, RateLimitError, GovernmentAPIError) as exc:
                logger.warning("Live myScheme API call failed: %s. Returning structured unavailable response.", str(exc))
                return build_government_response(
                    status=APIResponseStatus.API_UNAVAILABLE if not isinstance(exc, RateLimitError) else APIResponseStatus.RATE_LIMITED,
                    data_source=SourceType.OFFICIAL_GOVERNMENT_API,
                    verification_status=VerificationStatus.CONTRACT_VERIFIED,
                    provider=self.source.organization,
                    api_name="myScheme Service API",
                    endpoint_identifier="APISETU_MYSCHEME_SEARCH",
                    source_url=self.source.documentation_url,
                    error_details={"error_type": type(exc).__name__, "message": str(exc)},
                )

        # Local Synthetic Fixture Mode: strictly CONTRACT_VERIFIED
        fixture_file = self._fixtures_dir / "apisetu_myscheme_search.json"
        if not fixture_file.exists():
            return build_government_response(
                status=APIResponseStatus.API_UNAVAILABLE,
                data_source=SourceType.SANDBOX_FIXTURE,
                verification_status=VerificationStatus.CONTRACT_VERIFIED,
                provider=self.source.organization,
                api_name="myScheme Service API",
                endpoint_identifier="APISETU_MYSCHEME_SEARCH",
                source_url=self.source.documentation_url,
                error_details={"message": f"Fixture file not found at {fixture_file}"},
            )

        with open(fixture_file, "r", encoding="utf-8") as f:
            raw_fixture = json.load(f)

        raw_schemes = raw_fixture.get("data", {}).get("schemes", [])
        filtered_schemes = []

        for s in raw_schemes:
            text_corpus = f"{s.get('scheme_name', '')} {s.get('brief_description', '')} {' '.join(s.get('target_beneficiaries', []))} {' '.join(s.get('eligibility_tags', []))}".lower()
            if query and query not in text_corpus:
                continue
            if category and category not in text_corpus:
                continue
            filtered_schemes.append(s)

        # If query filtered everything out, return all from fixture to provide helpful candidates
        if not filtered_schemes and query:
            filtered_schemes = raw_schemes

        response_payload = {
            "total_records": len(filtered_schemes),
            "schemes": filtered_schemes,
        }

        # Local synthetic fixture is strictly CONTRACT_VERIFIED
        result = build_government_response(
            status=APIResponseStatus.SUCCESS,
            data_source=SourceType.SANDBOX_FIXTURE,
            verification_status=VerificationStatus.CONTRACT_VERIFIED,
            provider=self.source.organization,
            api_name="myScheme Service API",
            endpoint_identifier="APISETU_MYSCHEME_SEARCH",
            source_url=self.source.documentation_url,
            payload=response_payload,
            data_freshness=DataFreshness.LIVE,
        )

        self._cache.set(cache_key, {"data_source": result.data_source, "verification_status": result.verification_status, "payload": result.payload})
        return result

    def _get_scheme_details(self, params: Dict[str, Any]) -> NormalizedGovernmentResponse:
        """Fetch detailed information for a specific scheme ID."""
        scheme_id = params.get("scheme_id", "").strip()
        fixture_file = self._fixtures_dir / "apisetu_myscheme_detail.json"

        if not fixture_file.exists():
            return build_government_response(
                status=APIResponseStatus.NOT_FOUND,
                data_source=SourceType.SANDBOX_FIXTURE,
                verification_status=VerificationStatus.CONTRACT_VERIFIED,
                provider=self.source.organization,
                api_name="myScheme Service API",
                endpoint_identifier="APISETU_MYSCHEME_DETAIL",
                source_url=self.source.documentation_url,
                error_details={"message": f"Scheme {scheme_id} details not found."},
            )

        with open(fixture_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        return build_government_response(
            status=APIResponseStatus.SUCCESS,
            data_source=SourceType.SANDBOX_FIXTURE,
            verification_status=VerificationStatus.CONTRACT_VERIFIED,
            provider=self.source.organization,
            api_name="myScheme Service API",
            endpoint_identifier="APISETU_MYSCHEME_DETAIL",
            source_url=self.source.documentation_url,
            payload=raw_data.get("data", {}),
            data_freshness=DataFreshness.LIVE,
        )
