"""Factory for creating standard AgentOrchestrator instances with configured tools."""
from typing import Optional

from src.agent.agent import AgentOrchestrator
from src.agent.tool_registry import ToolRegistry
from src.retrieval.retriever import SchemeRetriever
from src.embeddings.sentence_transformer_embedder import get_embedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.tools.rag_tool import SchemeSearchTool
from src.tools.mysql_tool import CitizenProfileTool
from src.tools.api_tool import ApplicationStatusTool
from src.tools.document_tool import DocumentAnalysisTool
from src.tools.eligibility_tool import EligibilityCheckTool
from src.tools.need_tool import NeedDetectionTool
from src.tools.government_api_tool import GovernmentSchemeDiscoveryTool


_default_retriever: Optional[SchemeRetriever] = None


def get_default_retriever() -> SchemeRetriever:
    """Instantiate standard SchemeRetriever with singleton embedder and vector store."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = SchemeRetriever(embedder=get_embedder(), vector_store=QdrantVectorStore())
    return _default_retriever


def clear_retriever_cache() -> None:
    """Clear cached default retriever instance."""
    global _default_retriever
    _default_retriever = None


def create_agent_tool_registry(
    retriever: Optional[SchemeRetriever] = None,
    citizen_id: Optional[str] = None,
) -> ToolRegistry:
    """Create and configure ToolRegistry with all M1-M8 tools bound to citizen context."""
    registry = ToolRegistry()
    r = retriever or get_default_retriever()
    registry.register(SchemeSearchTool(retriever=r))
    registry.register(CitizenProfileTool(default_citizen_id=citizen_id))
    registry.register(ApplicationStatusTool())
    registry.register(DocumentAnalysisTool())
    registry.register(EligibilityCheckTool())
    registry.register(NeedDetectionTool())
    registry.register(GovernmentSchemeDiscoveryTool())
    return registry


def create_agent_orchestrator(
    citizen_id: Optional[str] = None,
    retriever: Optional[SchemeRetriever] = None,
    verbose: bool = False,
) -> AgentOrchestrator:
    """Construct an AgentOrchestrator configured with all tools and optional citizen binding."""
    registry = create_agent_tool_registry(retriever=retriever, citizen_id=citizen_id)
    return AgentOrchestrator(tool_registry=registry, verbose=verbose)
