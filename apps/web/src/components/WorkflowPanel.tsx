'use client';

import { Play, AlertCircle } from 'lucide-react';
import type { WorkflowResponse } from '@/types/api';

interface WorkflowPanelProps {
  workflowResult: WorkflowResponse | null;
  isLoading: boolean;
  currentRole: string;
  onRunWorkflow: (type: string) => void;
}

const WORKFLOWS = [
  {
    id: 'discharge-planning',
    title: 'Discharge Planning Agent',
    description: 'Retrieves governed data → detects blockers → drafts summary → creates Human Review Task when items are missing.',
    roles: ['care_coordinator'],
    color: 'amber',
  },
  {
    id: 'chart-summary',
    title: '72h Clinician Chart Summary',
    description: 'LangGraph agent that pulls vitals, labs, notes, meds, and consults with citations.',
    roles: ['clinician'],
    color: 'blue',
  },
  {
    id: 'risk-signal',
    title: 'Clinical Risk Signal Detection',
    description: 'Overnight risk signal detection on assigned patients.',
    roles: ['nurse'],
    color: 'red',
  },
];

export function WorkflowPanel({ workflowResult, isLoading, currentRole, onRunWorkflow }: WorkflowPanelProps) {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h3 className="font-semibold text-lg">Agentic Workflows (LangGraph)</h3>
        <p className="text-sm text-slate-400 mt-1">
          These are real multi-step state machines with human review gates — not simple prompts.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {WORKFLOWS.map((wf) => {
          const allowed = wf.roles.includes(currentRole);
          return (
            <div 
              key={wf.id} 
              className={`border border-slate-700 rounded-xl p-5 ${!allowed ? 'opacity-60' : ''}`}
            >
              <div className="font-medium mb-1 flex items-center gap-2">
                {wf.title}
                {!allowed && <span className="text-[10px] text-slate-500">(role restricted)</span>}
              </div>
              <div className="text-xs text-slate-400 mb-4 leading-relaxed">{wf.description}</div>

              <button
                onClick={() => onRunWorkflow(wf.id)}
                disabled={isLoading || !allowed}
                className={`text-xs px-4 py-2 rounded flex items-center gap-2 transition disabled:opacity-50
                  ${wf.color === 'amber' ? 'bg-amber-600 hover:bg-amber-700' : ''}
                  ${wf.color === 'blue' ? 'bg-blue-600 hover:bg-blue-700' : ''}
                  ${wf.color === 'red' ? 'bg-red-600 hover:bg-red-700' : ''}
                `}
              >
                <Play className="w-3.5 h-3.5" /> Run {wf.title.split(' ')[0]} Workflow
              </button>
            </div>
          );
        })}
      </div>

      {workflowResult && (
        <div className="bg-slate-900 border border-slate-700 p-5 rounded-xl">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-3">
            <AlertCircle className="w-4 h-4" /> WORKFLOW RESULT
          </div>
          <pre className="whitespace-pre-wrap text-xs text-slate-200 overflow-auto max-h-[420px] bg-black/30 p-4 rounded-lg">
            {JSON.stringify(workflowResult, null, 2)}
          </pre>
          <p className="text-[10px] text-slate-500 mt-2">
            In production this view would render a structured clinical summary with provenance.
          </p>
        </div>
      )}
    </div>
  );
}
