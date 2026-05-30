from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy import select, update

from app.core.context import get_current_user, get_current_tenant
from app.core.exceptions import ForbiddenError
from app.db.session import async_session
from app.models.workflow import HumanReviewTask

router = APIRouter()


class ReviewAction(BaseModel):
    notes: Optional[str] = None


@router.get("/")
async def list_reviews(user=Depends(get_current_user)):
    """Role-filtered human review queue from DB."""
    tenant = get_current_tenant()
    
    async with async_session() as session:
        query = select(HumanReviewTask).where(
            HumanReviewTask.tenant_id == tenant.tenant_id,
            HumanReviewTask.status == "pending_review"
        )
        
        # Clinicians and care coordinators see clinical reviews; compliance sees everything
        if user.role in {"compliance_officer", "admin"}:
            pass # No additional role filter
        elif user.role in {"clinician", "nurse", "care_coordinator"}:
            query = query.where(HumanReviewTask.assigned_to_role.in_([user.role, "clinician", "care_coordinator"]))
        else:
            return {"reviews": [], "count": 0, "message": "No reviews visible"}
            
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        visible = []
        for t in tasks:
            visible.append({
                "id": t.id,
                "tenant_id": t.tenant_id,
                "task_type": t.task_type,
                "status": t.status,
                "patient_id": t.patient_id,
                "reason": t.reason,
                "assigned_to_role": t.assigned_to_role,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "context_snapshot": t.context_snapshot,
            })

    return {
        "reviews": visible,
        "count": len(visible),
        "message": "Human review queue. Approving a task releases the workflow."
    }


async def _resolve_task(review_id: str, new_status: str, action: ReviewAction, user) -> dict:
    async with async_session() as session:
        result = await session.execute(
            select(HumanReviewTask).where(HumanReviewTask.id == review_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(404, "Review task not found")
        if task.tenant_id != get_current_tenant().tenant_id:
            raise ForbiddenError("Cross-tenant access denied")
            
        task.status = new_status
        task.resolved_by_user_id = user.user_id
        task.resolution_notes = action.notes or new_status.capitalize()
        
        await session.commit()
        
        return {
            "id": task.id,
            "status": task.status,
            "resolved_by": task.resolved_by_user_id,
            "resolution_notes": task.resolution_notes
        }

@router.post("/{review_id}/approve")
async def approve(review_id: str, action: ReviewAction, user=Depends(get_current_user)):
    review_data = await _resolve_task(review_id, "approved", action, user)
    return {"status": "approved", "review": review_data}


@router.post("/{review_id}/reject")
async def reject(review_id: str, action: ReviewAction, user=Depends(get_current_user)):
    review_data = await _resolve_task(review_id, "rejected", action, user)
    return {"status": "rejected", "review": review_data}


@router.post("/{review_id}/revise")
async def revise(review_id: str, action: ReviewAction, user=Depends(get_current_user)):
    review_data = await _resolve_task(review_id, "needs_revision", action, user)
    return {"status": "needs_revision", "review": review_data}


# Internal helper used by agents/workflows
async def create_review_task(
    task_type: str,
    patient_id: str,
    reason: str,
    assigned_to: str = "clinician",
    tenant_id: str = "tenant_hospital_a",
) -> dict:
    async with async_session() as session:
        task_id = f"rev_{uuid.uuid4().hex[:12]}"
        new_task = HumanReviewTask(
            id=task_id,
            tenant_id=tenant_id,
            task_type=task_type,
            status="pending_review",
            patient_id=patient_id,
            reason=reason,
            assigned_to_role=assigned_to,
            context_snapshot={"source": "agent_workflow"}
        )
        session.add(new_task)
        await session.commit()
        
        return {
            "id": task_id,
            "tenant_id": tenant_id,
            "task_type": task_type,
            "status": "pending_review",
            "patient_id": patient_id,
            "reason": reason,
            "assigned_to_role": assigned_to,
            "context_snapshot": {"source": "agent_workflow"},
        }
