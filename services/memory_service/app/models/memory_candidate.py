"""Memory candidate model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryCandidate:
    content: str
    memory_type: str
    tenant_id: str
    user_id: str
    role: str
    patient_id: Optional[str] = None
    source_workflow_id: Optional[str] = None

