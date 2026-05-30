from fastapi import APIRouter, Depends
from app.core.context import get_current_user
from app.services.audit.service import list_audit_events

router = APIRouter()


@router.get("/events")
async def list_audit(user=Depends(get_current_user)):
    events = await list_audit_events(user.tenant_id)
    return {"events": events, "count": len(events)}


@router.get("/access")
async def list_access_audit(user=Depends(get_current_user)):
    events = await list_audit_events(user.tenant_id)
    access_events = [e for e in events if e.get("event_type") in {"phi_access", "route_decision", "mcp_decision"}]
    return {"events": access_events, "count": len(access_events)}


@router.get("/model-usage")
async def list_model_usage(user=Depends(get_current_user)):
    events = await list_audit_events(user.tenant_id)
    model_events = [e for e in events if e.get("event_type") in {"model_invocation", "route_decision"}]
    return {"events": model_events, "count": len(model_events)}
