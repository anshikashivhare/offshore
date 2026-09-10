"use client";

import React from "react";
import { VesselTelemetry } from "@/lib/data/antarctic-data";
import { X, Shield, Navigation, Wind, Thermometer, Compass, Fuel } from "lucide-react";
import Link from "next/link";

interface VesselPanelProps {
  vessel: VesselTelemetry;
  onClose: () => void;
}

export function VesselPanel({ vessel, onClose }: VesselPanelProps) {
  return (
    <div className="w-80 rounded-lg bg-[#102631]/95 backdrop-blur-md border border-[rgba(120,180,200,0.25)] shadow-2xl p-4 text-xs font-mono select-none z-30 animate-in fade-in slide-in-from-right-2 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-[rgba(120,180,200,0.15)]">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-cyan-400" />
            <h3 className="font-semibold text-sm text-white tracking-wide font-sans">
              {vessel.name}
            </h3>
          </div>
          <span className="text-[10px] text-[#628294]">
            Callsign: {vessel.callsign} · {vessel.iceClass}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded text-[#8ea8b7] hover:text-white hover:bg-[#0B1820]"
          aria-label="Close Vessel Panel"
        >
          <X size={15} />
        </button>
      </div>

      {/* Navigation Metrics */}
      <div className="grid grid-cols-2 gap-2 my-3">
        <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
          <div className="flex items-center gap-1 text-[#628294] text-[10px]">
            <Compass size={12} className="text-cyan-400" />
            <span>HEADING</span>
          </div>
          <div className="text-sm font-bold text-white mt-0.5">
            {vessel.heading}° <span className="text-[10px] text-[#8ea8b7]">SSW</span>
          </div>
        </div>

        <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
          <div className="flex items-center gap-1 text-[#628294] text-[10px]">
            <Navigation size={12} className="text-cyan-400" />
            <span>SPEED</span>
          </div>
          <div className="text-sm font-bold text-white mt-0.5">
            {vessel.speedKnots} <span className="text-[10px] text-[#8ea8b7]">knots</span>
          </div>
        </div>
      </div>

      {/* Hull Ice Load & Risk */}
      <div className="space-y-2 mb-3">
        <div>
          <div className="flex justify-between text-[10px] text-[#8ea8b7] mb-1">
            <span>Hull Structural Ice Load</span>
            <span className="text-cyan-300 font-semibold">{vessel.hullIceLoadPct}%</span>
          </div>
          <div className="h-1.5 w-full bg-[#061014] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-amber-500 transition-all duration-500"
              style={{ width: `${vessel.hullIceLoadPct}%` }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between p-2 rounded bg-[#0B1820] border border-[rgba(120,180,200,0.12)]">
          <span className="text-[#628294]">Corridor Risk Index</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-950/60 text-amber-300 border border-amber-800/50">
            {vessel.corridorRisk.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Environmental Feeds */}
      <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)] space-y-1 text-[11px] text-[#8ea8b7] mb-3">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[#628294]">
            <Wind size={12} /> Surface Wind
          </span>
          <span>{vessel.windSpeedKnots} kn {vessel.windDirection}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[#628294]">
            <Thermometer size={12} /> Air / Sea Temp
          </span>
          <span>{vessel.airTempC}°C / {vessel.waterTempC}°C</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[#628294]">
            <Fuel size={12} /> Burn Rate
          </span>
          <span>{vessel.fuelConsumptionBurnRate}</span>
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex items-center gap-2">
        <Link
          href="/routes"
          className="flex-1 py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-center text-xs tracking-wider transition-colors"
        >
          CALCULATE SAFE ROUTE →
        </Link>
      </div>
    </div>
  );
}

