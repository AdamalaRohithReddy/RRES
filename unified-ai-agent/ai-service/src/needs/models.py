"""Data models for Milestone 6: Multi-Need Detection."""
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class NeedCategory(str, Enum):
    """Controlled taxonomy of citizen support domains."""
    EMPLOYMENT = "employment"
    FINANCIAL_HARDSHIP = "financial_hardship"
    EDUCATION = "education"
    HOUSING = "housing"
    HEALTHCARE = "healthcare"
    AGRICULTURE = "agriculture"
    ENTREPRENEURSHIP = "entrepreneurship"
    SOCIAL_WELFARE = "social_welfare"
    DISABILITY_SUPPORT = "disability_support"
    SENIOR_CITIZEN_SUPPORT = "senior_citizen_support"
    WOMEN_SUPPORT = "women_support"
    SKILL_DEVELOPMENT = "skill_development"
    FOOD_BASIC_NEEDS = "food_basic_needs"
    OTHER = "other"
    UNKNOWN_AMBIGUOUS = "unknown_ambiguous"


class NeedType(str, Enum):
    """Distinction between direct citizen assertion and derived/inferred suggestion."""
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"


class NeedConfidenceLevel(str, Enum):
    """Operational confidence bands for detected needs."""
    HIGH = "HIGH"          # >= 0.80: Direct pattern match with explicit context
    MEDIUM = "MEDIUM"      # 0.50 - 0.79: Inferred or contextual match
    LOW = "LOW"            # < 0.50: Ambiguous or weak signal (requires clarification)


DISCLAIMER_TEXT: str = (
    "Need classification interprets citizen-described requirements to identify relevant assistance; "
    "it does NOT determine eligibility or guarantee government benefit approval."
)


class Need(BaseModel):
    """Structured representation of an individual citizen hardship or goal."""
    need_id: str = Field(default="", description="Unique need identifier (e.g. need_emp_01)")
    category: NeedCategory = Field(description="Standardized welfare domain category")
    description: str = Field(description="Concise description of the citizen's specific problem")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score of detection (0.0 to 1.0)")
    confidence_level: NeedConfidenceLevel = Field(description="Operational confidence band")
    explicit_or_inferred: NeedType = Field(default=NeedType.EXPLICIT, description="Direct vs implied need")
    evidence_span: Optional[str] = Field(default=None, description="Exact text substring from query evidencing this need")
    is_ambiguous: bool = Field(default=False, description="Flag indicating if the phrasing is unspecific")
    clarification_needed: Optional[str] = Field(default=None, description="Targeted prompt if clarification is required")
    related_categories: List[NeedCategory] = Field(default_factory=list, description="Associated secondary categories")
    suggested_scheme_query: Optional[str] = Field(default=None, description="Suggested internal search query for this need")


class MultiNeedResult(BaseModel):
    """Aggregated output of multi-need detection."""
    status: str = Field(default="success")
    original_text: str = Field(default="", description="Original user query analyzed")
    needs: List[Need] = Field(default_factory=list, description="Deduplicated list of detected needs")
    total_needs: int = Field(default=0)
    has_ambiguous_needs: bool = Field(default=False)
    is_ambiguous: bool = Field(default=False)
    clarification_prompts: List[str] = Field(default_factory=list)
    suggested_scheme_queries: Dict[str, str] = Field(
        default_factory=dict,
        description="Internal semantic retrieval queries keyed by category. NOTE: Retrieval queries only, not official scheme names."
    )
    disclaimer: str = Field(default=DISCLAIMER_TEXT)
