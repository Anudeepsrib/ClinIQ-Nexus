import type { Metadata } from "next";
import "./globals.css";
import { QueryClientProvider } from "./providers";
import { ErrorBoundary } from "../components/ErrorBoundary";

export const metadata: Metadata = {
  title: "careOS | Enterprise Clinical Intelligence Platform",
  description: "HIPAA-conscious, multi-tenant clinical AI platform. All clinical outputs require licensed human review.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-200">
        <QueryClientProvider>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </QueryClientProvider>
      </body>
    </html>
  );
}
