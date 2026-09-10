import Link from "next/link";
import { ShieldCheck, RefreshCw, LayoutDashboard, Activity, FileCheck, ArrowRight, Zap, CheckCircle2, AlertTriangle } from "lucide-react";

export default function Home() {
  return (
    <div className="space-y-10 py-4">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-900/40 via-indigo-900/30 to-purple-900/40 border border-blue-500/20 p-8 md:p-12 glass-panel">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-400/30 text-blue-300 text-xs font-semibold uppercase tracking-wider">
            <Zap className="w-3.5 h-3.5" /> Hackathon Core Demo
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Interoperable Government Data Exchange & Consent Gateway
          </h1>
          <p className="text-slate-300 text-base md:text-lg leading-relaxed">
            Eliminating redundant citizen verification across disparate municipal, identity, and tax systems using protocol adapters and purpose-gated consent.
          </p>
        </div>
      </div>

      {/* Main Acts & Tools Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Act 1 Card */}
        <Link href="/apply?act=1" className="group rounded-2xl glass-panel p-6 glass-panel-hover flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Act 1 Demo</span>
              <h3 className="text-xl font-bold text-white mt-1 group-hover:text-blue-300 transition-colors">
                Business Registration
              </h3>
              <p className="text-slate-400 text-sm mt-2 leading-relaxed">
                Full 4-step orchestration: Identity (JSON), Tax (Raw XML), Address (Legacy Dict), & Business Registry.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-blue-400 group-hover:translate-x-1 transition-transform">
            Start Application <ArrowRight className="w-4 h-4" />
          </div>
        </Link>

        {/* Act 2 Card */}
        <Link href="/apply?act=2" className="group rounded-2xl glass-panel p-6 glass-panel-hover flex flex-col justify-between space-y-6 border-emerald-500/20">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-110 transition-transform">
              <RefreshCw className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Act 2 Demo</span>
              <h3 className="text-xl font-bold text-white mt-1 group-hover:text-emerald-300 transition-colors">
                Trade License Reuse
              </h3>
              <p className="text-slate-400 text-sm mt-2 leading-relaxed">
                Re-uses pre-verified credentials for same citizen ID with single-click authorization.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-emerald-400 group-hover:translate-x-1 transition-transform">
            Authorize Reuse <ArrowRight className="w-4 h-4" />
          </div>
        </Link>

        {/* Officer Dashboard */}
        <Link href="/officer" className="group rounded-2xl glass-panel p-6 glass-panel-hover flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
              <LayoutDashboard className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-purple-400">Audit & Control</span>
              <h3 className="text-xl font-bold text-white mt-1 group-hover:text-purple-300 transition-colors">
                Officer Dashboard
              </h3>
              <p className="text-slate-400 text-sm mt-2 leading-relaxed">
                Inspect cross-department verification statuses and immutable timestamped audit trails.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-purple-400 group-hover:translate-x-1 transition-transform">
            View Applications <ArrowRight className="w-4 h-4" />
          </div>
        </Link>

        {/* System Monitor */}
        <Link href="/monitor" className="group rounded-2xl glass-panel p-6 glass-panel-hover flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 group-hover:scale-110 transition-transform">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Resilience Demo</span>
              <h3 className="text-xl font-bold text-white mt-1 group-hover:text-amber-300 transition-colors">
                System Monitor
              </h3>
              <p className="text-slate-400 text-sm mt-2 leading-relaxed">
                Simulate Municipality failure toggle (Stage 11) and view health metrics live.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-amber-400 group-hover:translate-x-1 transition-transform">
            Monitor Health <ArrowRight className="w-4 h-4" />
          </div>
        </Link>
      </div>
    </div>
  );
}
