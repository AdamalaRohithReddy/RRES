"""Pydantic data models for the Deterministic Eligibility Engine (Milestone 5)."""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RuleOperator(str, Enum):
    """Supported comparison operators for deterministic rule evaluation."""
    GTE = ">="
    LTE = "<="
    GT = ">"
    LT = "<"
    EQ = "=="
    NEQ = "!="
    IN = "IN"
    NOT_IN = "NOT_IN"
    REQUIRED = "REQUIRED"


class RuleStatus(str, Enum):
    """Evaluation status for an individual eligibility rule."""
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class FinalEligibilityStatus(str, Enum):
    """Authoritative outcome of the scheme eligibility assessment."""
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class EvidenceSource(str, Enum):
    """Source provenance for an observed evidence attribute."""
    CITIZEN_PROFILE = "CITIZEN_PROFILE"
    DOCUMENT_AI = "DOCUMENT_AI"
    USER_INPUT = "USER_INPUT"


class EligibilityEvidence(BaseModel):
    """Individual attribute evidence used during rule evaluation with full provenance."""
    field_name: str
    value: Optional[Any] = None
    raw_value: Optional[Any] = None
    source: EvidenceSource = EvidenceSource.CITIZEN_PROFILE
    confidence: float = 1.0
    confidence_level: str = "HIGH"
    source_reference: Optional[str] = None
    page: Optional[int] = None
    source_text: Optional[str] = None


class EligibilityRule(BaseModel):
    """Structured eligibility condition defining an authoritative requirement for a scheme."""
    rule_id: str
    scheme_id: str
    scheme_name: str
    field_name: str
    operator: RuleOperator
    threshold: Any
    description: str
    is_mandatory: bool = True
    is_synthetic: bool = False
    official_source: str
    official_page: Optional[int] = None
    official_section: Optional[str] = None
    official_quote: Optional[str] = None


class RuleEvaluation(BaseModel):
    """Detailed evaluation outcome for a single eligibility rule."""
    rule: EligibilityRule
    status: RuleStatus
    citizen_value: Optional[Any] = None
    threshold_value: Any
    reason: str
    evidence_used: Optional[EligibilityEvidence] = None
    missing_evidence: bool = False
    discrepancy_warning: Optional[str] = None


class EligibilityResult(BaseModel):
    """Final, authoritative outcome of the deterministic scheme eligibility assessment.

    IMPORTANT: "Eligibility Engine determines eligibility. The Agent orchestrates.
    The LLM explains the result." The LLM must not override or invent rule decisions.
    """
    status: FinalEligibilityStatus
    scheme_id: str
    scheme_name: str
    citizen_id: Optional[str] = None
    total_rules: int = 0
    mandatory_rules: int = 0
    passed_rules: List[RuleEvaluation] = Field(default_factory=list)
    failed_rules: List[RuleEvaluation] = Field(default_factory=list)
    unknown_rules: List[RuleEvaluation] = Field(default_factory=list)
    summary_reasons: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Preliminary eligibility assessment based on available structured rules and evidence. "
        "Does NOT constitute official government sanction, legal eligibility, or guaranteed benefit approval."
    )
    is_synthetic_scheme: bool = False
