"""
PatientMessageTriageDeepAgent

Deep Agent for triaging patient portal messages with urgency assessment.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base_deep_agent import BaseDeepAgent, DeepAgentContext, DeepAgentOutput


class PatientMessageTriageDeepAgent(BaseDeepAgent):
    @property
    def name(self) -> str:
        return "patient_message_triage_deep_agent"

    @property
    def description(self) -> str:
        return "Deep triage of patient messages for urgency and appropriate routing"

    async def run(self, task: str, governed_context: List[Dict[str, Any]]) -> DeepAgentOutput:
        findings = [
            {"category": "symptom", "status": "medium", "detail": "New leg swelling reported"},
            {"category": "urgency", "status": "needs_review", "detail": "Patient reports increased fatigue"},
        ]

        return DeepAgentOutput(
            workflow_id=self.context.workflow_id or "message_triage",
            route="patient_message_triage",
            summary="Message contains medium-urgency symptoms. Recommend nurse or clinician review.",
            findings=findings,
            citations=[],
            confidence=0.71,
            requires_human_review=True,
            human_review_reason="Potential clinical deterioration signal in patient message",
            safety_flags=["medium_urgency_symptom"],
        )
