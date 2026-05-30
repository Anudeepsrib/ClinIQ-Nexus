"""
Document tools for Deep Agents — now wired to real governed data.
"""

from __future__ import annotations

from typing import Any, Dict
import asyncio
import sys
from pathlib import Path
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from ..base_deep_agent import DeepAgentContext

# Bridge to platform DB models
PLATFORM_ROOT = Path(__file__).resolve().parents[4] / "platform-api"
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

try:
    from app.models.document import Document
    from app.db.session import async_session
    from sqlalchemy import select
    REAL_DB_AVAILABLE = True
except Exception:
    REAL_DB_AVAILABLE = False
    Document = None
    async_session = None


class GetDocumentMetadataInput(BaseModel):
    document_id: str = Field(..., description="Governed document ID")


class GetDocumentMetadataTool(BaseTool):
    name: str = "get_document_metadata"
    description: str = "Fetch metadata for a specific authorized document (title, type, author, date). Never returns clinical content."
    args_schema: type[BaseModel] = GetDocumentMetadataInput
    _context: DeepAgentContext = PrivateAttr()

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self._context = context

    @property
    def context(self) -> DeepAgentContext:
        return self._context

    async def _arun(self, document_id: str, **kwargs: Any) -> Dict[str, Any]:
        if not REAL_DB_AVAILABLE or not Document:
            return {"error": "Database access not available", "document_id": document_id}

        async with async_session() as session:
            stmt = select(Document).where(
                Document.id == document_id,
                Document.tenant_id == self.context.tenant_id
            )
            if self.context.patient_id:
                stmt = stmt.where(Document.patient_id == self.context.patient_id)

            result = await session.execute(stmt)
            doc = result.scalar_one_or_none()

            if not doc:
                return {"error": "Document not found or not authorized", "document_id": document_id}

            return {
                "document_id": str(doc.id),
                "doc_type": doc.doc_type,
                "title": doc.title,
                "source_system": doc.source_system,
                "sensitivity_level": doc.sensitivity_level,
                "created_at": str(doc.created_at) if doc.created_at else None,
            }

    def _run(self, document_id: str, **kwargs: Any) -> Dict[str, Any]:
        return asyncio.run(self._arun(document_id))
