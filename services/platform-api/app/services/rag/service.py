"""
RAG Retrieval Service (local pgvector implementation with real embeddings).

This is now a high-quality vector search with strict governance.
Production swaps to Amazon OpenSearch hybrid search with the same interface.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy import text
import json

from app.db.session import async_session
from app.core.context import UserContext
from app.core.config import settings
from app.providers.embedding_provider import embedding_provider
import structlog

try:
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth
    import boto3
except ImportError:
    OpenSearch = None

logger = structlog.get_logger(__name__)

def get_opensearch_client():
    if not OpenSearch or not boto3:
        raise ImportError("opensearch-py and boto3 are required")
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        settings.AWS_REGION,
        "es",
        session_token=credentials.token
    )
    
    # In production, parse OPENSEARCH_URL properly. 
    # For now, strip https://
    host = settings.OPENSEARCH_URL.replace("https://", "").replace("http://", "")
    
    return OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )


async def retrieve_authorized_chunks(
    query: str,
    user: UserContext,
    patient_id: Optional[str] = None,
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """
    Real vector similarity search + strict ABAC/tenant/patient filtering.
    """
    # Generate query embedding
    query_embedding = embedding_provider.embed(query)

    if settings.USE_REAL_AWS:
        # ---------------------------------------------------------
        # REAL OPENSEARCH HYBRID RETRIEVAL
        # ---------------------------------------------------------
        try:
            client = get_opensearch_client()
            
            # Construct strict ABAC filter
            filter_clauses = [
                {"term": {"tenant_id.keyword": user.tenant_id}}
            ]
            
            if patient_id and user.can_access_patient(patient_id):
                filter_clauses.append({"term": {"patient_id.keyword": patient_id}})
            elif user.role == "patient":
                filter_clauses.append({"term": {"patient_id.keyword": user.user_id}})
                
            # Hybrid search query: Vector k-NN + Keyword BM25 + Filters
            search_body = {
                "size": top_k,
                "query": {
                    "hybrid": {
                        "queries": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_embedding,
                                        "k": top_k
                                    }
                                }
                            },
                            {
                                "match": {
                                    "content": query
                                }
                            }
                        ]
                    }
                },
                "post_filter": {
                    "bool": {
                        "must": filter_clauses
                    }
                }
            }
            
            response = client.search(
                body=search_body,
                index="document-chunks-v1"
            )
            
            chunks = []
            for hit in response["hits"]["hits"]:
                src = hit["_source"]
                chunks.append({
                    "chunk_id": hit["_id"],
                    "document_id": src.get("document_id"),
                    "patient_id": src.get("patient_id"),
                    "content": src.get("content", ""),
                    "doc_type": src.get("doc_type", "unknown"),
                    "sensitivity_level": src.get("sensitivity_level", "high"),
                    "consent_scope": src.get("consent_scope", "treatment"),
                    "relevance": round(hit["_score"] or 0.75, 4),
                    "tenant_id": src.get("tenant_id", user.tenant_id),
                })
            return chunks
            
        except Exception as e:
            logger.error("opensearch_retrieval_failed", error=str(e))
            # Fall back to empty list on failure in prod rather than exposing data incorrectly
            return []

    # ---------------------------------------------------------
    # LOCAL PGVECTOR RETRIEVAL (MOCK/DEV MODE)
    # ---------------------------------------------------------
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    async with async_session() as session:
        params: Dict[str, Any] = {
            "tenant_id": user.tenant_id,
            "top_k": top_k,
            "query_emb": embedding_str,
        }

        where_clauses = ["tenant_id = :tenant_id"]

        if patient_id and user.can_access_patient(patient_id):
            where_clauses.append("patient_id = :patient_id")
            params["patient_id"] = patient_id
        elif user.role == "patient":
            where_clauses.append("patient_id = :patient_id")
            params["patient_id"] = user.user_id

        # Real cosine similarity using pgvector
        sql = f"""
            SELECT 
                id, 
                document_id, 
                patient_id, 
                chunk_index, 
                content, 
                doc_type, 
                sensitivity_level, 
                consent_scope, 
                metadata_json,
                1 - (embedding <=> :query_emb::vector) as relevance
            FROM document_chunks
            WHERE {" AND ".join(where_clauses)}
              AND embedding IS NOT NULL
            ORDER BY relevance DESC
            LIMIT :top_k
        """

        result = await session.execute(text(sql), params)
        rows = result.mappings().all()

        chunks = []
        for r in rows:
            chunks.append({
                "chunk_id": str(r["id"]),
                "document_id": str(r["document_id"]),
                "patient_id": str(r["patient_id"]) if r["patient_id"] else None,
                "content": r["content"],
                "doc_type": r["doc_type"],
                "sensitivity_level": r["sensitivity_level"],
                "consent_scope": r["consent_scope"],
                "relevance": round(float(r["relevance"]), 4) if r["relevance"] else 0.75,
                "tenant_id": user.tenant_id,
            })
        return chunks
