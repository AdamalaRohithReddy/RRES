"""Integration tests for Agent Orchestrator and Government API Tool (Milestone 8)."""

import pytest
from unittest.mock import MagicMock

from src.agent.agent import AgentOrchestrator, AgentResponse
from src.agent.tool_registry import ToolRegistry
from src.llm.client import OpenAIClientWrapper, AgentTurnResponse, ToolCallRequest
from src.tools.government_api_tool import GovernmentSchemeDiscoveryTool
from src.tools.mysql_tool import CitizenProfileTool
from src.tools.rag_tool import SchemeSearchTool


def test_agent_orchestrator_calls_discover_government_schemes():
    registry = ToolRegistry()
    registry.register(GovernmentSchemeDiscoveryTool())

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    # Turn 1: LLM calls discover_government_schemes
    # Turn 2: LLM generates final answer grounded in API Setu discovery
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_gov_1",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_gov_1",
                    name="discover_government_schemes",
                    arguments={"query": "farmer income support"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_gov_2",
            content=(
                "According to the official national scheme directory (via API Setu myScheme), "
                "the Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) provides financial assistance "
                "of Rs. 6,000 per year for eligible farmer families. You can apply at https://pmkisan.gov.in/."
            ),
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    resp = orchestrator.run("What official schemes exist for farmers?")

    assert "discover_government_schemes" in resp.tools_called
    assert resp.iterations == 2
    assert "PM-KISAN" in resp.answer
    assert "https://pmkisan.gov.in/" in resp.answer


def test_agent_orchestrator_chains_profile_and_government_api():
    registry = ToolRegistry()
    registry.register(CitizenProfileTool())
    registry.register(GovernmentSchemeDiscoveryTool())

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    # Turn 1: Get citizen profile
    # Turn 2: Discover government schemes based on profile
    # Turn 3: Final integrated answer
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_t1",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_p1",
                    name="get_citizen_profile",
                    arguments={"citizen_id": "rural-farmer"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_t2",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_g1",
                    name="discover_government_schemes",
                    arguments={"query": "agriculture farmer support", "state": "Gujarat"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_t3",
            content=(
                "Hello Suresh Patel. Based on your profile in Gujarat, you may explore the "
                "PM-KISAN scheme from the Ministry of Agriculture. Details were retrieved from the "
                "official national directory."
            ),
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    resp = orchestrator.run("Based on my profile, what government schemes should I look into?")

    assert resp.tools_called == ["get_citizen_profile", "discover_government_schemes"]
    assert resp.iterations == 3
    assert "Suresh Patel" in resp.answer
    assert "PM-KISAN" in resp.answer


def test_agent_orchestrator_handles_api_unavailable_with_rag_fallback():
    registry = ToolRegistry()

    from src.government_api.models import (
        NormalizedGovernmentResponse,
        APIResponseStatus,
        SourceType,
        VerificationStatus,
    )

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
    gov_tool = GovernmentSchemeDiscoveryTool(adapter=mock_adapter)
    registry.register(gov_tool)

    # Mock RAG tool
    mock_rag = MagicMock(spec=SchemeSearchTool)
    mock_rag.name = "search_government_schemes"
    mock_rag.to_openai_tool.return_value = {
        "type": "function",
        "name": "search_government_schemes",
        "description": "rag search",
        "parameters": {},
    }
    mock_rag.execute.return_value = {
        "status": "success",
        "results": [
            {
                "scheme": "Startup India Seed Fund Scheme",
                "section": "Eligibility",
                "page": 2,
                "score": 0.92,
                "content": "Official guideline text for early stage startup founders.",
                "source": "https://www.startupindia.gov.in",
            }
        ],
    }
    registry.register(mock_rag)

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    # Turn 1: Calls discover_government_schemes -> returns service_unavailable
    # Turn 2: Fallback to search_government_schemes (M1 RAG)
    # Turn 3: Final grounded answer explaining the fallback
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_f1",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_f1",
                    name="discover_government_schemes",
                    arguments={"query": "tech startup"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_f2",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_f2",
                    name="search_government_schemes",
                    arguments={"query": "Startup India Seed Fund eligibility"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_f3",
            content=(
                "The live government scheme directory is temporarily unavailable. "
                "However, consulting our official offline guidelines, the Startup India Seed Fund Scheme "
                "(Page 2, Eligibility) supports early stage startups."
            ),
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    resp = orchestrator.run("What support is available for my tech startup?")

    assert resp.tools_called == ["discover_government_schemes", "search_government_schemes"]
    assert resp.iterations == 3
    assert "temporarily unavailable" in resp.answer
    assert "Startup India Seed Fund" in resp.answer
