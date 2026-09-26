"""Direct Scheme Search (M1 RAG) and Discovery (M8) endpoints."""
import logging
from fastapi import APIRouter, Depends

from src.api.dependencies import verify_internal_api_key, get_correlation_id
from src.api.schemas.schemes import (
    SchemeSearchRequest,
    SchemeSearchResponse,
    SchemeSearchResultItem,
    SchemeDiscoveryRequest,
    SchemeDiscoveryResponse,
    SchemeDiscoveryItem,
)
from src.agent.factory import get_default_retriever
from src.tools.government_api_tool import GovernmentSchemeDiscoveryTool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/schemes", tags=["Schemes"])
_gov_tool = GovernmentSchemeDiscoveryTool()


@router.post("/search", response_model=SchemeSearchResponse)
def search_schemes(
    request: SchemeSearchRequest,
    _auth: str = Depends(verify_internal_api_key),
    correlation_id: str = Depends(get_correlation_id),
) -> SchemeSearchResponse:
    """Execute semantic vector search against official government scheme guidelines (M1 RAG)."""
    logger.info(f"[{correlation_id}] Scheme search query: {request.query[:80]}...")
    retriever = get_default_retriever()
    results = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        score_threshold=request.score_threshold,
    )

    items = [
        SchemeSearchResultItem(
            scheme=r.scheme_name,
            section=r.section,
            page=r.page,
            score=round(r.score, 4),
            content=r.text,
            source=r.source_url or "Official Government Circular",
        )
        for r in results
    ]

    return SchemeSearchResponse(
        query=request.query,
        total_results=len(items),
        results=items,
    )


@router.post("/discover", response_model=SchemeDiscoveryResponse)
def discover_government_schemes(
    request: SchemeDiscoveryRequest,
    _auth: str = Depends(verify_internal_api_key),
    correlation_id: str = Depends(get_correlation_id),
) -> SchemeDiscoveryResponse:
    """Query external official government scheme directory (M8 myScheme / API Setu)."""
    logger.info(f"[{correlation_id}] Government scheme discovery: keyword={request.keyword}, state={request.state}")
    res = _gov_tool.execute(
        query=request.keyword or "",
        state=request.state,
        category=request.category,
    )

    schemes_data = res.get("schemes", [])
    items = []
    for s in schemes_data:
        tb = s.get("target_beneficiaries")
        if isinstance(tb, list):
            tb_list = [str(x) for x in tb]
        elif tb:
            tb_list = [str(tb)]
        else:
            tb_list = []
        items.append(
            SchemeDiscoveryItem(
                scheme_id=s.get("scheme_id", ""),
                scheme_name=s.get("scheme_name", ""),
                ministry=s.get("nodal_ministry") or s.get("ministry"),
                category=s.get("category"),
                state=s.get("state"),
                target_beneficiaries=tb_list,
                brief_description=s.get("brief_description", ""),
                application_url=s.get("application_url"),
                verification_status=res.get("verification_status", "CONTRACT_VERIFIED"),
                data_source=res.get("data_source", "SANDBOX_FIXTURE"),
            )
        )

    return SchemeDiscoveryResponse(
        total_schemes=res.get("total_schemes", len(items)),
        data_freshness=res.get("data_freshness", "CACHED_SNAPSHOT"),
        verification_status=res.get("verification_status", "CONTRACT_VERIFIED"),
        data_source=res.get("data_source", "SANDBOX_FIXTURE"),
        schemes=items,
        notice=res.get("notice"),
    )
