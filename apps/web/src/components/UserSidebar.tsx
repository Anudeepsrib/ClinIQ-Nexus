'use client';

import { User, Shield } from 'lucide-react';
import { useAuth, DEMO_USERS } from '@/app/hooks/useAuth';

interface UserSidebarProps {
  onLoadExample: () => void;
  onRunWorkflow?: (type: string) => void;
  isLoading?: boolean;
}

export function UserSidebar({ onLoadExample, onRunWorkflow, isLoading }: UserSidebarProps) {
  const auth = useAuth();
  const { demoUser, setDemoUser, isDemoMode } = auth;

  return (
    <div className="w-72 border-r border-slate-800 bg-slate-900 p-4 space-y-4 overflow-y-auto">
      <div>
        <div className="text-xs uppercase tracking-widest text-slate-500 mb-2 flex items-center gap-1.5">
          <User className="w-3 h-3" /> DEMO USER (SWITCH ANYTIME)
        </div>
        
        {DEMO_USERS.map((u) => (
          <button
            key={u.email}
            onClick={() => {
              if (isDemoMode) {
                setDemoUser(u);
              }
            }}
            disabled={!isDemoMode}
            className={`w-full text-left px-3 py-2 rounded text-sm mb-1 flex items-center gap-2 transition ${
              demoUser.email === u.email 
                ? 'bg-[#0284c8] text-white' 
                : 'hover:bg-slate-800 disabled:opacity-60'
            }`}
            aria-current={demoUser.email === u.email ? 'true' : undefined}
          >
            <User className="w-4 h-4 flex-shrink-0" aria-hidden />
            <span className="truncate">{u.label}</span>
          </button>
        ))}
      </div>

      <div className="pt-3 border-t border-slate-800 space-y-2">
        <button
          onClick={onLoadExample}
          className="w-full text-xs bg-slate-800 hover:bg-slate-700 py-2 rounded transition"
        >
          Load canonical example for this role
        </button>

        {/* Workflow shortcuts - role gated */}
        {demoUser.role === 'care_coordinator' && (
          <button
            onClick={() => onRunWorkflow?.('discharge-planning')}
            disabled={isLoading}
            className="w-full text-xs bg-amber-600 hover:bg-amber-700 disabled:opacity-50 py-2 rounded flex items-center justify-center gap-2 transition"
          >
            Run Discharge Planning Workflow
          </button>
        )}

        {demoUser.role === 'clinician' && (
          <button
            onClick={() => onRunWorkflow?.('chart-summary')}
            disabled={isLoading}
            className="w-full text-xs bg-blue-600 hover:bg-blue-700 disabled:opacity-50 py-2 rounded transition"
          >
            Run 72h Chart Summary Agent
          </button>
        )}

        {demoUser.role === 'nurse' && (
          <button
            onClick={() => onRunWorkflow?.('risk-signal')}
            disabled={isLoading}
            className="w-full text-xs bg-red-600 hover:bg-red-700 disabled:opacity-50 py-2 rounded transition"
          >
            Run Clinical Risk Signal Agent
          </button>
        )}
      </div>

      <div className="text-[10px] text-slate-500 pt-4 leading-snug border-t border-slate-800">
        Every query goes through: <b>Deterministic Intent Router</b> → <b>MCP Governance</b> → <b>Safe Generation</b>.
        <br /><br />
        Clinical-risk workflows create real Human Review Tasks that block final output until approved.
      </div>

      <div className="pt-2 text-[10px] text-emerald-400/70 flex items-center gap-1.5">
        <Shield className="w-3 h-3" /> Tenant isolation + full audit trail active
      </div>
    </div>
  );
}
