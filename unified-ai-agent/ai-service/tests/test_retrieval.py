"""Unit tests for SchemeRetriever."""
import pytest
from typing import List

from src.embeddings.base import BaseEmbedder
from src.chunking.models import DocumentChunk
from src.vector_store.qdrant_store import QdrantVectorStore
from src.retrieval.retriever import SchemeRetriever, InvalidQueryError


class MockEmbedder(BaseEmbedder):
    """Deterministic mock embedder for fast unit testing."""

    @property
    def model_name(self) -> str:
        return "mock-embedder"

    @property
    def dimension(self) -> int:
        return 3

    def embed_text(self, text: str) -> List[float]:
        t = text.lower()
        if "eligib" in t or "criteria" in t or "18 to 40" in t:
            return [1.0, 0.0, 0.0]
        elif "guaranteed" in t or "monthly pension" in t or "benefits" in t:
            return [0.0, 1.0, 0.0]
        elif "aadhaar" in t or "mandatory kyc" in t or "documents" in t:
            return [0.0, 0.0, 1.0]
        return [0.33, 0.33, 0.33]

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


@pytest.fixture
def retriever_setup():
    embedder = MockEmbedder()
    store = QdrantVectorStore(collection_name="test_retrieval", path=":memory:", dimension=3)
    store.initialize_collection()

    chunks = [
        DocumentChunk(
            chunk_id="chunk_elig_01",
            document_id="doc_apy",
            scheme_id="APY",
            scheme_name="Atal Pension Yojana",
            text="Citizens aged 18 to 40 years are eligible for Atal Pension Yojana.",
            page_start=1,
            page_end=1,
            section="Eligibility",
            source_type="official",
            source_url="https://gov.in/apy",
            last_verified="2026-01-01",
        ),
        DocumentChunk(
            chunk_id="chunk_ben_01",
            document_id="doc_apy",
            scheme_id="APY",
            scheme_name="Atal Pension Yojana",
            text="Subscribers receive guaranteed pension of Rs 1,000 to Rs 5,000 monthly at age 60.",
            page_start=2,
            page_end=2,
            section="Benefits",
            source_type="official",
            source_url="https://gov.in/apy",
            last_verified="2026-01-01",
        ),
        DocumentChunk(
            chunk_id="chunk_doc_01",
            document_id="doc_apy",
            scheme_id="APY",
            scheme_name="Atal Pension Yojana",
            text="Aadhaar card and bank account details are mandatory KYC documents.",
            page_start=3,
            page_end=3,
            section="Required Documents",
            source_type="official",
            source_url="https://gov.in/apy",
            last_verified="2026-01-01",
        ),
    ]

    vectors = [embedder.embed_text(c.text) for c in chunks]
    store.upsert_chunks(chunks, vectors)

    retriever = SchemeRetriever(embedder=embedder, vector_store=store, default_top_k=2)
    return retriever


def test_empty_or_whitespace_query_raises_error(retriever_setup):
    retriever = retriever_setup
    with pytest.raises(InvalidQueryError):
        retriever.retrieve("")

    with pytest.raises(InvalidQueryError):
        retriever.retrieve("   \n\t  ")

    with pytest.raises(InvalidQueryError):
        retriever.retrieve(None)  # type: ignore


def test_semantic_retrieval_matches_expected_chunk(retriever_setup):
    retriever = retriever_setup
    results = retriever.retrieve("What are the eligibility criteria and age requirements?", top_k=1)
    assert len(results) == 1
    top = results[0]

    assert top.section == "Eligibility"
    assert top.scheme_name == "Atal Pension Yojana"
    assert top.page == 1
    assert "18 to 40 years" in top.text
    assert top.source_url == "https://gov.in/apy"
    assert top.score > 0.9


def test_retrieval_as_dict_provenance_format(retriever_setup):
    retriever = retriever_setup
    results = retriever.retrieve_as_dict("What benefits or pension amount do I get?", top_k=1)
    assert len(results) == 1
    top = results[0]

    # Verify all expected provenance keys are present
    assert "score" in top
    assert "text" in top
    assert "scheme_name" in top
    assert "page" in top
    assert "section" in top
    assert "source_url" in top
    assert top["section"] == "Benefits"
    assert top["page"] == 2
