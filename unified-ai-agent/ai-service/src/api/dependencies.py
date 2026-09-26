"""Security and context dependencies for FastAPI internal endpoints."""
import uuid
from typing import Optional
from fastapi import Header, HTTPException, status
from src.config.settings import get_settings


def verify_internal_api_key(
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-API-Key"),
) -> str:
    """Validate internal service-to-service credential."""
    settings = get_settings()
    expected_key = settings.ai_service_internal_key

    if not expected_key:
        # Development fallback if key not configured
        return "dev-internal-key"

    if not x_internal_api_key or x_internal_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal service API key (X-Internal-API-Key)",
        )
    return x_internal_api_key


def get_citizen_id(
    x_citizen_id: Optional[str] = Header(None, alias="X-Citizen-ID"),
) -> str:
    """Extract authenticated citizen ID derived by Spring Boot."""
    if not x_citizen_id or not x_citizen_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing or empty X-Citizen-ID header",
        )
    return x_citizen_id.strip()


def get_optional_citizen_id(
    x_citizen_id: Optional[str] = Header(None, alias="X-Citizen-ID"),
) -> Optional[str]:
    """Extract optional citizen ID if present."""
    if x_citizen_id and x_citizen_id.strip():
        return x_citizen_id.strip()
    return None


def get_correlation_id(
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID"),
) -> str:
    """Extract or generate request correlation ID."""
    if x_correlation_id and x_correlation_id.strip():
        return x_correlation_id.strip()
    return str(uuid.uuid4())
