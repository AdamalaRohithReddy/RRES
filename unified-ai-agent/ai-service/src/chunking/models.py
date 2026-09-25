"""Data models for document chunks and chunking metadata."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents a chunk of a scheme document with comprehensive source provenance."""
    chunk_id: str = Field(description="Unique identifier for the chunk")
    document_id: str = Field(description="ID of the parent document")
    scheme_id: Optional[str] = Field(default=None, description="Official scheme ID (e.g. APY)")
    scheme_name: Optional[str] = Field(default=None, description="Official scheme name")
    text: str = Field(description="Cleaned text content of the chunk")
    page_start: int = Field(description="1-based starting page number")
    page_end: int = Field(description="1-based ending page number")
    section: str = Field(default="General", description="Logical section (e.g. Eligibility, Benefits)")
    source_type: str = Field(default="official", description="Source classification")
    source_url: Optional[str] = Field(default=None, description="Official source URL")
    last_verified: Optional[str] = Field(default=None, description="Date verified")

    def to_qdrant_payload(self) -> Dict[str, Any]:
        """Convert chunk into a JSON-serializable dictionary for Qdrant payload."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "text": self.text,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "section": self.section,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "last_verified": self.last_verified,
        }
