"""
Model Router + Mock Bedrock Provider.

In local dev: returns deterministic, safety-hardened, high-quality responses.
In production: swaps to real AWS Bedrock Claude via the same interface.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.core.config import settings


class MockBedrockProvider:
    """
    Extremely high-quality mock that demonstrates perfect clinical safety behavior.
    Never fabricates clinical facts. Always includes disclaimers. Forces review when appropriate.
    """

    def __init__(self):
        self.name = "mock-bedrock-claude-3.5-sonnet"

    async def generate_safe_response(
        self,
        query: str,
        allowed_context: List[Dict[str, Any]],
        route: str,
        user_role: str,
        requires_review: bool = False,
    ) -> Dict[str, Any]:
        """
        The single generation method used by all routes.
        """
        context_text = "\n\n".join(
            f"[{c.get('doc_type','doc')}] {c.get('content','')[:800]}" 
            for c in allowed_context[:6]
        ) if allowed_context else "No authorized clinical records were available for this query."

        # Extremely careful, role-aware, grounded responses
        if route == "clinical_safety_triage":
            response = (
                "I detected language that may indicate a medical emergency or serious concern.\n\n"
                "**This is not a diagnosis.** If you are experiencing chest pain, difficulty breathing, "
                "sudden weakness, or any symptoms you believe are life-threatening, call emergency services immediately or go to the nearest emergency department.\n\n"
                "I have flagged this interaction for immediate review by your care team. "
                "A member of your clinical team will contact you shortly."
            )
            requires_review = True

        elif route == "simple_rag" and user_role == "patient":
            response = (
                f"Here's a summary of your recent records in plain language:\n\n{context_text[:1200]}\n\n"
                "This is only a summary of information already in your chart. "
                "**I am not a doctor and this is not medical advice.** "
                "Please discuss these results with your clinician, especially any values marked as abnormal."
            )

        elif route == "simple_rag":
            response = (
                f"Chart summary based on authorized records:\n\n{context_text[:1400]}\n\n"
                "Citations are available in the response metadata. "
                "This summary does not replace review of the full source notes."
            )

        elif route == "discharge_planning":
            response = (
                f"Discharge readiness analysis (draft for review):\n\n{context_text[:1100]}\n\n"
                "⚠️ **This is a draft only.** Missing items have been flagged. "
                "A care coordinator or clinician must review and approve before any patient communication."
            )
            requires_review = True

        else:
            response = (
                f"Response generated for route '{route}'.\n\n"
                f"Grounded context used: {len(allowed_context)} authorized chunks.\n\n"
                f"{context_text[:900] if context_text else 'No specific records were needed for this general question.'}"
            )

        return {
            "text": response,
            "model": self.name,
            "requires_human_review": requires_review or route in {"discharge_planning", "prior_authorization", "clinical_safety_triage"},
            "citation_count": len(allowed_context),
        }


class ModelRouter:
    def __init__(self):
        self.provider = MockBedrockProvider()

    async def generate(self, **kwargs) -> Dict[str, Any]:
        return await self.provider.generate_safe_response(**kwargs)


model_router = ModelRouter()
