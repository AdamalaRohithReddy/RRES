"""Government API Integration Layer for Unified Citizen AI Agent (Milestone 8)."""

from src.government_api.models import (
    SourceType,
    VerificationStatus,
    DataFreshness,
    APIResponseStatus,
    FactType,
    GovernmentSource,
    NormalizedGovernmentResponse,
)
from src.government_api.exceptions import (
    GovernmentAPIError,
    SecurityViolationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    TimeoutError,
    NetworkError,
    ServerError,
    SchemaValidationError,
    ResponseTooLargeError,
)
from src.government_api.client import GovernmentAPIClient
from src.government_api.registry import GovernmentAPIRegistry, get_api_registry

__all__ = [
    "SourceType",
    "VerificationStatus",
    "DataFreshness",
    "APIResponseStatus",
    "FactType",
    "GovernmentSource",
    "NormalizedGovernmentResponse",
    "GovernmentAPIError",
    "SecurityViolationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "TimeoutError",
    "NetworkError",
    "ServerError",
    "SchemaValidationError",
    "ResponseTooLargeError",
    "GovernmentAPIClient",
    "GovernmentAPIRegistry",
    "get_api_registry",
]
