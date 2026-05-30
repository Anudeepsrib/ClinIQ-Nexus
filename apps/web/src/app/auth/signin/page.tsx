"use client";

import { signIn } from "next-auth/react";
import { Stethoscope, Shield, Lock } from "lucide-react";

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="max-w-md w-full mx-auto">
        {/* Logo & Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 mb-4">
            <Stethoscope className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            MediCore AI
          </h1>
          <p className="text-slate-400 text-sm mt-2">
            Enterprise Clinical Intelligence Platform
          </p>
        </div>

        {/* Sign-in Card */}
        <div className="bg-slate-900/80 backdrop-blur border border-slate-800 rounded-2xl p-8 shadow-2xl shadow-cyan-500/5">
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-200 text-center">
              Sign in to your account
            </h2>
            <p className="text-xs text-slate-400 text-center">
              Authenticate with your hospital identity provider via AWS Cognito
            </p>

            {/* Cognito SSO Button */}
            <button
              onClick={() => signIn("cognito", { callbackUrl: "/" })}
              className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium py-3 px-6 rounded-xl transition-all duration-200 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30"
            >
              <Lock className="w-4 h-4" />
              Sign in with Hospital SSO
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3 my-4">
              <div className="flex-1 h-px bg-slate-700" />
              <span className="text-xs text-slate-500">or for local development</span>
              <div className="flex-1 h-px bg-slate-700" />
            </div>

            {/* Demo mode link */}
            <a
              href="/?demo=true"
              className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium py-3 px-6 rounded-xl transition-all duration-200 border border-slate-700 text-sm"
            >
              Continue in Demo Mode
            </a>
          </div>

          {/* Compliance badge */}
          <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-center gap-2 text-[10px] text-slate-500">
            <Shield className="w-3 h-3" />
            HIPAA-conscious • SOC 2 aligned • End-to-end encryption
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[10px] text-slate-600 mt-6">
          All clinical outputs require licensed human review.<br />
          MediCore AI never diagnoses, prescribes, or makes final clinical decisions.
        </p>
      </div>
    </div>
  );
}
