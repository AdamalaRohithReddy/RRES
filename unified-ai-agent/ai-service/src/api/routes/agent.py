"""Primary Agent Orchestration endpoint (M3, M4, M5, M6, M7, M8)."""
import logging
from fastapi import APIRouter, Depends, Header
from typing import Optional

from src.api.dependencies import verify_internal_api_key, get_citizen_id, get_correlation_id
from src.api.schemas.chat import ChatRequest, ChatResponse
from src.agent.factory import create_agent_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/agent", tags=["Agent Orchestrator"])


@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(
    request: ChatRequest,
    _auth: str = Depends(verify_internal_api_key),
    citizen_id: str = Depends(get_citizen_id),
    correlation_id: str = Depends(get_correlation_id),
) -> ChatResponse:
    """Execute citizen conversational turn through Agent Orchestrator.
    
    The orchestrator reasons over the input query and dynamically calls registered tools
    (RAG search, citizen profile, document analysis, need detection, eligibility engine,
    and government scheme discovery) before returning a grounded response.
    """
    logger.info(f"[{correlation_id}] Chat request for citizen={citizen_id}: {request.query[:80]}...")
    orchestrator = create_agent_orchestrator(citizen_id=citizen_id, verbose=False)
    agent_response = orchestrator.run(query=request.query)

    return ChatResponse(
        answer=agent_response.answer,
        tools_called=agent_response.tools_called,
        sources=agent_response.sources,
        detected_needs=agent_response.detected_needs,
        is_mock_used=agent_response.is_mock_used,
        iterations=agent_response.iterations,
        quota_limited=agent_response.quota_limited,
        session_id=request.session_id,
    )
