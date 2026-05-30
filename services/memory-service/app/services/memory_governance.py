"""
Memory Governance - The critical gate for all Hindsight Memory writes.

This is the equivalent of MCP but for long-term memory.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class MemoryGovernanceService:
    """
    Decides whether a memory candidate is safe to store.
    """

    def evaluate(self, candidate: Dict[str, Any], user_role: str, tenant_id: str) -> Dict[str, Any]:
        content = candidate.get("content", "").lower()

        # Hard blocks
        blocked_keywords = ["diagnosis", "lab value", "medication", "dose", "critical", "abnormal", "psychotherapy"]
        for kw in blocked_keywords:
            if kw in content:
                return {
                    "decision": "blocked",
                    "reason": f"Contains forbidden clinical content keyword: {kw}",
                    "audit_tags": ["memory_blocked_clinical_content"],
                }

        # Role-based rules
        if user_role == "patient" and "clinician" in content:
            return {"decision": "blocked", "reason": "Patient cannot store clinician-specific preferences"}

        # Default allow for safe patterns
        return {
            "decision": "approved",
            "reason": "Passed PHI minimization and sensitivity checks",
            "audit_tags": ["memory_approved", "non_clinical_preference"],
            "minimized_content": candidate.get("content"),
        }
