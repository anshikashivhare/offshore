"use client";

import React from "react";
import { RiskZone } from "@/lib/data/antarctic-data";
import { X, AlertTriangle, ShieldAlert, CheckCircle2 } from "lucide-react";
import Link from "next/link";

interface RiskPanelProps {
  zone: RiskZone;
  onClose: () => void;
}

export function RiskPanel({ zone, onClose }: RiskPanelProps) {
  const isCritical = zone.level === "Critical";
  const isHigh = zone.level === "High";

  return (
    <div className="w-84 rounded-lg bg-[#102631]/95 backdrop-blur-md border border-[rgba(120,180,200,0.25)] shadow-2xl p-4 text-xs font-mono select-none z-30 animate-in fade-in slide-in-from-right-2 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-[rgba(120,180,200,0.15)]">
        <div>
          <div className="flex items-center gap-1.5">
            <AlertTriangle
              size={14}
              className={isCritical ? "text-rose-400" : isHigh ? "text-orange-400" : "text-amber-400"}
            />
            <h3 className="font-semibold text-sm text-white tracking-wide font-sans">
              {zone.name}
            </h3>
          </div>
          <span className="text-[10px] text-[#628294]">
            {zone.latRange} · {zone.lonRange}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded text-[#8ea8b7] hover:text-white hover:bg-[#0B1820]"
          aria-label="Close Risk Panel"
        >
          <X size={15} />
        </button>
      </div>

      {/* Composite Score Meter */}
      <div className="my-3 p-3 rounded bg-[#061014] border border-[rgba(120,180,200,0.15)]">
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-[#8ea8b7]">Composite Nav Risk Index</span>
          <span
            className={`px-2 py-0.5 rounded text-[11px] font-bold ${
              isCritical
                ? "bg-rose-950/60 text-rose-300 border border-rose-800/50"
                : isHigh
                ? "bg-orange-950/60 text-orange-300 border border-orange-800/50"
                : "bg-amber-950/60 text-amber-300 border border-amber-800/50"
            }`}
          >
            {zone.score} / 100 [{zone.level}]
          </span>
        </div>
        <div className="h-2 w-full bg-[#0B1820] rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              isCritical
                ? "bg-gradient-to-r from-orange-500 to-rose-500"
                : isHigh
                ? "bg-gradient-to-r from-amber-500 to-orange-500"
                : "bg-gradient-to-r from-emerald-500 to-amber-500"
            }`}
            style={{ width: `${zone.score}%` }}
          />
        </div>
      </div>

      {/* Dominant Hazards */}
      <div className="mb-3 space-y-1.5">
        <span className="text-[10px] uppercase tracking-wider text-[#628294] font-semibold">
          Primary Contributing Hazards
        </span>
        <div className="space-y-1">
          {zone.dominantHazards.map((hazard, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 p-1.5 rounded bg-[#0B1820] text-[11px] text-[#8ea8b7]"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />
              <span>{hazard}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Advisory & Recommendation */}
      <div className="p-2.5 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)] mb-3 text-[11px] leading-relaxed text-[#9cb6c5]">
        <div className="flex items-center gap-1.5 text-cyan-300 font-semibold mb-1">
          <ShieldAlert size={13} />
          <span>MARITIME ADVISORY</span>
        </div>
        <p>{zone.recommendation}</p>
      </div>

      {/* Action CTA */}
      <Link
        href="/routes"
        className="block w-full py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-center text-xs tracking-wider transition-colors"
      >
        VIEW SAFE ROUTES & DETOURS →
      </Link>
    </div>
  );
}

