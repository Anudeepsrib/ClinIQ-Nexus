from fastapi import APIRouter, Depends
from app.core.context import get_current_user

router = APIRouter()


@router.post("/upload")
async def upload_document(user=Depends(get_current_user)):
    return {"message": "Upload endpoint ready. Full ingestion in Phase 2.", "status": "stub"}


@router.post("/{document_id}/ingest")
async def trigger_ingest(document_id: str, user=Depends(get_current_user)):
    return {"message": f"Ingestion triggered for {document_id} (stub)", "status": "accepted"}
