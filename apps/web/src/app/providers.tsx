"use client";

import { QueryClient, QueryClientProvider as TanstackProvider } from "@tanstack/react-query";
import { SessionProvider } from "next-auth/react";
import { useState } from "react";
import { Toaster } from "sonner";

export function QueryClientProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
        staleTime: 30_000,
      },
      mutations: {
        retry: 0,
      },
    },
  }));

  return (
    <SessionProvider>
      <TanstackProvider client={queryClient}>
        {children}
        <Toaster 
          position="top-center" 
          richColors 
          closeButton 
          theme="dark"
          className="sonner-toaster"
        />
      </TanstackProvider>
    </SessionProvider>
  );
}
