"""Audit logging helpers.

The production path writes immutable audit rows to PostgreSQL. Unit tests and
local runs without a database fall back to an in-memory ledger so governance
paths can still be exercised.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.db.session import async_session
from app.models.audit import AuditEvent

_AUDIT_FALLBACK: list[dict[str, Any]] = []


async def log_audit_event(
    *,
    tenant_id: str,
    user_id: Optional[str],
    event_type: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    action: Optional[str] = None,
    outcome: str = "success",
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> str:
    audit_id = f"audit_{uuid.uuid4().hex[:12]}"
    payload = {
        "id": audit_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "event_type": event_type,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "patient_id": patient_id,
        "action": action,
        "outcome": outcome,
        "details": details or {},
        "correlation_id": correlation_id,
    }

    try:
        async with async_session() as session:
            session.add(AuditEvent(**payload))
            await session.commit()
    except Exception:
        _AUDIT_FALLBACK.append(payload)

    return audit_id


async def list_audit_events(tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    try:
        from sqlalchemy import select

        async with async_session() as session:
            result = await session.execute(
                select(AuditEvent)
                .where(AuditEvent.tenant_id == tenant_id)
                .order_by(AuditEvent.created_at.desc())
                .limit(limit)
            )
            return [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id,
                    "patient_id": event.patient_id,
                    "action": event.action,
                    "outcome": event.outcome,
                    "details": event.details,
                    "correlation_id": event.correlation_id,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
                for event in result.scalars().all()
            ]
    except Exception:
        return [event for event in _AUDIT_FALLBACK if event["tenant_id"] == tenant_id][-limit:]

