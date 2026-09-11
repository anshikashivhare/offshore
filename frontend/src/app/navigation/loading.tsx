import React from "react";

export default function Loading() {
  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#061014] text-cyan-400 font-mono select-none">
      <div className="relative flex items-center justify-center mb-6">
        <div className="h-20 w-20 rounded-full border-2 border-cyan-500/15 border-t-cyan-400 animate-spin" />
        <div className="absolute h-12 w-12 rounded-full border border-dashed border-cyan-400/40 animate-ping" />
        <div className="h-2 w-2 rounded-full bg-cyan-400" />
      </div>

      <div className="text-sm font-semibold tracking-[0.25em] text-cyan-300 uppercase">
        Entering Polar Command Center
      </div>
      <div className="text-xs text-[#526f80] mt-1.5 tracking-wider">
        CALIBRATING ANTARCTIC TACTICAL HUD
      </div>
    </div>
  );
}
