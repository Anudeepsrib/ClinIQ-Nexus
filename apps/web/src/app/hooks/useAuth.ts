"use client";

/**
 * useAuth - Unified authentication hook.
 * 
 * In production (Cognito): Uses NextAuth session to get JWT, role, and tenant info.
 * In demo mode: Falls back to the local /api/v1/auth/login endpoint with mock users.
 */

import { useSession, signIn, signOut } from "next-auth/react";
import { useState, useEffect, useCallback, useMemo } from "react";

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
}

const DEMO_USERS = [
  { email: 'patient@hospital-a.demo', label: 'Maria Gonzalez (Patient)', role: 'patient' },
  { email: 'clinician@hospital-a.demo', label: 'Dr. Sarah Chen (Clinician)', role: 'clinician' },
  { email: 'nurse@hospital-a.demo', label: 'James Rivera, RN (Nurse)', role: 'nurse' },
  { email: 'care_coordinator@hospital-a.demo', label: 'Aisha Patel (Care Coordinator)', role: 'care_coordinator' },
  { email: 'admin@hospital-a.demo', label: 'Robert Kim (Admin)', role: 'admin' },
  { email: 'compliance@hospital-a.demo', label: 'Elena Vasquez (Compliance)', role: 'compliance_officer' },
];

export function useAuth(): AuthState {
  const { data: session, status } = useSession();
  const [demoToken, setDemoToken] = useState<string | null>(null);
  const [demoUser, setDemoUser] = useState(DEMO_USERS[1]);
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Detect demo mode from URL
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      setIsDemoMode(params.get('demo') === 'true' || status === 'unauthenticated');
    }
  }, [status]);

  // Production auth via NextAuth/Cognito
  const cognitoToken = (session as any)?.accessToken || null;
  const cognitoRole = (session as any)?.role || "user";
  const cognitoTenant = (session as any)?.tenantId || "";

  // Demo login
  const demoLogin = useCallback(async (email?: string) => {
    const user = email ? DEMO_USERS.find(u => u.email === email) || DEMO_USERS[1] : demoUser;
    setDemoUser(user);
    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user.email }),
      });
      const data = await res.json();
      setDemoToken(data.access_token);
    } catch {
      console.error('Demo login failed — is the API running?');
    }
  }, [demoUser]);

  // Auto-login in demo mode
  useEffect(() => {
    if (isDemoMode && !demoToken) {
      demoLogin();
    }
  }, [isDemoMode, demoToken, demoLogin]);

  const logout = useCallback(() => {
    if (isDemoMode) {
      setDemoToken(null);
    } else {
      signOut();
    }
  }, [isDemoMode]);

  const prodLogin = useCallback(async () => {
    await signIn("cognito");
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
  };
}

export { DEMO_USERS };
