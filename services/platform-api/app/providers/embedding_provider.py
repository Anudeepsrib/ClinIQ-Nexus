"""
Embedding Provider Abstraction.

Local: sentence-transformers (all-MiniLM-L6-v2)
Production: Amazon Titan Text Embeddings v2 via Bedrock (same interface)
"""

from __future__ import annotations

from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore


class LocalEmbeddingProvider:
    """
    High-quality local embeddings for demo and development.
    384 dimensions (all-MiniLM-L6-v2).
    """

    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self._model = None
        self.dimension = 384

    @property
    def model(self):
        if self._model is None and SentenceTransformer is not None:
            # Lazy load to keep cold starts fast
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension
        if self.model is None:
            # Fallback deterministic vector if model not available
            return [(hash(text) % 1000) / 10000.0] * self.dimension
        vec = self.model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.model is None:
            return [self.embed(t) for t in texts]
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()


embedding_provider = LocalEmbeddingProvider()
