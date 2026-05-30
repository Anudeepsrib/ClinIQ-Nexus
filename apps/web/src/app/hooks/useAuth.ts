"use client";

/**
 * useAuth - Unified authentication hook for MediCore AI.
 *
 * Production: NextAuth + Cognito (JWT passthrough)
 * Demo: Local mock users via platform-api /auth/login
 *
 * This hook is intentionally kept simple. For production SSO hardening,
 * consider adding token refresh observers and automatic logout on 401.
 */

import { useSession, signIn, signOut } from "next-auth/react";
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

export interface DemoUser {
  email: string;
  label: string;
  role: string;
}

export const DEMO_USERS: DemoUser[] = [
  { email: 'patient@hospital-a.demo', label: 'Maria Gonzalez (Patient)', role: 'patient' },
  { email: 'clinician@hospital-a.demo', label: 'Dr. Sarah Chen (Clinician)', role: 'clinician' },
  { email: 'nurse@hospital-a.demo', label: 'James Rivera, RN (Nurse)', role: 'nurse' },
  { email: 'care_coordinator@hospital-a.demo', label: 'Aisha Patel (Care Coordinator)', role: 'care_coordinator' },
  { email: 'admin@hospital-a.demo', label: 'Robert Kim (Admin)', role: 'admin' },
  { email: 'compliance@hospital-a.demo', label: 'Elena Vasquez (Compliance)', role: 'compliance_officer' },
];

interface AuthState {
  token: string | null;
  role: string;
  tenantId: string;
  userName: string;
  isAuthenticated: boolean;
  isLoading: boolean;
  isDemoMode: boolean;
  login: (email?: string) => Promise<void>;
  logout: () => void;
  /** Current demo user (only meaningful in demo mode) */
  demoUser: DemoUser;
  setDemoUser: (u: DemoUser) => void;
}

export function useAuth(): AuthState {
  const { data: session, status } = useSession();

  const [demoToken, setDemoToken] = useState<string | null>(null);
  const [demoUser, setDemoUserState] = useState<DemoUser>(DEMO_USERS[1]);
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Detect demo mode (URL flag or unauthenticated in dev)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const forcedDemo = params.get('demo') === 'true';
      setIsDemoMode(forcedDemo || status === 'unauthenticated');
    }
  }, [status]);

  // Production (Cognito via NextAuth)
  const cognitoToken = (session as any)?.accessToken || null;
  const cognitoRole = (session as any)?.role || "user";
  const cognitoTenant = (session as any)?.tenantId || "";

  // Demo login using centralized client
  const demoLogin = useCallback(async (email?: string) => {
    const user = email
      ? DEMO_USERS.find((u) => u.email === email) || DEMO_USERS[1]
      : demoUser;

    setDemoUserState(user);

    try {
      const data = await api.demoLogin(user.email);
      setDemoToken(data.access_token);
    } catch (err) {
      console.error('[useAuth] Demo login failed:', err);
      // Keep UI functional even if backend is down
    }
  }, [demoUser]);

  // Auto-login when entering demo mode
  useEffect(() => {
    if (isDemoMode && !demoToken) {
      demoLogin();
    }
  }, [isDemoMode, demoToken, demoLogin]);

  const logout = useCallback(() => {
    if (isDemoMode) {
      setDemoToken(null);
      // Optional: clear local demo state
    } else {
      // For real Cognito, you may want to pass id_token_hint + post_logout_redirect_uri
      signOut({ callbackUrl: '/auth/signin' });
    }
  }, [isDemoMode]);

  const prodLogin = useCallback(async () => {
    await signIn("cognito", { callbackUrl: "/" });
  }, []);

  return {
    token: isDemoMode ? demoToken : cognitoToken,
    role: isDemoMode ? demoUser.role : cognitoRole,
    tenantId: isDemoMode ? "tenant_hospital_a" : cognitoTenant,
    userName: isDemoMode ? demoUser.label : (session?.user?.name || "Unknown"),
    isAuthenticated: isDemoMode ? !!demoToken : status === "authenticated",
    isLoading: status === "loading",
    isDemoMode,
    login: isDemoMode ? demoLogin : prodLogin,
    logout,
    demoUser,
    setDemoUser: setDemoUserState,
  };
}

export { DEMO_USERS as DEMO_USERS_CONST }; // for backward compat if anything imports it
