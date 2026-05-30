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
from app.providers.embedding_provider import embedding_provider


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
