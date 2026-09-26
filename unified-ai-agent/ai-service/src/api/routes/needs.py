"""Direct Multi-Need Detection endpoint (M6)."""
import logging
from fastapi import APIRouter, Depends

from src.api.dependencies import verify_internal_api_key, get_correlation_id
from src.api.schemas.needs import NeedDetectionRequest, NeedDetectionResponse, DetectedNeedItem
from src.needs.detector import NeedDetector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/needs", tags=["Needs Detection"])
_detector = NeedDetector()


@router.post("/detect", response_model=NeedDetectionResponse)
def detect_needs(
    request: NeedDetectionRequest,
    _auth: str = Depends(verify_internal_api_key),
    correlation_id: str = Depends(get_correlation_id),
) -> NeedDetectionResponse:
    """Analyze citizen situation text and extract structured needs deterministically."""
    logger.info(f"[{correlation_id}] Multi-need detection for query: {request.text[:80]}...")
    result = _detector.detect_needs(request.text)

    needs_items = [
        DetectedNeedItem(
            category=n.category.value,
            urgency="HIGH" if n.confidence >= 0.9 else "MEDIUM",
            explicit_or_inferred=n.explicit_or_inferred.value,
            confidence_level=n.confidence_level.value,
            description=n.description,
            evidence_span=n.evidence_span,
        )
        for n in result.needs
    ]

    suggested_queries = {
        (cat.value if hasattr(cat, "value") else str(cat)): q
        for cat, q in result.suggested_scheme_queries.items()
    } if result.suggested_scheme_queries else {}

    return NeedDetectionResponse(
        total_needs=result.total_needs,
        needs=needs_items,
        suggested_scheme_queries=suggested_queries,
        clarification_prompts=result.clarification_prompts or [],
        disclaimer="Citizen needs detected for informational guidance only. Official scheme eligibility requires statutory verification.",
    )
