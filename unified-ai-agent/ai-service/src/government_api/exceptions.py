"""Standard exception hierarchy for the Government API Integration Layer."""

from typing import Optional


class GovernmentAPIError(Exception):
    """Base exception for all Government API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class SecurityViolationError(GovernmentAPIError):
    """Raised when an operation violates security policy (e.g. non-HTTPS, unwhitelisted domain, SSRF attempt)."""
    pass


class AuthenticationError(GovernmentAPIError):
    """Raised when upstream API credentials are missing or invalid (HTTP 401)."""
    pass


class AuthorizationError(GovernmentAPIError):
    """Raised when access is forbidden or subscription is inactive (HTTP 403)."""
    pass


class RateLimitError(GovernmentAPIError):
    """Raised when client or upstream rate limits are exceeded (HTTP 429)."""
    pass


class TimeoutError(GovernmentAPIError):
    """Raised when connect, read, or total request timeout expires."""
    pass


class NetworkError(GovernmentAPIError):
    """Raised on socket, connection reset, or DNS resolution failures."""
    pass


class ServerError(GovernmentAPIError):
    """Raised on upstream server outages or errors (HTTP 500/502/503/504)."""
    pass


class SchemaValidationError(GovernmentAPIError):
    """Raised when an external API response fails strict schema validation."""
    pass


class ResponseTooLargeError(GovernmentAPIError):
    """Raised when response payload exceeds maximum allowable size (e.g. 2 MB)."""
    pass


class AdapterNotFoundError(GovernmentAPIError):
    """Raised when a requested government API adapter is not registered."""
    pass
