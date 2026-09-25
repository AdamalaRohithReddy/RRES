"""Security and credential redaction tests for Government API Integration (Milestone 8)."""

import logging
import pytest
from unittest.mock import patch, MagicMock

from src.government_api.client import GovernmentAPIClient, ALLOWED_DOMAINS
from src.government_api.exceptions import SecurityViolationError
from src.tools.government_api_tool import GovernmentSchemeDiscoveryTool
from src.agent.tool_registry import ToolRegistry


def test_no_arbitrary_urls_accepted():
    client = GovernmentAPIClient()
    unauthorized_urls = [
        "http://apisetu.gov.in/test",
        "https://google.com/search",
        "https://evil-attacker.com/steal",
        "ftp://apisetu.gov.in/files",
        "file:///etc/passwd",
        "javascript:alert(1)",
    ]
    for url in unauthorized_urls:
        with pytest.raises(SecurityViolationError):
            client.validate_url(url)


def test_tool_registry_rejects_arbitrary_api_calls():
    registry = ToolRegistry()
    registry.register(GovernmentSchemeDiscoveryTool())

    # Attempt to execute an arbitrary / unauthorized tool name
    res = registry.execute("call_arbitrary_url", {"url": "https://apisetu.gov.in/secret"})
    assert res["status"] == "error"
    assert res["error_type"] == "UNAUTHORIZED_TOOL"
    assert "Access Denied" in res["message"]


def test_credentials_not_leaked_in_tool_output():
    tool = GovernmentSchemeDiscoveryTool()
    output = tool.execute(query="farmer")

    output_str = str(output)
    # Ensure sensitive credential placeholders or patterns are absent
    assert "X-APISETU-APIKEY" not in output_str
    assert "APISETU_API_KEY" not in output_str
    assert "SecretStr" not in output_str


def test_sensitive_citizen_records_not_cached():
    from src.government_api.adapters.digilocker_adapter import DigiLockerCertificateAdapter
    from src.government_api.cache import MetadataCache

    adapter = DigiLockerCertificateAdapter()
    # Execute certificate verification
    res = adapter.execute("verify_income_certificate", {"certificate_id": "TS-INC-2026-0091823"})
    assert res.status.value == "SUCCESS"

    # Adapter must not possess or use a public cache
    assert not hasattr(adapter, "_cache")
