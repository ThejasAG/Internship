"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Database, Zap, Server, RefreshCw, AlertOctagon, CheckCircle } from "lucide-react";
import { fetchHealthStatus, HealthResponse } from "@/lib/api";
import { StatusCard } from "@/components/StatusCard";

export default function StatusPage() {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHealthStatus();
      setHealthData(data);
      setLastChecked(new Date());
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unable to connect to the backend API.");
      }
      setHealthData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();

    if (!autoRefresh) return;
    const interval = setInterval(() => {
      loadStatus();
    }, 15000);

    return () => clearInterval(interval);
  }, [loadStatus, autoRefresh]);

  const getSystemBanner = () => {
    if (error) {
      return (
        <div className="p-4 rounded-2xl bg-rose-950/60 border border-rose-800/80 text-rose-200 flex items-start gap-3 shadow-lg">
          <AlertOctagon className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <span className="font-semibold block text-rose-100">API Connection Unavailable</span>
            <span>{error}</span>
            <span className="block mt-1 text-xs text-rose-300">
              Ensure FastAPI backend is running at <code className="bg-rose-900/50 px-1 py-0.5 rounded font-mono">http://localhost:8000</code>.
            </span>
          </div>
        </div>
      );
    }

    if (!healthData) return null;

    if (healthData.status === "healthy") {
      return (
        <div className="p-4 rounded-2xl bg-emerald-950/50 border border-emerald-800/60 text-emerald-200 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <div>
              <span className="font-semibold text-sm text-emerald-100">All Systems Operational</span>
              <p className="text-xs text-emerald-300/80">
                FastAPI, PostgreSQL database, and Redis background services are verified responsive.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-900/60 border border-emerald-700/50 text-emerald-200">
            {healthData.environment.toUpperCase()}
          </span>
        </div>
      );
    }

    return (
      <div className="p-4 rounded-2xl bg-amber-950/60 border border-amber-800/80 text-amber-200 flex items-center gap-3 shadow-lg">
        <AlertOctagon className="w-5 h-5 text-amber-400 flex-shrink-0" />
        <div>
          <span className="font-semibold text-sm text-amber-100">System Partially Degraded</span>
          <p className="text-xs text-amber-300/80">
            One or more backing services is disconnected or responding with latency.
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full space-y-8">
      {/* Title & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            System Infrastructure Status
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time health telemetry connecting to InternPilot AI backend service.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 flex items-center gap-2 cursor-pointer bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-slate-700 text-indigo-500 focus:ring-0"
            />
            Auto-refresh (15s)
          </label>

          <button
            onClick={() => loadStatus()}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-all disabled:opacity-50 shadow-md shadow-indigo-600/20"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Global Status Banner */}
      {getSystemBanner()}

      {/* Component Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatusCard
          title="FastAPI Backend"
          subtitle="Core REST API gateway"
          icon={<Server className="w-6 h-6" />}
          status={
            healthData
              ? {
                  status: "connected",
                  latency_ms: null,
                  details: `v${healthData.version} (${healthData.environment})`,
                  error: null,
                }
              : error
              ? {
                  status: "disconnected",
                  latency_ms: null,
                  details: null,
                  error: error,
                }
              : null
          }
          isLoading={loading}
        />

        <StatusCard
          title="PostgreSQL 16"
          subtitle="Primary relational database via SQLAlchemy 2.0"
          icon={<Database className="w-6 h-6" />}
          status={healthData ? healthData.database : null}
          isLoading={loading}
        />

        <StatusCard
          title="Redis & Celery"
          subtitle="Task queue broker & state store"
          icon={<Zap className="w-6 h-6" />}
          status={healthData ? healthData.queue : null}
          isLoading={loading}
        />
      </div>

      {/* Telemetry Details */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <h2 className="text-base font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <span>Active Diagnostics Payload</span>
          <span className="text-xs font-normal text-slate-500">
            {lastChecked ? `(Updated ${lastChecked.toLocaleTimeString()})` : ""}
          </span>
        </h2>

        <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800/80 font-mono text-xs text-indigo-300 overflow-x-auto">
          <pre>{JSON.stringify(healthData || { error: error || "No payload loaded" }, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
}
