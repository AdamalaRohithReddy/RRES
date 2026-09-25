"""Unit and integration tests for EligibilityCheckTool and Agent integration."""
import json
from unittest.mock import MagicMock
from src.tools.eligibility_tool import EligibilityCheckTool
from src.agent.tool_registry import ToolRegistry
from src.agent.agent import AgentOrchestrator
from src.llm.client import OpenAIClientWrapper
from src.llm.models import AgentTurnResponse, ToolCallRequest



def test_tool_metadata():
    """Verify tool naming, description, and OpenAI function parameters schema."""
    tool = EligibilityCheckTool()
    assert tool.name == "check_eligibility"
    assert "deterministic rule evaluation" in tool.description.lower()

    params = tool.parameters
    assert params["type"] == "object"
    assert "scheme_id" in params["properties"]
    assert "scheme_id" in params["required"]
    assert "citizen_id" in params["properties"]

    openai_spec = tool.to_openai_tool()
    assert openai_spec["type"] == "function"
    assert openai_spec["name"] == "check_eligibility"


def test_tool_registration_in_registry():
    """Verify EligibilityCheckTool registers correctly in ToolRegistry."""
    registry = ToolRegistry()
    tool = EligibilityCheckTool()
    registry.register(tool)

    assert "check_eligibility" in registry
    assert registry.get("check_eligibility") is tool
    assert "check_eligibility" in registry.list_tool_names()
    tool_defs = registry.get_tool_definitions()
    assert any(t["name"] == "check_eligibility" for t in tool_defs)



def test_tool_execution_sisfs_demo_user():
    """Verify SISFS evaluation on demo-user returns INSUFFICIENT_INFORMATION."""
    tool = EligibilityCheckTool()
    res = tool.execute(scheme_id="SISFS", citizen_id="demo-user")

    assert res["status"] == "success"
    assert res["scheme_id"] == "SISFS"
    assert res["eligibility_status"] == "INSUFFICIENT_INFORMATION"
    assert res["passed_rules_count"] == 2
    assert res["unknown_rules_count"] == 2
    assert len(res["next_steps"]) > 0
    assert "Preliminary eligibility assessment" in res["disclaimer"]


def test_tool_execution_telangana_youth_eligible():
    """Verify TELANGANA_YOUTH_SUPPORT on demo-user (age 28, income 240,000) returns ELIGIBLE."""
    tool = EligibilityCheckTool()
    res = tool.execute(scheme_id="TELANGANA_YOUTH_SUPPORT", citizen_id="demo-user")

    assert res["status"] == "success"
    assert res["eligibility_status"] == "ELIGIBLE"
    assert res["passed_rules_count"] == 4
    assert res["failed_rules_count"] == 0


def test_tool_execution_senior_citizen_not_eligible():
    """Verify TELANGANA_YOUTH_SUPPORT on senior-citizen (age 65) returns NOT_ELIGIBLE."""
    tool = EligibilityCheckTool()
    res = tool.execute(scheme_id="TELANGANA_YOUTH_SUPPORT", citizen_id="senior-citizen")

    assert res["status"] == "success"
    assert res["eligibility_status"] == "NOT_ELIGIBLE"
    assert res["failed_rules_count"] >= 1
    failed_ids = [f["rule_id"] for f in res["rule_breakdown"]["failed"]]
    assert "TYS-02" in failed_ids  # Max age 35 exceeded


def test_tool_execution_with_document_ai():
    """Verify tool successfully extracts facts from Document AI and incorporates into evaluation."""
    tool = EligibilityCheckTool()
    res = tool.execute(
        scheme_id="TELANGANA_YOUTH_SUPPORT",
        citizen_id="demo-user",
        document_path="tests/fixtures/documents/digital_income_certificate.pdf",
    )

    assert res["status"] == "success"
    assert res["eligibility_status"] == "ELIGIBLE"
    # Document verified income was 150,000 (overriding profile 240,000)
    income_rule = next(
        p for p in res["rule_breakdown"]["passed"] if p["rule_id"] == "TYS-03"
    )
    assert income_rule["citizen_value"] == 150000
    assert any("Evidence Conflict on 'annual_income'" in w for w in res["warnings"])


def test_tool_execution_unknown_scheme():
    """Verify tool returns structured error on unrecognized scheme."""
    tool = EligibilityCheckTool()
    res = tool.execute(scheme_id="NON_EXISTENT_SCHEME")

    assert res["status"] == "error"
    assert res["error_type"] == "SchemeNotFoundError"
    assert "Available schemes:" in res["error"]


def test_agent_orchestrator_check_eligibility_flow():
    """Verify Agent Orchestrator invokes check_eligibility and explains results accurately."""
    registry = ToolRegistry()
    registry.register(EligibilityCheckTool())

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-4o-mini",
            response_id="resp_001",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_elig_1",
                    name="check_eligibility",
                    arguments={"scheme_id": "TELANGANA_YOUTH_SUPPORT", "citizen_id": "demo-user"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-4o-mini",
            response_id="resp_002",
            content="Based on your profile, you are ELIGIBLE for the Telangana Youth Financial Support scheme. All 4 mandatory requirements are satisfied.",
        ),
    ]

    agent = AgentOrchestrator(
        llm_client=mock_llm,
        tool_registry=registry,
        max_steps=3,
        verbose=False,
    )

    response = agent.run("Am I eligible for Telangana Youth Support?")

    assert "check_eligibility" in response.tools_called
    assert "ELIGIBLE" in response.answer
    assert response.iterations == 2

