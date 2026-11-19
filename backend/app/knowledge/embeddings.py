"""Embedding providers for the Knowledge Grid."""
from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        ...

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic 384-dim vectors for testing without a real model.
    Same text always gives the same vector.
    """

    _dimension: int = 384

    @property
    def dimension(self) -> int:
        return self._dimension

    def _text_to_vector(self, text: str) -> List[float]:
        import numpy as np

        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        rng = np.random.RandomState(seed)
        v = rng.randn(self._dimension).astype(float)
        norm = np.linalg.norm(v)
        if norm == 0:
            norm = 1.0
        return (v / norm).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._text_to_vector(query)


class SentenceTransformerProvider(EmbeddingProvider):
    """
    Wraps sentence-transformers. Falls back to MockEmbeddingProvider
    if the library is not installed.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._fallback: MockEmbeddingProvider | None = None
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            self._dimension = self.model.get_sentence_embedding_dimension()
            logger.info("SentenceTransformer loaded: %s (dim=%d)", model_name, self._dimension)
        except ImportError:
            logger.warning(
                "sentence-transformers not installed — falling back to MockEmbeddingProvider"
            )
            self._fallback = MockEmbeddingProvider()
            self.model = None
            self._dimension = self._fallback.dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._fallback:
            return self._fallback.embed_documents(texts)
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [e.tolist() for e in embeddings]

    def embed_query(self, query: str) -> List[float]:
        if self._fallback:
            return self._fallback.embed_query(query)
        embedding = self.model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        return embedding[0].tolist()


def get_embedding_provider(provider: str = "mock", model_name: str | None = None) -> EmbeddingProvider:
    """Factory: return the right provider based on config string."""
    if provider == "sentence_transformers":
        return SentenceTransformerProvider(model_name or "all-MiniLM-L6-v2")
    return MockEmbeddingProvider()
