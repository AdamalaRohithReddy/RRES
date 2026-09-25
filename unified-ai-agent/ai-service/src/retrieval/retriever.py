"""Semantic Retrieval Engine for Government Scheme Knowledge Base."""
from typing import List, Optional, Dict, Any

from src.embeddings.base import BaseEmbedder
from src.vector_store.qdrant_store import QdrantVectorStore
from src.retrieval.models import RetrievalResult
from src.config.settings import get_settings


class InvalidQueryError(ValueError):
    """Raised when an empty or invalid query is provided."""
    pass


class SchemeRetriever:
    """Orchestrates query embedding, vector database search, and source provenance assembly."""

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: QdrantVectorStore,
        default_top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ):
        settings = get_settings()
        self.embedder = embedder
        self.vector_store = vector_store
        self.default_top_k = default_top_k or settings.default_top_k
        self.score_threshold = score_threshold if score_threshold is not None else settings.score_threshold

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_criteria: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """Perform semantic retrieval for a natural-language query.

        Args:
            query: The user query string.
            top_k: Maximum number of chunks to return.
            filter_criteria: Optional metadata filters (e.g. {"scheme_id": "APY"}).
            score_threshold: Minimum similarity score.

        Returns:
            List of RetrievalResult objects with similarity scores and full source provenance.
        """
        # Step 1: Input validation
        if not isinstance(query, str):
            raise InvalidQueryError(f"Query must be a string, got {type(query).__name__}.")

        cleaned_query = query.strip()
        if not cleaned_query:
            raise InvalidQueryError("Query cannot be empty or contain only whitespace.")

        limit = top_k if top_k is not None else self.default_top_k
        threshold = score_threshold if score_threshold is not None else self.score_threshold

        # Step 2: Generate dense query embedding
        query_vector = self.embedder.embed_text(cleaned_query)

        # Step 3: Query vector database
        raw_matches = self.vector_store.search(
            query_vector=query_vector,
            top_k=limit,
            score_threshold=threshold,
            filter_criteria=filter_criteria,
        )

        # Step 4: Map raw matches into structured provenance results
        results: List[RetrievalResult] = []
        for match in raw_matches:
            results.append(
                RetrievalResult(
                    score=match["score"],
                    text=match["text"],
                    chunk_id=match.get("chunk_id", ""),
                    document_id=match.get("document_id", ""),
                    scheme_id=match.get("scheme_id"),
                    scheme_name=match.get("scheme_name") or "Unknown Scheme",
                    page=match.get("page_start", 1),
                    page_start=match.get("page_start", 1),
                    page_end=match.get("page_end", 1),
                    section=match.get("section", "General"),
                    source_url=match.get("source_url"),
                    source_type=match.get("source_type", "official"),
                    last_verified=match.get("last_verified"),
                )
            )

        return results

    def retrieve_as_dict(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_criteria: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve results formatted as user-facing dictionaries."""
        results = self.retrieve(
            query=query,
            top_k=top_k,
            filter_criteria=filter_criteria,
            score_threshold=score_threshold,
        )
        return [r.to_provenance_dict() for r in results]
