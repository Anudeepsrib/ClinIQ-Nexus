"""
MCP / Context Governance Service

This is the single most critical safety component in the platform.

RAG retrieves data.
MCP decides what context is safe to pass to the LLM.

Every LLM call in the entire system MUST go through this service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.context import UserContext
from app.core.config import settings


@dataclass
class MCPDecision:
    allowed_context: List[Dict[str, Any]] = field(default_factory=list)
    redacted_context: List[Dict[str, Any]] = field(default_factory=list)
    blocked_context_count: int = 0
    policy_decisions: List[str] = field(default_factory=list)
    requires_human_review: bool = False
    disclaimer_required: bool = True
    audit_tags: List[str] = field(default_factory=list)
    transformed_for_role: Optional[str] = None


class MCPContextGovernanceService:
    """
    Applies consent, role, sensitivity, minimum-necessary, and safety rules
    before any context reaches a model.
    """

    def __init__(self):
        self.safety_threshold = settings.REQUIRE_HUMAN_REVIEW_CONFIDENCE_BELOW

    async def govern(
        self,
        candidate_chunks: List[Dict[str, Any]],
        user: UserContext,
        route: str,
        patient_id: Optional[str] = None,
        query: str = "",
    ) -> MCPDecision:
        """
        The core governance function.
        """
        decision = MCPDecision()

        if not candidate_chunks:
            decision.policy_decisions.append("no_retrieved_context")
            decision.disclaimer_required = True
            return decision

        allowed: List[Dict] = []
        redacted: List[Dict] = []

        for chunk in candidate_chunks:
            # 1. Tenant isolation (should already be filtered, but double-check)
            if chunk.get("tenant_id") != user.tenant_id:
                decision.blocked_context_count += 1
                decision.policy_decisions.append("tenant_mismatch_blocked")
                continue

            # 2. Patient scoping (minimum necessary)
            chunk_patient = chunk.get("patient_id")
            if chunk_patient and not user.can_access_patient(chunk_patient):
                decision.blocked_context_count += 1
                decision.policy_decisions.append("patient_scope_violation")
                continue

            # 3. Sensitivity + consent
            sensitivity = chunk.get("sensitivity_level", "phi")
            consent_scope = chunk.get("consent_scope", "treatment")

            if sensitivity == "phi" and "treatment" not in user.consent_scopes:
                decision.blocked_context_count += 1
                decision.policy_decisions.append("consent_scope_violation")
                continue

            # 4. Role-based transformation / redaction
            transformed = self._transform_for_role(chunk, user.role, route)

            # 5. High-risk content detection in patient-facing responses
            if user.role == "patient" and self._contains_abnormal_or_concerning(transformed["content"]):
                decision.requires_human_review = True
                decision.policy_decisions.append("abnormal_value_in_patient_facing_output")
                decision.audit_tags.append("requires_clinician_review")

            allowed.append(transformed)

        decision.allowed_context = allowed
        decision.redacted_context = redacted
        decision.transformed_for_role = user.role

        # Final policy: any clinical risk or low-confidence route forces human review
        if route in {"clinical_safety_triage", "discharge_planning", "prior_authorization"}:
            decision.requires_human_review = True
            decision.audit_tags.append("high_risk_workflow")

        if "safety" in route or "triage" in route:
            decision.audit_tags.append("safety_critical")

        decision.audit_tags.append("mcp_governed")
        decision.disclaimer_required = True

        return decision

    def _transform_for_role(self, chunk: Dict, role: str, route: str) -> Dict:
        """Simplify or redact content based on who is asking."""
        content = chunk.get("content", "")

        if role == "patient":
            # Patient-friendly language (very simplified in real system)
            content = content[:600] + "..." if len(content) > 600 else content
            content = "Summary of your records: " + content  # In real impl use LLM simplification after governance

        if role in {"admin", "compliance_officer"}:
            # De-identify aggressively
            content = "[De-identified operational excerpt]"

        return {**chunk, "content": content, "governed_for_role": role}

    def _contains_abnormal_or_concerning(self, text: str) -> bool:
        """Simple heuristic. In production this would be a trained signal detector."""
        concerning = ["critical", "abnormal", "panic", "high risk", "elevated", "positive for"]
        return any(word in text.lower() for word in concerning)
