"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { RISK_TREND_DATA } from "@/lib/data/antarctic-data";

export function RiskChart() {
  return (
    <div className="w-full rounded-lg bg-[#102631]/90 backdrop-blur-md border border-[rgba(120,180,200,0.2)] p-4 text-xs font-mono select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pb-2.5 border-b border-[rgba(120,180,200,0.12)]">
        <div>
          <h4 className="text-sm font-semibold text-white tracking-wide font-sans">
            24-Hour Corridor Risk Evolution
          </h4>
          <span className="text-[10px] text-[#526f80]">
            Multi-Source Hazard Weighting: Pack Ice (45%) · Icebergs (35%) · Weather (20%)
          </span>
        </div>

        <div className="flex items-center gap-3 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-400" />
            <span className="text-[#8ea8b7]">Critical (&gt;75)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-orange-400" />
            <span className="text-[#8ea8b7]">High (&gt;60)</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-44 w-full mt-3">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={RISK_TREND_DATA} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(120, 180, 200, 0.08)"
              vertical={false}
            />

            <XAxis
              dataKey="hour"
              stroke="#526f80"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: "rgba(120, 180, 200, 0.15)" }}
            />

            <YAxis
              stroke="#526f80"
              fontSize={10}
              domain={[0, 100]}
              tickLine={false}
              axisLine={{ stroke: "rgba(120, 180, 200, 0.15)" }}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="rounded-md bg-[#061014] border border-[rgba(120,180,200,0.25)] p-2.5 shadow-xl text-[11px]">
                    <div className="text-[#8ea8b7] font-semibold">{label} Projected</div>
                    <div className="text-white mt-1">
                      Composite Risk: <span className="text-orange-400 font-bold">{d.score} / 100</span>
                    </div>
                    <div className="text-[10px] text-[#628294]">
                      Interval: {d.lower} – {d.upper}
                    </div>
                  </div>
                );
              }}
            />

            <ReferenceLine y={60} stroke="#fb923c" strokeDasharray="3 3" />
            <ReferenceLine y={75} stroke="#f87171" strokeDasharray="3 3" />

            <Area
              type="monotone"
              dataKey="score"
              stroke="#f97316"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#riskGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-[rgba(120,180,200,0.1)] text-[10px] text-[#526f80]">
        <span>Corridor Checkpoint: Gerlache Northern Approaches</span>
        <span className="text-cyan-400">Peak Threat at +16h (71 Index)</span>
      </div>
    </div>
  );
}

