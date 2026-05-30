from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy import select

from app.core.context import get_current_user, get_current_tenant
from app.core.exceptions import ForbiddenError
from app.db.session import async_session
from app.models.workflow import HumanReviewTask
from app.services.audit.service import log_audit_event

router = APIRouter()
_REVIEW_FALLBACK: list[dict] = []
ADMIN_REVIEW_ROLES = {"admin", "operations", "hospital_operations"}


class ReviewAction(BaseModel):
    notes: Optional[str] = None


@router.get("/")
async def list_reviews(user=Depends(get_current_user)):
    """Role-filtered human review queue from DB."""
    tenant = get_current_tenant()
    try:
        async with async_session() as session:
            query = select(HumanReviewTask).where(
                HumanReviewTask.tenant_id == tenant.tenant_id,
                HumanReviewTask.status == "pending_review"
            )
            
            # Compliance sees all metadata. Admins do not automatically see clinical PHI queues.
            if user.role == "compliance_officer":
                pass # No additional role filter
            elif user.role in {"admin", "super_admin"}:
                query = query.where(HumanReviewTask.assigned_to_role.in_(list(ADMIN_REVIEW_ROLES)))
            elif user.role in {"clinician", "nurse", "care_coordinator"}:
                query = query.where(HumanReviewTask.assigned_to_role.in_([user.role, "clinician", "care_coordinator"]))
            else:
                return {"reviews": [], "count": 0, "message": "No reviews visible"}

            result = await session.execute(query)
            tasks = result.scalars().all()

            visible = [_serialize_review_task(t) for t in tasks]
    except Exception:
        visible = [
            task for task in _REVIEW_FALLBACK
            if task["tenant_id"] == tenant.tenant_id
            and task["status"] == "pending_review"
            and (
                user.role == "compliance_officer"
                or _can_view_review(user.role, task.get("assigned_to_role"))
            )
        ]

    return {
        "reviews": visible,
        "count": len(visible),
        "message": "Human review queue. Approving a task releases the workflow."
    }


async def _resolve_task(review_id: str, new_status: str, action: ReviewAction, user) -> dict:
    tenant = get_current_tenant()
    try:
        async with async_session() as session:
            result = await session.execute(
                select(HumanReviewTask).where(HumanReviewTask.id == review_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise HTTPException(404, "Review task not found")
            if task.tenant_id != tenant.tenant_id:
                raise ForbiddenError("Cross-tenant access denied")
            if not _can_resolve_review(user.role, task.assigned_to_role):
                raise ForbiddenError("User role cannot resolve this review task")

            task.status = new_status
            task.resolved_by_user_id = user.user_id
            task.resolution_notes = action.notes or new_status.capitalize()
            task.resolved_at = datetime.now(timezone.utc)

            await session.commit()
            review_data = {
                "id": task.id,
                "status": task.status,
                "resolved_by": task.resolved_by_user_id,
                "resolution_notes": task.resolution_notes,
                "resolved_at": task.resolved_at.isoformat() if task.resolved_at else None,
            }
    except (ForbiddenError, HTTPException):
        raise
    except Exception:
        review_data = _resolve_fallback_task(review_id, new_status, action, user, tenant.tenant_id)

    await log_audit_event(
        tenant_id=tenant.tenant_id,
        user_id=user.user_id,
        event_type="human_review_decision",
        resource_type="human_review_task",
        resource_id=review_id,
        action=new_status,
        outcome="success",
        details={"notes_present": bool(action.notes), "status": new_status},
    )
    return review_data


def _can_view_review(user_role: str, assigned_to_role: str | None) -> bool:
    if user_role == "compliance_officer":
        return True
    if user_role in {"admin", "super_admin"}:
        return assigned_to_role in ADMIN_REVIEW_ROLES
    if user_role in {"clinician", "nurse", "care_coordinator"}:
        return assigned_to_role in {user_role, "clinician", "care_coordinator"}
    return False


def _can_resolve_review(user_role: str, assigned_to_role: str | None) -> bool:
    if user_role == "compliance_officer":
        return True
    if user_role in {"admin", "super_admin"}:
        return assigned_to_role in ADMIN_REVIEW_ROLES
    if assigned_to_role is None:
        return user_role in {"clinician", "nurse", "care_coordinator"}
    if user_role == assigned_to_role:
        return True
    return assigned_to_role in {"clinician", "care_coordinator"} and user_role in {"clinician", "care_coordinator"}


def _resolve_fallback_task(review_id: str, new_status: str, action: ReviewAction, user, tenant_id: str) -> dict:
    for task in _REVIEW_FALLBACK:
        if task["id"] == review_id:
            if task["tenant_id"] != tenant_id:
                raise ForbiddenError("Cross-tenant access denied")
            if not _can_resolve_review(user.role, task.get("assigned_to_role")):
                raise ForbiddenError("User role cannot resolve this review task")
            task["status"] = new_status
            task["resolved_by"] = user.user_id
            task["resolution_notes"] = action.notes or new_status.capitalize()
            task["resolved_at"] = datetime.now(timezone.utc).isoformat()
            return task
    raise HTTPException(404, "Review task not found")


def _serialize_review_task(task: HumanReviewTask) -> dict:
    return {
        "id": task.id,
        "tenant_id": task.tenant_id,
        "workflow_id": task.workflow_id,
        "task_type": task.task_type,
        "status": task.status,
        "priority": task.priority,
        "patient_id": task.patient_id,
        "reason": task.reason,
        "assigned_to_role": task.assigned_to_role,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "context_snapshot": task.context_snapshot,
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


@router.post("/{review_id}/escalate")
async def escalate(review_id: str, action: ReviewAction, user=Depends(get_current_user)):
    review_data = await _resolve_task(review_id, "escalated", action, user)
    return {"status": "escalated", "review": review_data}


# Internal helper used by agents/workflows
async def create_review_task(
    task_type: str,
    patient_id: str,
    reason: str,
    assigned_to: str = "clinician",
    tenant_id: str = "tenant_hospital_a",
    priority: str = "medium",
    workflow_id: str | None = None,
    requested_by_user_id: str | None = None,
    context_snapshot: dict | None = None,
) -> dict:
    task_id = f"rev_{uuid.uuid4().hex[:12]}"
    snapshot = context_snapshot or {"source": "agent_workflow"}
    task = {
        "id": task_id,
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "task_type": task_type,
        "status": "pending_review",
        "priority": priority,
        "patient_id": patient_id,
        "reason": reason,
        "requested_by_user_id": requested_by_user_id,
        "assigned_to_role": assigned_to,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "context_snapshot": snapshot,
    }
    try:
        async with async_session() as session:
            new_task = HumanReviewTask(
                id=task_id,
                tenant_id=tenant_id,
                task_type=task_type,
                status="pending_review",
                priority=priority,
                workflow_id=workflow_id,
                patient_id=patient_id,
                reason=reason,
                requested_by_user_id=requested_by_user_id,
                assigned_to_role=assigned_to,
                context_snapshot=snapshot
            )
            session.add(new_task)
            await session.commit()
    except Exception:
        _REVIEW_FALLBACK.append(task)

    await log_audit_event(
        tenant_id=tenant_id,
        user_id=None,
        event_type="human_review_task_created",
        resource_type="human_review_task",
        resource_id=task_id,
        patient_id=patient_id,
        action="create",
        outcome="success",
        details={"task_type": task_type, "assigned_to_role": assigned_to, "priority": priority},
    )
    return task
