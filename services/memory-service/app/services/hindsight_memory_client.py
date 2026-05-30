"""
HindsightMemoryClient - The main interface used by Deep Agents and LangGraph workflows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .memory_extractor import MemoryExtractor
from .memory_governance import MemoryGovernanceService


class HindsightMemoryClient:
    """
    Governed interface to Hindsight Memory.
    All reads and writes go through this client.
    """

    def __init__(self):
        self.extractor = MemoryExtractor()
        self.governance = MemoryGovernanceService()

    async def retrieve_governed_memories(
        self,
        tenant_id: str,
        user_id: str,
        role: str,
        patient_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve only approved, minimized memories."""
        # In real implementation this would query the memory repository with filters
        return []  # Placeholder - will connect to real store

    async def propose_and_govern_memory(
        self,
        candidate: Dict[str, Any],
        user_role: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Extract → Classify → Govern → (optionally) Write
        """
        decision = self.governance.evaluate(candidate, user_role, tenant_id)

        if decision["decision"] == "approved":
            # In production we would call memory_writer here
            return {
                "status": "stored",
                "memory_id": "mem_" + "placeholder",
                "decision": decision,
            }
        else:
            return {
                "status": "blocked",
                "reason": decision["reason"],
                "decision": decision,
            }
