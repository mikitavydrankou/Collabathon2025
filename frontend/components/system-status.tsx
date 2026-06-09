"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, XCircle, Loader2 } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type State = "up" | "down" | "loading";

const SERVICES = [
  { id: "gateway", label: "API Gateway", path: "/health", role: "nginx · routes by prefix" },
  { id: "auth", label: "Auth Service", path: "/status/auth", role: "JWT · users" },
  { id: "transactions", label: "Transactions Service", path: "/status/transactions", role: "transfers · Kafka producer" },
  { id: "chatbot", label: "Chatbot Service", path: "/status/chatbot", role: "LLM · MCP" },
  { id: "qa", label: "QA Service", path: "/status/qa", role: "RAG · SQL agents" },
];

const WORKERS = [
  { label: "Embedding Worker", role: "consumes transactions.created → ChromaDB" },
  { label: "Anomaly Worker", role: "consumes transactions.created → flags" },
];

const STACK = [
  "FastAPI", "PostgreSQL", "Kafka (KRaft)", "Redis", "ChromaDB",
  "Nginx", "Prometheus", "Docker", "Kubernetes", "Terraform",
];

// Static nginx rate-limit zones, mirrored from gateway/nginx.conf.
const RATE_LIMITS = [
  { label: "General traffic", value: "20 req/s", note: "burst 40" },
  { label: "AI endpoints (chatbot, QA)", value: "20 req/min", note: "burst 5" },
  { label: "Money creation", value: "30 req/min", note: "burst 10" },
];

type Usage = { used: number; limit: number; enabled: boolean };

async function ping(path: string): Promise<State> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 4000);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, { signal: controller.signal });
    return res.ok ? "up" : "down";
  } catch {
    return "down";
  } finally {
    clearTimeout(timer);
  }
}

function StatusDot({ state }: { state: State }) {
  if (state === "loading")
    return <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />;
  if (state === "up")
    return <CheckCircle2 className="w-5 h-5 text-green-500" />;
  return <XCircle className="w-5 h-5 text-red-500" />;
}

export default function SystemStatus({ onBack }: { onBack: () => void }) {
  const [status, setStatus] = useState<Record<string, State>>(
    Object.fromEntries(SERVICES.map((s) => [s.id, "loading"])),
  );
  const [usage, setUsage] = useState<Usage | null>(null);
  const [resetting, setResetting] = useState(false);
  const [resetMsg, setResetMsg] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);

  const handleReset = async () => {
    setResetting(true);
    setResetMsg(null);
    try {
      const res = await fetch(`${API_BASE_URL}/admin/reset-db`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResetMsg("Demo data reset successfully. Reloading…");
      setConfirmReset(false);
      // Wipe client state so the app opens like a fresh first launch.
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch {}
      setTimeout(() => window.location.reload(), 1200);
    } catch (e) {
      setResetMsg("Reset failed — try again.");
      setResetting(false);
      setConfirmReset(false);
    }
  };

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      const entries = await Promise.all(
        SERVICES.map(async (s) => [s.id, await ping(s.path)] as const),
      );
      if (active) setStatus(Object.fromEntries(entries));

      try {
        const res = await fetch(`${API_BASE_URL}/status/usage`);
        if (active && res.ok) setUsage(await res.json());
      } catch {
        if (active) setUsage(null);
      }
    };
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const upCount = Object.values(status).filter((s) => s === "up").length;

  return (
    <div className="min-h-screen bg-slate-50 pb-24">
      <div className="bg-gradient-to-b from-slate-800 to-slate-700 text-white px-4 pt-12 pb-6">
        <button onClick={onBack} className="flex items-center gap-2 text-slate-200 mb-4">
          <ArrowLeft className="w-5 h-5" />
          <span className="text-sm">Back</span>
        </button>
        <h1 className="text-2xl font-semibold">System</h1>
        <p className="text-slate-300 text-sm mt-1">
          Live status of the microservices behind this app · {upCount}/{SERVICES.length} up
        </p>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-4 space-y-4">
        <div className="bg-amber-50 border border-amber-100 rounded-xl shadow-sm p-4">
          <p className="text-amber-800 text-xs">
            💡 Tip: stay on the dashboard — every 10 seconds help windows
            pop up (3 types).
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-slate-900 font-medium text-sm mb-3">Services</h2>
          <div className="space-y-2">
            {SERVICES.map((s) => (
              <div key={s.id} className="flex items-center gap-3 py-1">
                <StatusDot state={status[s.id]} />
                <div className="flex-1">
                  <div className="text-slate-900 text-sm font-medium">{s.label}</div>
                  <div className="text-slate-400 text-xs">{s.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-slate-900 font-medium text-sm mb-1">Async pipeline</h2>
          <p className="text-slate-400 text-xs mb-3">
            A transfer publishes <code>transactions.created</code> to Kafka; two
            independent consumer groups process it off the request path.
          </p>
          <div className="space-y-2">
            {WORKERS.map((w) => (
              <div key={w.label} className="flex items-center gap-3 py-1">
                <span className="w-2 h-2 rounded-full bg-purple-500" />
                <div className="flex-1">
                  <div className="text-slate-900 text-sm font-medium">{w.label}</div>
                  <div className="text-slate-400 text-xs">{w.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-slate-900 font-medium text-sm mb-1">Limits</h2>
          <p className="text-slate-400 text-xs mb-3">
            This is a public demo, so AI usage and request rates are capped to
            protect the OpenAI budget.
          </p>

          {usage && usage.enabled ? (
            (() => {
              const left = Math.max(0, usage.limit - usage.used);
              const pct = Math.min(100, Math.round((usage.used / usage.limit) * 100));
              const bar =
                pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-amber-500" : "bg-green-500";
              const leftColor =
                left === 0 ? "text-red-600" : left <= usage.limit * 0.3 ? "text-amber-600" : "text-green-600";
              return (
                <div className="mb-4">
                  <div className="flex items-baseline justify-between mb-1">
                    <span className="text-slate-600 text-xs">AI calls left today</span>
                    <span className={`font-bold text-2xl tabular-nums ${leftColor}`}>
                      {left}
                      <span className="text-slate-400 text-sm font-normal"> / {usage.limit}</span>
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div className={`h-full ${bar}`} style={{ width: `${pct}%` }} />
                  </div>
                  <div className="text-slate-400 text-xs mt-1">
                    {usage.used} used · resets daily
                  </div>
                </div>
              );
            })()
          ) : (
            <div className="text-slate-400 text-xs mb-4">
              AI daily cap inactive (no Redis) — requests run uncapped.
            </div>
          )}

          <div className="space-y-2">
            {RATE_LIMITS.map((r) => (
              <div key={r.label} className="flex items-center justify-between gap-3">
                <div className="flex-1">
                  <div className="text-slate-900 text-sm">{r.label}</div>
                  <div className="text-slate-400 text-xs">{r.note}</div>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs whitespace-nowrap">
                  {r.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-slate-900 font-medium text-sm mb-3">Stack</h2>
          <div className="flex flex-wrap gap-2">
            {STACK.map((tag) => (
              <span
                key={tag}
                className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-xs"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4 border border-red-100">
          <h2 className="text-slate-900 font-medium text-sm mb-1">Demo data</h2>
          <p className="text-slate-400 text-xs mb-3">
            Wipe all users, transactions and contacts, then re-seed the original
            demo dataset. This cannot be undone.
          </p>

          {resetMsg && (
            <div
              className={`text-xs mb-3 ${
                resetMsg.includes("success") ? "text-green-600" : "text-red-600"
              }`}
            >
              {resetMsg}
            </div>
          )}

          {confirmReset ? (
            <div className="flex gap-2">
              <button
                onClick={handleReset}
                disabled={resetting}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-60 transition-colors"
              >
                {resetting && <Loader2 className="w-4 h-4 animate-spin" />}
                {resetting ? "Resetting…" : "Yes, reset"}
              </button>
              <button
                onClick={() => setConfirmReset(false)}
                disabled={resetting}
                className="flex-1 px-3 py-2 rounded-lg bg-slate-100 text-slate-700 text-sm font-medium hover:bg-slate-200 disabled:opacity-60 transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => {
                setResetMsg(null);
                setConfirmReset(true);
              }}
              className="w-full px-3 py-2 rounded-lg border border-red-300 text-red-600 text-sm font-medium hover:bg-red-50 transition-colors"
            >
              Reset demo data
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
