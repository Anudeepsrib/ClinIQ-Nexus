import type { Citation } from './api';

/**
 * UI-only message shape used in the chat interface.
 * This is intentionally more flexible than the strict backend ChatResponse.
 */
export interface ChatMessage {
  type: 'system' | 'user' | 'assistant' | 'error';
  content: string;
  route?: string;
  confidence?: number;
  requires_human_review?: boolean;
  citations?: Citation[];
  disclaimer?: string | null;
  safety_flags?: string[];
  review_task_id?: string | null;
  memory_used?: boolean;
}
