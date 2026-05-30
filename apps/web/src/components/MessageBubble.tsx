'use client';

import { AlertTriangle, Clock, Copy } from 'lucide-react';
import type { Citation } from '@/types/api';
import { toast } from 'sonner';

interface Message {
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

export function MessageBubble({ m }: { m: Message }) {
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Copied to clipboard');
    } catch {
      toast.error('Failed to copy');
    }
  };

  if (m.type === 'system') {
    return (
      <div className="text-xs bg-slate-900 border border-slate-700 p-3 rounded-lg" role="status">
        {m.content}
      </div>
    );
  }

  if (m.type === 'user') {
    return (
      <div className="text-right">
        <div className="inline-block bg-[#0284c8] text-white px-4 py-2.5 rounded-2xl rounded-tr-none max-w-[75%] text-sm">
          {m.content}
        </div>
      </div>
    );
  }

  if (m.type === 'error') {
    return (
      <div className="max-w-2xl">
        <div className="bg-red-950/70 border border-red-900 text-red-300 px-4 py-3 rounded-xl text-sm">
          <div className="flex items-center gap-2 font-medium mb-1">
            <AlertTriangle className="w-4 h-4" /> Error
          </div>
          {m.content}
        </div>
      </div>
    );
  }

  // Assistant message (the important one)
  return (
    <div className="max-w-3xl text-left group">
      <div className="flex items-center gap-2 mb-1.5 text-xs flex-wrap">
        {m.route && (
          <span className="font-mono bg-slate-800 px-2 py-0.5 rounded text-[#0284c8]">
            {m.route}
          </span>
        )}
        {typeof m.confidence === 'number' && (
          <span className="text-emerald-400">conf {Math.round(m.confidence * 100)}%</span>
        )}
        {m.requires_human_review && (
          <span className="flex items-center gap-1 text-amber-400 font-medium">
            <Clock className="w-3.5 h-3.5" /> REQUIRES HUMAN REVIEW
          </span>
        )}
        {m.safety_flags && m.safety_flags.length > 0 && (
          <span className="text-red-400 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> {m.safety_flags.join(', ')}
          </span>
        )}
        <button
          onClick={() => copyToClipboard(m.content)}
          className="ml-auto opacity-0 group-hover:opacity-100 transition text-slate-500 hover:text-slate-300 p-1"
          aria-label="Copy response"
        >
          <Copy className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl rounded-tl-none whitespace-pre-wrap text-sm leading-relaxed">
        {m.content}
      </div>

      {m.disclaimer && (
        <div className="mt-2 text-xs text-slate-400 italic pl-1">{m.disclaimer}</div>
      )}

      {m.citations && m.citations.length > 0 && (
        <div className="mt-3 pl-1">
          <div className="text-xs text-slate-400 mb-1.5 font-medium">Citations (authorized records only)</div>
          <div className="space-y-1">
            {m.citations.map((c, idx) => (
              <div key={idx} className="citation text-xs" title={`Relevance: ${c.relevance}`}>
                [{c.doc_type}] {c.snippet}
              </div>
            ))}
          </div>
        </div>
      )}

      {m.review_task_id && (
        <div className="mt-2 pl-1 text-xs text-amber-400 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          Human Review Task created: <span className="font-mono">{m.review_task_id}</span>
        </div>
      )}

      {m.memory_used && (
        <div className="mt-1.5 pl-1 text-xs text-purple-400">Governed memory preference applied</div>
      )}
    </div>
  );
}
