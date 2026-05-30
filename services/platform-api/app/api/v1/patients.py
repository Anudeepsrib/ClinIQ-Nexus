"""Patient endpoints with proper ABAC."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.context import get_current_user, get_current_tenant
from app.core.exceptions import ForbiddenError

router = APIRouter()


@router.get("/")
async def list_patients(user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    # In real system this would query with ABAC filters
    if user.role == "patient":
        return [{"id": user.user_id, "name": user.full_name, "mrn": "MRN-001"}]
    # Demo data
    return [
        {"id": "pat_001", "name": "Maria Gonzalez", "mrn": "MRN-001", "tenant_id": tenant.tenant_id},
        {"id": "pat_002", "name": "Robert Thompson", "mrn": "MRN-002", "tenant_id": tenant.tenant_id},
    ]


@router.get("/{patient_id}")
async def get_patient(patient_id: str, user=Depends(get_current_user)):
    if not user.can_access_patient(patient_id):
        raise ForbiddenError("You do not have access to this patient's records")
    return {"id": patient_id, "name": "Demo Patient", "access_granted": True}


@router.get("/{patient_id}/summary")
async def get_patient_summary(patient_id: str, user=Depends(get_current_user)):
    if not user.can_access_patient(patient_id):
        raise ForbiddenError("You do not have access to this patient's records")
    return {
        "patient_id": patient_id,
        "summary": "Authorized patient summary endpoint. Use /ai/rag/query for grounded record-specific summaries.",
        "source_of_truth": "authorized_records",
    }


@router.get("/{patient_id}/timeline")
async def get_patient_timeline(patient_id: str, user=Depends(get_current_user)):
    if not user.can_access_patient(patient_id):
        raise ForbiddenError("You do not have access to this patient's records")
    return {
        "patient_id": patient_id,
        "events": [],
        "message": "Timeline endpoint ready for encounter/document-backed events.",
    }
