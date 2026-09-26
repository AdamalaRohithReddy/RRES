"""Deterministic eligibility schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EligibilityEvaluationRequest(BaseModel):
    """Request to evaluate eligibility against deterministic rules."""
    scheme_id: str = Field(..., description="Target scheme identifier (e.g. SISFS, APY, TELANGANA_YOUTH_SUPPORT)")
    document_path: Optional[str] = Field(None, description="Optional path to uploaded document")
    api_data: Optional[Dict[str, Any]] = Field(None, description="Optional verified external API data")


class RuleEvaluationResult(BaseModel):
    """Detailed evaluation result for a single rule."""
    rule_id: str
    criterion: str
    status: str  # PASSED, FAILED, UNKNOWN
    reason: str


class EligibilityEvaluationResponse(BaseModel):
    """Deterministic eligibility assessment report."""
    scheme_id: str
    scheme_name: str
    citizen_id: str
    eligibility_status: str  # ELIGIBLE, NOT_ELIGIBLE, INCONCLUSIVE
    passed_rules_count: int
    failed_rules_count: int
    unknown_rules_count: int
    summary_reasons: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    conflict_detected: bool = False
    disclaimer: str
    rules: List[RuleEvaluationResult] = Field(default_factory=list)
