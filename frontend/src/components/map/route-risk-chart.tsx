"use client";

import React, { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useRouteStore } from "@/stores/use-route-store";

export function RouteRiskChart() {
  const result = useRouteStore((s) => s.result);

  const chartData = useMemo(() => {
    if (!result || !result.pathMetrics || result.pathMetrics.length === 0) return null;
    return result.pathMetrics.map((m) => ({
      distance: Math.round(m.distance),
      risk: Math.round(m.risk),
    }));
  }, [result]);

  if (!chartData) {
    return (
      <div className="w-full h-32 flex items-center justify-center text-[10px] uppercase text-[color:var(--fg-muted)] border border-dashed border-[color:var(--border-subtle)] rounded font-mono">
        No route planned
      </div>
    );
  }

  return (
    <div className="w-full mt-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)] font-mono">
          Risk Profile
        </span>
        <span className="text-[9px] text-[#526f80] font-mono">
          Distance (NM) vs Risk
        </span>
      </div>
      <div className="w-full h-36 overflow-hidden rounded bg-[rgba(11,24,32,0.6)] border border-[rgba(120,180,200,0.15)] p-1.5">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 8, right: 10, left: -22, bottom: 0 }}>
            <defs>
              <linearGradient id="routeRiskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="2 3"
              stroke="rgba(120, 180, 200, 0.1)"
              vertical={false}
            />
            <XAxis
              dataKey="distance"
              tick={{ fontSize: 9, fill: "#7894a2", fontFamily: "monospace" }}
              tickLine={{ stroke: "rgba(120, 180, 200, 0.2)" }}
              axisLine={{ stroke: "rgba(120, 180, 200, 0.2)" }}
              unit=" NM"
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 9, fill: "#7894a2", fontFamily: "monospace" }}
              tickLine={{ stroke: "rgba(120, 180, 200, 0.2)" }}
              axisLine={{ stroke: "rgba(120, 180, 200, 0.2)" }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="rounded bg-[#0B1820]/95 border border-cyan-500/40 px-2.5 py-1.5 text-[10px] font-mono shadow-xl backdrop-blur-md">
                      <div className="text-[#8ea8b7]">
                        Distance: <span className="text-white font-bold">{data.distance} NM</span>
                      </div>
                      <div className="text-[#8ea8b7]">
                        Risk Index: <span className="text-cyan-400 font-bold">{data.risk} / 100</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="risk"
              stroke="#22d3ee"
              strokeWidth={2}
              fill="url(#routeRiskGradient)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
