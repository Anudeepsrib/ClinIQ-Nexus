/**
 * TypeScript contracts matching the platform-api backend schemas.
 * Keep these in sync with services/platform-api/app/schemas/*
 */

export interface Citation {
  document_id: string;
  chunk_id: string;
  doc_type: string;
  relevance: number;
  snippet: string;
}

export interface ChatResponse {
  response: string;
  route: string;
  confidence: number;
  requires_human_review: boolean;
  citations: Citation[];
  safety_flags: string[];
  disclaimer?: string | null;
  human_review_task_id?: string | null;
  memory_used?: boolean;
}

export interface ChatRequest {
  query: string;
  patient_id?: string;
  encounter_id?: string;
  conversation_id?: string;
  context?: Record<string, unknown>;
}

export interface ReviewTask {
  id: string;
  tenant_id: string;
  workflow_id?: string | null;
  task_type: string;
  status: 'pending_review' | 'approved' | 'rejected' | 'needs_revision' | 'escalated';
  priority: 'low' | 'medium' | 'high' | 'critical';
  patient_id?: string | null;
  reason?: string | null;
  assigned_to_role?: string | null;
  created_at?: string | null;
  context_snapshot?: Record<string, unknown> | null;
  resolution_notes?: string | null;
  resolved_by_user_id?: string | null;
  resolved_at?: string | null;
}

export interface ReviewsResponse {
  reviews: ReviewTask[];
  count: number;
  message?: string;
}

export interface ReviewActionRequest {
  notes?: string;
}

export interface WorkflowRequest {
  patient_id: string;
  query: string;
  context?: Record<string, unknown>;
}

export interface WorkflowResponse {
  workflow_id?: string;
  status: string;
  result?: unknown;
  review_task_id?: string | null;
  [key: string]: unknown;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}
