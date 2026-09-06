"use client";

import dynamic from "next/dynamic";
import { useRouteStore } from "@/stores/use-route-store";
import { useMemo } from "react";

// Dynamically import plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function RouteRiskChart() {
  const result = useRouteStore((s) => s.result);

  const plotData = useMemo(() => {
    if (!result || !result.pathMetrics) return null;
    
    return {
      x: result.pathMetrics.map(m => m.distance),
      y: result.pathMetrics.map(m => m.risk),
    };
  }, [result]);

  if (!plotData) {
    return (
      <div className="w-full h-32 flex items-center justify-center text-[10px] uppercase text-[color:var(--fg-muted)] border border-dashed border-[color:var(--border-subtle)] rounded">
        No route planned
      </div>
    );
  }

  return (
    <div className="w-full mt-4">
      <div className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)] mb-2">
        Risk Profile
      </div>
      <div className="w-full h-40 overflow-hidden rounded">
        <Plot
          data={[
            {
              x: plotData.x,
              y: plotData.y,
              type: "scatter",
              mode: "lines",
              fill: "tozeroy",
              line: { color: "var(--accent-route)", width: 2 },
              fillcolor: "rgba(34, 211, 238, 0.2)",
            },
          ]}
          layout={{
            margin: { t: 5, r: 5, l: 25, b: 20 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            xaxis: {
              title: { text: "Distance (NM)", font: { size: 9, color: "#94a3b8" } },
              tickfont: { size: 9, color: "#94a3b8" },
              gridcolor: "rgba(255,255,255,0.05)",
              zerolinecolor: "rgba(255,255,255,0.1)",
            },
            yaxis: {
              tickfont: { size: 9, color: "#94a3b8" },
              gridcolor: "rgba(255,255,255,0.05)",
              zerolinecolor: "rgba(255,255,255,0.1)",
              range: [0, Math.max(...plotData.y, 100)],
            },
            hovermode: "x unified",
            dragmode: false,
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </div>
  );
}
