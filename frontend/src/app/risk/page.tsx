"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { AppShell } from "@/components/layout/AppShell";

const NavigationMap = dynamic(
  () => import("@/components/map/NavigationMap").then((mod) => mod.NavigationMap),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#061014] text-cyan-400 font-mono">
        <div className="h-12 w-12 rounded-full border border-cyan-500/20 border-t-cyan-400 animate-spin mb-3" />
        <span className="text-xs uppercase tracking-widest text-cyan-300">Loading Hazard Matrix…</span>
      </div>
    ),
  }
);
import { MapLayers, LayerVisibilityState } from "@/components/map/MapLayers";
import { RiskPanel } from "@/components/panels/RiskPanel";
import { RiskChart } from "@/components/charts/RiskChart";
import { RISK_ZONES, RiskZone } from "@/lib/data/antarctic-data";
import { AlertTriangle, ShieldCheck, Flame, Waves, Wind } from "lucide-react";

export default function RiskPage() {
  const [selectedZone, setSelectedZone] = useState<RiskZone>(RISK_ZONES[1]); // Default to Gerlache
  const [activeHazardFilter, setActiveHazardFilter] = useState<string>("all");
  const [showRiskChart, setShowRiskChart] = useState(true);

  const [layers, setLayers] = useState<LayerVisibilityState>({
    coastline: true,
    seaIce: true,
    icebergs: true,
    vesselTrack: true,
    riskZones: true,
    contours: true,
  });

  return (
    <AppShell title="Risk Intelligence" subtitle="Multi-Hazard Threat Assessment" hideChromePadding>
      <div className="relative w-full h-full overflow-hidden flex flex-col">
        {/* Top Hazard Filter Bar */}
        <div className="h-12 px-6 bg-[#0B1820]/95 backdrop-blur-md border-b border-[rgba(120,180,200,0.15)] flex items-center justify-between z-20 select-none text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-[#628294] mr-2">HAZARD WEIGHT:</span>
            {[
              { id: "all", label: "Composite Matrix" },
              { id: "ice", label: "Pack Ice Pressure" },
              { id: "berg", label: "Iceberg Drift Vectors" },
              { id: "swell", label: "Gale Swell" },
            ].map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => setActiveHazardFilter(f.id)}
                className={`px-3 py-1 rounded text-xs font-semibold tracking-wider transition-colors ${
                  activeHazardFilter === f.id
                    ? "bg-cyan-500 text-black shadow-md"
                    : "bg-[#061014] text-[#8ea8b7] border border-[rgba(120,180,200,0.15)] hover:text-white"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowRiskChart(!showRiskChart)}
              className="px-2.5 py-1 rounded bg-[#102631] text-cyan-300 border border-cyan-500/30 hover:bg-[#153444] transition-colors"
            >
              {showRiskChart ? "HIDE CORRIDOR CHART" : "VIEW 24H RISK CHART"}
            </button>
          </div>
        </div>

        {/* Map Viewport */}
        <div className="relative flex-1 w-full h-full overflow-hidden">
          <NavigationMap
            layers={layers}
            highlightZoneId={selectedZone.id}
            onSelectRiskZone={setSelectedZone}
          />

          {/* Floating Layers */}
          <div className="absolute top-4 left-4 z-20">
            <MapLayers layers={layers} onChange={setLayers} />
          </div>

          {/* Right Floating Risk Detail Panel */}
          <div className="absolute top-4 right-4 z-20">
            <RiskPanel
              zone={selectedZone}
              onClose={() => {}}
            />
          </div>

          {/* Bottom 24-Hour Corridor Risk Evolution Chart */}
          {showRiskChart && (
            <div className="absolute bottom-4 left-4 right-96 z-20 animate-in slide-in-from-bottom-2 duration-200">
              <RiskChart />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

