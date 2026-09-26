"""Multi-need detection schemas."""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class NeedDetectionRequest(BaseModel):
    """Request to detect citizen needs from natural language text."""
    text: str = Field(..., min_length=1, description="Citizen text describing their situation")


class DetectedNeedItem(BaseModel):
    """Individual citizen need identified."""
    category: str
    urgency: str
    explicit_or_inferred: str
    confidence_level: str
    description: str
    evidence_span: Optional[str] = None


class NeedDetectionResponse(BaseModel):
    """Response containing extracted needs and recommended queries."""
    total_needs: int
    needs: List[DetectedNeedItem] = Field(default_factory=list)
    suggested_scheme_queries: Dict[str, str] = Field(default_factory=dict)
    clarification_prompts: List[str] = Field(default_factory=list)
    disclaimer: str
