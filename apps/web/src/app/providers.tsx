"use client";

import { QueryClient, QueryClientProvider as TanstackProvider } from "@tanstack/react-query";
import { SessionProvider } from "next-auth/react";
import { useState } from "react";

export function QueryClientProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <SessionProvider>
      <TanstackProvider client={queryClient}>{children}</TanstackProvider>
    </SessionProvider>
  );
}
