"""Base Embedder Abstract Interface."""
from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """Abstract interface for text embedding models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name or identifier of the embedding model."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single string.

        Args:
            text: Input string.

        Returns:
            List of floats representing the dense embedding vector.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embedding vectors for a list of strings.

        Args:
            texts: List of input strings.
            batch_size: Processing batch size.

        Returns:
            List of embedding vectors.
        """
        pass
