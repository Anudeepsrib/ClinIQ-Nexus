"""Memory record model used by the standalone service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MemoryRecord:
    memory_id: str
    tenant_id: str
    hospital_id: Optional[str]
    facility_id: Optional[str]
    user_id: str
    role: str
    patient_id: Optional[str]
    encounter_id: Optional[str]
    memory_type: str
    memory_text_minimized: str
    sensitivity_level: str
    policy_decision_id: str
    created_at: datetime
    is_active: bool = True

