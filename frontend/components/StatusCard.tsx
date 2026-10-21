import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, Clock } from "lucide-react";
import { ServiceComponentStatus } from "@/lib/api";

interface StatusCardProps {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  status: ServiceComponentStatus | null;
  isLoading: boolean;
}

export function StatusCard({
  title,
  subtitle,
  icon,
  status,
  isLoading,
}: StatusCardProps) {
  const getStatusBadge = () => {
    if (isLoading) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 animate-pulse border border-slate-700">
          <Clock className="w-3.5 h-3.5" /> Checking...
        </span>
      );
    }
    if (!status) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800/80 text-slate-400 border border-slate-700">
          <Clock className="w-3.5 h-3.5" /> Unknown
        </span>
      );
    }
    switch (status.status) {
      case "connected":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 shadow-sm shadow-emerald-900/30">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Operational
          </span>
        );
      case "degraded":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-950/80 text-amber-300 border border-amber-800/80">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Degraded
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-950/80 text-rose-300 border border-rose-800/80">
            <XCircle className="w-3.5 h-3.5 text-rose-400" /> Disconnected
          </span>
        );
    }
  };

  return (
    <div className="glass-card rounded-2xl p-6 border border-slate-800/80 hover:border-slate-700/80 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="p-3 rounded-xl bg-slate-800/70 border border-slate-700/50 text-indigo-400">
            {icon}
          </div>
          {getStatusBadge()}
        </div>

        <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
        <p className="text-xs text-slate-400 mt-1 mb-4">{subtitle}</p>
      </div>

      <div className="pt-4 border-t border-slate-800/60 text-xs space-y-2">
        <div className="flex items-center justify-between text-slate-400">
          <span>Latency:</span>
          <span className="font-mono text-slate-200">
            {status?.latency_ms !== null && status?.latency_ms !== undefined
              ? `${status.latency_ms} ms`
              : "—"}
          </span>
        </div>

        {status?.details && (
          <div className="flex items-center justify-between text-slate-400">
            <span>Message:</span>
            <span className="text-slate-300 truncate max-w-[200px]" title={status.details}>
              {status.details}
            </span>
          </div>
        )}

        {status?.error && (
          <div className="p-2.5 rounded-lg bg-rose-950/50 border border-rose-900/60 text-rose-300 text-xs break-all mt-2 font-mono">
            {status.error}
          </div>
        )}
      </div>
    </div>
  );
}
