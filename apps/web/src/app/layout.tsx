import type { Metadata } from "next";
import "./globals.css";
import { QueryClientProvider } from "./providers";

export const metadata: Metadata = {
  title: "ClinIQ-Nexus | Clinical AI Platform",
  description: "Safe, governed AI for hospitals. All clinical outputs require human review.",
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
