"""Pydantic schemas for the Hindsight Memory service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class MemoryCandidateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    memory_type: str = "preference"
    tenant_id: str
    user_id: str
    user_role: str
    patient_id: Optional[str] = None
    source_workflow_id: Optional[str] = None


class MemoryRetrieveRequest(BaseModel):
    tenant_id: str
    user_id: str
    role: str
    patient_id: Optional[str] = None


class MemoryRecordResponse(BaseModel):
    memory_id: str
    tenant_id: str
    user_id: str
    role: str
    memory_type: str
    memory_text_minimized: str
    sensitivity_level: str
    patient_id: Optional[str] = None
    created_at: Optional[datetime | str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

