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
        <span className="text-xs uppercase tracking-widest text-cyan-300">Loading Sea Ice Mesh…</span>
      </div>
    ),
  }
);
import { MapLayers, LayerVisibilityState } from "@/components/map/MapLayers";
import { SeaIceLegend } from "@/components/map/SeaIceLegend";
import { SeaIcePanel } from "@/components/panels/SeaIcePanel";
import { SeaIceChart } from "@/components/charts/SeaIceChart";
import { Calendar, ChevronDown, Radio } from "lucide-react";

export default function SeaIcePage() {
  const [region, setRegion] = useState("Gerlache Passage");
  const [layers, setLayers] = useState<LayerVisibilityState>({
    coastline: true,
    seaIce: true,
    icebergs: false,
    vesselTrack: false,
    riskZones: false,
    contours: true,
  });
  const [showForecastChart, setShowForecastChart] = useState(false);

  return (
    <AppShell title="Sea Ice Intelligence" subtitle="SAR Pack Ice Concentration & Modeling" hideChromePadding>
      <div className="relative w-full h-full overflow-hidden flex flex-col">
        {/* Top Minimal Control Strip */}
        <div className="h-12 px-6 bg-[#0B1820]/95 backdrop-blur-md border-b border-[rgba(120,180,200,0.15)] flex items-center justify-between z-20 select-none text-xs font-mono">
          <div className="flex items-center gap-4">
            {/* Region Selector */}
            <div className="flex items-center gap-2">
              <span className="text-[#628294]">SECTOR:</span>
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="bg-[#061014] border border-[rgba(120,180,200,0.2)] text-white px-2.5 py-1 rounded focus:outline-none focus:border-cyan-400 cursor-pointer"
              >
                <option value="Gerlache Passage">Gerlache Passage Corridor</option>
                <option value="Weddell Sea">Weddell Sea Pack</option>
                <option value="Ross Sea">Ross Sea Marginal Zone</option>
                <option value="Bellingshausen">Bellingshausen Shelf</option>
              </select>
            </div>

            {/* Satellite Source Indicator */}
            <div className="hidden sm:flex items-center gap-2 text-[#8ea8b7]">
              <Radio size={13} className="text-cyan-400" />
              <span>Sentinel-1 SAR C-Band · 25m Resolution</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowForecastChart(!showForecastChart)}
              className={`px-3 py-1 rounded text-xs font-semibold tracking-wider transition-colors ${
                showForecastChart
                  ? "bg-cyan-500 text-black"
                  : "bg-[#102631] text-cyan-300 border border-cyan-500/40 hover:bg-[#163545]"
              }`}
            >
              {showForecastChart ? "HIDE FORECAST CHART" : "EXPAND FORECAST MODEL"}
            </button>
          </div>
        </div>

        {/* Tactical Map Container */}
        <div className="relative flex-1 w-full h-full overflow-hidden">
          <NavigationMap
            layers={layers}
            iceOpacity={0.8}
            activeRouteId="safest"
          />

          {/* Floating Controls */}
          <div className="absolute top-4 left-4 z-20">
            <MapLayers layers={layers} onChange={setLayers} />
          </div>



          {/* Right Floating Inspection Panel */}
          <div className="absolute top-4 right-4 z-20">
            <SeaIcePanel
              regionName={region}
              concentration={68}
              thicknessM={1.4}
              pressureKPa={142}
              onViewForecast={() => setShowForecastChart(true)}
            />
          </div>

          {/* Bottom Expandable Forecast Chart Drawer */}
          {showForecastChart && (
            <div className="absolute bottom-4 left-64 right-96 z-30 animate-in slide-in-from-bottom-3 duration-300">
              <SeaIceChart />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

