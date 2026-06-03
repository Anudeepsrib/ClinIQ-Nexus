"use client";

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { TopNav } from '@/components/TopNav';
import { UserSidebar } from '@/components/UserSidebar';
import { ChatInterface } from '@/components/ChatInterface';
import { ReviewQueue } from '@/components/ReviewQueue';
import { WorkflowPanel } from '@/components/WorkflowPanel';
import { useAuth } from './hooks/useAuth';
import { api } from '@/lib/api';
import type { ChatMessage } from '@/types/ui';

const EXAMPLE_QUERIES: Record<string, string> = {
  patient: "Can you summarize my recent lab results in simple language?",
  clinician: "Summarize this patient's last 72 hours before rounds.",
  nurse: "Which patients on my floor may need follow-up based on overnight notes?",
  care_coordinator: "Create a discharge readiness summary for Maria Gonzalez.",
  admin: "What are the top reasons for delayed discharge this week?",
  compliance_officer: "Show me any recent high-risk access patterns.",
};

type Tab = 'chat' | 'reviews' | 'workflows';

export default function CareOSClinicalPlatform() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [workflowResult, setWorkflowResult] = useState<any>(null);
  const [chatPrefill, setChatPrefill] = useState<string | undefined>();

  const token = auth.token;
  const currentUser = auth.demoUser;
  const effectiveRole = auth.role;

  // Initialize welcome message when auth state or demo user changes
  useEffect(() => {
    if (auth.isDemoMode && auth.isAuthenticated) {
      setMessages([{
        type: 'system',
        content: `Logged in as ${currentUser.label}. Every response is governed by MCP Context Governance.`,
      }]);
      setWorkflowResult(null);
    } else if (!auth.isDemoMode && auth.isAuthenticated) {
      setMessages([{
        type: 'system',
        content: `Authenticated as ${auth.userName} (${auth.role}). Full governance and audit active.`,
      }]);
    }
  }, [auth.isAuthenticated, auth.isDemoMode, currentUser.label, auth.userName, auth.role]);

  // React Query: Reviews (auto-refreshes on mutation)
  const { 
    data: reviewsData, 
    isLoading: reviewsLoading, 
    refetch: refetchReviews 
  } = useQuery({
    queryKey: ['reviews', token, currentUser.email],
    queryFn: () => api.listReviews(token, currentUser.email),
    enabled: !!token,
    staleTime: 15_000,
  });

  const reviews = reviewsData?.reviews || [];

  // Mutation: Resolve review (approve/reject/revise/escalate)
  const resolveReviewMutation = useMutation({
    mutationFn: ({ id, action, notes }: { id: string; action: 'approve' | 'reject' | 'revise' | 'escalate'; notes?: string }) =>
      api.resolveReview(id, action, { notes }, token, currentUser.email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] });
    },
  });

  // Mutation: Run workflow
  const runWorkflowMutation = useMutation({
    mutationFn: ({ workflow, patientId, query }: { workflow: string; patientId?: string; query: string }) =>
      api.runWorkflow(workflow, {
        patient_id: patientId || 'pat_001',
        query,
      }, token, currentUser.email),
    onSuccess: (data, variables) => {
      setWorkflowResult(data);
      setActiveTab('workflows');

      if (data.review_task_id) {
        // Refresh reviews and switch user to review queue
        queryClient.invalidateQueries({ queryKey: ['reviews'] });
        setTimeout(() => setActiveTab('reviews'), 600);
      }

      toast.success(`${variables.workflow} completed`);
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Workflow failed');
    },
  });

  /* ----------------------------- Handlers ----------------------------- */

  const handleSendMessage = async (query: string) => {
    if (!token) {
      toast.error('Not authenticated');
      return;
    }

    const userMsg: ChatMessage = { type: 'user', content: query };
    setMessages((prev) => [...prev, userMsg]);
    setIsChatLoading(true);

    try {
      const res = await api.sendChat(
        {
          query,
          patient_id: effectiveRole === 'patient' ? 'pat_001' : undefined,
        },
        token,
        currentUser.email
      );

      const assistantMsg: ChatMessage = {
        type: 'assistant',
        content: res.response,
        route: res.route,
        confidence: res.confidence,
        requires_human_review: res.requires_human_review,
        citations: res.citations,
        disclaimer: res.disclaimer,
        safety_flags: res.safety_flags,
        review_task_id: res.human_review_task_id,
        memory_used: res.memory_used,
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // If this created a review task, refresh the queue
      if (res.human_review_task_id) {
        queryClient.invalidateQueries({ queryKey: ['reviews'] });
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          type: 'error',
          content: err?.message || 'API unreachable. Is the backend running?',
        },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleResolveReview = async (id: string, action: 'approve' | 'reject' | 'revise' | 'escalate', notes?: string) => {
    await resolveReviewMutation.mutateAsync({ id, action, notes });
  };

  const handleRunWorkflow = (workflowType: string) => {
    if (!token) return;

    const queryMap: Record<string, string> = {
      'discharge-planning': 'Create discharge readiness summary for Maria Gonzalez',
      'chart-summary': "Summarize this patient’s last 72 hours before rounds",
      'risk-signal': 'Risk signal detection on my patients',
    };

    runWorkflowMutation.mutate({
      workflow: workflowType,
      patientId: 'pat_001',
      query: queryMap[workflowType] || 'Execute workflow',
    });
  };

  const loadExampleQuery = () => {
    const example = EXAMPLE_QUERIES[effectiveRole] || EXAMPLE_QUERIES.patient;
    setActiveTab('chat');
    setChatPrefill(example);
    toast.success('Example prompt loaded');
  };

  const handlePrefillConsumed = () => {
    setChatPrefill(undefined);
  };

  const isLoading = isChatLoading || runWorkflowMutation.isPending;

  /* ----------------------------- Render ----------------------------- */

  return (
    <div className="min-h-screen flex flex-col bg-slate-950">
      <TopNav />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <UserSidebar
          onLoadExample={loadExampleQuery}
          onRunWorkflow={handleRunWorkflow}
          isLoading={isLoading}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Tabs */}
          <div className="flex border-b border-slate-800 bg-slate-900 px-6 shrink-0" role="tablist">
            {(['chat', 'reviews', 'workflows'] as const).map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={activeTab === t}
                onClick={() => setActiveTab(t)}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === t 
                    ? 'border-[#0284c8] text-white' 
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                {t === 'chat' && 'AI Assistant'}
                {t === 'reviews' && `Human Review Queue (${reviews.length})`}
                {t === 'workflows' && 'Agentic Workflows'}
              </button>
            ))}
          </div>

          {/* Tab Panels */}
          {activeTab === 'chat' && (
            <ChatInterface
              messages={messages}
              isLoading={isChatLoading}
              onSend={handleSendMessage}
              placeholder="Ask anything (labs, discharge planning, chest pain concern, general medical question...)"
              prefill={chatPrefill}
              onPrefillConsumed={handlePrefillConsumed}
            />
          )}

          {activeTab === 'reviews' && (
            <ReviewQueue
              reviews={reviews}
              isLoading={reviewsLoading || resolveReviewMutation.isPending}
              onResolve={handleResolveReview}
              onRefresh={() => refetchReviews()}
            />
          )}

          {activeTab === 'workflows' && (
            <WorkflowPanel
              workflowResult={workflowResult}
              isLoading={runWorkflowMutation.isPending}
              currentRole={effectiveRole}
              onRunWorkflow={handleRunWorkflow}
            />
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 text-center py-2 text-[10px] text-slate-500 shrink-0">
        REFERENCE IMPLEMENTATION — Deterministic routing • Mandatory MCP governance • Full audit • Human review state machine • Never for production clinical use
      </footer>
    </div>
  );
}
