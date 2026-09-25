"""Unit and integration tests for Milestone 3: Agent Orchestrator & Tool Calling."""
from unittest.mock import MagicMock
from src.retrieval.retriever import SchemeRetriever
from src.embeddings.sentence_transformer_embedder import get_embedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.config.settings import get_settings
from src.tools.rag_tool import SchemeSearchTool
from src.tools.mysql_tool import CitizenProfileTool
from src.tools.api_tool import ApplicationStatusTool
from src.agent.tool_registry import ToolRegistry
from src.agent.state import AgentState
from src.agent.agent import AgentOrchestrator, AgentResponse
from src.llm.models import AgentTurnResponse, ToolCallRequest
from src.llm.client import OpenAIClientWrapper


from src.chunking.models import DocumentChunk
from src.embeddings.base import BaseEmbedder


class _TestEmbedder(BaseEmbedder):
    @property
    def model_name(self) -> str:
        return "mock-embedder"

    @property
    def dimension(self) -> int:
        return 3

    def embed_text(self, text: str):
        return [1.0, 0.0, 0.0]

    def embed_batch(self, texts, batch_size=32):
        return [[1.0, 0.0, 0.0] for _ in texts]


# ---------------------------------------------------------------------------
# Test 1: RAG Tool Execution & Provenance
# ---------------------------------------------------------------------------
def test_rag_tool_execution_preserves_provenance():
    embedder = _TestEmbedder()
    store = QdrantVectorStore(collection_name="test_agent_rag", path=":memory:", dimension=3)
    store.initialize_collection()

    test_chunk = DocumentChunk(
        chunk_id="chunk_test_01",
        document_id="doc_test_01",
        scheme_id="SISFS",
        scheme_name="Startup India Seed Fund Scheme",
        text="A startup recognized by DPIIT within 2 years of incorporation is eligible.",
        page_start=3,
        page_end=3,
        section="Eligibility",
        source_type="official",
        source_url="https://seedfund.startupindia.gov.in",
        last_verified="2026-01-01",
    )
    store.upsert_chunks([test_chunk], embeddings=[[1.0, 0.0, 0.0]])

    retriever = SchemeRetriever(
        embedder=embedder,
        vector_store=store,
        default_top_k=2,
        score_threshold=0.1,
    )

    rag_tool = SchemeSearchTool(retriever=retriever)
    assert rag_tool.name == "search_government_schemes"
    assert "query" in rag_tool.parameters["properties"]

    result = rag_tool.execute(
        query="What are the eligibility criteria for the Startup India Seed Fund Scheme?",
        top_k=2,
    )

    assert result["status"] == "success"
    assert result["total_found"] > 0
    assert result["is_evidence_sufficient"] is True

    # Verify first chunk provenance
    top_chunk = result["results"][0]
    assert top_chunk["scheme"] == "Startup India Seed Fund Scheme"
    assert top_chunk["section"] == "Eligibility"
    assert top_chunk["page"] == 3
    assert "score" in top_chunk
    assert "content" in top_chunk
    assert "source" in top_chunk
    assert top_chunk["source"] == "https://seedfund.startupindia.gov.in"
    assert top_chunk["page"] >= 1


# ---------------------------------------------------------------------------
# Test 2: MySQL Tool (Mock Citizen Profile)
# ---------------------------------------------------------------------------
def test_mysql_mock_tool_returns_profile_data():
    profile_tool = CitizenProfileTool()
    assert profile_tool.name == "get_citizen_profile"

    # Test default demo user
    res = profile_tool.execute(citizen_id="demo-user")
    assert res["status"] == "success"
    assert res["is_mock"] is True
    assert "DEMO MOCK DATA" in res["notice"]

    profile = res["profile"]
    assert profile["citizen_id"] == "demo-user"
    assert profile["age"] == 28
    assert profile["state"] == "Telangana"
    assert profile["annual_income"] == 240000

    # Test senior citizen profile
    res_senior = profile_tool.execute(citizen_id="senior-citizen")
    assert res_senior["profile"]["age"] == 65
    assert res_senior["profile"]["state"] == "Telangana"


# ---------------------------------------------------------------------------
# Test 3: API Tool (Mock Application Status)
# ---------------------------------------------------------------------------
def test_api_mock_tool_returns_application_status():
    api_tool = ApplicationStatusTool()
    assert api_tool.name == "get_application_status"

    res = api_tool.execute(application_id="DEMO-001")
    assert res["status"] == "success"
    assert res["is_mock"] is True
    assert "DEMO MOCK DATA" in res["notice"]

    record = res["record"]
    assert record["application_id"] == "DEMO-001"
    assert "Under Evaluation" in record["status"]
    assert record["scheme_name"] == "Startup India Seed Fund Scheme"


# ---------------------------------------------------------------------------
# Test 4: Agent Orchestrator Single Tool (RAG)
# ---------------------------------------------------------------------------
def test_agent_orchestrator_rag_scenario():
    registry = ToolRegistry()
    mock_rag = MagicMock(spec=SchemeSearchTool)
    mock_rag.name = "search_government_schemes"
    mock_rag.to_openai_tool.return_value = {
        "type": "function",
        "name": "search_government_schemes",
        "description": "search schemes",
        "parameters": {},
    }
    mock_rag.execute.return_value = {
        "status": "success",
        "results": [
            {
                "scheme": "Startup India Seed Fund Scheme",
                "section": "Eligibility",
                "page": 2,
                "score": 0.86,
                "content": "Startups recognized by DPIIT within 2 years are eligible.",
                "source": "https://www.startupindia.gov.in",
            }
        ],
    }
    registry.register(mock_rag)

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    # Turn 1: LLM requests search tool
    # Turn 2: LLM produces final grounded answer
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_001",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_001",
                    name="search_government_schemes",
                    arguments={"query": "Startup India Seed Fund eligibility"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_002",
            content="Under the Startup India Seed Fund Scheme, startups recognized by DPIIT within 2 years of incorporation are eligible (Page 2, Eligibility).",
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    resp = orchestrator.run("What are the eligibility criteria for the Startup India Seed Fund Scheme?")

    assert isinstance(resp, AgentResponse)
    assert "search_government_schemes" in resp.tools_called
    assert len(resp.sources) == 1
    assert resp.sources[0]["page"] == 2
    assert "DPIIT" in resp.answer
    assert resp.iterations == 2


# ---------------------------------------------------------------------------
# Test 5: Agent Orchestrator Profile Tool (MySQL Mock)
# ---------------------------------------------------------------------------
def test_agent_orchestrator_profile_scenario():
    registry = ToolRegistry()
    registry.register(CitizenProfileTool())

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_001",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_prof",
                    name="get_citizen_profile",
                    arguments={"citizen_id": "demo-user"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_002",
            content="According to your development demo profile, you are Ramesh Kumar, 28 years old, residing in Telangana with an annual income of Rs. 2,40,000.",
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    resp = orchestrator.run("What information do we have about my profile?")

    assert "get_citizen_profile" in resp.tools_called
    assert resp.is_mock_used is True
    assert "Ramesh Kumar" in resp.answer
    assert "Telangana" in resp.answer


# ---------------------------------------------------------------------------
# Test 6: Agent Orchestrator Multi-Tool Flow (Profile -> Scheme Search -> Answer)
# ---------------------------------------------------------------------------
def test_agent_orchestrator_multitool_flow():
    registry = ToolRegistry()
    registry.register(CitizenProfileTool())

    mock_rag = MagicMock(spec=SchemeSearchTool)
    mock_rag.name = "search_government_schemes"
    mock_rag.to_openai_tool.return_value = {
        "type": "function",
        "name": "search_government_schemes",
        "description": "search",
        "parameters": {},
    }
    mock_rag.execute.return_value = {
        "status": "success",
        "results": [
            {
                "scheme": "Startup India Seed Fund Scheme",
                "section": "Eligibility",
                "page": 2,
                "score": 0.89,
                "content": "Early stage tech startups in Telangana can apply through incubators.",
                "source": "https://www.startupindia.gov.in",
            }
        ],
        "is_mock": False,
    }
    registry.register(mock_rag)

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    # Turn 1: Get citizen profile
    # Turn 2: Search schemes based on citizen's profile
    # Turn 3: Final integrated natural-language answer
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_t1",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_t1",
                    name="get_citizen_profile",
                    arguments={"citizen_id": "demo-user"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_t2",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_t2",
                    name="search_government_schemes",
                    arguments={"query": "tech startup founder support Telangana"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_t3",
            content="Based on your profile as a 28-year-old tech entrepreneur in Telangana, you may be eligible for the Startup India Seed Fund Scheme (Page 2, Eligibility). Please note your profile was retrieved from demo records.",
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    resp = orchestrator.run("Based on my profile, what government support might be relevant to me?")

    assert resp.tools_called == ["get_citizen_profile", "search_government_schemes"]
    assert resp.is_mock_used is True
    assert len(resp.sources) == 1
    assert resp.iterations == 3
    assert "Startup India Seed Fund" in resp.answer


# ---------------------------------------------------------------------------
# Test 7: Agent Orchestrator Application Status (API Tool)
# ---------------------------------------------------------------------------
def test_agent_orchestrator_application_status():
    registry = ToolRegistry()
    registry.register(ApplicationStatusTool())

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_app1",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_app1",
                    name="get_application_status",
                    arguments={"application_id": "DEMO-001"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_app2",
            content="Based on demo tracking records, application DEMO-001 for Startup India Seed Fund Scheme is currently Under Evaluation by the Incubator Committee.",
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    resp = orchestrator.run("What is the status of my application DEMO-001?")

    assert "get_application_status" in resp.tools_called
    assert resp.is_mock_used is True
    assert "Under Evaluation" in resp.answer


# ---------------------------------------------------------------------------
# Test 8: Unknown / Insufficient Information Handling
# ---------------------------------------------------------------------------
def test_agent_orchestrator_handles_insufficient_information():
    registry = ToolRegistry()
    mock_rag = MagicMock(spec=SchemeSearchTool)
    mock_rag.name = "search_government_schemes"
    mock_rag.to_openai_tool.return_value = {
        "type": "function",
        "name": "search_government_schemes",
        "description": "search",
        "parameters": {},
    }
    mock_rag.execute.return_value = {
        "status": "success",
        "results": [],
        "is_evidence_sufficient": False,
    }
    registry.register(mock_rag)

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    mock_llm.create_agent_turn.side_effect = [
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_u1",
            tool_calls=[
                ToolCallRequest(
                    call_id="call_u1",
                    name="search_government_schemes",
                    arguments={"query": "subsidy for underwater drone exploration"},
                )
            ],
        ),
        AgentTurnResponse(
            model="gpt-5.6-luna",
            response_id="resp_u2",
            content="The available verified government scheme documents do not contain information regarding subsidies for underwater drone exploration.",
        ),
    ]

    orchestrator = AgentOrchestrator(llm_client=mock_llm, tool_registry=registry, verbose=False)
    resp = orchestrator.run("Can I get a subsidy for underwater drone exploration?")

    assert "search_government_schemes" in resp.tools_called
    assert "do not contain information" in resp.answer.lower()


# ---------------------------------------------------------------------------
# Test 9: Tool Safety - Rejection of Arbitrary System / Python / SQL Calls
# ---------------------------------------------------------------------------
def test_tool_registry_safety_rejects_unauthorized_tools():
    registry = ToolRegistry()
    registry.register(CitizenProfileTool())

    # Attempt arbitrary Python execution
    python_hack = registry.execute("exec_python", {"code": "import os; os.system('echo hacked')"})
    assert python_hack["status"] == "error"
    assert python_hack["error_type"] == "UNAUTHORIZED_TOOL"

    # Attempt arbitrary SQL execution
    sql_hack = registry.execute("run_sql_query", {"query": "SELECT * FROM users; DROP TABLE citizens;"})
    assert sql_hack["status"] == "error"
    assert sql_hack["error_type"] == "UNAUTHORIZED_TOOL"

    # Attempt shell command execution
    shell_hack = registry.execute("bash", {"command": "cat /etc/passwd"})
    assert shell_hack["status"] == "error"
    assert shell_hack["error_type"] == "UNAUTHORIZED_TOOL"

    # Attempt arbitrary HTTP requests
    http_hack = registry.execute("http_fetch", {"url": "http://malicious-site.com"})
    assert http_hack["status"] == "error"
    assert http_hack["error_type"] == "UNAUTHORIZED_TOOL"


# ---------------------------------------------------------------------------
# Test 10: Loop Limit Prevents Infinite Tool Calls
# ---------------------------------------------------------------------------
def test_agent_orchestrator_loop_limit_prevents_infinite_loop():
    registry = ToolRegistry()
    registry.register(CitizenProfileTool())

    mock_llm = MagicMock(spec=OpenAIClientWrapper)
    # LLM keeps requesting tools repeatedly on every turn
    mock_llm.create_agent_turn.return_value = AgentTurnResponse(
        model="gpt-5.6-luna",
        response_id="resp_loop",
        tool_calls=[
            ToolCallRequest(
                call_id="call_infinite",
                name="get_citizen_profile",
                arguments={"citizen_id": "demo-user"},
            )
        ],
    )

    orchestrator = AgentOrchestrator(
        llm_client=mock_llm,
        tool_registry=registry,
        max_steps=4,
        verbose=False,
    )
    resp = orchestrator.run("Loop test query")

    # Verify that orchestrator terminated safely at max_steps (4 iterations)
    assert resp.iterations == 4
    assert len(resp.tools_called) == 4
    assert "reached the processing limit" in resp.answer.lower()
