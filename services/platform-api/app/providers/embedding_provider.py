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

try:
    import boto3
except ImportError:
    boto3 = None

from app.core.config import settings
import json
import structlog

logger = structlog.get_logger(__name__)


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

class BedrockTitanEmbeddingProvider:
    """
    Amazon Titan Text Embeddings V2 using AWS Bedrock.
    Produces high-quality vectors for hybrid OpenSearch retrieval.
    """
    
    def __init__(self):
        if not boto3:
            raise ImportError("boto3 is required for BedrockTitanEmbeddingProvider")
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        self.model_id = "amazon.titan-embed-text-v2:0"
        self.dimension = 1024 # Titan v2 default dimension

    def embed(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension
            
        try:
            body = json.dumps({
                "inputText": text,
                "dimensions": self.dimension,
                "normalize": True
            })
            response = self.client.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )
            response_body = json.loads(response.get('body').read())
            return response_body.get('embedding', [])
        except Exception as e:
            logger.error("titan_embedding_failed", error=str(e))
            # Fallback to zeros to not break entire pipeline, but log heavily
            return [0.0] * self.dimension

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Titan doesn't natively support batch API in invoke_model, 
        # so we iterate. In production, consider batch inference jobs or concurrency.
        return [self.embed(t) for t in texts]


if settings.USE_REAL_AWS:
    embedding_provider = BedrockTitanEmbeddingProvider()
else:
    embedding_provider = LocalEmbeddingProvider()
