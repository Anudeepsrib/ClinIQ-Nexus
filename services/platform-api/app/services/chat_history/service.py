"""Minimized chat history persistence."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from app.db.session import async_session
from app.models.conversation import Conversation, Message
from app.core.context import UserContext


async def save_minimized_chat_history(
    *,
    user: UserContext,
    conversation_id: Optional[str],
    patient_id: Optional[str],
    query: str,
    response: str,
    intent_route: str,
    retrieved_document_ids: list[str],
    model_used: str,
    confidence: float,
    requires_human_review: bool,
    safety_flags: list[str],
    audit_event_id: Optional[str],
) -> Optional[str]:
    try:
        async with async_session() as session:
            conv_id = conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
            if conversation_id is None:
                session.add(Conversation(
                    id=conv_id,
                    tenant_id=user.tenant_id,
                    user_id=user.user_id,
                    patient_id=patient_id,
                    role=user.role,
                ))

            session.add(Message(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                conversation_id=conv_id,
                role="user",
                content=query[:4000],
                intent_route=intent_route,
                model_used=model_used,
                confidence=confidence,
                requires_human_review=requires_human_review,
                safety_flags=safety_flags,
                retrieved_document_ids=retrieved_document_ids,
                audit_event_id=audit_event_id,
            ))
            session.add(Message(
                id=f"msg_{uuid.uuid4().hex[:12]}",
                conversation_id=conv_id,
                role="assistant",
                content=response[:4000],
                intent_route=intent_route,
                model_used=model_used,
                confidence=confidence,
                requires_human_review=requires_human_review,
                safety_flags=safety_flags,
                retrieved_document_ids=retrieved_document_ids,
                audit_event_id=audit_event_id,
            ))
            await session.commit()
            return conv_id
    except Exception:
        return None

