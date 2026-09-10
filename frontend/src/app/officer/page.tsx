"use client";

import { useState, useEffect } from "react";
import { 
  LayoutDashboard, Search, Filter, ShieldCheck, CheckCircle2, 
  XCircle, Clock, FileText, ChevronRight, UserCheck, Activity, Eye, Code, User, Lock
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
  const [officerToken, setOfficerToken] = useState<string | null>(null);
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [selectedAppDetails, setSelectedAppDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch Officer Auth JWT Token on mount
  useEffect(() => {
    async function fetchOfficerToken() {
      try {
        const res = await fetch(`${API_BASE}/auth/token-demo`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ citizen_id: "C_OFFICER_01", role: "officer" })
        });
        if (res.ok) {
          const data = await res.json();
          setOfficerToken(data.access_token);
        }
      } catch (err) {
        console.error("Officer token error:", err);
      }
    }
    fetchOfficerToken();
  }, []);

  const fetchApplications = async () => {
    if (!officerToken) return;
    try {
      const res = await fetch(`${API_BASE}/applications`, {
        headers: { "Authorization": `Bearer ${officerToken}` }
      });
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
    if (officerToken) {
      fetchApplications();
      const interval = setInterval(fetchApplications, 2000);
      return () => clearInterval(interval);
    }
  }, [officerToken]);

  useEffect(() => {
    if (!selectedAppId || !officerToken) return;
    const fetchDetails = async () => {
      try {
        const res = await fetch(`${API_BASE}/applications/${selectedAppId}`, {
          headers: { "Authorization": `Bearer ${officerToken}` }
        });
        if (res.ok) {
          const data = await res.json();
          setSelectedAppDetails(data);
        }
      } catch (err) {
        console.error("Fetch app detail error:", err);
      }
    };
    fetchDetails();
  }, [selectedAppId, officerToken]);

  const filteredApps = applications.filter(a => 
    a.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.citizen_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 py-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-600">
            Administrative Control Panel (Boundary 1 Protected)
          </span>
          <h2 className="text-3xl font-extrabold text-slate-900 mt-1">Officer Verification Dashboard</h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search App ID / Citizen ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-white border border-slate-200 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-900 focus:outline-none focus:border-indigo-500 w-64 shadow-xs"
            />
          </div>
          <button
            onClick={fetchApplications}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl border border-slate-200 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column: Applications Table */}
        <div className="lg:col-span-1 glass-panel rounded-3xl p-6 space-y-4 max-h-[75vh] flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <h3 className="font-bold text-slate-900 text-base">Applications ({filteredApps.length})</h3>
            <span className="text-xs text-slate-500 font-semibold">Live Stream</span>
          </div>

          <div className="overflow-y-auto space-y-3 flex-1 pr-1">
            {filteredApps.map((app) => (
              <div
                key={app.id}
                onClick={() => setSelectedAppId(app.id)}
                className={`p-4 rounded-2xl cursor-pointer border transition-all ${
                  selectedAppId === app.id
                    ? "bg-indigo-50/70 border-indigo-300 shadow-sm"
                    : "bg-white border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">{app.id}</span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      app.status === "APPROVED"
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                        : app.status === "FAILED"
                        ? "bg-rose-100 text-rose-800 border border-rose-300"
                        : app.status === "MANUAL_REVIEW_FLAGGED"
                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                        : "bg-indigo-100 text-indigo-800 border border-indigo-300"
                    }`}
                  >
                    {app.status}
                  </span>
                </div>

                <div className="text-xs text-slate-500 mt-2 space-y-1">
                  <div>Citizen ID: <span className="text-slate-900 font-mono font-bold">{app.citizen_id}</span></div>
                  <div>Service: <span className="text-slate-700">{app.service_type}</span></div>
                  {app.govbridge_person_id && (
                    <div className="text-[11px] text-indigo-700 font-bold">Anchor: {app.govbridge_person_id}</div>
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
              <div className="flex items-center justify-between border-b border-slate-200 pb-4">
                <div>
                  <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">
                    Application Administrative Inspection
                  </span>
                  <h3 className="text-2xl font-extrabold text-slate-900 mt-0.5">{selectedAppDetails.id}</h3>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-500">GovBridge Master Neutral Anchor</div>
                  <div className="text-sm font-mono font-extrabold text-indigo-700">
                    {selectedAppDetails.govbridge_person_id || "Resolving..."}
                  </div>
                </div>
              </div>

              {/* Master Data Linking Visualizer */}
              {selectedAppDetails.govbridge_person_id && (
                <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-200 space-y-2">
                  <div className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                    <User className="w-4 h-4 text-indigo-600" /> Master Data Linking (Local ID Resolution)
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                    <div className="p-2.5 rounded-xl bg-white border border-indigo-100 shadow-xs">
                      <span className="text-slate-500 block text-[10px] font-sans font-medium">Identity Dept ID</span>
                      <span className="text-indigo-900 font-bold">{selectedAppDetails.citizen_id}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white border border-indigo-100 shadow-xs">
                      <span className="text-slate-500 block text-[10px] font-sans font-medium">Tax Dept PAN</span>
                      <span className="text-indigo-900 font-bold">ABCDE1234F</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white border border-indigo-100 shadow-xs">
                      <span className="text-slate-500 block text-[10px] font-sans font-medium">Municipality Owner Code</span>
                      <span className="text-indigo-900 font-bold">OWN77821</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Steps Progress Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                  Departmental Step Statuses
                </h4>
                <div className="grid sm:grid-cols-4 gap-3">
                  {selectedAppDetails.steps?.map((step: any) => (
                    <div key={step.step_name} className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold capitalize text-slate-800">{step.step_name}</span>
                        {step.status === "DONE" || step.status === "REUSED" ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : step.status === "FAILED" ? (
                          <XCircle className="w-4 h-4 text-rose-600" />
                        ) : (
                          <Clock className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                      <div className="text-[10px] font-extrabold text-slate-500 uppercase">{step.status}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Timestamped Audit Log Timeline */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-600" /> Immutable Timestamped Audit Trail
                </h4>
                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3 max-h-64 overflow-y-auto">
                  {selectedAppDetails.audit_trail?.map((log: any) => (
                    <div key={log.id} className="flex items-start justify-between text-xs border-b border-slate-200/80 pb-2">
                      <div className="space-y-0.5">
                        <div className="font-bold text-slate-800">{log.action}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{log.timestamp}</div>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          log.result === "SUCCESS" || log.result === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800"
                            : log.result.includes("FAILED")
                            ? "bg-rose-100 text-rose-800"
                            : log.result.includes("FLAGGED")
                            ? "bg-amber-100 text-amber-800"
                            : "bg-indigo-100 text-indigo-800"
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
