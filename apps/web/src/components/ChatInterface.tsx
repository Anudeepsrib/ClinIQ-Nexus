'use client';

import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import type { Citation } from '@/types/api';

interface ChatMessage {
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

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSend: (query: string) => Promise<void>;
  placeholder?: string;
  /** Optional: externally controlled prefill value (e.g. from "Load example" button) */
  prefill?: string;
  onPrefillConsumed?: () => void;
}

export function ChatInterface({ 
  messages, 
  isLoading, 
  onSend, 
  placeholder, 
  prefill, 
  onPrefillConsumed 
}: ChatInterfaceProps) {
  const [query, setQuery] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Support external "Load example" buttons
  useEffect(() => {
    if (prefill) {
      setQuery(prefill);
      onPrefillConsumed?.();
    }
  }, [prefill]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async () => {
    const trimmed = query.trim();
    if (!trimmed || isLoading) return;
    
    await onSend(trimmed);
    setQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-auto p-6 chat-container space-y-6"
        style={{ maxHeight: 'calc(100vh - 280px)' }}
        aria-live="polite"
        aria-label="Chat conversation"
      >
        {messages.length === 0 && (
          <div className="text-center text-slate-500 mt-12">
            <div className="text-sm">Start a conversation with the governed clinical AI.</div>
            <div className="text-xs mt-1">All responses are routed, governed, and may require human review.</div>
          </div>
        )}

        {messages.map((m, i) => (
          <MessageBubble key={i} m={m} />
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-slate-400 text-sm pl-1" role="status">
            <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse" />
            Thinking with full governance...
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-800 bg-slate-900">
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || "Ask anything (labs, discharge, chest pain concern...)"}
            className="flex-1 bg-slate-950 border border-slate-700 focus:border-[#0284c8] rounded-2xl px-5 py-3 text-sm outline-none placeholder:text-slate-600"
            disabled={isLoading}
            aria-label="Clinical query input"
          />
          <button
            onClick={handleSend}
            disabled={!query.trim() || isLoading}
            className="px-8 rounded-2xl bg-white text-slate-950 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 hover:bg-slate-200 transition"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>

        <div className="text-[10px] text-center text-slate-500 mt-2.5">
          Reference implementation. Never for clinical use without formal validation and compliance sign-off.
        </div>
      </div>
    </div>
  );
}
