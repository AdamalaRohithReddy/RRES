"""Data models for retrieval results."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    """Result returned by the semantic retriever with full source provenance."""
    score: float = Field(description="Cosine similarity score (0.0 to 1.0)")
    text: str = Field(description="Cleaned text of the retrieved chunk")
    chunk_id: str = Field(description="Unique ID of the chunk")
    document_id: str = Field(description="Source document ID")
    scheme_id: Optional[str] = Field(default=None, description="Official scheme ID")
    scheme_name: str = Field(default="Unknown Scheme", description="Official scheme name")
    page: int = Field(description="Starting page number of the source chunk")
    page_start: int = Field(description="Start page number")
    page_end: int = Field(description="End page number")
    section: str = Field(default="General", description="Logical section (e.g. Eligibility, Benefits)")
    source_url: Optional[str] = Field(default=None, description="Official source URL")
    source_type: str = Field(default="official", description="Source classification")
    last_verified: Optional[str] = Field(default=None, description="Verification date")

    def to_provenance_dict(self) -> Dict[str, Any]:
        """Format as standard user-facing provenance structure."""
        return {
            "score": self.score,
            "text": self.text,
            "scheme_name": self.scheme_name,
            "page": self.page,
            "section": self.section,
            "source_url": self.source_url,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
        }
