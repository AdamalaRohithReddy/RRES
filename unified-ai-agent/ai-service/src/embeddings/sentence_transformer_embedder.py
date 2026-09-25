"""Sentence Transformers Embedding Implementation."""
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from src.embeddings.base import BaseEmbedder
from src.config.settings import get_settings


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


class SentenceTransformerEmbedder(BaseEmbedder):
    """Embedder using the HuggingFace Sentence Transformers library."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        settings = get_settings()
        self._model_name = model_name or settings.embedding_model_name
        self._device = device or settings.embedding_device

        try:
            # Load the sentence transformer model
            self._model = SentenceTransformer(self._model_name, device=self._device)
            # Retrieve dynamic dimension from the model architecture
            if hasattr(self._model, "get_embedding_dimension"):
                self._dimension = int(self._model.get_embedding_dimension())
            else:
                self._dimension = int(self._model.get_sentence_embedding_dimension())
        except Exception as e:
            raise EmbeddingError(
                f"Failed to load SentenceTransformer model '{self._model_name}' on device '{self._device}': {e}"
            ) from e

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty or whitespace-only text.")

        try:
            vector = self._model.encode(
                text.strip(),
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return vector.tolist()
        except Exception as e:
            raise EmbeddingError(f"Error generating embedding for text: {e}") from e

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed a batch of text strings."""
        if not texts:
            return []

        cleaned_texts = [t.strip() if t and t.strip() else " " for t in texts]

        try:
            vectors = self._model.encode(
                cleaned_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return vectors.tolist()
        except Exception as e:
            raise EmbeddingError(f"Error generating batch embeddings: {e}") from e


def get_embedder(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
) -> BaseEmbedder:
    """Factory function to instantiate the configured embedder."""
    return SentenceTransformerEmbedder(model_name=model_name, device=device)
