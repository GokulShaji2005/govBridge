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
          <span className="text-xs font-bold uppercase tracking-widest text-amber-400">
            Resilience & Protocol Monitoring
          </span>
          <h2 className="text-3xl font-extrabold text-white mt-1">Integration Health Dashboard</h2>
        </div>

        <button
          onClick={handleToggleMunicipality}
          disabled={toggling}
          className={`px-5 py-3 rounded-2xl font-bold text-xs flex items-center gap-2.5 transition-all shadow-lg ${
            isMuniDown
              ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20"
              : "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/20"
          }`}
        >
          <Power className="w-4 h-4" />
          {isMuniDown ? "Restore Municipality Endpoint (UP)" : "Simulate Municipality Outage (503)"}
        </button>
      </div>

      {/* Failure Warning Banner */}
      {isMuniDown && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <div>
              <strong className="text-sm">Stage 11 Failure Simulation Engaged</strong>
              <p className="text-xs text-rose-300/80">
                Municipality Endpoint returning HTTP 503. Subsequent workflow executions will fail gracefully without server crash.
              </p>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-xs font-bold font-mono">
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
                isUp ? "border-slate-800" : "border-rose-500/50 bg-rose-950/20"
              }`}
            >
              <div className="flex items-center justify-between">
                <Server className={`w-5 h-5 ${isUp ? "text-blue-400" : "text-rose-400"}`} />
                <span
                  className={`px-3 py-1 rounded-full text-xs font-extrabold font-mono ${
                    isUp
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/30 animate-pulse"
                  }`}
                >
                  {info.status}
                </span>
              </div>

              <div>
                <h4 className="text-lg font-bold text-white capitalize">{dept}</h4>
                <p className="text-xs text-slate-400 mt-1">
                  {dept === "identity" && "National Identity REST API"}
                  {dept === "tax" && "Central Tax XML Gateway"}
                  {dept === "municipality" && "Local Property Legacy System"}
                  {dept === "registry" && "Commercial Register API"}
                </p>
              </div>

              <div className="border-t border-slate-800/80 pt-3 flex items-center justify-between text-xs text-slate-400">
                <span>Latency</span>
                <span className={`font-mono font-bold ${isUp ? "text-slate-200" : "text-rose-400"}`}>
                  {info.latency_ms} ms
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="glass-panel p-6 rounded-3xl space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
          <span>Live Polling Frequency: 1.0s</span>
          <span>Last System Ping: {lastUpdated || "Checking..."}</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          The System Monitor continuously verifies connectivity across disparate protocol endpoints. Toggling the Municipality Outage lever demonstrates GovBridge&apos;s fault isolation and retry capability without destabilizing other departmental services.
        </p>
      </div>
    </div>
  );
}
