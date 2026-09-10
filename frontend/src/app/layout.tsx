import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { ShieldCheck, LayoutDashboard, Activity, FileCode, Landmark } from "lucide-react";

export const metadata: Metadata = {
  title: "GovBridge — Interoperable Government Data Exchange",
  description: "Unified Data Exchange & Consent-Gated Citizen Service Architecture",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col">
        <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="p-2.5 bg-blue-600/20 border border-blue-500/40 rounded-xl text-blue-400 group-hover:bg-blue-600/30 transition-all">
                <Landmark className="w-6 h-6" />
              </div>
              <div>
                <div className="font-bold text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-blue-400 bg-clip-text text-transparent">
                  GovBridge
                </div>
                <div className="text-xs text-blue-400/80 font-medium">
                  Protocol Adapter & Consent Gateway
                </div>
              </div>
            </Link>

            <nav className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
              <Link
                href="/apply"
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
              >
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Citizen Portal
              </Link>
              <Link
                href="/officer"
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
              >
                <LayoutDashboard className="w-4 h-4 text-blue-400" />
                Officer Dashboard
              </Link>
              <Link
                href="/monitor"
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
              >
                <Activity className="w-4 h-4 text-purple-400" />
                System Monitor
              </Link>
            </nav>
          </div>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          {children}
        </main>

        <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 glass-panel mt-auto">
          GovBridge Interoperability Platform &copy; 2026 — Demonstrating REST, Raw XML & Legacy Protocol Normalization
        </footer>
      </body>
    </html>
  );
}
