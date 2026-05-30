"""
Real AWS Bedrock Provider for production use.
Handles Converse API for Claude models.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import structlog

try:
    import boto3
except ImportError:
    boto3 = None

from app.core.config import settings

logger = structlog.get_logger(__name__)


class BedrockProvider:
    """
    AWS Bedrock integration using the Converse API.
    Enforces MCP constraints explicitly through prompt engineering.
    """

    def __init__(self):
        if not boto3:
            raise ImportError("boto3 is required to use BedrockProvider")
            
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)

    async def generate_safe_response(
        self,
        query: str,
        allowed_context: List[Dict[str, Any]],
        route: str,
        user_role: str,
        requires_review: bool = False,
    ) -> Dict[str, Any]:
        """
        Generates a response using Claude 3.5 Sonnet on AWS Bedrock.
        """
        model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        
        # Format the context
        context_text = "\n\n".join(
            f"[{c.get('doc_type','doc')}] {c.get('content','')[:800]}" 
            for c in allowed_context
        ) if allowed_context else "No authorized clinical records were available for this query."
        
        system_prompt = (
            "You are a clinical AI assistant operating under strict HIPAA-conscious constraints. "
            "You must only rely on the authorized context provided. "
            "You must never hallucinate clinical details. "
            f"The user role is: {user_role}. Adjust your tone appropriately. "
            "If the context lacks sufficient information, you must state that."
        )
        
        prompt = (
            f"Context:\n<context>\n{context_text}\n</context>\n\n"
            f"Task: {route}\n\n"
            f"Query: {query}"
        )
        
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
        
        try:
            response = self.client.converse(
                modelId=model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": 2048,
                    "temperature": 0.0,
                    "topP": 0.9,
                }
            )
            
            output_text = response["output"]["message"]["content"][0]["text"]
            
            # Post-generation review flagging
            force_review = requires_review or route in {"discharge_planning", "prior_authorization", "clinical_safety_triage"}
            
            return {
                "text": output_text,
                "model": model_id,
                "requires_human_review": force_review,
                "citation_count": len(allowed_context),
            }
            
        except Exception as e:
            logger.error("bedrock_generation_failed", error=str(e), route=route)
            raise RuntimeError(f"AWS Bedrock generation failed: {e}") from e

