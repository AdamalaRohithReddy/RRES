"""Unit tests for Embeddings module."""
import pytest
from src.embeddings.sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
    EmbeddingError,
    get_embedder,
)


def test_embedder_initialization():
    embedder = get_embedder("all-MiniLM-L6-v2", device="cpu")
    assert embedder.dimension == 384
    assert embedder.model_name == "all-MiniLM-L6-v2"


def test_embed_single_text():
    embedder = get_embedder("all-MiniLM-L6-v2", device="cpu")
    text = "Atal Pension Yojana eligibility criteria"
    vec = embedder.embed_text(text)
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(v, float) for v in vec)


def test_embed_batch():
    embedder = get_embedder("all-MiniLM-L6-v2", device="cpu")
    texts = [
        "Government scheme benefits",
        "Required documents for Aadhaar verification",
        "Age criteria 18 to 40 years",
    ]
    vectors = embedder.embed_batch(texts)
    assert len(vectors) == 3
    for v in vectors:
        assert len(v) == 384


def test_embed_empty_text_raises_value_error():
    embedder = get_embedder("all-MiniLM-L6-v2", device="cpu")
    with pytest.raises(ValueError):
        embedder.embed_text("")
    with pytest.raises(ValueError):
        embedder.embed_text("   ")


def test_invalid_model_raises_embedding_error():
    with pytest.raises(EmbeddingError):
        SentenceTransformerEmbedder(model_name="non_existent_invalid_model_12345")
