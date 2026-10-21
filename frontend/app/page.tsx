"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, ShieldCheck, Activity, Terminal, Layers, Cpu, Database } from "lucide-react";
import { fetchPing } from "@/lib/api";

export default function HomePage() {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    fetchPing()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  return (
    <div className="relative isolate overflow-hidden flex-1 flex flex-col justify-center py-16 sm:py-24">
      {/* Background glow decoration */}
      <div
        className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80"
        aria-hidden="true"
      >
        <div
          className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-indigo-500 to-sky-400 opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"
          style={{
            clipPath:
              "polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)",
          }}
        />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
        {/* Status Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-700/80 text-xs text-slate-300 shadow-inner">
          <span
            className={`w-2 h-2 rounded-full ${
              apiOnline === true
                ? "bg-emerald-400 animate-pulse"
                : apiOnline === false
                ? "bg-rose-400"
                : "bg-amber-400 animate-ping"
            }`}
          />
          <span className="font-medium">Phase 1: Core Foundation & Telemetry</span>
          <span className="text-slate-500">|</span>
          <span className="text-indigo-400">
            {apiOnline === true ? "Backend Connected" : apiOnline === false ? "Backend Offline" : "Probing Backend..."}
          </span>
        </div>

        {/* Hero Headlines */}
        <div className="max-w-3xl mx-auto space-y-4">
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            InternPilot <span className="bg-gradient-to-r from-indigo-400 to-sky-400 bg-clip-text text-transparent">AI</span>
          </h1>
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
            The next-generation career co-pilot for discovering verified internships, analyzing credibility,
            matching candidates to high-impact roles, and accelerating outreach.
          </p>
        </div>

        {/* Call to Actions */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link
            href="/status"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all shadow-lg shadow-indigo-600/30 glow-border"
          >
            <Activity className="w-4 h-4" />
            View Live Health Status
            <ArrowRight className="w-4 h-4" />
          </Link>

          <a
            href="http://localhost:8000/api/v1/docs"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 font-medium text-sm transition-all shadow-sm"
          >
            <Terminal className="w-4 h-4 text-indigo-400" />
            FastAPI OpenAPI Docs
          </a>
        </div>

        {/* Architectural Pillars */}
        <div className="pt-12 grid grid-cols-1 md:grid-cols-4 gap-6 text-left max-w-5xl mx-auto">
          <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
            <Layers className="w-5 h-5 text-indigo-400 mb-2" />
            <h2 className="text-sm font-semibold text-white">Modular Monorepo</h2>
            <p className="text-xs text-slate-400 mt-1">
              Separation of concerns across Next.js frontend, FastAPI backend, and shared contracts.
            </p>
          </div>

          <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
            <Cpu className="w-5 h-5 text-sky-400 mb-2" />
            <h2 className="text-sm font-semibold text-white">FastAPI & Pydantic v2</h2>
            <p className="text-xs text-slate-400 mt-1">
              High-performance asynchronous REST services with strict type models and runtime validation.
            </p>
          </div>

          <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
            <Database className="w-5 h-5 text-emerald-400 mb-2" />
            <h2 className="text-sm font-semibold text-white">PostgreSQL & Alembic</h2>
            <p className="text-xs text-slate-400 mt-1">
              SQLAlchemy 2.0 async engine with safe versioned schema migration workflows.
            </p>
          </div>

          <div className="glass-card p-5 rounded-2xl border border-slate-800/80">
            <ShieldCheck className="w-5 h-5 text-amber-400 mb-2" />
            <h2 className="text-sm font-semibold text-white">Live Health Probing</h2>
            <p className="text-xs text-slate-400 mt-1">
              Active round-trip connection probes for database and cache latency telemetry.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
