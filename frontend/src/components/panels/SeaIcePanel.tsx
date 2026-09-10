"use client";

import React from "react";
import { X, Layers, Activity, Gauge, Compass } from "lucide-react";

interface SeaIcePanelProps {
  regionName?: string;
  concentration?: number;
  thicknessM?: number;
  pressureKPa?: number;
  stage?: string;
  onClose?: () => void;
  onViewForecast?: () => void;
}

export function SeaIcePanel({
  regionName = "Gerlache Passage Corridor",
  concentration = 68,
  thicknessM = 1.4,
  pressureKPa = 142,
  stage = "Medium First-Year Pack Ice",
  onClose,
  onViewForecast,
}: SeaIcePanelProps) {
  return (
    <div className="w-80 rounded-lg bg-[#102631]/95 backdrop-blur-md border border-[rgba(120,180,200,0.25)] shadow-2xl p-4 text-xs font-mono select-none z-30 animate-in fade-in slide-in-from-right-2 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-[rgba(120,180,200,0.15)]">
        <div>
          <div className="flex items-center gap-1.5">
            <Layers size={14} className="text-cyan-400" />
            <h3 className="font-semibold text-sm text-white tracking-wide font-sans">
              {regionName}
            </h3>
          </div>
          <span className="text-[10px] text-[#628294]">
            Synthetic Aperture Radar · Polarimetric Analysis
          </span>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded text-[#8ea8b7] hover:text-white hover:bg-[#0B1820]"
            aria-label="Close Sea Ice Panel"
          >
            <X size={15} />
          </button>
        )}
      </div>

      {/* Primary Concentration Metric */}
      <div className="my-3 p-3 rounded bg-[#061014] border border-[rgba(120,180,200,0.15)]">
        <div className="flex justify-between items-center mb-1">
          <span className="text-[#8ea8b7]">Ice Concentration</span>
          <span className="text-lg font-bold text-white">{concentration}%</span>
        </div>
        <div className="h-2 w-full bg-[#0B1820] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-sky-400 to-cyan-300 transition-all duration-500"
            style={{ width: `${concentration}%` }}
          />
        </div>
        <div className="flex justify-between text-[9px] text-[#526f80] mt-1">
          <span>Navigation: Restricted</span>
          <span>WMO Stage: {stage}</span>
        </div>
      </div>

      {/* Physical State Breakdown */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
          <div className="flex items-center gap-1 text-[10px] text-[#628294]">
            <Gauge size={12} className="text-cyan-400" />
            <span>THICKNESS</span>
          </div>
          <div className="text-white font-bold mt-0.5">{thicknessM} meters</div>
          <span className="text-[9px] text-[#8ea8b7]">Ridge: Up to 2.8m</span>
        </div>

        <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
          <div className="flex items-center gap-1 text-[10px] text-[#628294]">
            <Activity size={12} className="text-cyan-400" />
            <span>PRESSURE</span>
          </div>
          <div className="text-white font-bold mt-0.5">{pressureKPa} kPa</div>
          <span className="text-[9px] text-amber-300">Moderate Shear</span>
        </div>
      </div>

      {/* Navigability Guidance */}
      <div className="p-2.5 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)] mb-3 text-[11px] leading-snug text-[#8ea8b7]">
        <div className="flex items-center gap-1 text-cyan-300 font-semibold mb-1">
          <Compass size={12} />
          <span>OPEN LEAD DETECTION</span>
        </div>
        <p>Continuous leads identified along 284° bearing. Minimum channel width 45m with 0.8m level ice floes.</p>
      </div>

      {/* Trigger */}
      {onViewForecast && (
        <button
          type="button"
          onClick={onViewForecast}
          className="w-full py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-center text-xs tracking-wider transition-colors"
        >
          VIEW 7-DAY FORECAST MODEL →
        </button>
      )}
    </div>
  );
}

