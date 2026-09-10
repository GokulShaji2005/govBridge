"use client";

import { useState, useEffect } from "react";
import { 
  LayoutDashboard, Search, Filter, ShieldCheck, CheckCircle2, 
  XCircle, Clock, FileText, ChevronRight, UserCheck, Activity, Eye, Code
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

interface ApplicationSummary {
  id: string;
  citizen_id: string;
  service_type: string;
  status: string;
  created_at: string;
  govbridge_person_id: string | null;
  steps: Record<string, string>;
}

export default function OfficerDashboard() {
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [selectedAppDetails, setSelectedAppDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchApplications = async () => {
    try {
      const res = await fetch(`${API_BASE}/applications`);
      if (res.ok) {
        const data = await res.json();
        setApplications(data);
        if (data.length > 0 && !selectedAppId) {
          setSelectedAppId(data[0].id);
        }
      }
    } catch (err) {
      console.error("Fetch applications error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
    const interval = setInterval(fetchApplications, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedAppId) return;
    const fetchDetails = async () => {
      try {
        const res = await fetch(`${API_BASE}/applications/${selectedAppId}`);
        if (res.ok) {
          const data = await res.json();
          setSelectedAppDetails(data);
        }
      } catch (err) {
        console.error("Fetch app detail error:", err);
      }
    };
    fetchDetails();
  }, [selectedAppId]);

  const filteredApps = applications.filter(a => 
    a.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.citizen_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 py-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-purple-400">
            Administrative Control Panel
          </span>
          <h2 className="text-3xl font-extrabold text-white mt-1">Officer Verification Dashboard</h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search App ID / Citizen ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-purple-500 w-64"
            />
          </div>
          <button
            onClick={fetchApplications}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column: Applications Table */}
        <div className="lg:col-span-1 glass-panel rounded-3xl p-6 space-y-4 max-h-[75vh] flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-bold text-white text-base">Applications ({filteredApps.length})</h3>
            <span className="text-xs text-slate-400">Live Polling</span>
          </div>

          <div className="overflow-y-auto space-y-3 flex-1 pr-1">
            {filteredApps.map((app) => (
              <div
                key={app.id}
                onClick={() => setSelectedAppId(app.id)}
                className={`p-4 rounded-2xl cursor-pointer border transition-all ${
                  selectedAppId === app.id
                    ? "bg-purple-950/30 border-purple-500/50 shadow-lg shadow-purple-950/40"
                    : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-white">{app.id}</span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      app.status === "APPROVED"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        : app.status === "FAILED"
                        ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                        : "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                    }`}
                  >
                    {app.status}
                  </span>
                </div>

                <div className="text-xs text-slate-400 mt-2 space-y-1">
                  <div>Citizen ID: <span className="text-slate-200 font-mono">{app.citizen_id}</span></div>
                  <div>Service: <span className="text-slate-300">{app.service_type}</span></div>
                  {app.govbridge_person_id && (
                    <div className="text-[11px] text-purple-300">GovBridge ID: {app.govbridge_person_id}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Application Details & Audit Log */}
        <div className="lg:col-span-2 space-y-6">
          {selectedAppDetails ? (
            <div className="glass-panel rounded-3xl p-6 space-y-6">
              {/* Header Info */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <span className="text-xs font-bold text-purple-400 uppercase tracking-widest">
                    Application Inspection
                  </span>
                  <h3 className="text-2xl font-extrabold text-white mt-0.5">{selectedAppDetails.id}</h3>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400">GovBridge Person Identifier</div>
                  <div className="text-sm font-mono font-bold text-purple-300">
                    {selectedAppDetails.govbridge_person_id || "Not Linked Yet"}
                  </div>
                </div>
              </div>

              {/* Steps Progress Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Departmental Step Statuses
                </h4>
                <div className="grid sm:grid-cols-4 gap-3">
                  {selectedAppDetails.steps?.map((step: any) => (
                    <div key={step.step_name} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold capitalize text-slate-200">{step.step_name}</span>
                        {step.status === "DONE" || step.status === "REUSED" ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        ) : step.status === "FAILED" ? (
                          <XCircle className="w-4 h-4 text-rose-400" />
                        ) : (
                          <Clock className="w-4 h-4 text-slate-500" />
                        )}
                      </div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase">{step.status}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Timestamped Audit Log Timeline */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-purple-400" /> Immutable Timestamped Audit Log
                </h4>
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3 max-h-64 overflow-y-auto">
                  {selectedAppDetails.audit_trail?.map((log: any) => (
                    <div key={log.id} className="flex items-start justify-between text-xs border-b border-slate-900 pb-2">
                      <div className="space-y-0.5">
                        <div className="font-bold text-slate-200">{log.action}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{log.timestamp}</div>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          log.result === "SUCCESS" || log.result === "APPROVED"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : log.result.includes("FAILED")
                            ? "bg-rose-500/10 text-rose-400"
                            : "bg-blue-500/10 text-blue-400"
                        }`}
                      >
                        {log.result}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel rounded-3xl p-12 text-center text-slate-500">
              Select an application from the table to view its detailed step breakdown and audit log.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
