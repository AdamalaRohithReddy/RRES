"""Integration tests for Milestone 6 Multi-Need Detection within the complete architecture.

Verifies:
1. Architectural Flow: Need Detection -> RAG Retrieval -> M5 Eligibility.
2. Inviolable Rule: Need Detection / LLM NEVER determines official government eligibility.
3. Agent Orchestrator integration with tool calling.
4. Safe 429 quota handling for multi-need queries.
"""
from unittest.mock import MagicMock
import pytest

from src.needs.detector import NeedDetector
from src.needs.models import NeedCategory
from src.tools.need_tool import NeedDetectionTool
from src.tools.eligibility_tool import EligibilityCheckTool
from src.eligibility.engine import EligibilityEngine
from src.eligibility.models import FinalEligibilityStatus
from src.agent.tool_registry import ToolRegistry
from src.agent.agent import AgentOrchestrator
from src.llm.models import AgentTurnResponse, ToolCallRequest
from src.llm.client import OpenAIClientWrapper


def test_core_flow_need_to_rag_to_eligibility():
    """Verify the decoupled architectural progression:

    1. Need Detection identifies the problem.
    2. Suggested query directs retrieval to official scheme evidence.
    3. M5 Eligibility Engine deterministically evaluates eligibility.
    4. Need Detector NEVER decides government eligibility.
    """
    detector = NeedDetector()
    problem_text = "I am launching an innovative tech startup and need early-stage seed funding support."
    need_result = detector.detect(problem_text)

    # 1. Need Detection identifies ENTREPRENEURSHIP
    categories = [n.category for n in need_result.needs]
    assert NeedCategory.ENTREPRENEURSHIP in categories
    assert NeedCategory.ENTREPRENEURSHIP.value in need_result.suggested_scheme_queries

    # Crucial check: Need result disclaims eligibility evaluation
    assert "does NOT determine eligibility" in need_result.disclaimer

    # 2. Suggested query can be used for RAG
    suggested_q = need_result.suggested_scheme_queries[NeedCategory.ENTREPRENEURSHIP.value]
    assert len(suggested_q) > 0

    # 3. Deterministic Eligibility Engine (M5) is the ONLY authority for eligibility
    from src.eligibility.models import EligibilityEvidence, EvidenceSource
    engine = EligibilityEngine()
    evidence = {
        "has_dpiit_recognition": EligibilityEvidence(
            field_name="has_dpiit_recognition",
            value=True,
            source=EvidenceSource.CITIZEN_PROFILE,
        ),
        "business_incorporated_years": EligibilityEvidence(
            field_name="business_incorporated_years",
            value=1,
            source=EvidenceSource.CITIZEN_PROFILE,
        ),
        "previous_govt_monetary_support": EligibilityEvidence(
            field_name="previous_govt_monetary_support",
            value=500000,
            source=EvidenceSource.CITIZEN_PROFILE,
        ),
        "indian_promoter_shareholding": EligibilityEvidence(
            field_name="indian_promoter_shareholding",
            value=60,
            source=EvidenceSource.CITIZEN_PROFILE,
        ),
    }
    eval_result = engine.evaluate(
        scheme_id="SISFS",
        evidence_store=evidence,
        citizen_id="test-founder",
    )

    # Only M5 sets evaluation status and resolves criteria
    assert eval_result.status == FinalEligibilityStatus.ELIGIBLE
    assert eval_result.scheme_name == "Startup India Seed Fund Scheme"


def test_agent_orchestrator_need_detection_tool_call():
    """Verify AgentOrchestrator properly routes detect_citizen_needs tool calls."""
    registry = ToolRegistry()
    registry.register(NeedDetectionTool())

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    # Turn 1: LLM decides to call detect_citizen_needs
    step1_response = AgentTurnResponse(
        model="gpt-5.6-luna",
        content=None,
        tool_calls=[
            ToolCallRequest(
                call_id="call_need_1",
                name="detect_citizen_needs",
                arguments={"text": "I lost my job and cannot afford my children's school fees"},
            )
        ],
    )
    # Turn 2: LLM receives tool output and explains result
    step2_response = AgentTurnResponse(
        model="gpt-5.6-luna",
        content=(
            "Based on your requirements, I have identified two primary needs: Employment assistance and Education support. "
            "Please note this analysis does not determine official scheme eligibility."
        ),
        tool_calls=[],
    )
    mock_llm.create_agent_turn.side_effect = [step1_response, step2_response]

    agent = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    response = agent.run("I lost my job and cannot afford my children's school fees")

    assert "detect_citizen_needs" in response.tools_called
    assert len(response.detected_needs) >= 2
    assert "Employment" in response.answer or "employment" in response.answer
    assert response.iterations == 2


def test_agent_quota_fallback_for_multi_need_query():
    """Verify safe 429 quota fallback dispatches detect_citizen_needs directly."""
    registry = ToolRegistry()
    registry.register(NeedDetectionTool())

    # Simulated LLM throwing 429 credit_balance_exhausted
    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    mock_llm.create_agent_turn.side_effect = Exception("Error code: 429 - credit_balance_exhausted")

    agent = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    query = "I lost my job, have low income, and need school fees for my children"
    response = agent.run(query)

    assert response.quota_limited is True
    assert "detect_citizen_needs" in response.tools_called
    assert len(response.detected_needs) >= 2
    assert "[OpenAI Quota Notice]" in response.answer
    assert "EMPLOYMENT" in response.answer
    assert "EDUCATION" in response.answer
    assert "does NOT determine eligibility" in response.answer
