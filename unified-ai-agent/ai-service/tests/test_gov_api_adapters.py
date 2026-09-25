"""Tests for Government API Adapters (Milestone 8.2)."""

import pytest
from unittest.mock import MagicMock, patch

from src.government_api.adapters.myscheme_adapter import MySchemeAdapter
from src.government_api.exceptions import TimeoutError, ServerError
from src.government_api.models import (
    APIResponseStatus,
    DataFreshness,
    SourceType,
    VerificationStatus,
)


def test_myscheme_adapter_search_fixture():
    adapter = MySchemeAdapter()
    res = adapter.execute("search_schemes", {"query": "farmer"})

    assert res.status == APIResponseStatus.SUCCESS
    assert res.data_source == SourceType.SANDBOX_FIXTURE
    assert res.verification_status == VerificationStatus.CONTRACT_VERIFIED
    assert res.data_freshness == DataFreshness.LIVE
    assert "schemes" in res.payload
    assert len(res.payload["schemes"]) >= 1

    scheme_names = [s["scheme_name"] for s in res.payload["schemes"]]
    assert any("PM-KISAN" in name or "Kisan" in name for name in scheme_names)


def test_myscheme_adapter_caching():
    adapter = MySchemeAdapter()
    params = {"query": "startup"}

    # First call - LIVE
    res1 = adapter.execute("search_schemes", params)
    assert res1.data_freshness == DataFreshness.LIVE

    # Second call - CACHED
    res2 = adapter.execute("search_schemes", params)
    assert res2.data_freshness == DataFreshness.CACHED
    assert res2.payload == res1.payload


def test_myscheme_adapter_details():
    adapter = MySchemeAdapter()
    res = adapter.execute("get_scheme_details", {"scheme_id": "MYSCHEME-ENT-003"})

    assert res.status == APIResponseStatus.SUCCESS
    assert res.payload["scheme_id"] == "MYSCHEME-ENT-003"
    assert "Startup India Seed Fund" in res.payload["scheme_name"]


def test_myscheme_adapter_graceful_failure():
    adapter = MySchemeAdapter()

    # Mock client failure in production mode
    with patch("src.government_api.adapters.myscheme_adapter.get_settings") as mock_settings:
        mock_settings.return_value.gov_api_enabled = True
        mock_settings.return_value.gov_api_environment = "production"
        mock_settings.return_value.apisetu_api_key = "test_key"
        mock_settings.return_value.apisetu_client_id = "test_client"
        mock_settings.return_value.apisetu_base_url = "https://apisetu.gov.in/api/v1"

        with patch.object(adapter._client, "get", side_effect=TimeoutError("Request timed out.")):
            res = adapter.execute("search_schemes", {"query": "unique_query_123"})
            assert res.status == APIResponseStatus.API_UNAVAILABLE
            assert res.error_details is not None
            assert "TimeoutError" in res.error_details["error_type"]


def test_adapter_3_tier_verification_mapping():
    adapter = MySchemeAdapter()

    # Tier 1: Local synthetic fixture -> SANDBOX_FIXTURE + CONTRACT_VERIFIED
    res_fixture = adapter.execute("search_schemes", {"query": "farmer"})
    assert res_fixture.data_source == SourceType.SANDBOX_FIXTURE
    assert res_fixture.verification_status == VerificationStatus.CONTRACT_VERIFIED

    # Tier 2: Actual official sandbox endpoint -> OFFICIAL_GOVERNMENT_API + SANDBOX_VERIFIED
    with patch("src.government_api.adapters.myscheme_adapter.get_settings") as mock_settings:
        mock_settings.return_value.gov_api_enabled = True
        mock_settings.return_value.gov_api_environment = "sandbox"
        mock_settings.return_value.apisetu_api_key = "sandbox_key"
        mock_settings.return_value.apisetu_client_id = "sandbox_client"
        mock_settings.return_value.apisetu_base_url = "https://partners.apisetu.gov.in/api/v1"

        with patch.object(adapter._client, "get", return_value={"schemes": [{"scheme_name": "Sandbox Scheme"}]}):
            res_sandbox = adapter.execute("search_schemes", {"query": "official_sandbox_test"})
            assert res_sandbox.data_source == SourceType.OFFICIAL_GOVERNMENT_API
            assert res_sandbox.verification_status == VerificationStatus.SANDBOX_VERIFIED

    # Tier 3: Actual authorized production API -> OFFICIAL_GOVERNMENT_API + PRODUCTION_CONNECTED
    with patch("src.government_api.adapters.myscheme_adapter.get_settings") as mock_settings:
        mock_settings.return_value.gov_api_enabled = True
        mock_settings.return_value.gov_api_environment = "production"
        mock_settings.return_value.apisetu_api_key = "prod_key"
        mock_settings.return_value.apisetu_client_id = "prod_client"
        mock_settings.return_value.apisetu_base_url = "https://apisetu.gov.in/api/v1"

        with patch.object(adapter._client, "get", return_value={"schemes": [{"scheme_name": "Prod Scheme"}]}):
            res_prod = adapter.execute("search_schemes", {"query": "official_production_test"})
            assert res_prod.data_source == SourceType.OFFICIAL_GOVERNMENT_API
            assert res_prod.verification_status == VerificationStatus.PRODUCTION_CONNECTED

