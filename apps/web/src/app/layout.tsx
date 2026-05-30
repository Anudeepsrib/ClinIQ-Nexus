import type { Metadata } from "next";
import "./globals.css";
import { QueryClientProvider } from "./providers";

export const metadata: Metadata = {
  title: "MediCore AI | Enterprise Clinical Intelligence Platform",
  description: "HIPAA-conscious, multi-tenant clinical AI platform. All clinical outputs require licensed human review.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-200">
        <QueryClientProvider>{children}</QueryClientProvider>
      </body>
    </html>
  );
}
