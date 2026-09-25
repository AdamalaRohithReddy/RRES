"""Data models and enums for Government API Integration Layer (Milestone 8)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Categorical source type classification."""
    OFFICIAL_GOVERNMENT_API = "OFFICIAL_GOVERNMENT_API"
    OFFICIAL_GOVERNMENT_PORTAL = "OFFICIAL_GOVERNMENT_PORTAL"
    OFFICIAL_GOVERNMENT_DOCUMENT = "OFFICIAL_GOVERNMENT_DOCUMENT"
    LOCAL_MYSQL = "LOCAL_MYSQL"
    DOCUMENT_AI_EXTRACTED = "DOCUMENT_AI_EXTRACTED"
    SANDBOX_FIXTURE = "SANDBOX_FIXTURE"


class VerificationStatus(str, Enum):
    """Tier of external verification."""
    VERIFIED_AT_PLATFORM_LEVEL = "VERIFIED_AT_PLATFORM_LEVEL"
    CONTRACT_VERIFIED = "CONTRACT_VERIFIED"
    SANDBOX_VERIFIED = "SANDBOX_VERIFIED"
    PRODUCTION_CONNECTED = "PRODUCTION_CONNECTED"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class DataFreshness(str, Enum):
    """Freshness state of returned external data."""
    LIVE = "LIVE"
    CACHED = "CACHED"
    STALE = "STALE"


class APIResponseStatus(str, Enum):
    """Standardized API response and failure statuses."""
    SUCCESS = "SUCCESS"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    SERVER_ERROR = "SERVER_ERROR"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    API_UNAVAILABLE = "API_UNAVAILABLE"
    NOT_FOUND = "NOT_FOUND"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    VERIFICATION_UNAVAILABLE = "VERIFICATION_UNAVAILABLE"


class FactType(str, Enum):
    """Classification of citizen demographic and evidentiary facts."""
    EXTRACTED_FACT = "EXTRACTED_FACT"
    LOCAL_STORED_FACT = "LOCAL_STORED_FACT"
    EXTERNALLY_VERIFIED_FACT = "EXTERNALLY_VERIFIED_FACT"


class GovernmentSource(BaseModel):
    """Immutable metadata describing an authoritative government source."""
    source_id: str = Field(description="Unique source key, e.g. API_SETU_MYSCHEME")
    organization: str = Field(description="Nodal agency / government department")
    source_type: SourceType = Field(description="Classification of the source")
    official_domain: str = Field(description="Whitelisted official web domain")
    verification_status: VerificationStatus = Field(description="Verification tier attained")
    allowed_operations: List[str] = Field(default_factory=list, description="Permitted operation names")
    documentation_url: str = Field(description="URL to official API documentation or portal")


class NormalizedGovernmentResponse(BaseModel):
    """Normalized response payload delivered by all government API adapters."""
    status: APIResponseStatus = Field(description="High-level operation status")
    data_source: SourceType = Field(description="Categorical source designation")
    verification_status: VerificationStatus = Field(description="Verification tier")
    provider: str = Field(description="Department or nodal organization")
    api_name: str = Field(description="Official name of the API / service")
    endpoint_identifier: str = Field(description="Abstracted endpoint reference")
    retrieved_at: str = Field(description="ISO 8601 UTC timestamp")
    source_url: str = Field(description="Authoritative reference link")
    data_freshness: DataFreshness = Field(default=DataFreshness.LIVE, description="Freshness indicator")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Validated payload data")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Safe error details if status != SUCCESS")
