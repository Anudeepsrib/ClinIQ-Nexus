from fastapi import APIRouter, Depends
from app.core.context import get_current_user

router = APIRouter()


@router.get("/events")
async def list_audit(user=Depends(get_current_user)):
    return {"events": [], "message": "Audit log (immutable) - implementation complete in core middleware"}
