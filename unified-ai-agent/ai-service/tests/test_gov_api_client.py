"""Unit tests for Government API Client, Security Controls, and Foundation (Milestone 8.1)."""

import time
import pytest
from unittest.mock import MagicMock, patch
import httpx

from src.government_api.client import GovernmentAPIClient, ALLOWED_DOMAINS, MAX_RESPONSE_BYTES
from src.government_api.exceptions import (
    AuthenticationError,
    AuthorizationError,
    GovernmentAPIError,
    NetworkError,
    RateLimitError,
    ResponseTooLargeError,
    SecurityViolationError,
    ServerError,
    TimeoutError,
)
from src.government_api.models import (
    SourceType,
    VerificationStatus,
    DataFreshness,
    APIResponseStatus,
)
from src.government_api.trust import get_source_registry
from src.government_api.provenance import build_government_response
from src.government_api.cache import MetadataCache


# ---------------------------------------------------------------------------
# 1. URL Validation & SSRF Security Tests
# ---------------------------------------------------------------------------

def test_client_enforces_https():
    client = GovernmentAPIClient()
    with pytest.raises(SecurityViolationError, match="Protocol violation: Only HTTPS"):
        client.validate_url("http://apisetu.gov.in/api/v1/schemes")


def test_client_rejects_unwhitelisted_domains():
    client = GovernmentAPIClient()
    with pytest.raises(SecurityViolationError, match="Domain access denied"):
        client.validate_url("https://malicious-site.com/api/steal")


def test_client_allows_whitelisted_domains():
    client = GovernmentAPIClient()
    for domain in ALLOWED_DOMAINS:
        # Should not raise exception
        client.validate_url(f"https://{domain}/api/v1/test")


def test_client_blocks_ssrf_ip_literals():
    client = GovernmentAPIClient()
    # Loopback
    with pytest.raises(SecurityViolationError, match="SSRF violation|Security violation"):
        client.validate_url("https://127.0.0.1/admin")

    # Cloud metadata endpoint (AWS / GCP / Azure)
    with pytest.raises(SecurityViolationError, match="SSRF violation|Security violation"):
        client.validate_url("https://169.254.169.254/latest/meta-data")

    # Private RFC1918 subnets
    with pytest.raises(SecurityViolationError, match="SSRF violation|Security violation"):
        client.validate_url("https://10.0.0.1/internal")

    with pytest.raises(SecurityViolationError, match="SSRF violation|Security violation"):
        client.validate_url("https://192.168.1.1/router")


# ---------------------------------------------------------------------------
# 2. Response Size Cap & HTTP Parsing Tests
# ---------------------------------------------------------------------------

def _mock_stream_ctx(mock_response):
    """Helper to mock httpx.Client.stream context manager."""
    ctx = MagicMock()
    ctx.__enter__.return_value = mock_response
    ctx.__exit__.return_value = False
    return ctx


def test_client_rejects_oversized_content_length():
    client = GovernmentAPIClient()
    mock_response = MagicMock()
    mock_response.headers = {"Content-Length": str(MAX_RESPONSE_BYTES + 1024)}

    with patch.object(client.session, "stream", return_value=_mock_stream_ctx(mock_response)):
        with pytest.raises(ResponseTooLargeError, match="Response payload exceeds maximum size"):
            client.get("https://apisetu.gov.in/api/v1/schemes")


def test_client_rejects_oversized_stream():
    client = GovernmentAPIClient()
    mock_response = MagicMock()
    mock_response.headers = {}
    mock_response.iter_bytes.return_value = [b"x" * (1024 * 1024), b"x" * (1024 * 1024), b"x" * 1024]

    with patch.object(client.session, "stream", return_value=_mock_stream_ctx(mock_response)):
        with pytest.raises(ResponseTooLargeError, match="Response stream exceeded"):
            client.get("https://apisetu.gov.in/api/v1/schemes")


def test_client_handles_status_codes():
    client = GovernmentAPIClient(max_retries=0)

    # 401 Unauthorized
    resp_401 = MagicMock()
    resp_401.headers = {}
    resp_401.iter_bytes.return_value = [b'{"error": "unauthorized"}']
    resp_401.status_code = 401
    with patch.object(client.session, "stream", return_value=_mock_stream_ctx(resp_401)):
        with pytest.raises(AuthenticationError):
            client.get("https://apisetu.gov.in/api/v1/schemes")

    # 403 Forbidden
    resp_403 = MagicMock()
    resp_403.headers = {}
    resp_403.iter_bytes.return_value = [b'{"error": "forbidden"}']
    resp_403.status_code = 403
    with patch.object(client.session, "stream", return_value=_mock_stream_ctx(resp_403)):
        with pytest.raises(AuthorizationError):
            client.get("https://apisetu.gov.in/api/v1/schemes")

    # 500 Server Error
    resp_500 = MagicMock()
    resp_500.headers = {}
    resp_500.iter_bytes.return_value = [b'{"error": "internal error"}']
    resp_500.status_code = 500
    with patch.object(client.session, "stream", return_value=_mock_stream_ctx(resp_500)):
        with pytest.raises(ServerError):
            client.get("https://apisetu.gov.in/api/v1/schemes")


# ---------------------------------------------------------------------------
# 3. Source Trust Registry & Provenance Tests
# ---------------------------------------------------------------------------

def test_source_trust_registry():
    reg = get_source_registry()
    myscheme = reg.get_source("API_SETU_MYSCHEME")
    assert myscheme is not None
    assert myscheme.source_type == SourceType.OFFICIAL_GOVERNMENT_API
    assert myscheme.official_domain == "apisetu.gov.in"
    assert myscheme.verification_status == VerificationStatus.CONTRACT_VERIFIED

    # Check allowed operations
    assert reg.is_operation_permitted("API_SETU_MYSCHEME", "search_schemes") is True
    assert reg.is_operation_permitted("API_SETU_MYSCHEME", "arbitrary_operation") is False


def test_provenance_builder():
    resp = build_government_response(
        status=APIResponseStatus.SUCCESS,
        data_source=SourceType.SANDBOX_FIXTURE,
        verification_status=VerificationStatus.CONTRACT_VERIFIED,
        provider="NeGD / MeitY",
        api_name="myScheme Service API",
        endpoint_identifier="APISETU_MYSCHEME_SEARCH",
        source_url="https://www.myscheme.gov.in/",
        payload={"count": 2},
    )
    assert resp.status == APIResponseStatus.SUCCESS
    assert resp.data_source == SourceType.SANDBOX_FIXTURE
    assert resp.verification_status == VerificationStatus.CONTRACT_VERIFIED
    assert resp.provider == "NeGD / MeitY"
    assert resp.data_freshness == DataFreshness.LIVE
    assert resp.retrieved_at is not None


# ---------------------------------------------------------------------------
# 4. Metadata Cache Tests
# ---------------------------------------------------------------------------

def test_metadata_cache_ttl():
    cache = MetadataCache(default_ttl_seconds=1)
    key = MetadataCache.generate_key("myscheme", "search", {"query": "farmer"})

    # Store item
    cache.set(key, {"schemes": ["PM-KISAN"]})
    assert cache.get(key) == {"schemes": ["PM-KISAN"]}
    assert len(cache) == 1

    # Wait for expiry
    time.sleep(1.1)
    assert cache.get(key) is None
    assert len(cache) == 0
