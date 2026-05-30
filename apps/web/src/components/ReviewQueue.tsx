'use client';

import { useState } from 'react';
import { CheckCircle, XCircle, RefreshCw, ArrowUp, Clock } from 'lucide-react';
import type { ReviewTask } from '@/types/api';
import { toast } from 'sonner';

interface ReviewQueueProps {
  reviews: ReviewTask[];
  isLoading: boolean;
  onResolve: (id: string, action: 'approve' | 'reject' | 'revise' | 'escalate', notes?: string) => Promise<void>;
  onRefresh: () => void;
}

export function ReviewQueue({ reviews, isLoading, onResolve, onRefresh }: ReviewQueueProps) {
  const [actionNotes, setActionNotes] = useState<Record<string, string>>({});
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  const handleResolve = async (id: string, action: 'approve' | 'reject' | 'revise' | 'escalate') => {
    const notes = actionNotes[id]?.trim() || undefined;
    setPendingAction(id + action);
    
    try {
      await onResolve(id, action, notes);
      toast.success(`Review ${action === 'approve' ? 'approved' : action}`);
      setActionNotes(prev => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } catch (e: any) {
      toast.error(e?.message || `Failed to ${action} review`);
    } finally {
      setPendingAction(null);
    }
  };

  if (isLoading) {
    return <div className="p-6 text-slate-400 text-sm">Loading review queue...</div>;
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-lg">Human Review Queue</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            These tasks were created by agentic workflows when clinical risk or missing information was detected. 
            Approving releases the final output. All actions are audited.
          </p>
        </div>
        <button 
          onClick={onRefresh} 
          className="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {reviews.length === 0 && (
        <div className="text-slate-400 border border-slate-800 rounded-xl p-6 text-sm">
          No pending reviews for your current role. 
          Try running the <b>Discharge Planning</b> workflow as a Care Coordinator.
        </div>
      )}

      {reviews.map((r) => {
        const isPending = r.status === 'pending_review';
        const actionKey = (id: string) => id + (pendingAction?.slice(r.id.length) || '');

        return (
          <div key={r.id} className="review-card">
            <div className="flex justify-between gap-4">
              <div className="min-w-0">
                <div className="font-medium flex items-center gap-2">
                  {r.task_type}
                  {r.priority === 'high' || r.priority === 'critical' ? (
                    <span className="text-[10px] px-1.5 py-px rounded bg-red-900 text-red-300">{r.priority}</span>
                  ) : null}
                </div>
                <div className="text-sm text-slate-400 mt-0.5">{r.reason || 'No reason provided'}</div>
                {r.patient_id && (
                  <div className="text-[10px] text-slate-500 mt-1 font-mono">Patient: {r.patient_id}</div>
                )}
              </div>

              <div className={`text-xs px-3 py-1 rounded-full self-start whitespace-nowrap ${getStatusClass(r.status)}`}>
                {r.status.replace('_', ' ')}
              </div>
            </div>

            {isPending && (
              <div className="mt-4 space-y-3">
                <textarea
                  value={actionNotes[r.id] || ''}
                  onChange={(e) => setActionNotes(prev => ({ ...prev, [r.id]: e.target.value }))}
                  placeholder="Add notes (optional, will be recorded in audit log)..."
                  className="w-full bg-slate-950 border border-slate-700 focus:border-slate-500 rounded-lg px-3 py-2 text-sm placeholder:text-slate-600 resize-y min-h-[60px]"
                  rows={2}
                />

                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleResolve(r.id, 'approve')}
                    disabled={!!pendingAction}
                    className="flex items-center gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 px-4 py-1.5 rounded-lg font-medium transition"
                  >
                    <CheckCircle className="w-3.5 h-3.5" /> Approve
                  </button>

                  <button
                    onClick={() => handleResolve(r.id, 'reject')}
                    disabled={!!pendingAction}
                    className="flex items-center gap-1.5 text-xs bg-red-600 hover:bg-red-500 disabled:opacity-60 px-4 py-1.5 rounded-lg transition"
                  >
                    <XCircle className="w-3.5 h-3.5" /> Reject
                  </button>

                  <button
                    onClick={() => handleResolve(r.id, 'revise')}
                    disabled={!!pendingAction}
                    className="flex items-center gap-1.5 text-xs bg-amber-600 hover:bg-amber-500 disabled:opacity-60 px-4 py-1.5 rounded-lg transition"
                  >
                    <RefreshCw className="w-3.5 h-3.5" /> Request Revision
                  </button>

                  <button
                    onClick={() => handleResolve(r.id, 'escalate')}
                    disabled={!!pendingAction}
                    className="flex items-center gap-1.5 text-xs bg-slate-600 hover:bg-slate-500 disabled:opacity-60 px-4 py-1.5 rounded-lg transition"
                  >
                    <ArrowUp className="w-3.5 h-3.5" /> Escalate
                  </button>
                </div>
              </div>
            )}

            {!isPending && r.resolution_notes && (
              <div className="mt-3 text-xs text-slate-400 pl-1">
                Resolution notes: <span className="text-slate-300">{r.resolution_notes}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function getStatusClass(status: string) {
  switch (status) {
    case 'pending_review': return 'bg-amber-900 text-amber-300';
    case 'approved': return 'bg-emerald-900 text-emerald-300';
    case 'rejected': return 'bg-red-900 text-red-300';
    case 'needs_revision': return 'bg-orange-900 text-orange-300';
    case 'escalated': return 'bg-purple-900 text-purple-300';
    default: return 'bg-slate-700 text-slate-300';
  }
}
