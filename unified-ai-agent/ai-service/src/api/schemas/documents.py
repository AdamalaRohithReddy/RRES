"""Document AI analysis schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentAnalysisRequest(BaseModel):
    """Request to analyze an uploaded document file."""
    file_path: str = Field(..., description="Absolute or relative path to document file on server")
    document_id: Optional[int] = Field(None, description="Optional MySQL document_id if pre-registered by Spring Boot")


class ExtractedFieldItem(BaseModel):
    """Structured fact extracted from document."""
    value: Any = None
    confidence_score: float = 0.0
    confidence_level: str = "LOW"
    provenance_method: str = "PATTERN_MATCH"
    page: int = 1


class DocumentAnalysisResponse(BaseModel):
    """Document AI analysis results."""
    document_path: str
    apparent_document_type: str
    document_type_confidence: float
    ocr_used: bool
    fields: Dict[str, ExtractedFieldItem] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str
