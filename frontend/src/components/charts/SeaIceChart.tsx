"use client";

import React, { useState } from "react";
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
import { SEA_ICE_FORECAST_DATA } from "@/lib/data/antarctic-data";

export function SeaIceChart() {
  const [horizon, setHorizon] = useState<"24h" | "48h" | "72h" | "7d">("48h");

  return (
    <div className="w-full rounded-lg bg-[#102631]/90 backdrop-blur-md border border-[rgba(120,180,200,0.2)] p-4 text-xs font-mono select-none">
      {/* Chart Header with Horizon Pills */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-[rgba(120,180,200,0.12)]">
        <div>
          <h4 className="text-sm font-semibold text-white tracking-wide font-sans">
            Sea Ice Concentration Evolution & Forecast
          </h4>
          <span className="text-[10px] text-[#526f80]">
            Ensemble Polar Ice Ocean Modeling (PIOMAS + Sentinel-1 SAR)
          </span>
        </div>

        <div className="flex items-center gap-1 p-1 rounded bg-[#061014] border border-[rgba(120,180,200,0.15)]">
          {(["24h", "48h", "72h", "7d"] as const).map((h) => (
            <button
              key={h}
              type="button"
              onClick={() => setHorizon(h)}
              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors ${
                horizon === h
                  ? "bg-cyan-500 text-black shadow-sm"
                  : "text-[#8ea8b7] hover:text-white"
              }`}
            >
              {h.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Body */}
      <div className="h-52 w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={SEA_ICE_FORECAST_DATA}
            margin={{ top: 10, right: 10, left: -25, bottom: 0 }}
          >
            <defs>
              <linearGradient id="iceForecastGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(120, 180, 200, 0.08)"
              vertical={false}
            />

            <XAxis
              dataKey="time"
              stroke="#526f80"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: "rgba(120, 180, 200, 0.15)" }}
            />

            <YAxis
              stroke="#526f80"
              fontSize={10}
              domain={[50, 90]}
              tickLine={false}
              axisLine={{ stroke: "rgba(120, 180, 200, 0.15)" }}
              tickFormatter={(val) => `${val}%`}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                const data = payload[0].payload;
                return (
                  <div className="rounded-md bg-[#061014] border border-[rgba(120,180,200,0.25)] p-2.5 shadow-xl text-[11px]">
                    <div className="text-[#8ea8b7] font-semibold">{label} UTC</div>
                    {data.current !== null && (
                      <div className="text-white mt-1">
                        Observed: <span className="text-cyan-300 font-bold">{data.current}%</span>
                      </div>
                    )}
                    <div className="text-sky-300">
                      Forecast Model: <span className="font-bold">{data.predicted}%</span>
                    </div>
                  </div>
                );
              }}
            />

            <ReferenceLine
              y={75}
              stroke="#f87171"
              strokeDasharray="3 3"
              label={{
                value: "Polar Class 6 Operational Limit (75%)",
                fill: "#f87171",
                fontSize: 9,
                position: "top",
              }}
            />

            <Area
              type="monotone"
              dataKey="predicted"
              stroke="#38bdf8"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#iceForecastGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-[rgba(120,180,200,0.1)] text-[10px] text-[#526f80]">
        <span>Horizontal Resolution: 1 km Sentinel Synthetic Mesh</span>
        <span className="text-[#8ea8b7]">Confidence Index: 92.4%</span>
      </div>
    </div>
  );
}

