"use client";

import React, { useState } from 'react';
import { Stethoscope, User, Shield, AlertTriangle, Clock, CheckCircle, XCircle, LogOut } from 'lucide-react';
import { useAuth, DEMO_USERS } from './hooks/useAuth';

const EXAMPLE_QUERIES: Record<string, string> = {
  patient: "Can you summarize my recent lab results in simple language?",
  clinician: "Summarize this patient's last 72 hours before rounds.",
  nurse: "Which patients on my floor may need follow-up based on overnight notes?",
  care_coordinator: "Create a discharge readiness summary for Maria Gonzalez.",
  admin: "What are the top reasons for delayed discharge this week?",
  compliance_officer: "Show me any recent high-risk access patterns.",
};

type Tab = 'chat' | 'reviews' | 'workflows';

export default function ClinIQNexusDemo() {
  const auth = useAuth();
  const [selectedUser, setSelectedUser] = useState(DEMO_USERS[1]);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [reviews, setReviews] = useState<any[]>([]);
  const [workflowResult, setWorkflowResult] = useState<any>(null);

  // Derive effective token and role from unified auth
  const token = auth.token;
  const effectiveRole = auth.isDemoMode ? selectedUser.role : auth.role;

  React.useEffect(() => {
    if (auth.isDemoMode) {
      // Demo mode: switch user via local API
      const login = async () => {
        await auth.login(selectedUser.email);
        setMessages([{ type: 'system', content: `Logged in as ${selectedUser.label}. Every response is governed by MCP.` }]);
        setWorkflowResult(null);
      };
      login();
    } else if (auth.isAuthenticated) {
      // Production mode: session is active
      setMessages([{ type: 'system', content: `Authenticated as ${auth.userName} (${auth.role}). Full governance active.` }]);
    }
  }, [selectedUser, auth.isAuthenticated]);

  React.useEffect(() => {
    if (token) loadReviews(token);
  }, [token]);

  const loadReviews = async (tkn?: string) => {
    const useToken = tkn || token;
    if (!useToken) return;
    const res = await fetch('http://localhost:8000/api/v1/reviews/', {
      headers: { Authorization: `Bearer ${useToken}`, 'X-Demo-User': selectedUser.email },
    });
    const data = await res.json();
    setReviews(data.reviews || []);
  };

  const sendMessage = async () => {
    if (!query.trim() || !token) return;
    const userMessage = { type: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/v1/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, 'X-Demo-User': selectedUser.email },
        body: JSON.stringify({ query, patient_id: selectedUser.role === 'patient' ? 'pat_001' : undefined }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        type: 'assistant', content: data.response, route: data.route, confidence: data.confidence,
        requires_human_review: data.requires_human_review, citations: data.citations || [],
        disclaimer: data.disclaimer, safety_flags: data.safety_flags, review_task_id: data.human_review_task_id,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { type: 'error', content: 'API unreachable. Is docker compose running?' }]);
    } finally {
      setIsLoading(false);
      setQuery("");
    }
  };

  const runDischargeWorkflow = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/workflows/discharge-planning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, 'X-Demo-User': selectedUser.email },
        body: JSON.stringify({ patient_id: 'pat_001', query: 'Create discharge readiness summary for Maria Gonzalez' }),
      });
      const data = await res.json();
      setWorkflowResult(data);
      if (data.review_task_id) {
        await loadReviews();
        setActiveTab('reviews');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const approveReview = async (id: string) => {
    if (!token) return;
    await fetch(`http://localhost:8000/api/v1/reviews/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, 'X-Demo-User': selectedUser.email },
      body: JSON.stringify({ notes: 'Approved in demo UI' }),
    });
    await loadReviews();
  };

  const loadExample = () => setQuery(EXAMPLE_QUERIES[selectedUser.role] || EXAMPLE_QUERIES.patient);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950">
      <div className="border-b border-slate-800 bg-slate-900 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Stethoscope className="w-6 h-6 text-[#0284c8]" />
          <div>
            <div className="font-semibold text-xl tracking-tight">MediCore AI</div>
            <div className="text-[10px] text-slate-500 -mt-1">HIPAA-GRADE CLINICAL AI • ENTERPRISE PLATFORM</div>
          </div>
          <div className={`ml-4 px-2 py-0.5 rounded text-xs font-mono ${auth.isDemoMode ? 'bg-emerald-950 text-emerald-400' : 'bg-cyan-950 text-cyan-400'}`}>
            {auth.isDemoMode ? 'LOCAL DEMO' : 'AWS COGNITO'} • FULL GOVERNANCE ACTIVE
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Shield className="w-4 h-4" /> MCP Governance • Intent Router • Human-in-the-Loop • Audit
          </div>
          <button onClick={auth.logout} className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition px-2 py-1 rounded hover:bg-slate-800">
            <LogOut className="w-3 h-3" /> Sign out
          </button>
        </div>
      </div>

      <div className="flex flex-1">
        {/* Sidebar */}
        <div className="w-72 border-r border-slate-800 bg-slate-900 p-4 space-y-4">
          <div>
            <div className="text-xs uppercase tracking-widest text-slate-500 mb-2">DEMO USER (SWITCH ANYTIME)</div>
            {DEMO_USERS.map(u => (
              <button key={u.email} onClick={() => setSelectedUser(u)}
                className={`w-full text-left px-3 py-2 rounded text-sm mb-1 flex items-center gap-2 transition ${selectedUser.email === u.email ? 'bg-[#0284c8] text-white' : 'hover:bg-slate-800'}`}>
                <User className="w-4 h-4" /> {u.label}
              </button>
            ))}
          </div>

          <div className="pt-3 border-t border-slate-800 space-y-2">
            <button onClick={loadExample} className="w-full text-xs bg-slate-800 hover:bg-slate-700 py-2 rounded">Load canonical example for this role</button>
            {selectedUser.role === 'care_coordinator' && (
              <button onClick={runDischargeWorkflow} disabled={isLoading}
                className="w-full text-xs bg-amber-600 hover:bg-amber-700 py-2 rounded flex items-center justify-center gap-2">
                Run Real LangGraph Discharge Workflow
              </button>
            )}

            {selectedUser.role === 'clinician' && (
              <button 
                onClick={async () => {
                  if (!token) return;
                  setIsLoading(true);
                  const res = await fetch('http://localhost:8000/api/v1/workflows/chart-summary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, 'X-Demo-User': selectedUser.email },
                    body: JSON.stringify({ patient_id: 'pat_001', query: 'Summarize this patient’s last 72 hours before rounds' }),
                  });
                  const data = await res.json();
                  setWorkflowResult(data);
                  setActiveTab('workflows');
                  setIsLoading(false);
                }}
                disabled={isLoading}
                className="w-full text-xs bg-blue-600 hover:bg-blue-700 py-2 rounded">
                Run 72h Chart Summary Agent
              </button>
            )}

            {selectedUser.role === 'nurse' && (
              <button 
                onClick={async () => {
                  if (!token) return;
                  setIsLoading(true);
                  const res = await fetch('http://localhost:8000/api/v1/workflows/risk-signal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, 'X-Demo-User': selectedUser.email },
                    body: JSON.stringify({ patient_id: 'pat_001', query: 'Risk signal detection on my patients' }),
                  });
                  const data = await res.json();
                  setWorkflowResult(data);
                  setActiveTab('workflows');
                  setIsLoading(false);
                }}
                disabled={isLoading}
                className="w-full text-xs bg-red-600 hover:bg-red-700 py-2 rounded">
                Run Clinical Risk Signal Agent
              </button>
            )}
          </div>

          <div className="text-[10px] text-slate-500 pt-4 leading-snug">
            Every query goes through: <b>Deterministic Intent Router</b> → <b>MCP Governance</b> → <b>Safe Generation</b>.<br /><br />
            Clinical-risk workflows create real Human Review Tasks that block final output.
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Tabs */}
          <div className="flex border-b border-slate-800 bg-slate-900 px-6">
            {(['chat', 'reviews', 'workflows'] as Tab[]).map(t => (
              <button key={t} onClick={() => setActiveTab(t)}
                className={`px-6 py-3 text-sm font-medium border-b-2 ${activeTab === t ? 'border-[#0284c8] text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
                {t === 'chat' && 'AI Assistant'}
                {t === 'reviews' && `Human Review Queue (${reviews.length})`}
                {t === 'workflows' && 'Agentic Workflows'}
              </button>
            ))}
          </div>

          {/* CHAT TAB */}
          {activeTab === 'chat' && (
            <>
              <div className="flex-1 overflow-auto p-6 chat-container space-y-6" style={{ maxHeight: 'calc(100vh - 260px)' }}>
                {messages.map((m, i) => (
                  <div key={i} className={m.type === 'user' ? 'text-right' : ''}>
                    {m.type === 'system' && <div className="text-xs bg-slate-900 border border-slate-700 p-3 rounded">{m.content}</div>}
                    {m.type === 'user' && <div className="inline-block bg-[#0284c8] text-white px-4 py-2 rounded-2xl rounded-tr-none max-w-[70%]">{m.content}</div>}
                    {m.type === 'assistant' && (
                      <div className="max-w-3xl text-left">
                        <div className="flex items-center gap-2 mb-1 text-xs">
                          <span className="font-mono bg-slate-800 px-2 py-0.5 rounded">{m.route}</span>
                          <span className="text-emerald-400">conf {Math.round((m.confidence || 0) * 100)}%</span>
                          {m.requires_human_review && <span className="flex items-center gap-1 text-amber-400"><Clock className="w-3 h-3"/> REQUIRES HUMAN REVIEW</span>}
                          {m.safety_flags?.length > 0 && <span className="text-red-400 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> {m.safety_flags.join(', ')}</span>}
                        </div>
                        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl rounded-tl-none whitespace-pre-wrap text-sm leading-relaxed">{m.content}</div>
                        {m.disclaimer && <div className="mt-2 text-xs text-slate-400 italic">{m.disclaimer}</div>}
                        {m.citations?.length > 0 && (
                          <div className="mt-2">
                            <div className="text-xs text-slate-400 mb-1">Citations (from authorized records only):</div>
                            {m.citations.map((c: any, idx: number) => (
                              <div key={idx} className="citation mb-1 text-xs">[{c.doc_type}] {c.snippet}</div>
                            ))}
                          </div>
                        )}
                        {m.review_task_id && <div className="mt-2 text-xs text-amber-400">Human Review Task created: {m.review_task_id} (see Review Queue tab)</div>}
                        {m.memory_used && <div className="mt-1 text-xs text-purple-400">Governed memory preference applied</div>}
                      </div>
                    )}
                  </div>
                ))}
                {isLoading && <div className="text-slate-400 text-sm">Thinking with full governance...</div>}
              </div>
              <div className="p-4 border-t border-slate-800 bg-slate-900">
                <div className="flex gap-2">
                  <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
                    placeholder="Ask anything (labs, discharge, chest pain concern, general medical question...)" className="flex-1 bg-slate-950 border border-slate-700 focus:border-[#0284c8] rounded-xl px-5 py-3 text-sm outline-none" />
                  <button onClick={sendMessage} disabled={!query.trim() || isLoading} className="px-8 rounded-xl bg-white text-slate-950 font-medium disabled:opacity-50">Send</button>
                </div>
                <div className="text-[10px] text-center text-slate-500 mt-2">This is a reference implementation. Never for clinical use without formal validation and compliance sign-off.</div>
              </div>
            </>
          )}

          {/* REVIEWS TAB */}
          {activeTab === 'reviews' && (
            <div className="p-6 space-y-4">
              <h3 className="font-semibold text-lg">Human Review Queue</h3>
              <p className="text-sm text-slate-400">These tasks were created by agentic workflows when clinical risk or missing information was detected. Approving them releases the final output.</p>
              {reviews.length === 0 && <div className="text-slate-400">No pending reviews for your role. Try running the Discharge Planning workflow as a Care Coordinator.</div>}
              {reviews.map(r => (
                <div key={r.id} className="review-card">
                  <div className="flex justify-between">
                    <div>
                      <div className="font-medium">{r.task_type}</div>
                      <div className="text-sm text-slate-400">{r.reason}</div>
                    </div>
                    <div className={`text-xs px-3 py-1 rounded-full self-start ${r.status === 'pending_review' ? 'bg-amber-900 text-amber-300' : 'bg-emerald-900 text-emerald-300'}`}>{r.status}</div>
                  </div>
                  {r.status === 'pending_review' && (
                    <div className="mt-3 flex gap-2">
                      <button onClick={() => approveReview(r.id)} className="flex items-center gap-1 text-xs bg-emerald-600 px-3 py-1 rounded"><CheckCircle className="w-3 h-3"/> Approve</button>
                      <button className="flex items-center gap-1 text-xs bg-red-600 px-3 py-1 rounded"><XCircle className="w-3 h-3"/> Reject</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* WORKFLOWS TAB */}
          {activeTab === 'workflows' && (
            <div className="p-6 space-y-6">
              <div>
                <h3 className="font-semibold text-lg">Agentic Workflows (LangGraph)</h3>
                <p className="text-sm text-slate-400 mt-1">These are real multi-step state machines with human review gates — not simple prompts.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-slate-700 rounded-xl p-5">
                  <div className="font-medium mb-1">Discharge Planning Agent</div>
                  <div className="text-xs text-slate-400 mb-3">Retrieves governed data → detects blockers → drafts summary → creates Human Review Task when items are missing.</div>
                  <button onClick={runDischargeWorkflow} disabled={isLoading || selectedUser.role !== 'care_coordinator'} className="bg-amber-600 text-xs px-4 py-2 rounded disabled:opacity-50">
                    Run Discharge Workflow (Care Coordinator only)
                  </button>
                </div>
                <div className="border border-slate-700 rounded-xl p-5 opacity-60">
                  <div className="font-medium mb-1">72h Clinician Chart Summary (coming next)</div>
                  <div className="text-xs">LangGraph agent that pulls vitals, labs, notes, meds, and consults with citations.</div>
                </div>
              </div>

              {workflowResult && (
                <div className="bg-slate-900 border border-slate-700 p-5 rounded-xl text-sm">
                  <div className="font-mono text-xs mb-2">WORKFLOW RESULT</div>
                  <pre className="whitespace-pre-wrap text-slate-200">{JSON.stringify(workflowResult, null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="bg-slate-900 border-t border-slate-800 text-center py-2 text-[10px] text-slate-500">
        REFERENCE IMPLEMENTATION — Deterministic routing • Mandatory MCP governance • Full audit • Human review state machine • Never for production clinical use
      </div>
    </div>
  );
}
