"""Optional live smoke tests for Government API Integration (Milestone 8.4).

These tests run ONLY if explicitly enabled with environment variable:
    RUN_LIVE_GOV_API_TESTS=true
and valid credentials are provided in .env:
    APISETU_CLIENT_ID
    APISETU_API_KEY
"""

import os
import pytest

from src.config.settings import get_settings
from src.government_api.adapters.myscheme_adapter import MySchemeAdapter
from src.government_api.models import APIResponseStatus, SourceType, VerificationStatus


LIVE_TESTS_ENABLED = os.getenv("RUN_LIVE_GOV_API_TESTS", "false").lower() in ("true", "1", "yes")


@pytest.mark.skipif(not LIVE_TESTS_ENABLED, reason="Live government API tests disabled by default.")
def test_live_myscheme_api_smoke():
    settings = get_settings()
    if not settings.apisetu_api_key or not settings.apisetu_client_id:
        pytest.skip("API Setu credentials not configured in environment.")

    adapter = MySchemeAdapter()
    res = adapter.execute("search_schemes", {"query": "agriculture"})

    assert res.status == APIResponseStatus.SUCCESS
    assert res.data_source == SourceType.OFFICIAL_GOVERNMENT_API
    assert res.verification_status == VerificationStatus.PRODUCTION_CONNECTED
