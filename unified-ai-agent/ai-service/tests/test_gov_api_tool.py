"""Tests for GovernmentSchemeDiscoveryTool (Milestone 8.2)."""

import pytest
from unittest.mock import MagicMock

from src.tools.government_api_tool import GovernmentSchemeDiscoveryTool
from src.government_api.models import (
    APIResponseStatus,
    DataFreshness,
    NormalizedGovernmentResponse,
    SourceType,
    VerificationStatus,
)


def test_government_scheme_discovery_tool_metadata():
    tool = GovernmentSchemeDiscoveryTool()
    assert tool.name == "discover_government_schemes"
    assert "API Setu myScheme" in tool.description

    # Test OpenAI function definition schema
    openai_tool = tool.to_openai_tool()
    assert openai_tool["type"] == "function"
    assert openai_tool["name"] == "discover_government_schemes"
    assert "query" in openai_tool["parameters"]["properties"]
    assert "query" in openai_tool["parameters"]["required"]


def test_government_scheme_discovery_tool_successful_execution():
    tool = GovernmentSchemeDiscoveryTool()
    result = tool.execute(query="scholarship")

    assert result["status"] == "success"
    assert result["total_found"] >= 1
    assert result["data_source"] == "SANDBOX_FIXTURE"
    assert result["verification_status"] == "CONTRACT_VERIFIED"
    assert "schemes" in result
    assert result["source_url"] == "https://apisetu.gov.in/"


def test_government_scheme_discovery_tool_empty_query():
    tool = GovernmentSchemeDiscoveryTool()
    result = tool.execute(query="")
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_government_scheme_discovery_tool_unavailable_fallback():
    mock_adapter = MagicMock()
    mock_adapter.adapter_id = "myscheme_service"
    mock_adapter.execute.return_value = NormalizedGovernmentResponse(
        status=APIResponseStatus.API_UNAVAILABLE,
        data_source=SourceType.OFFICIAL_GOVERNMENT_API,
        verification_status=VerificationStatus.CONTRACT_VERIFIED,
        provider="NeGD / MeitY",
        api_name="myScheme Service API",
        endpoint_identifier="APISETU_MYSCHEME_SEARCH",
        retrieved_at="2026-09-26T00:00:00Z",
        source_url="https://apisetu.gov.in/",
        payload={},
        error_details={"message": "Upstream service timeout"},
    )

    tool = GovernmentSchemeDiscoveryTool(adapter=mock_adapter)
    result = tool.execute(query="agriculture")

    assert result["status"] == "service_unavailable"
    assert result["fallback_recommended_tool"] == "search_government_schemes"
    assert "search_government_schemes" in result["message"]
