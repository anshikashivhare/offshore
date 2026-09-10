"use client";

import React from "react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { ANALYTICS_TRENDS } from "@/lib/data/antarctic-data";

interface AnalyticsChartProps {
  type: "seaIce" | "icebergs" | "performance";
}

export function AnalyticsChart({ type }: AnalyticsChartProps) {
  if (type === "seaIce") {
    return (
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={ANALYTICS_TRENDS.seaIce} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="currentIceGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(120, 180, 200, 0.08)" vertical={false} />
            <XAxis dataKey="month" stroke="#526f80" fontSize={10} tickLine={false} />
            <YAxis stroke="#526f80" fontSize={10} tickLine={false} tickFormatter={(v) => `${v}%`} />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                return (
                  <div className="rounded-md bg-[#061014] border border-[rgba(120,180,200,0.25)] p-2.5 shadow-xl text-[11px] font-mono">
                    <div className="text-[#8ea8b7] font-semibold">{label} Concentration</div>
                    <div className="text-cyan-300 mt-1">2025: {payload[0]?.value}%</div>
                    <div className="text-[#628294]">Baseline (10-yr): {payload[1]?.value}%</div>
                  </div>
                );
              }}
            />
            <Area type="monotone" dataKey="year2025" stroke="#22d3ee" strokeWidth={2} fill="url(#currentIceGrad)" name="2025 Observed" />
            <Area type="monotone" dataKey="baseline" stroke="#64748b" strokeWidth={1.5} strokeDasharray="4 4" fill="none" name="10-Yr Mean Baseline" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === "icebergs") {
    return (
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={ANALYTICS_TRENDS.icebergs} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(120, 180, 200, 0.08)" vertical={false} />
            <XAxis dataKey="week" stroke="#526f80" fontSize={10} tickLine={false} />
            <YAxis stroke="#526f80" fontSize={10} tickLine={false} />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="rounded-md bg-[#061014] border border-[rgba(120,180,200,0.25)] p-2.5 shadow-xl text-[11px] font-mono">
                    <div className="text-white font-semibold">{label} Detections</div>
                    <div className="text-[#38bdf8] mt-1">Total Tracked: {d.detected}</div>
                    <div className="text-orange-400">High Risk Bergs: {d.highRisk}</div>
                  </div>
                );
              }}
            />
            <Bar dataKey="detected" fill="#0284c7" radius={[2, 2, 0, 0]} name="Total Detected" />
            <Bar dataKey="highRisk" fill="#fb923c" radius={[2, 2, 0, 0]} name="High Collision Risk" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={ANALYTICS_TRENDS.performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(120, 180, 200, 0.08)" vertical={false} />
          <XAxis dataKey="voyage" stroke="#526f80" fontSize={10} tickLine={false} />
          <YAxis stroke="#526f80" fontSize={10} domain={[60, 100]} tickLine={false} tickFormatter={(v) => `${v}%`} />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || !payload.length) return null;
              const d = payload[0].payload;
              return (
                <div className="rounded-md bg-[#061014] border border-[rgba(120,180,200,0.25)] p-2.5 shadow-xl text-[11px] font-mono">
                  <div className="text-white font-semibold">{label} Efficiency</div>
                  <div className="text-emerald-400 mt-1">Safety Index: {d.safeScore}%</div>
                  <div className="text-cyan-300">Fuel Optimization: {d.fuelEfficiency}%</div>
                </div>
              );
            }}
          />
          <Bar dataKey="safeScore" fill="#34d399" radius={[2, 2, 0, 0]} name="Safety Index" />
          <Bar dataKey="fuelEfficiency" fill="#22d3ee" radius={[2, 2, 0, 0]} name="Fuel Efficiency" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

