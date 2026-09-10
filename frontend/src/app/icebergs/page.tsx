"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { NavigationMap } from "@/components/map/NavigationMap";
import { MapLayers, LayerVisibilityState } from "@/components/map/MapLayers";
import { IcebergPanel } from "@/components/panels/IcebergPanel";
import { TRACKED_ICEBERGS, Iceberg } from "@/lib/data/antarctic-data";
import { Mountain, Play, Pause, RotateCcw, AlertTriangle } from "lucide-react";

export default function IcebergsPage() {
  const [selectedBerg, setSelectedBerg] = useState<Iceberg>(TRACKED_ICEBERGS[0]);
  const [forecastHours, setForecastHours] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const [layers, setLayers] = useState<LayerVisibilityState>({
    coastline: true,
    seaIce: false,
    icebergs: true,
    vesselTrack: true,
    riskZones: false,
    contours: true,
  });

  return (
    <AppShell title="Iceberg Intelligence" subtitle="Target Tracking & Drift Projection" hideChromePadding>
      <div className="relative w-full h-full overflow-hidden flex flex-col">
        {/* Top Hazard Target Switcher Bar */}
        <div className="h-12 px-6 bg-[#0B1820]/95 backdrop-blur-md border-b border-[rgba(120,180,200,0.15)] flex items-center justify-between z-20 select-none text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-[#628294] mr-2">TRACKED TARGETS:</span>
            {TRACKED_ICEBERGS.map((berg) => {
              const isSelected = selectedBerg.id === berg.id;
              const isHigh = berg.riskLevel === "High";
              return (
                <button
                  key={berg.id}
                  type="button"
                  onClick={() => setSelectedBerg(berg)}
                  className={`flex items-center gap-2 px-3 py-1 rounded text-xs font-semibold tracking-wider transition-colors ${
                    isSelected
                      ? "bg-cyan-500 text-black shadow-md"
                      : "bg-[#061014] text-[#8ea8b7] border border-[rgba(120,180,200,0.15)] hover:text-white"
                  }`}
                >
                  <Mountain size={13} className={isHigh && !isSelected ? "text-orange-400" : ""} />
                  <span>{berg.name}</span>
                </button>
              );
            })}
          </div>

          <div className="hidden md:flex items-center gap-2 text-[#8ea8b7]">
            <span className="h-2 w-2 rounded-full bg-orange-400 animate-pulse" />
            <span className="text-orange-300 font-semibold">
              B-102 CPA: 14.2 nm in 9.4h
            </span>
          </div>
        </div>

        {/* Map Viewport */}
        <div className="relative flex-1 w-full h-full overflow-hidden">
          <NavigationMap
            layers={layers}
            selectedIcebergId={selectedBerg.id}
            onSelectIceberg={setSelectedBerg}
          />

          {/* Floating Layers */}
          <div className="absolute top-4 left-4 z-20">
            <MapLayers layers={layers} onChange={setLayers} />
          </div>

          {/* Right Floating Inspection Drawer */}
          <div className="absolute top-4 right-4 z-20">
            <IcebergPanel
              iceberg={selectedBerg}
              onClose={() => {}}
              onProjectDrift={() => setForecastHours(24)}
            />
          </div>

          {/* Bottom Floating Drift Timeline Scrubber */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 w-full max-w-xl px-4">
            <div className="p-3 rounded-lg bg-[#0B1820]/95 backdrop-blur-md border border-[rgba(120,180,200,0.25)] shadow-2xl text-xs font-mono select-none">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-white font-semibold">DRIFT PROJECTION SIMULATOR</span>
                  <span className="px-1.5 py-0.5 rounded bg-[#102631] text-[10px] text-cyan-300">
                    +{forecastHours} HOURS AHEAD
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="p-1 rounded text-[#8ea8b7] hover:text-white hover:bg-[#102631]"
                    title={isPlaying ? "Pause" : "Play"}
                  >
                    {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                  </button>
                  <button
                    type="button"
                    onClick={() => setForecastHours(0)}
                    className="p-1 rounded text-[#8ea8b7] hover:text-white hover:bg-[#102631]"
                    title="Reset to Present"
                  >
                    <RotateCcw size={14} />
                  </button>
                </div>
              </div>

              {/* Range Slider */}
              <input
                type="range"
                min="0"
                max="48"
                step="6"
                value={forecastHours}
                onChange={(e) => setForecastHours(parseInt(e.target.value, 10))}
                className="w-full h-1.5 bg-[#061014] rounded-lg accent-cyan-400 cursor-pointer"
              />

              <div className="flex justify-between text-[10px] text-[#526f80] mt-1.5">
                <span>Present (0h)</span>
                <span>+12h</span>
                <span>+24h</span>
                <span>+36h</span>
                <span>+48h Forecast</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

