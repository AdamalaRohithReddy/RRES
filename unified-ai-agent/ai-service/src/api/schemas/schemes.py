"""Scheme search and discovery schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field


class SchemeSearchRequest(BaseModel):
    """Semantic scheme search request."""
    query: str = Field(..., min_length=1, description="Citizen inquiry or scheme keywords")
    top_k: int = Field(default=3, ge=1, le=10, description="Max clauses to retrieve")
    score_threshold: Optional[float] = Field(default=None, description="Minimum similarity threshold")


class SchemeSearchResultItem(BaseModel):
    """Retrieved scheme clause."""
    scheme: str
    section: str
    page: int
    score: float
    content: str
    source: str


class SchemeSearchResponse(BaseModel):
    """Results of semantic RAG search."""
    query: str
    total_results: int
    results: List[SchemeSearchResultItem] = Field(default_factory=list)


class SchemeDiscoveryRequest(BaseModel):
    """External government scheme discovery request."""
    keyword: Optional[str] = Field(None, description="Search keyword")
    state: Optional[str] = Field(None, description="State filter")
    category: Optional[str] = Field(None, description="Beneficiary category")


class SchemeDiscoveryItem(BaseModel):
    """Government scheme discovery item."""
    scheme_id: str
    scheme_name: str
    ministry: Optional[str] = None
    category: Optional[str] = None
    state: Optional[str] = None
    target_beneficiaries: List[str] = Field(default_factory=list)
    brief_description: str = ""
    application_url: Optional[str] = None
    verification_status: str
    data_source: str


class SchemeDiscoveryResponse(BaseModel):
    """Government directory discovery response."""
    total_schemes: int
    data_freshness: str
    verification_status: str
    data_source: str
    schemes: List[SchemeDiscoveryItem] = Field(default_factory=list)
    notice: Optional[str] = None
