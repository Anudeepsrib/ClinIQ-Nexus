"""Chat and intent schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Any


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=4000)
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None
    conversation_id: Optional[str] = None
    context: dict = Field(default_factory=dict)


class RouteDecision(BaseModel):
    intent: str
    confidence: float
    requires_agent: bool = False
    requires_rag: bool = False
    requires_human_review: bool = False
    data_sources: List[str] = Field(default_factory=list)
    safety_flags: List[str] = Field(default_factory=list)
    reason: str
    model_used_for_classification: str = "deterministic+mock-llm"


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    doc_type: str
    relevance: float
    snippet: str


class ChatResponse(BaseModel):
    response: str
    route: str
    confidence: float
    requires_human_review: bool
    citations: List[Citation] = Field(default_factory=list)
    safety_flags: List[str] = Field(default_factory=list)
    disclaimer: Optional[str] = None
    human_review_task_id: Optional[str] = None
    memory_used: bool = False
