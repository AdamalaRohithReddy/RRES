"""Unit tests for Qdrant Vector Store."""
import pytest
from src.chunking.models import DocumentChunk
from src.vector_store.qdrant_store import (
    QdrantVectorStore,
    CollectionNotFoundError,
)


@pytest.fixture
def mock_chunks():
    chunk1 = DocumentChunk(
        chunk_id="doc1_c01",
        document_id="doc1",
        scheme_id="APY",
        scheme_name="Atal Pension Yojana",
        text="Citizens between 18 and 40 years can enroll in APY.",
        page_start=1,
        page_end=1,
        section="Eligibility",
        source_type="official",
        source_url="https://gov.in/apy",
        last_verified="2026-01-01",
    )
    chunk2 = DocumentChunk(
        chunk_id="doc1_c02",
        document_id="doc1",
        scheme_id="APY",
        scheme_name="Atal Pension Yojana",
        text="Subscribers receive monthly pension of Rs 1,000 to Rs 5,000.",
        page_start=2,
        page_end=2,
        section="Benefits",
        source_type="official",
        source_url="https://gov.in/apy",
        last_verified="2026-01-01",
    )
    chunk3 = DocumentChunk(
        chunk_id="doc2_c01",
        document_id="doc2",
        scheme_id="PMJJBY",
        scheme_name="PM Jeevan Jyoti Bima Yojana",
        text="Life insurance cover of Rs 2 lakh for death due to any cause.",
        page_start=1,
        page_end=1,
        section="Benefits",
        source_type="official",
        source_url="https://gov.in/pmjjby",
        last_verified="2026-01-01",
    )
    return [chunk1, chunk2, chunk3]


def test_qdrant_in_memory_initialization_and_health():
    store = QdrantVectorStore(collection_name="test_col", path=":memory:", dimension=4)
    assert store.health_check() is True
    assert not store.collection_exists()

    store.initialize_collection()
    assert store.collection_exists()
    assert store.count() == 0


def test_upsert_and_count(mock_chunks):
    store = QdrantVectorStore(collection_name="test_upsert", path=":memory:", dimension=3)
    vectors = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    count = store.upsert_chunks(mock_chunks, vectors)
    assert count == 3
    assert store.count() == 3


def test_search_and_provenance(mock_chunks):
    store = QdrantVectorStore(collection_name="test_search", path=":memory:", dimension=3)
    vectors = [
        [1.0, 0.0, 0.0],  # chunk1: Eligibility
        [0.0, 1.0, 0.0],  # chunk2: Benefits
        [0.0, 0.0, 1.0],  # chunk3: PMJJBY
    ]
    store.upsert_chunks(mock_chunks, vectors)

    # Search for vector close to chunk1
    results = store.search(query_vector=[0.9, 0.1, 0.0], top_k=1)
    assert len(results) == 1
    top = results[0]
    assert top["chunk_id"] == "doc1_c01"
    assert top["scheme_name"] == "Atal Pension Yojana"
    assert top["section"] == "Eligibility"
    assert top["page_start"] == 1
    assert top["source_url"] == "https://gov.in/apy"
    assert top["score"] > 0.8


def test_metadata_filtering(mock_chunks):
    store = QdrantVectorStore(collection_name="test_filter", path=":memory:", dimension=3)
    vectors = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    store.upsert_chunks(mock_chunks, vectors)

    # Filter by scheme_id="PMJJBY"
    results = store.search(
        query_vector=[0.5, 0.5, 0.5],
        top_k=5,
        filter_criteria={"scheme_id": "PMJJBY"},
    )
    assert len(results) == 1
    assert results[0]["scheme_id"] == "PMJJBY"
    assert results[0]["scheme_name"] == "PM Jeevan Jyoti Bima Yojana"


def test_search_non_existent_collection():
    store = QdrantVectorStore(collection_name="does_not_exist", path=":memory:", dimension=3)
    with pytest.raises(CollectionNotFoundError):
        store.search([1.0, 0.0, 0.0])


def test_dimension_mismatch_raises_error(mock_chunks):
    store = QdrantVectorStore(collection_name="test_dim", path=":memory:", dimension=4)
    # Vectors have length 3 instead of 4
    vectors = [[1.0, 0.0, 0.0]]
    with pytest.raises(ValueError):
        store.upsert_chunks([mock_chunks[0]], vectors)
