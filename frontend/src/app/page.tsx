import Link from "next/link";
import { ShieldCheck, RefreshCw, LayoutDashboard, Activity, ArrowRight, Zap, Building2, CheckCircle2, Lock } from "lucide-react";

export default function Home() {
  return (
    <div className="space-y-10 py-4">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900 via-indigo-800 to-blue-900 border border-indigo-700/30 p-8 md:p-12 text-white shadow-xl shadow-indigo-900/10">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-indigo-200 text-xs font-bold uppercase tracking-wider backdrop-blur-md">
            <Zap className="w-3.5 h-3.5 text-amber-300" /> National Single Window Gateway
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight">
            Consent-Gated Business Registration Portal
          </h1>
          <p className="text-indigo-100 text-base md:text-lg leading-relaxed">
            Register your business, trade licenses, and permits with one-click credential reuse. Powered by identity resolution and Aadhaar eKYC verification.
          </p>
        </div>
      </div>

      {/* Main Services Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Business Registration Card */}
        <Link href="/apply?act=1" className="group rounded-2xl glass-panel p-6 glass-panel-hover flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 group-hover:scale-110 transition-transform">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">New Registration</span>
              <h3 className="text-xl font-bold text-slate-900 mt-1 group-hover:text-indigo-600 transition-colors">
                Business Application
              </h3>
              <p className="text-slate-500 text-sm mt-2 leading-relaxed">
                Submit company details, complete Aadhaar eKYC verification, and issue registration certificates.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-bold text-indigo-600 group-hover:translate-x-1 transition-transform">
            Start Application <ArrowRight className="w-4 h-4" />
          </div>
        </Link>

        {/* Trade License Fast-Track Card */}
        <Link href="/apply?act=2" className="group rounded-2xl glass-panel p-6 glass-panel-hover flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 group-hover:scale-110 transition-transform">
              <RefreshCw className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">Fast-Track Permit</span>
              <h3 className="text-xl font-bold text-slate-900 mt-1 group-hover:text-emerald-600 transition-colors">
                Trade License Reuse
              </h3>
              <p className="text-slate-500 text-sm mt-2 leading-relaxed">
                Re-uses pre-verified canonical credentials for instant permit issuance without redundant form filling.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-bold text-emerald-600 group-hover:translate-x-1 transition-transform">
            Fast-Track Apply <ArrowRight className="w-4 h-4" />
          </div>
        </Link>

        {/* Officer Verification Dashboard */}
        <Link href="/officer" className="group rounded-2xl glass-panel p-6 glass-panel-hover flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600 group-hover:scale-110 transition-transform">
              <LayoutDashboard className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-purple-600">Admin Control</span>
              <h3 className="text-xl font-bold text-slate-900 mt-1 group-hover:text-purple-600 transition-colors">
                Officer Dashboard
              </h3>
              <p className="text-slate-500 text-sm mt-2 leading-relaxed">
                Inspect application status, Master Data Linking identity mapping anchors, and audit trails.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-bold text-purple-600 group-hover:translate-x-1 transition-transform">
            View Applications <ArrowRight className="w-4 h-4" />
          </div>
        </Link>

        {/* System Monitor */}
        <Link href="/monitor" className="group rounded-2xl glass-panel p-6 glass-panel-hover flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 group-hover:scale-110 transition-transform">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600">Health Status</span>
              <h3 className="text-xl font-bold text-slate-900 mt-1 group-hover:text-amber-600 transition-colors">
                System Status
              </h3>
              <p className="text-slate-500 text-sm mt-2 leading-relaxed">
                Check departmental health metrics and toggle municipality outage simulation.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-bold text-amber-600 group-hover:translate-x-1 transition-transform">
            Check Status <ArrowRight className="w-4 h-4" />
          </div>
        </Link>
      </div>
    </div>
  );
}
