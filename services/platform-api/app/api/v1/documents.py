from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.core.context import get_current_user
from app.core.config import settings
from app.db.session import async_session
from app.models.document import Document
from sqlalchemy import select
import uuid
import structlog
import time

try:
    import boto3
except ImportError:
    boto3 = None

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    patient_id: str = Form(None),
    doc_type: str = Form("clinical_note"),
    sensitivity_level: str = Form("normal"),
    consent_scope: str = Form("treatment"),
    user=Depends(get_current_user)
):
    """
    Uploads a document to S3 (landing bucket) and creates an initial DB record.
    """
    if not file.filename.endswith((".txt", ".pdf", ".json")):
        raise HTTPException(400, "Unsupported file format. Only txt, pdf, json allowed.")
        
    document_id = str(uuid.uuid4())
    s3_key = f"tenant={user.tenant_id}/patient={patient_id or 'none'}/{document_id}_{file.filename}"
    
    # 1. Malware Scan Hook (Conceptual)
    # In production, files upload to a quarantine bucket first, trigger EventBridge/Lambda
    # ClamAV scan, and move to the clean bucket. We simulate that hook here.
    logger.info("malware_scan_triggered", document_id=document_id)
    
    if settings.USE_REAL_AWS:
        if not boto3:
            raise HTTPException(500, "boto3 not installed")
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        try:
            s3.upload_fileobj(
                file.file,
                settings.S3_BUCKET_NAME,
                s3_key,
                ExtraArgs={
                    "ServerSideEncryption": "AES256",
                    "Metadata": {
                        "tenant_id": user.tenant_id,
                        "patient_id": patient_id or "",
                        "doc_type": doc_type
                    }
                }
            )
        except Exception as e:
            logger.error("s3_upload_failed", error=str(e))
            raise HTTPException(500, "Failed to upload to S3")
    else:
        logger.info("local_upload_mock", s3_key=s3_key)

    # 2. RDS Metadata Persistence
    try:
        async with async_session() as session:
            new_doc = Document(
                id=document_id,
                tenant_id=user.tenant_id,
                patient_id=patient_id,
                doc_type=doc_type,
                title=file.filename,
                source_system="manual_upload",
                sensitivity_level=sensitivity_level,
                consent_scope=consent_scope,
                s3_key=s3_key
            )
            session.add(new_doc)
            await session.commit()
    except Exception as e:
        logger.error("db_insert_failed", error=str(e))
        raise HTTPException(500, "Failed to record document metadata")

    return {
        "message": "Upload successful", 
        "document_id": document_id, 
        "status": "uploaded"
    }


@router.post("/{document_id}/ingest")
async def trigger_ingest(document_id: str, user=Depends(get_current_user)):
    """
    Triggers asynchronous extraction, chunking, titan embedding, and OpenSearch indexing.
    In a full production system, this is usually driven by S3 event notifications (EventBridge -> SQS -> Worker).
    """
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id, Document.tenant_id == user.tenant_id)
            )
            document = result.scalar_one_or_none()
            if not document:
                raise HTTPException(404, "Document not found")
                
            # document.status = "processing" # Removed because status is not in the schema yet
            await session.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ingest_trigger_failed", error=str(e))
        raise HTTPException(500, "Failed to trigger ingestion")
        
    # Send message to SQS or ingestion worker queue here...
    logger.info("ingestion_queued", document_id=document_id)
    
    return {"message": f"Ingestion triggered for {document_id}", "status": "processing"}


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
