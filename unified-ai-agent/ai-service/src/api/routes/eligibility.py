"""Direct Deterministic Eligibility Evaluation endpoint (M5)."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import verify_internal_api_key, get_citizen_id, get_correlation_id
from src.api.schemas.eligibility import (
    EligibilityEvaluationRequest,
    EligibilityEvaluationResponse,
    RuleEvaluationResult,
)
from src.tools.eligibility_tool import EligibilityCheckTool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/eligibility", tags=["Eligibility"])
_eligibility_tool = EligibilityCheckTool()


@router.post("/evaluate", response_model=EligibilityEvaluationResponse)
def evaluate_eligibility(
    request: EligibilityEvaluationRequest,
    _auth: str = Depends(verify_internal_api_key),
    citizen_id: str = Depends(get_citizen_id),
    correlation_id: str = Depends(get_correlation_id),
) -> EligibilityEvaluationResponse:
    """Evaluate citizen eligibility for a scheme using deterministic statutory rules (M5).
    
    The evaluation is calculated mathematically based on verified demographic data from MySQL,
    extracted facts from Document AI (if a document is provided), and external API evidence.
    """
    logger.info(f"[{correlation_id}] Evaluating eligibility for scheme={request.scheme_id}, citizen={citizen_id}")
    res = _eligibility_tool.execute(
        scheme_id=request.scheme_id,
        citizen_id=citizen_id,
        document_path=request.document_path,
        api_data=request.api_data,
    )

    if res.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Eligibility evaluation failed"),
        )

    rules_results = []
    breakdown = res.get("rule_breakdown", {})
    for p in breakdown.get("passed", []):
        rules_results.append(RuleEvaluationResult(
            rule_id=p.get("rule_id", ""),
            criterion=p.get("description", ""),
            status="PASSED",
            reason=p.get("reason", ""),
        ))
    for f in breakdown.get("failed", []):
        rules_results.append(RuleEvaluationResult(
            rule_id=f.get("rule_id", ""),
            criterion=f.get("description", ""),
            status="FAILED",
            reason=f.get("reason", ""),
        ))
    for u in breakdown.get("unknown", []):
        rules_results.append(RuleEvaluationResult(
            rule_id=u.get("rule_id", ""),
            criterion=u.get("description", ""),
            status="UNKNOWN",
            reason=u.get("reason", ""),
        ))

    return EligibilityEvaluationResponse(
        scheme_id=res.get("scheme_id", request.scheme_id),
        scheme_name=res.get("scheme_name", request.scheme_id),
        citizen_id=citizen_id,
        eligibility_status=res.get("eligibility_status", "INSUFFICIENT_INFORMATION"),
        passed_rules_count=res.get("passed_rules_count", 0),
        failed_rules_count=res.get("failed_rules_count", 0),
        unknown_rules_count=res.get("unknown_rules_count", 0),
        summary_reasons=res.get("summary_reasons", []),
        next_steps=res.get("next_steps", []),
        warnings=res.get("warnings", []),
        conflict_detected=res.get("conflict_detected", False),
        disclaimer=res.get("disclaimer", "Statutory eligibility evaluation. Final grant decisions rest with the competent authority."),
        rules=rules_results,
    )
