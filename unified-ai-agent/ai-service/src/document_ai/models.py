"""Pydantic data models for Document AI and OCR pipeline."""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Apparent document categories classified from observable textual features."""
    INCOME_CERTIFICATE = "income_certificate"
    IDENTITY_DOCUMENT = "identity_document"
    ADDRESS_DOCUMENT = "address_document"
    EDUCATION_CERTIFICATE = "education_certificate"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Operational confidence categories for extraction reliability.

    HIGH (0.85 - 1.00): Strong pattern match, context confirmed, passes validation.
    UNCERTAIN (0.50 - 0.84): Matched pattern with ambiguous context or OCR artifacts; warning emitted.
    UNRELIABLE (< 0.50): Ambiguous or invalid; value forced to None.
    """
    HIGH = "HIGH"
    UNCERTAIN = "UNCERTAIN"
    UNRELIABLE = "UNRELIABLE"


class ExtractedField(BaseModel):
    """Structured field extracted from a document with confidence and page provenance."""
    field: str
    value: Optional[Any] = None
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNRELIABLE
    page: Optional[int] = None
    source_text: Optional[str] = None


class ExtractedPageText(BaseModel):
    """Text extracted from a single document page."""
    page_number: int
    raw_text: str
    cleaned_text: str
    ocr_used: bool
    char_count: int


class DocumentMetadata(BaseModel):
    """File metadata and security integrity checksums."""
    file_name: str
    file_path: str
    file_size_bytes: int
    total_pages: int
    sha256_checksum: str
    mime_type: str


class DocumentAnalysisResult(BaseModel):
    """Final output of the Document AI pipeline for citizen-support documents.

    IMPORTANT: Document type classification is not document authenticity verification.
    """
    status: str = "success"
    apparent_document_type: DocumentType = DocumentType.UNKNOWN
    document_type_confidence: float = 0.0
    ocr_used: bool = False
    fields: Dict[str, ExtractedField] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    metadata: Optional[DocumentMetadata] = None
    disclaimer: str = (
        "Document type classification is not document authenticity verification. "
        "Extracted fields represent observable textual facts, not verified citizen credentials."
    )
