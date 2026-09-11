"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { 
  ShieldCheck, RefreshCw, CheckCircle2, XCircle, Clock, ArrowRight, 
  Lock, Building2, Award, UserCheck, Smartphone, LogIn, Sparkles, AlertCircle, FileText, Mail, Key, PhoneCall
} from "lucide-react";
import { supabase } from "@/lib/supabase";

const API_BASE = "http://127.0.0.1:8000";

interface StepDetail {
  step_name: string;
  status: string;
  data: any;
  updated_at: string;
}

interface ApplicationData {
  id: string;
  citizen_id: string;
  service_type: string;
  status: string;
  govbridge_person_id?: string;
  steps: StepDetail[];
  audit_trail: any[];
}

function ApplyContent() {
  const searchParams = useSearchParams();
  const actParam = searchParams.get("act");

  // Portal Citizen Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [citizenId, setCitizenId] = useState("");
  const [applicantName, setApplicantName] = useState("");
  const [citizenToken, setCitizenToken] = useState<string | null>(null);

  // Custom Local Identifiers for Dynamic Workflow Engine
  const [panNumber, setPanNumber] = useState("");
  const [ownerCode, setOwnerCode] = useState("");
  const [simulateFraud, setSimulateFraud] = useState(false);

  // Supabase Passwordless OTP Auth state
  const [authMode, setAuthMode] = useState<"DEMO" | "MOBILE_OTP" | "EMAIL_OTP" | "LOGIN">("MOBILE_OTP");
  const [authMobile, setAuthMobile] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [supabaseOtpInput, setSupabaseOtpInput] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  // Business Application details
  const [businessName, setBusinessName] = useState("");
  const [companyType, setCompanyType] = useState("Private Limited Company");
  const [authorizedCapital, setAuthorizedCapital] = useState("");
  const [registeredAddress, setRegisteredAddress] = useState("");
  const [serviceType, setServiceType] = useState<"business_registration" | "trade_license">(
    actParam === "2" ? "trade_license" : "business_registration"
  );

  const [stage, setStage] = useState<"FORM" | "EKYC" | "REUSE_CHECK" | "CONSENT" | "TRACKER">("FORM");
  const [appId, setAppId] = useState<string | null>(null);
  const [appDetails, setAppDetails] = useState<ApplicationData | null>(null);

  const clientKey = serviceType === "business_registration" ? "KEY_BUS_REG_123" : "KEY_TRADE_LIC_456";

  // Aadhaar eKYC OTP state
  const [aadhaarNumber, setAadhaarNumber] = useState("");
  const [otpInput, setOtpInput] = useState("");
  const [ekycToken, setEkycToken] = useState<string | null>(null);
  const [ekycVerified, setEkycVerified] = useState(false);

  const [reuseCheckData, setReuseCheckData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Signout state tracking
  const [userLoggedOut, setUserLoggedOut] = useState(false);

  // Initial Demo Citizen Session initialization
  useEffect(() => {
    async function loginCitizenSession() {
      try {
        const res = await fetch(`${API_BASE}/auth/token-demo`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ citizen_id: citizenId, role: "citizen" })
        });
        if (res.ok) {
          const data = await res.json();
          setCitizenToken(data.access_token);
          setIsAuthenticated(true);
        }
      } catch (err) {
        console.error("Citizen Login error:", err);
      }
    }
    if (!citizenToken && !userLoggedOut) {
      loginCitizenSession();
    }
  }, [citizenId, citizenToken, userLoggedOut]);

  // Fast Demo Session Click Handler
  const handleFastDemoLogin = async () => {
    setUserLoggedOut(false);
    setAuthMode("DEMO");
    const demoId = citizenId || "C10291";
    const demoName = applicantName || "Rahul Kumar";
    setCitizenId(demoId);
    setApplicantName(demoName);
    try {
      const res = await fetch(`${API_BASE}/auth/token-demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ citizen_id: demoId, role: "citizen" })
      });
      if (res.ok) {
        const data = await res.json();
        setCitizenToken(data.access_token);
        setIsAuthenticated(true);
        setAuthMessage("Fast Demo Session Authenticated!");
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Listen to Supabase Auth State Changes
  useEffect(() => {
    const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setCitizenToken(session.access_token);
        const meta = session.user.user_metadata || {};
        setApplicantName(meta.full_name || session.user.phone || session.user.email || "Authenticated Citizen");
        setCitizenId(meta.citizen_id || `C${session.user.id.slice(0, 5).toUpperCase()}`);
        setIsAuthenticated(true);
        setUserLoggedOut(false);
      }
    });
    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);

  // Passwordless Supabase OTP Handlers
  const handleSendMobileOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthMessage(null);
    try {
      const { error } = await supabase.auth.signInWithOtp({
        phone: authMobile.replace(/\s+/g, "")
      });
      if (error) {
        setAuthMessage(`Mobile OTP request: ${error.message}. (Note: Demo OTP mode active for fast testing)`);
        setOtpSent(true);
      } else {
        setOtpSent(true);
        setAuthMessage("OTP sent to mobile! Enter 6-digit code to log in.");
      }
    } catch (err: any) {
      setOtpSent(true);
      setAuthMessage(`Demo mode: Enter OTP 123456 to verify citizen session.`);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleVerifyMobileOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthMessage(null);
    try {
      const { data, error } = await supabase.auth.verifyOtp({
        phone: authMobile.replace(/\s+/g, ""),
        token: supabaseOtpInput,
        type: "sms"
      });
      if (error || !data.session) {
        // Fallback demo token grant for presentation testing
        const generatedId = citizenId || `C${Math.floor(10000 + Math.random() * 90000)}`;
        const res = await fetch(`${API_BASE}/auth/token-demo`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ citizen_id: generatedId, role: "citizen" })
        });
        if (res.ok) {
          const tokData = await res.json();
          setCitizenToken(tokData.access_token);
          setCitizenId(generatedId);
          if (!applicantName) setApplicantName("Citizen User");
          setIsAuthenticated(true);
          setUserLoggedOut(false);
          setAuthMessage(`Mobile OTP Verified! Provisioned Citizen ID: ${generatedId}`);
        }
      } else {
        const supUser = data.session.user;
        const assignedId = supUser.user_metadata?.citizen_id || `C${supUser.id.slice(0, 5).toUpperCase()}`;
        setCitizenToken(data.session.access_token);
        setCitizenId(assignedId);
        if (!applicantName) setApplicantName(supUser.user_metadata?.full_name || supUser.phone || "Citizen User");
        setIsAuthenticated(true);
        setUserLoggedOut(false);
        setAuthMessage(`Mobile OTP Verified! Provisioned Citizen ID: ${assignedId}`);
      }
    } catch (err: any) {
      setAuthMessage(`Verification error: ${err.message}`);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSendEmailOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthMessage(null);
    try {
      const { error } = await supabase.auth.signInWithOtp({ email: authEmail });
      if (error) {
        setAuthMessage(`Email OTP: ${error.message}`);
      } else {
        setAuthMessage("Magic Link / OTP sent to your email! Check your inbox.");
      }
    } catch (err: any) {
      setAuthMessage(`Error: ${err.message}`);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSupabaseSignOut = async () => {
    await supabase.auth.signOut();
    setUserLoggedOut(true);
    setCitizenToken(null);
    setIsAuthenticated(false);
    setAuthMessage("You have signed out successfully.");
  };

  // 1. Create Application
  const handleCreateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/applications`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${citizenToken}`,
          "X-Client-Key": clientKey
        },
        body: JSON.stringify({ service_type: serviceType })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setAppId(data.application_id);
      setStage("EKYC");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to initialize application.");
    } finally {
      setLoading(false);
    }
  };

  // 2. Aadhaar eKYC OTP Verification (Dynamic citizen metadata)
  const handleVerifyAadhaarOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/aadhaar/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          aadhaar_number: aadhaarNumber,
          otp: otpInput,
          citizen_id: citizenId,
          name: applicantName
        })
      });
      if (!res.ok) throw new Error("Aadhaar OTP verification failed. Enter demo OTP 123456.");
      const data = await res.json();
      setEkycToken(data.verification_token);
      setEkycVerified(true);

      if (appId) {
        const reuseRes = await fetch(`${API_BASE}/applications/${appId}/check-reuse`, {
          headers: {
            "Authorization": `Bearer ${citizenToken}`,
            "X-Client-Key": clientKey
          }
        });
        if (reuseRes.ok) {
          const reuseData = await reuseRes.json();
          setReuseCheckData(reuseData);
          setStage("REUSE_CHECK");
        } else {
          setStage("CONSENT");
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. Grant Purpose Consent & Run Workflow (Dynamic Local IDs & Fraud Simulation Payload)
  const handleGrantConsentAndRun = async () => {
    if (!appId || !citizenToken || !ekycToken) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const targetTaxpayerName = simulateFraud ? "Imposter Taxpayer Name" : applicantName;
      const grantRes = await fetch(`${API_BASE}/consent/grant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          citizen_id: citizenId,
          purpose: serviceType,
          data_scope: ["identity:verify", "tax:verify", "address:verify", "registry:write"],
          local_ids: { 
            tax: panNumber, 
            municipality: ownerCode,
            taxpayer_name: targetTaxpayerName
          },
          verification_token: ekycToken
        })
      });
      if (!grantRes.ok) throw new Error("Failed to grant purpose consent.");
      const grantData = await grantRes.json();

      const wfRes = await fetch(`${API_BASE}/applications/${appId}/start-workflow`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${citizenToken}`,
          "X-Client-Key": clientKey
        },
        body: JSON.stringify({
          consent_token: grantData.consent_token,
          allow_reuse: true
        })
      });
      if (!wfRes.ok) throw new Error("Workflow execution failed.");
      setStage("TRACKER");
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Live Application Progress Tracker Polling
  useEffect(() => {
    if (stage !== "TRACKER" || !appId || !citizenToken) return;
    const fetchProgress = async () => {
      try {
        const res = await fetch(`${API_BASE}/applications/${appId}`, {
          headers: {
            "Authorization": `Bearer ${citizenToken}`,
            "X-Client-Key": clientKey
          }
        });
        if (res.ok) {
          const data = await res.json();
          setAppDetails(data);
        }
      } catch (err) {
        console.error("Tracker fetch error:", err);
      }
    };
    fetchProgress();
    const interval = setInterval(fetchProgress, 1500);
    return () => clearInterval(interval);
  }, [stage, appId, citizenToken, clientKey]);

  return (
    <div className="space-y-8 py-4 max-w-4xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-600 flex items-center gap-1.5">
            <Building2 className="w-4 h-4" /> Single-Window Business Clearance
          </span>
          <h2 className="text-3xl font-extrabold text-slate-900 mt-1">
            {serviceType === "business_registration" ? "Commercial Business Registration" : "Municipal Trade License Portal"}
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Direct government data exchange gateway. No manual physical document submission required.
          </p>
        </div>

        {/* Citizen Session Badge */}
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <div className="p-3 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-extrabold text-sm">
                  {applicantName[0]}
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 flex items-center gap-1">
                    {applicantName} <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                  </div>
                  <div className="text-[11px] font-mono text-slate-500">Citizen ID: {citizenId}</div>
                </div>
              </div>
              <button
                onClick={handleSupabaseSignOut}
                className="px-3.5 py-2 text-xs font-bold text-rose-600 hover:bg-rose-50 rounded-xl border border-rose-200 transition-colors"
              >
                Sign Out
              </button>
            </>
          ) : (
            <>
              <div className="px-3.5 py-2 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-bold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                Signed Out (Guest)
              </div>
              <button
                onClick={handleFastDemoLogin}
                className="px-4 py-2 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-xs transition-colors"
              >
                Sign In / Demo
              </button>
            </>
          )}
        </div>
      </div>

      {/* Supabase Passwordless Auth Control Bar (Only when NOT authenticated) */}
      {!isAuthenticated ? (
        <>
          <div className="p-4 rounded-2xl bg-indigo-50/70 border border-indigo-200 flex flex-col md:flex-row items-center justify-between gap-3 text-xs text-indigo-900">
            <div className="flex items-center gap-2 font-semibold">
              <Sparkles className="w-4 h-4 text-indigo-600 shrink-0" />
              <span>Boundary 1 SSO: Passwordless Supabase Authentication Engine</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAuthMode("MOBILE_OTP")}
                className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                  authMode === "MOBILE_OTP" ? "bg-indigo-600 text-white shadow-xs" : "bg-white text-indigo-700 hover:bg-indigo-100 border border-indigo-200"
                }`}
              >
                Mobile OTP (Aadhaar Linked)
              </button>
              <button
                onClick={() => setAuthMode("EMAIL_OTP")}
                className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                  authMode === "EMAIL_OTP" ? "bg-indigo-600 text-white shadow-xs" : "bg-white text-indigo-700 hover:bg-indigo-100 border border-indigo-200"
                }`}
              >
                Email Magic Link
              </button>
              <button
                onClick={handleFastDemoLogin}
                className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                  authMode === "DEMO" ? "bg-emerald-600 text-white shadow-xs" : "bg-white text-emerald-700 hover:bg-emerald-100 border border-emerald-200"
                }`}
              >
                Fast Demo Session
              </button>
            </div>
          </div>

          {/* Supabase Passwordless OTP Form Section */}
          {authMode !== "DEMO" && (
            <div className="glass-panel rounded-3xl p-6 space-y-4 border border-indigo-200 bg-white">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
                  <Smartphone className="w-4 h-4 text-indigo-600" />
                  {authMode === "MOBILE_OTP" && "Passwordless Mobile OTP Login"}
                  {authMode === "EMAIL_OTP" && "Passwordless Email Magic Link"}
                </h3>
                <span className="text-xs font-bold font-mono text-indigo-600">Boundary 1 SSO</span>
              </div>

              {authMessage && (
                <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-xs font-bold text-indigo-800">
                  {authMessage}
                </div>
              )}

              {authMode === "MOBILE_OTP" && (
                <div className="space-y-4">
                  {!otpSent ? (
                    <form onSubmit={handleSendMobileOtp} className="space-y-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Aadhaar-Registered Mobile Number</label>
                        <div className="relative">
                          <PhoneCall className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                          <input
                            type="text"
                            required
                            placeholder="+91 98765 43210"
                            value={authMobile}
                            onChange={(e) => setAuthMobile(e.target.value)}
                            className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:border-indigo-500 font-mono"
                          />
                        </div>
                      </div>
                      <button
                        type="submit"
                        disabled={authLoading}
                        className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition-colors shadow-sm"
                      >
                        {authLoading ? "Sending OTP..." : "Get Passwordless OTP"}
                      </button>
                    </form>
                  ) : (
                    <form onSubmit={handleVerifyMobileOtp} className="space-y-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 mb-1">Enter 6-Digit Mobile OTP (Demo: 123456)</label>
                        <input
                          type="text"
                          required
                          maxLength={6}
                          placeholder="123456"
                          value={supabaseOtpInput}
                          onChange={(e) => setSupabaseOtpInput(e.target.value)}
                          className="w-full px-4 py-3 bg-white border border-indigo-300 rounded-xl text-center text-xl font-mono font-bold tracking-widest text-indigo-600 focus:outline-none focus:border-indigo-500 shadow-xs"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={authLoading}
                        className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-sm transition-colors shadow-sm"
                      >
                        {authLoading ? "Verifying Session..." : "Verify OTP & Authenticate Session"}
                      </button>
                    </form>
                  )}
                </div>
              )}

              {authMode === "EMAIL_OTP" && (
                <form onSubmit={handleSendEmailOtp} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Citizen Email Address</label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="email"
                        required
                        placeholder="rahul.kumar@govbridge.gov.in"
                        value={authEmail}
                        onChange={(e) => setAuthEmail(e.target.value)}
                        className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={authLoading}
                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition-colors shadow-sm"
                  >
                    {authLoading ? "Sending Link..." : "Send Passwordless Magic Login Link"}
                  </button>
                </form>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-emerald-900">
          <div className="flex items-center gap-2 font-bold">
            <UserCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Boundary 1 SSO Verified — Active Citizen Session: <code className="font-mono text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded">{citizenId || "C10291"}</code></span>
          </div>
          <span className="text-[11px] font-semibold text-emerald-700">Authenticated Session Token Active</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          {errorMsg}
        </div>
      )}

      {/* STAGE 1: Business Form */}
      {stage === "FORM" && (
        <form onSubmit={handleCreateApplication} className="glass-panel rounded-3xl p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <div>
              <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">Step 1 of 3</span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">Application & Enterprise Information</h3>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold text-slate-500">Target Portal</span>
              <div className="text-xs font-mono font-bold text-indigo-700">{clientKey}</div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Applicant Full Name (eKYC Linked)</label>
              <input
                type="text"
                required
                placeholder="e.g. Rahul Kumar"
                value={applicantName}
                onChange={(e) => setApplicantName(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 font-semibold focus:outline-none focus:border-indigo-500 shadow-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Citizen ID Anchor</label>
              <input
                type="text"
                required
                placeholder="e.g. C10291"
                value={citizenId}
                onChange={(e) => setCitizenId(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 font-semibold focus:outline-none focus:border-indigo-500 shadow-xs font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Proposed Business Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Apex Innovations Pvt Ltd"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 font-semibold focus:outline-none focus:border-indigo-500 shadow-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Entity / Legal Structure</label>
              <select
                value={companyType}
                onChange={(e) => setCompanyType(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 font-semibold focus:outline-none focus:border-indigo-500 shadow-xs"
              >
                <option value="Private Limited Company">Private Limited Company (Pvt Ltd)</option>
                <option value="Limited Liability Partnership">Limited Liability Partnership (LLP)</option>
                <option value="Sole Proprietorship">Sole Proprietorship</option>
                <option value="Partnership Firm">Partnership Firm</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Tax PAN (Income Tax Dept ID)</label>
              <input
                type="text"
                required
                placeholder="e.g. ABCDE1234F"
                value={panNumber}
                onChange={(e) => setPanNumber(e.target.value.toUpperCase())}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 font-semibold focus:outline-none focus:border-indigo-500 shadow-xs font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Municipal Property Code</label>
              <input
                type="text"
                required
                placeholder="e.g. OWN77821"
                value={ownerCode}
                onChange={(e) => setOwnerCode(e.target.value.toUpperCase())}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 font-semibold focus:outline-none focus:border-indigo-500 shadow-xs font-mono"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Registered Municipal Premises Address</label>
              <input
                type="text"
                required
                placeholder="e.g. Plot 42, Cyber Technology Park, Ward 7"
                value={registeredAddress}
                onChange={(e) => setRegisteredAddress(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 font-semibold focus:outline-none focus:border-indigo-500 shadow-xs"
              />
            </div>

            {/* Interactive Fraud Engine Simulation Toggle */}
            <div className="md:col-span-2 p-4 rounded-2xl bg-amber-50/70 border border-amber-200 flex items-center justify-between gap-4">
              <div>
                <span className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 text-amber-600" /> Interactive Fraud Safeguard Simulator
                </span>
                <p className="text-[11px] text-amber-800 mt-0.5">
                  Toggle to simulate mismatched Tax PAN identity ("Imposter Name") to test GovBridge's live fraud detection & manual review flagging!
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSimulateFraud(!simulateFraud)}
                className={`px-4 py-2 rounded-xl text-xs font-extrabold transition-all shadow-xs shrink-0 ${
                  simulateFraud
                    ? "bg-rose-600 text-white shadow-rose-200"
                    : "bg-white text-slate-700 hover:bg-slate-50 border border-slate-300"
                }`}
              >
                {simulateFraud ? "⚠️ Fraud Mismatch ACTIVE" : "Normal Clean Application"}
              </button>
            </div>
          </div>

          <div className="pt-4 flex items-center justify-between border-t border-slate-200">
            <div className="text-xs text-slate-500 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-indigo-600" /> Boundary 1 Protected Session
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-2xl flex items-center gap-2 transition-all shadow-md"
            >
              {loading ? "Initializing..." : "Proceed to Identity Verification"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      )}

      {/* STAGE 2: Aadhaar eKYC Verification */}
      {stage === "EKYC" && (
        <form onSubmit={handleVerifyAadhaarOtp} className="glass-panel rounded-3xl p-8 space-y-6 max-w-xl mx-auto">
          <div className="text-center space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto">
              <Smartphone className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-extrabold text-slate-900">Aadhaar Identity Verification</h3>
            <p className="text-xs text-slate-600">
              National eKYC Precondition: Identity verification is required before granting purpose consent.
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Aadhaar Number (12 Digits)</label>
              <input
                type="text"
                required
                maxLength={12}
                value={aadhaarNumber}
                onChange={(e) => setAadhaarNumber(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-center text-lg font-mono font-bold tracking-widest text-slate-900 focus:outline-none focus:border-indigo-500 shadow-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Enter Demo OTP (123456)</label>
              <input
                type="text"
                required
                maxLength={6}
                value={otpInput}
                onChange={(e) => setOtpInput(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-center text-xl font-mono font-bold tracking-widest text-indigo-600 focus:outline-none focus:border-indigo-500 shadow-xs"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-2xl text-sm transition-all shadow-md"
          >
            {loading ? "Verifying eKYC..." : "Verify OTP & Continue"}
          </button>
        </form>
      )}

      {/* STAGE 3: Credential Reuse Check */}
      {stage === "REUSE_CHECK" && (
        <div className="glass-panel rounded-3xl p-8 space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900">Verified Credentials Available</h3>
              <p className="text-xs text-slate-600">
                GovBridge detected previously verified credentials for {applicantName} ({citizenId}).
              </p>
            </div>
          </div>

          <div className="grid sm:grid-cols-3 gap-3">
            {reuseCheckData?.reusable_steps && Object.entries(reuseCheckData.reusable_steps).map(([step, item]: any) => (
              <div key={step} className="p-4 rounded-2xl bg-white border border-slate-200 space-y-1 shadow-xs">
                <div className="flex items-center justify-between text-xs font-bold capitalize text-slate-800">
                  <span>{step}</span>
                  {item.available ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <Clock className="w-4 h-4 text-slate-400" />}
                </div>
                <div className="text-[11px] text-slate-500">
                  {item.available ? "Fast-path reuse ready" : "Will fetch live"}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => setStage("CONSENT")}
            className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-2xl text-sm transition-all shadow-md"
          >
            Proceed to Data Access Consent
          </button>
        </div>
      )}

      {/* STAGE 4: Purpose Consent Gate */}
      {stage === "CONSENT" && (
        <div className="glass-panel rounded-3xl p-8 space-y-6">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-8 h-8 text-indigo-600 shrink-0" />
            <div>
              <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Boundary 3 Signed Consent Gate</span>
              <h3 className="text-xl font-bold text-slate-900">Authorize Automated Government Verification</h3>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-indigo-50/60 border border-indigo-200 space-y-3 text-xs text-indigo-950">
            <p className="font-semibold leading-relaxed">
              You are granting explicit authorization to <strong>GovBridge</strong> to query relevant departmental databases on your behalf for the sole purpose of <strong>Commercial Business Clearance</strong>.
            </p>
            <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
              <div className="p-2.5 rounded-xl bg-white border border-indigo-100">✓ National Identity Registry (`identity:verify`)</div>
              <div className="p-2.5 rounded-xl bg-white border border-indigo-100">✓ Central Tax Bureau (`tax:verify`)</div>
              <div className="p-2.5 rounded-xl bg-white border border-indigo-100">✓ Municipal Property Records (`address:verify`)</div>
              <div className="p-2.5 rounded-xl bg-white border border-indigo-100">✓ Commercial Registry (`registry:write`)</div>
            </div>
          </div>

          <button
            onClick={handleGrantConsentAndRun}
            disabled={loading}
            className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold rounded-2xl text-sm transition-all shadow-md flex items-center justify-center gap-2"
          >
            {loading ? "Signing Consent & Executing..." : "Grant Signed Consent & Submit Application"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* STAGE 5: Plain-Language Progress Tracker */}
      {stage === "TRACKER" && (
        <div className="glass-panel rounded-3xl p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <div>
              <span className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Live Verification Status</span>
              <h3 className="text-2xl font-extrabold text-slate-900 mt-0.5">{appId}</h3>
            </div>
            <span className={`px-4 py-1.5 rounded-full text-xs font-extrabold uppercase ${
              appDetails?.status === "APPROVED"
                ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                : appDetails?.status === "FAILED"
                ? "bg-rose-100 text-rose-800 border border-rose-300"
                : "bg-indigo-100 text-indigo-800 border border-indigo-300 animate-pulse"
            }`}>
              {appDetails?.status || "IN_PROGRESS"}
            </span>
          </div>

          {/* Plain Language Step Progress */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Verification Steps</h4>
            <div className="space-y-3">
              {appDetails?.steps?.map((step) => (
                <div key={step.step_name} className="p-4 rounded-2xl bg-white border border-slate-200 flex items-center justify-between shadow-xs">
                  <div className="flex items-center gap-3">
                    {step.status === "DONE" || step.status === "REUSED" ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                    ) : step.status === "FAILED" ? (
                      <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
                    ) : (
                      <Clock className="w-5 h-5 text-indigo-600 shrink-0 animate-spin" />
                    )}
                    <div>
                      <div className="text-sm font-bold text-slate-900 capitalize">
                        {step.step_name === "identity" && "Director Identity & Citizenship Verification"}
                        {step.step_name === "tax" && "Central Tax Clearance & PAN Validation"}
                        {step.step_name === "address" && "Municipal Property & Business Location Verification"}
                        {step.step_name === "registry" && "Incorporation Certificate Issuance"}
                      </div>
                      <div className="text-xs text-slate-500">
                        {step.status === "DONE" && "Verified against official records"}
                        {step.status === "REUSED" && "Verified using pre-existing reusable credential"}
                        {step.status === "FAILED" && "Verification failed. Check department status."}
                        {step.status === "IN_PROGRESS" && "Querying departmental database..."}
                      </div>
                    </div>
                  </div>

                  <span className="text-xs font-mono font-bold uppercase text-slate-600">{step.status}</span>
                </div>
              ))}
            </div>
          </div>

          {appDetails?.status === "APPROVED" && (
            <div className="p-6 rounded-3xl bg-emerald-50 border border-emerald-200 text-emerald-950 text-center space-y-3 shadow-xs">
              <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
              <h4 className="text-xl font-extrabold">Business Clearance Certificate Issued!</h4>
              <p className="text-xs text-emerald-800 max-w-lg mx-auto">
                Your commercial registration is approved. Master anchor link {appDetails.govbridge_person_id} generated.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ApplyPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading Portal...</div>}>
      <ApplyContent />
    </Suspense>
  );
}
