import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from src.chunking.models import DocumentChunk
from src.config.settings import get_settings


_client_cache: Dict[str, QdrantClient] = {}


def clear_qdrant_client_cache() -> None:
    """Clear cached QdrantClient instances."""
    _client_cache.clear()


class QdrantStoreError(Exception):
    """Base exception for Qdrant vector store operations."""
    pass


class QdrantUnavailableError(QdrantStoreError):
    """Raised when the Qdrant instance is unreachable."""
    pass


class CollectionNotFoundError(QdrantStoreError):
    """Raised when querying a collection that has not been initialized."""
    pass


class QdrantVectorStore:
    """Manages Qdrant vector database interactions including storage and similarity search."""

    def __init__(
        self,
        collection_name: Optional[str] = None,
        path: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        settings = get_settings()
        self.collection_name = collection_name or settings.qdrant_collection_name
        self.dimension = dimension or settings.embedding_dimension
        self.url = url if url is not None else settings.qdrant_url
        self.api_key = api_key if api_key is not None else settings.qdrant_api_key
        self.path = path if path is not None else settings.qdrant_path

        try:
            if self.url:
                self.client = QdrantClient(url=self.url, api_key=self.api_key)
            elif self.path == ":memory:":
                self.client = QdrantClient(location=":memory:")
            else:
                norm_path = os.path.abspath(str(self.path))
                if norm_path not in _client_cache:
                    _client_cache[norm_path] = QdrantClient(path=str(self.path))
                self.client = _client_cache[norm_path]
        except Exception as e:
            target = self.url or self.path
            raise QdrantUnavailableError(
                f"Failed to connect to Qdrant at '{target}'. "
                f"Please verify connection settings or use ':memory:' for local testing: {e}"
            ) from e

    def health_check(self) -> bool:
        """Verify that the Qdrant client can communicate with the storage backend."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            raise QdrantUnavailableError(f"Qdrant health check failed: {e}") from e

    def initialize_collection(self, recreate: bool = False) -> None:
        """Create or initialize the collection with proper vector dimension and cosine metric."""
        try:
            collections_response = self.client.get_collections()
            existing_names = [col.name for col in collections_response.collections]

            if self.collection_name in existing_names:
                if recreate:
                    self.client.delete_collection(collection_name=self.collection_name)
                else:
                    return

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )
        except Exception as e:
            raise QdrantStoreError(
                f"Failed to initialize collection '{self.collection_name}': {e}"
            ) from e

    def collection_exists(self) -> bool:
        """Check whether the configured collection exists."""
        try:
            collections_response = self.client.get_collections()
            existing_names = [col.name for col in collections_response.collections]
            return self.collection_name in existing_names
        except Exception as e:
            raise QdrantUnavailableError(f"Error checking collections in Qdrant: {e}") from e

    @staticmethod
    def _chunk_id_to_uuid(chunk_id: str) -> str:
        """Derive a deterministic UUID5 from a chunk string ID for Qdrant compatibility."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    def upsert_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        """Store or update chunks along with their vector embeddings and metadata.

        Args:
            chunks: List of DocumentChunk instances.
            embeddings: Corresponding embedding vectors.

        Returns:
            Number of points successfully upserted.
        """
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Count mismatch between chunks ({len(chunks)}) and embeddings ({len(embeddings)})."
            )

        if not self.collection_exists():
            self.initialize_collection()

        points: List[PointStruct] = []
        for chunk, vector in zip(chunks, embeddings):
            if len(vector) != self.dimension:
                raise ValueError(
                    f"Vector dimension ({len(vector)}) does not match store dimension ({self.dimension})."
                )

            point_id = self._chunk_id_to_uuid(chunk.chunk_id)
            payload = chunk.to_qdrant_payload()

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )
            return len(points)
        except Exception as e:
            raise QdrantStoreError(f"Failed to upsert chunks into Qdrant: {e}") from e

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic similarity search on Qdrant.

        Args:
            query_vector: Dense embedding vector of the search query.
            top_k: Maximum number of points to retrieve.
            score_threshold: Optional minimum cosine similarity score.
            filter_criteria: Optional key-value pairs to filter payload metadata (e.g. {"scheme_id": "APY"}).

        Returns:
            List of matching records containing score, chunk text, and complete provenance metadata.
        """
        if not self.collection_exists():
            raise CollectionNotFoundError(
                f"Collection '{self.collection_name}' does not exist. Ingest documents before querying."
            )

        if len(query_vector) != self.dimension:
            raise ValueError(
                f"Query vector dimension ({len(query_vector)}) does not match collection dimension ({self.dimension})."
            )

        # Build Qdrant filter condition if filter_criteria provided
        query_filter = None
        if filter_criteria:
            conditions = []
            for key, val in filter_criteria.items():
                if val is not None:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=val))
                    )
            if conditions:
                query_filter = Filter(must=conditions)

        try:
            search_response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
            )

            results: List[Dict[str, Any]] = []
            for point in search_response.points:
                payload = point.payload or {}
                results.append({
                    "score": round(float(point.score), 4),
                    "chunk_id": payload.get("chunk_id"),
                    "document_id": payload.get("document_id"),
                    "scheme_id": payload.get("scheme_id"),
                    "scheme_name": payload.get("scheme_name"),
                    "text": payload.get("text", ""),
                    "page_start": payload.get("page_start"),
                    "page_end": payload.get("page_end"),
                    "section": payload.get("section", "General"),
                    "source_type": payload.get("source_type", "official"),
                    "source_url": payload.get("source_url"),
                    "last_verified": payload.get("last_verified"),
                })
            return results
        except Exception as e:
            raise QdrantStoreError(f"Failed to execute vector search in Qdrant: {e}") from e

    def count(self) -> int:
        """Count total vectors in collection."""
        if not self.collection_exists():
            return 0
        try:
            return self.client.count(collection_name=self.collection_name).count
        except Exception as e:
            raise QdrantStoreError(f"Failed to count points in Qdrant: {e}") from e
