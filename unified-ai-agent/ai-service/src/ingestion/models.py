"""Data models for document ingestion and extraction."""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ExtractionStatus(str, Enum):
    """Status of PDF extraction."""
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    EMPTY_DOCUMENT = "EMPTY_DOCUMENT"
    SCANNED_OCR_REQUIRED = "SCANNED_OCR_REQUIRED"
    FAILED = "FAILED"


class PageExtraction(BaseModel):
    """Extraction details for a single page."""
    page_number: int = Field(description="1-based page number")
    raw_text: str = Field(default="", description="Raw extracted text from page")
    cleaned_text: str = Field(default="", description="Cleaned text from page")
    char_count: int = Field(default=0, description="Number of characters in raw text")
    image_count: int = Field(default=0, description="Number of images detected on this page")
    status: ExtractionStatus = Field(default=ExtractionStatus.SUCCESS)
    is_scanned_likely: bool = Field(default=False, description="Flag if page appears image-based/scanned")


class DocumentMetadata(BaseModel):
    """Metadata describing the document and its provenance."""
    document_id: str = Field(description="Unique identifier for the document")
    file_name: str = Field(description="Name of the PDF file")
    file_path: str = Field(description="Absolute or relative path to the PDF")
    total_pages: int = Field(description="Total pages in the PDF")
    checksum_sha256: str = Field(description="SHA256 checksum for deduplication")
    scheme_id: Optional[str] = Field(default=None, description="Official scheme identifier (e.g., APY, PMJJBY)")
    scheme_name: Optional[str] = Field(default=None, description="Official scheme name")
    source_url: Optional[str] = Field(default=None, description="Official source URL of the publication")
    source_type: str = Field(default="official", description="Source classification (official, circular, gazette)")
    last_verified: Optional[str] = Field(default=None, description="Date/timestamp when document was verified")
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    """Full extracted document representation."""
    document_id: str
    metadata: DocumentMetadata
    pages: List[PageExtraction] = Field(default_factory=list)
    extraction_status: ExtractionStatus
    ocr_required: bool = False
    ocr_recommendation: Optional[str] = None

    @property
    def full_cleaned_text(self) -> str:
        """Combine cleaned text of all pages separated by newlines."""
        return "\n\n".join(
            p.cleaned_text for p in self.pages if p.cleaned_text.strip()
        )
