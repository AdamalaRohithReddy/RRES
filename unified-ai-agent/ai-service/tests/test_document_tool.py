"""Unit and integration tests for DocumentAnalysisTool and Agent Orchestrator integration."""
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.tools.document_tool import DocumentAnalysisTool, SecurityViolationError
from src.agent.tool_registry import ToolRegistry
from src.agent.agent import AgentOrchestrator, AgentResponse
from src.llm.client import OpenAIClientWrapper
from src.llm.models import AgentTurnResponse, ToolCallRequest


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "documents"


# ---------------------------------------------------------------------------
# Tool Registration & Schema Test
# ---------------------------------------------------------------------------
def test_document_tool_registration_and_schema():
    tool = DocumentAnalysisTool()
    assert tool.name == "analyze_document"
    assert "document_path" in tool.parameters["properties"]
    assert "document authenticity" in tool.description

    # Openai tool schema export
    openai_tool = tool.to_openai_tool()
    assert openai_tool["type"] == "function"
    assert openai_tool["name"] == "analyze_document"
    assert "document_path" in openai_tool["parameters"]["properties"]

    # Register in ToolRegistry
    registry = ToolRegistry()
    registry.register(tool)
    assert "analyze_document" in registry.list_tool_names()
    assert registry.get("analyze_document") is tool


# ---------------------------------------------------------------------------
# Test F: Strict Filesystem Security & Sandboxing
# ---------------------------------------------------------------------------
def test_document_tool_security_path_traversal_rejection():
    tool = DocumentAnalysisTool()

    # 1. Path traversal escape attempt
    traversal_path = "../../some_system_secret.txt"
    res = tool.execute(document_path=traversal_path)
    assert res["status"] == "error"
    assert res["error_type"] == "SecurityViolationError"
    assert "outside approved sandbox" in res["error"]

    # 2. Direct system path outside approved sandbox
    system_path = "C:\\Windows\\System32\\notepad.exe"
    res_sys = tool.execute(document_path=system_path)
    assert res_sys["status"] == "error"
    assert res_sys["error_type"] == "SecurityViolationError"

    # 3. Executable file rejection
    exe_path = str(FIXTURES_DIR / "malicious_file.exe")
    res_exe = tool.execute(document_path=exe_path)
    assert res_exe["status"] == "error"
    assert res_exe["error_type"] == "SecurityViolationError"
    assert "prohibited" in res_exe["error"]

    # 4. Zero-byte / empty file rejection
    empty_path = str(FIXTURES_DIR / "empty_document.pdf")
    res_empty = tool.execute(document_path=empty_path)
    assert res_empty["status"] == "error"
    assert res_empty["error_type"] == "CorruptedDocumentError"

    # 5. Corrupted file rejection
    corrupt_path = str(FIXTURES_DIR / "corrupt_document.pdf")
    res_corrupt = tool.execute(document_path=corrupt_path)
    assert res_corrupt["status"] == "error"


# ---------------------------------------------------------------------------
# Valid Execution & Non-Verification Disclaimer
# ---------------------------------------------------------------------------
def test_document_tool_execution_success():
    tool = DocumentAnalysisTool()
    valid_doc = str(FIXTURES_DIR / "digital_income_certificate.pdf")

    res = tool.execute(document_path=valid_doc)
    assert res["status"] == "success"
    assert res["apparent_document_type"] == "income_certificate"
    assert res["document_type_confidence"] >= 0.70

    fields = res["fields"]
    assert fields["annual_income"]["value"] == 150000
    assert fields["annual_income"]["confidence_level"] == "HIGH"
    assert fields["name"]["value"] == "Demo Citizen"

    # Verify non-authenticity disclaimer
    assert "authenticity" in res["disclaimer"].lower()
    assert res["is_mock"] is False


# ---------------------------------------------------------------------------
# Test H: Agent Orchestrator + Document Tool Integration (Mock LLM)
# ---------------------------------------------------------------------------
def test_agent_orchestrator_document_tool_flow_mock_llm():
    """Verify that Agent invokes analyze_document and explains facts without live OpenAI."""
    tool = DocumentAnalysisTool()
    registry = ToolRegistry()
    registry.register(tool)

    valid_doc = str(FIXTURES_DIR / "digital_income_certificate.pdf")

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    # Turn 1: LLM decides to call analyze_document
    # Turn 2: LLM produces grounded answer explaining extracted fields
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_doc_001",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_doc_001",
                    name="analyze_document",
                    arguments={"document_path": valid_doc},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_doc_002",
            content=(
                "Based on the uploaded document, it appears to be an Income Certificate (confidence 85%). "
                "The extracted annual income is Rs. 1,50,000 for Sri Demo Citizen residing in Telangana "
                "(Page 1). Note: Document classification is not legal authenticity verification."
            ),
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    query = "Please check the income certificate I uploaded and tell me what income is mentioned."
    response = orchestrator.run(query=query)

    assert isinstance(response, AgentResponse)
    assert "analyze_document" in response.tools_called
    assert "1,50,000" in response.answer
    assert "Income Certificate" in response.answer
    assert response.is_mock_used is False


# ---------------------------------------------------------------------------
# Test Missing Field: Agent Does Not Invent Values
# ---------------------------------------------------------------------------
def test_agent_orchestrator_handles_missing_field_in_document():
    tool = DocumentAnalysisTool()
    registry = ToolRegistry()
    registry.register(tool)

    missing_doc = str(FIXTURES_DIR / "missing_income_certificate.pdf")

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_doc_003",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_doc_002",
                    name="analyze_document",
                    arguments={"document_path": missing_doc},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_doc_004",
            content=(
                "I analyzed the uploaded document for Demo Citizen, but could not find an annual income "
                "value mentioned in the document. Please provide an official income certificate."
            ),
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    query = "What is the annual income in this certificate?"
    response = orchestrator.run(query=query)

    assert "analyze_document" in response.tools_called
    assert "could not find an annual income" in response.answer.lower()
