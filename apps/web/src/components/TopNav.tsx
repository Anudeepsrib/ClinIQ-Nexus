'use client';

import { Stethoscope, Shield, LogOut } from 'lucide-react';
import { useAuth } from '@/app/hooks/useAuth';

export function TopNav() {
  const auth = useAuth();

  return (
    <div className="border-b border-slate-800 bg-slate-900 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Stethoscope className="w-6 h-6 text-[#0284c8]" aria-hidden />
        <div>
          <div className="font-semibold text-xl tracking-tight">MediCore AI</div>
          <div className="text-[10px] text-slate-500 -mt-1">HIPAA-GRADE CLINICAL AI • ENTERPRISE PLATFORM</div>
        </div>
        <div 
          className={`ml-4 px-2 py-0.5 rounded text-xs font-mono ${auth.isDemoMode ? 'bg-emerald-950 text-emerald-400' : 'bg-cyan-950 text-cyan-400'}`}
          aria-label={auth.isDemoMode ? 'Running in local demo mode' : 'Production mode with AWS Cognito'}
        >
          {auth.isDemoMode ? 'LOCAL DEMO' : 'AWS COGNITO'} • FULL GOVERNANCE ACTIVE
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-slate-400" aria-hidden>
          <Shield className="w-4 h-4" /> MCP Governance • Intent Router • Human-in-the-Loop • Audit
        </div>
        <button 
          onClick={auth.logout}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition px-3 py-1.5 rounded hover:bg-slate-800 focus:outline-none"
          aria-label="Sign out of MediCore AI"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign out</span>
        </button>
      </div>
    </div>
  );
}
