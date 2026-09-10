"use client";

import React from "react";

interface SeaIceLegendProps {
  lastUpdated?: string;
  source?: string;
}

export function SeaIceLegend({
  lastUpdated = "14:00 UTC",
  source = "AMSR2 / Sentinel-1 SAR",
}: SeaIceLegendProps) {
  return (
    <div className="p-2.5 rounded-md bg-[#0B1820]/90 backdrop-blur-md border border-[rgba(120,180,200,0.2)] shadow-xl z-20 font-mono text-[10px] select-none min-w-[210px]">
      <div className="flex items-center justify-between text-[#628294] mb-1.5 uppercase tracking-wider font-semibold">
        <span>Sea Ice Concentration</span>
        <span className="text-cyan-400">SIC</span>
      </div>

      {/* Gradient Bar */}
      <div className="relative h-2 w-full rounded overflow-hidden bg-gradient-to-r from-transparent via-[#38bdf8]/40 to-[#e0f2fe]" />

      <div className="flex justify-between text-[#8ea8b7] mt-1 text-[9px]">
        <span>0% (Open)</span>
        <span>40%</span>
        <span>70%</span>
        <span>100% (Fast Ice)</span>
      </div>

      <div className="mt-2 pt-1.5 border-t border-[rgba(120,180,200,0.12)] flex items-center justify-between text-[9px] text-[#526f80]">
        <span>{source}</span>
        <span className="text-[#8ea8b7]">{lastUpdated}</span>
      </div>
    </div>
  );
}

