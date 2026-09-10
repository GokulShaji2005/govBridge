"use client";

import { useState, useEffect } from "react";
import { Activity, Server, AlertTriangle, CheckCircle2, XCircle, RefreshCw, Power } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

interface DepartmentHealth {
  status: "UP" | "DOWN";
  latency_ms: number;
}

interface HealthData {
  identity: DepartmentHealth;
  tax: DepartmentHealth;
  municipality: DepartmentHealth;
  registry: DepartmentHealth;
}

export default function SystemMonitor() {
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [toggling, setToggling] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/mock/health/all`);
      if (res.ok) {
        const data = await res.json();
        setHealthData(data);
        setLastUpdated(new Date().toLocaleTimeString());
      }
    } catch (err) {
      console.error("Health fetch error:", err);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleMunicipality = async () => {
    setToggling(true);
    try {
      const res = await fetch(`${API_BASE}/admin/toggle-municipality`, {
        method: "POST",
      });
      if (res.ok) {
        await fetchHealth();
      }
    } catch (err) {
      console.error("Toggle error:", err);
    } finally {
      setToggling(false);
    }
  };

  const isMuniDown = healthData?.municipality.status === "DOWN";

  return (
    <div className="space-y-8 py-4 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-600">
            Resilience & Protocol Health Monitoring
          </span>
          <h2 className="text-3xl font-extrabold text-slate-900 mt-1">Integration Health Dashboard</h2>
        </div>

        <button
          onClick={handleToggleMunicipality}
          disabled={toggling}
          className={`px-5 py-3 rounded-2xl font-bold text-xs flex items-center gap-2.5 transition-all shadow-md ${
            isMuniDown
              ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20"
              : "bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/20"
          }`}
        >
          <Power className="w-4 h-4" />
          {isMuniDown ? "Restore Municipality Endpoint (UP)" : "Simulate Municipality Outage (503)"}
        </button>
      </div>

      {/* Failure Warning Banner */}
      {isMuniDown && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            <div>
              <strong className="text-sm">Outage Simulation Engaged</strong>
              <p className="text-xs text-rose-700">
                Municipality Endpoint returning HTTP 503. Subsequent workflow executions will fail gracefully without server crash.
              </p>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full bg-rose-100 border border-rose-300 text-xs font-bold font-mono text-rose-800">
            OUTAGE SIMULATED
          </span>
        </div>
      )}

      {/* Health Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {healthData && Object.entries(healthData).map(([dept, info]) => {
          const isUp = info.status === "UP";
          return (
            <div
              key={dept}
              className={`p-6 rounded-3xl glass-panel space-y-4 border transition-all ${
                isUp ? "border-slate-200" : "border-rose-300 bg-rose-50/40"
              }`}
            >
              <div className="flex items-center justify-between">
                <Server className={`w-5 h-5 ${isUp ? "text-indigo-600" : "text-rose-600"}`} />
                <span
                  className={`px-3 py-1 rounded-full text-xs font-extrabold font-mono ${
                    isUp
                      ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                      : "bg-rose-100 text-rose-800 border border-rose-300 animate-pulse"
                  }`}
                >
                  {info.status}
                </span>
              </div>

              <div>
                <h4 className="text-lg font-bold text-slate-900 capitalize">{dept}</h4>
                <p className="text-xs text-slate-500 mt-1">
                  {dept === "identity" && "National Identity REST API"}
                  {dept === "tax" && "Central Tax XML Gateway"}
                  {dept === "municipality" && "Local Property Legacy System"}
                  {dept === "registry" && "Commercial Register API"}
                </p>
              </div>

              <div className="border-t border-slate-200 pt-3 flex items-center justify-between text-xs text-slate-500">
                <span>Latency</span>
                <span className={`font-mono font-bold ${isUp ? "text-slate-900" : "text-rose-600"}`}>
                  {info.latency_ms} ms
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="glass-panel p-6 rounded-3xl space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500 border-b border-slate-200 pb-2">
          <span>Live Polling Frequency: 1.0s</span>
          <span>Last System Ping: {lastUpdated || "Checking..."}</span>
        </div>
        <p className="text-xs text-slate-500 leading-relaxed">
          The System Monitor continuously verifies connectivity across disparate protocol endpoints. Toggling the Municipality Outage lever demonstrates GovBridge&apos;s fault isolation and retry capability without destabilizing other departmental services.
        </p>
      </div>
    </div>
  );
}
