"""Context Builder component for transforming retrieved chunks into structured LLM prompts."""
from typing import List, Optional
from pydantic import BaseModel, Field

from src.retrieval.models import RetrievalResult


class SourceReference(BaseModel):
    """Source reference metadata identifying where a piece of information originated."""
    scheme_name: str = Field(description="Name of the official scheme")
    document_id: str = Field(description="Unique document identifier")
    page: int = Field(description="Page number of the reference")
    section: str = Field(description="Logical section in the scheme document")
    source: str = Field(description="Source URL or official publication title")


class RAGContext(BaseModel):
    """Context bundle prepared for LLM prompt ingestion."""
    formatted_context: str = Field(description="Structured plain-text context for prompt injection")
    sources: List[SourceReference] = Field(default_factory=list, description="Extracted source references")
    total_chunks: int = Field(default=0, description="Total number of chunks bundled into context")


class ContextBuilder:
    """Converts a collection of RetrievalResult chunks into clean, labeled context blocks."""

    def build_context(self, retrieved_chunks: List[RetrievalResult]) -> RAGContext:
        """Transform retrieved chunks into formatted text and distinct source metadata.

        Preserves:
        - scheme name
        - document ID
        - section
        - page number
        - source URL / source label
        - similarity score
        - cleaned text
        """
        if not retrieved_chunks:
            return RAGContext(
                formatted_context="No relevant verified documents were found.",
                sources=[],
                total_chunks=0,
            )

        context_blocks: List[str] = []
        sources: List[SourceReference] = []
        seen_sources = set()

        for idx, chunk in enumerate(retrieved_chunks, start=1):
            source_label = chunk.source_url if chunk.source_url else "Official circular"

            block = (
                f"[Source {idx}]\n"
                f"Scheme Name: {chunk.scheme_name}\n"
                f"Document ID: {chunk.document_id}\n"
                f"Section: {chunk.section}\n"
                f"Page: {chunk.page} (Pages {chunk.page_start}-{chunk.page_end})\n"
                f"Source: {source_label}\n"
                f"Similarity Score: {chunk.score:.4f}\n"
                f"Verified Excerpt:\n{chunk.text.strip()}"
            )
            context_blocks.append(block)

            # Deduplicate source citations while preserving order
            source_key = (chunk.scheme_name, chunk.document_id, chunk.page, chunk.section, source_label)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append(
                    SourceReference(
                        scheme_name=chunk.scheme_name,
                        document_id=chunk.document_id,
                        page=chunk.page,
                        section=chunk.section,
                        source=source_label,
                    )
                )

        formatted_text = "\n\n" + ("\n\n" + "-" * 50 + "\n\n").join(context_blocks) + "\n\n"

        return RAGContext(
            formatted_context=formatted_text,
            sources=sources,
            total_chunks=len(retrieved_chunks),
        )
