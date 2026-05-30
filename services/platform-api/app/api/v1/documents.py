from fastapi import APIRouter, Depends, HTTPException
from app.core.context import get_current_user
from app.db.session import async_session
from app.models.document import Document
from sqlalchemy import select

router = APIRouter()


@router.post("/upload")
async def upload_document(user=Depends(get_current_user)):
    return {"message": "Upload endpoint ready. Full ingestion in Phase 2.", "status": "stub"}


@router.post("/{document_id}/ingest")
async def trigger_ingest(document_id: str, user=Depends(get_current_user)):
    return {"message": f"Ingestion triggered for {document_id} (stub)", "status": "accepted"}


@router.get("/{document_id}")
async def get_document(document_id: str, user=Depends(get_current_user)):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id, Document.tenant_id == user.tenant_id)
            )
            document = result.scalar_one_or_none()
            if not document:
                raise HTTPException(404, "Document not found")
            if document.patient_id and not user.can_access_patient(document.patient_id):
                raise HTTPException(403, "Not authorized for this document")
            return {
                "id": document.id,
                "patient_id": document.patient_id,
                "doc_type": document.doc_type,
                "title": document.title,
                "source_system": document.source_system,
                "sensitivity_level": document.sensitivity_level,
                "consent_scope": document.consent_scope,
            }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "Document store unavailable") from None
