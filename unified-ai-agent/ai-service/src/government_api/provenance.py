"""Provenance builder and validator for Government API responses."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.government_api.models import (
    SourceType,
    VerificationStatus,
    DataFreshness,
    APIResponseStatus,
    NormalizedGovernmentResponse,
)


def get_utc_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def build_government_response(
    status: APIResponseStatus,
    data_source: SourceType,
    verification_status: VerificationStatus,
    provider: str,
    api_name: str,
    endpoint_identifier: str,
    source_url: str,
    payload: Optional[Dict[str, Any]] = None,
    data_freshness: DataFreshness = DataFreshness.LIVE,
    error_details: Optional[Dict[str, Any]] = None,
    retrieved_at: Optional[str] = None,
) -> NormalizedGovernmentResponse:
    """Construct an immutable, type-checked NormalizedGovernmentResponse with authoritative provenance."""
    return NormalizedGovernmentResponse(
        status=status,
        data_source=data_source,
        verification_status=verification_status,
        provider=provider,
        api_name=api_name,
        endpoint_identifier=endpoint_identifier,
        retrieved_at=retrieved_at or get_utc_timestamp(),
        source_url=source_url,
        data_freshness=data_freshness,
        payload=payload or {},
        error_details=error_details,
    )
