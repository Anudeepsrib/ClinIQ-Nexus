"""Memory policy decision model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryPolicyDecision:
    policy_decision_id: str
    decision: str
    reason: str
    created_at: datetime

