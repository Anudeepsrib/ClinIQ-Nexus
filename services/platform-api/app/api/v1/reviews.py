from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.context import get_current_user, get_current_tenant
from app.core.exceptions import ForbiddenError

router = APIRouter()

# In-memory review store for the demo (production uses the DB + proper workflow engine)
REVIEW_QUEUE: List[dict] = []


class ReviewAction(BaseModel):
    notes: Optional[str] = None


@router.get("/")
async def list_reviews(user=Depends(get_current_user)):
    """Role-filtered human review queue."""
    tenant = get_current_tenant()
    visible = [r for r in REVIEW_QUEUE if r["tenant_id"] == tenant.tenant_id]
    
    # Clinicians and care coordinators see clinical reviews; compliance sees everything
    if user.role in {"compliance_officer", "admin"}:
        pass
    elif user.role in {"clinician", "nurse", "care_coordinator"}:
        visible = [r for r in visible if r.get("assigned_to_role") in {user.role, "clinician", "care_coordinator"}]
    else:
        visible = []  # patients and billing don't see the queue

    return {
        "reviews": visible,
        "count": len(visible),
        "message": "Human review queue. Approving a task releases the workflow."
    }


@router.post("/{review_id}/approve")
async def approve(review_id: str, action: ReviewAction, user=Depends(get_current_user)):
    for r in REVIEW_QUEUE:
        if r["id"] == review_id:
            if r["tenant_id"] != get_current_tenant().tenant_id:
                raise ForbiddenError("Cross-tenant access denied")
            r["status"] = "approved"
            r["resolved_by"] = user.user_id
            r["resolved_at"] = datetime.utcnow().isoformat()
            r["resolution_notes"] = action.notes or "Approved via UI"
            return {"status": "approved", "review": r}
    raise HTTPException(404, "Review task not found")


@router.post("/{review_id}/reject")
async def reject(review_id: str, action: ReviewAction, user=Depends(get_current_user)):
    for r in REVIEW_QUEUE:
        if r["id"] == review_id:
            if r["tenant_id"] != get_current_tenant().tenant_id:
                raise ForbiddenError("Cross-tenant access denied")
            r["status"] = "rejected"
            r["resolved_by"] = user.user_id
            r["resolution_notes"] = action.notes or "Rejected"
            return {"status": "rejected", "review": r}
    raise HTTPException(404, "Review task not found")


@router.post("/{review_id}/revise")
async def revise(review_id: str, action: ReviewAction, user=Depends(get_current_user)):
    for r in REVIEW_QUEUE:
        if r["id"] == review_id:
            if r["tenant_id"] != get_current_tenant().tenant_id:
                raise ForbiddenError("Cross-tenant access denied")
            r["status"] = "needs_revision"
            r["resolved_by"] = user.user_id
            r["resolution_notes"] = action.notes or "Needs revision"
            return {"status": "needs_revision", "review": r}
    raise HTTPException(404, "Review task not found")


# Internal helper used by agents/workflows
def create_review_task(
    task_type: str,
    patient_id: str,
    reason: str,
    assigned_to: str = "clinician",
    tenant_id: str = "tenant_hospital_a",
) -> dict:
    task = {
        "id": f"rev_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "task_type": task_type,
        "status": "pending_review",
        "patient_id": patient_id,
        "reason": reason,
        "assigned_to_role": assigned_to,
        "created_at": datetime.utcnow().isoformat(),
        "context_snapshot": {"source": "agent_workflow"},
    }
    REVIEW_QUEUE.append(task)
    return task
