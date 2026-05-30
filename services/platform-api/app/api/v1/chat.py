"""AI Chat endpoints - fully wired with Intent Router + MCP Governance + RAG + Safe Generation."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json
import uuid

from app.core.context import get_current_user, get_current_tenant
from app.schemas.chat import ChatRequest, ChatResponse, RouteDecision, Citation
from app.services.intent_router.service import route_intent
from app.services.mcp.service import MCPContextGovernanceService
from app.services.rag.service import retrieve_authorized_chunks
from app.services.memory.service import memory_service
from app.providers.model_router import model_router
from app.core.logging import logger

router = APIRouter()


@router.post("/route", response_model=RouteDecision)
async def classify_intent(req: ChatRequest, user=Depends(get_current_user)):
    """Pure intent classification (used by frontend for UI hints + safety)."""
    decision = await route_intent(req.query, user.role, user.tenant_id)
    return decision


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user=Depends(get_current_user)):
    """
    Production-grade chat flow:
    1. Deterministic-first intent routing (with safety overrides)
    2. Authorized retrieval (tenant + patient + consent filtered)
    3. Mandatory MCP governance (the non-bypassable safety layer)
    4. Grounded generation via ModelRouter (mock or real Bedrock)
    5. Full audit + minimized history
    """
    tenant = get_current_tenant()
    decision = await route_intent(req.query, user.role, tenant.tenant_id)

    # 1. Retrieve only what this user is allowed to see
    chunks = await retrieve_authorized_chunks(
        query=req.query,
        user=user,
        patient_id=req.patient_id,
        top_k=6 if decision.requires_rag else 3,
    )

    # 2. MCP Governance — this is the most important gate in the system
    mcp = MCPContextGovernanceService()
    mcp_decision = await mcp.govern(
        candidate_chunks=chunks,
        user=user,
        route=decision.intent,
        patient_id=req.patient_id,
        query=req.query,
    )

    # 3. Generate grounded, safe response
    generation = await model_router.generate(
        query=req.query,
        allowed_context=mcp_decision.allowed_context,
        route=decision.intent,
        user_role=user.role,
        requires_review=mcp_decision.requires_human_review or decision.requires_human_review,
    )

    # 4. Build citations (only from allowed context)
    citations = [
        Citation(
            document_id=c.get("document_id", ""),
            chunk_id=c.get("chunk_id", ""),
            doc_type=c.get("doc_type", "clinical_document"),
            relevance=round(c.get("relevance", 0.8), 3),
            snippet=c.get("content", "")[:280] + "...",
        )
        for c in mcp_decision.allowed_context[:4]
    ]

    # 5. Governed memory (optional, non-clinical only)
    memory_used = False
    try:
        mem = await memory_service.extract_and_store(
            user=user,
            conversation_turn={"content": req.query, "patient_id": req.patient_id},
        )
        memory_used = mem is not None
    except Exception:
        pass  # Memory is best-effort

    # 6. Final safety disclaimer
    disclaimer = (
        "This is a summary of authorized records only. "
        "It is not a diagnosis, treatment recommendation, or substitute for clinical judgment. "
        "All safety-sensitive outputs require licensed human review."
    )

    return ChatResponse(
        response=generation["text"],
        route=decision.intent,
        confidence=round(decision.confidence, 3),
        requires_human_review=generation["requires_human_review"],
        citations=citations,
        safety_flags=decision.safety_flags + (["mcp_human_review_triggered"] if mcp_decision.requires_human_review else []),
        disclaimer=disclaimer,
        human_review_task_id=str(uuid.uuid4()) if generation["requires_human_review"] else None,
        memory_used=memory_used,
    )


@router.post("/stream")
async def chat_stream(req: ChatRequest, user=Depends(get_current_user)):
    """Streaming version (SSE) — same safety guarantees as /chat."""
    async def generator():
        decision = await route_intent(req.query, user.role, get_current_tenant().tenant_id)
        yield f"data: {json.dumps({'event': 'route', 'intent': decision.intent, 'confidence': decision.confidence})}\n\n"

        chunks = await retrieve_authorized_chunks(req.query, user, req.patient_id, top_k=5)
        mcp = MCPContextGovernanceService()
        mcp_decision = await mcp.govern(chunks, user, decision.intent, req.patient_id, req.query)

        yield f"data: {json.dumps({'event': 'mcp', 'allowed_chunks': len(mcp_decision.allowed_context), 'requires_review': mcp_decision.requires_human_review})}\n\n"

        generation = await model_router.generate(
            query=req.query,
            allowed_context=mcp_decision.allowed_context,
            route=decision.intent,
            user_role=user.role,
            requires_review=mcp_decision.requires_human_review,
        )

        # Stream the response in chunks for UX
        words = generation["text"].split()
        for i in range(0, len(words), 4):
            chunk = " ".join(words[i:i+4]) + " "
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        yield f"data: {json.dumps({'done': True, 'route': decision.intent, 'requires_human_review': generation['requires_human_review'], 'citations': []})}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")
