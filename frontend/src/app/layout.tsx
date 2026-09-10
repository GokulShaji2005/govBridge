import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { ShieldCheck, LayoutDashboard, Activity, Landmark, UserCheck } from "lucide-react";

export const metadata: Metadata = {
  title: "GovBridge — National Single Window Government Gateway",
  description: "Consent-Gated Business Registration & Interoperable Data Exchange",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 min-h-screen flex flex-col antialiased">
        <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-xs px-6 py-3.5">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="p-2.5 bg-indigo-600 rounded-xl text-white shadow-md shadow-indigo-600/20 group-hover:bg-indigo-700 transition-all">
                <Landmark className="w-6 h-6" />
              </div>
              <div>
                <div className="font-extrabold text-xl tracking-tight text-slate-900 flex items-center gap-2">
                  GovBridge <span className="text-xs px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200">National Gateway</span>
                </div>
                <div className="text-xs text-slate-500 font-medium">
                  Consent-Gated Citizen & Business Services
                </div>
              </div>
            </Link>

            <nav className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-2xl border border-slate-200">
              <Link
                href="/apply"
                className="flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl bg-white text-indigo-600 shadow-xs border border-slate-200/80 hover:text-indigo-700 transition-all"
              >
                <ShieldCheck className="w-4 h-4 text-indigo-600" />
                Citizen Portal
              </Link>
              <Link
                href="/officer"
                className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl hover:bg-white/60 text-slate-600 hover:text-slate-900 transition-colors"
              >
                <LayoutDashboard className="w-4 h-4 text-slate-500" />
                Officer Dashboard
              </Link>
              <Link
                href="/monitor"
                className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl hover:bg-white/60 text-slate-600 hover:text-slate-900 transition-colors"
              >
                <Activity className="w-4 h-4 text-slate-500" />
                System Status
              </Link>
            </nav>
          </div>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          {children}
        </main>

        <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500 mt-auto">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between px-6 gap-2">
            <div>GovBridge Unified Interoperability Gateway &copy; 2026 — Government Data Exchange Platform</div>
            <div className="flex gap-4 text-slate-400">
              <span>Consent-Gated</span>
              <span>•</span>
              <span>Aadhaar eKYC Enabled</span>
              <span>•</span>
              <span>Single Window Registration</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
