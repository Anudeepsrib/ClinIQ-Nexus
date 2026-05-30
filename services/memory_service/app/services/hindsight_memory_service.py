"""
HindsightMemoryService - The complete, production-oriented Hindsight Memory implementation.

This is the central service that orchestrates:
- Extraction
- Classification
- Governance
- Writing (only after approval)
- Retrieval (always governed and scoped)
- Auditing
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .memory_extractor import MemoryExtractor
from .memory_classifier import MemoryClassifier
from .memory_governance import MemoryGovernanceService
from .memory_retriever import MemoryRetriever
from .memory_writer import MemoryWriter
from .memory_audit import MemoryAuditService
from ..repositories.memory_repository import MemoryRepository


class HindsightMemoryService:
    """
    Full governed Hindsight Memory implementation.
    This is what Deep Agents and LangGraph workflows should use.
    """

    def __init__(self):
        self.extractor = MemoryExtractor()
        self.classifier = MemoryClassifier()
        self.governance = MemoryGovernanceService()
        self.writer = MemoryWriter()
        self.audit = MemoryAuditService()
        self.repository = MemoryRepository()
        self.retriever = MemoryRetriever(self.repository)

    async def retrieve_governed_memories(
        self,
        tenant_id: str,
        user_id: str,
        role: str,
        patient_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Public method for Deep Agents to retrieve safe memories."""
        return await self.retriever.retrieve_for_context(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            patient_id=patient_id,
        )

    async def process_memory_candidate(
        self,
        candidate: Dict[str, Any],
        user_role: str,
        tenant_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Full write pipeline:
        Extract → Classify → Govern → (if approved) Write + Audit
        """
        candidate = self._normalize_candidate(candidate, user_role)

        classification = self.classifier.classify(candidate)
        candidate["memory_type"] = classification["memory_type"]

        gov_decision = self.governance.evaluate(candidate, user_role, tenant_id)

        audit_id = await self.audit.log_memory_decision(
            tenant_id=tenant_id,
            user_id=user_id,
            decision=gov_decision["decision"],
            candidate_content=candidate.get("content"),
            minimized_content=gov_decision.get("minimized_content"),
            reason=gov_decision["reason"],
            policy_tags=gov_decision.get("audit_tags", []),
        )

        if gov_decision["decision"] == "approved":
            record = await self.writer.write_approved_memory(
                tenant_id=tenant_id,
                user_id=user_id,
                role=user_role,
                minimized_content=gov_decision.get("minimized_content", candidate["content"]),
                memory_type=candidate["memory_type"],
                sensitivity_level=classification["sensitivity_level"],
                source_workflow_id=candidate.get("source_workflow_id"),
                patient_id=candidate.get("patient_id"),
            )
            await self.repository.save_memory_record(record)

            return {
                "status": "stored",
                "memory_id": record["memory_id"],
                "audit_id": audit_id,
            }
        else:
            return {
                "status": "blocked",
                "reason": gov_decision["reason"],
                "audit_id": audit_id,
            }

    def _normalize_candidate(self, candidate: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """
        Run the extractor before classification when the input is raw text.

        Deep Agents usually submit an already-formed candidate, while chat/API
        paths may submit a broader turn. In both cases we keep the original
        content if the conservative extractor finds no durable preference so
        clinical-content blocking still happens.
        """
        normalized = dict(candidate)
        content = str(normalized.get("content") or "").strip()
        if not content:
            return normalized

        extracted = self.extractor.extract_candidates(
            content,
            role=user_role,
            source=str(normalized.get("source") or "memory_candidate"),
        )
        if not extracted:
            return normalized

        first = extracted[0]
        normalized["content"] = first.get("content", content)
        normalized["memory_type"] = first.get("memory_type", normalized.get("memory_type", "preference"))
        normalized["source"] = first.get("source", normalized.get("source"))
        normalized["extracted_candidate_count"] = len(extracted)
        return normalized
