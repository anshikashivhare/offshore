"use client";

import React from "react";
import { Plus, Minus, Crosshair, Globe } from "lucide-react";

interface MapControlsProps {
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onResetView?: () => void;
  onTogglePerspective?: () => void;
  is3d?: boolean;
}

export function MapControls({
  onZoomIn,
  onZoomOut,
  onResetView,
  onTogglePerspective,
  is3d = false,
}: MapControlsProps) {
  return (
    <div className="flex flex-col gap-1.5 p-1 rounded-md bg-[#0B1820]/90 backdrop-blur-md border border-[rgba(120,180,200,0.2)] shadow-xl z-20">
      <button
        type="button"
        onClick={onZoomIn}
        className="h-8 w-8 flex items-center justify-center rounded text-[#8ea8b7] hover:text-white hover:bg-[#102631] transition-colors"
        title="Zoom In"
        aria-label="Zoom In"
      >
        <Plus size={16} />
      </button>

      <button
        type="button"
        onClick={onZoomOut}
        className="h-8 w-8 flex items-center justify-center rounded text-[#8ea8b7] hover:text-white hover:bg-[#102631] transition-colors"
        title="Zoom Out"
        aria-label="Zoom Out"
      >
        <Minus size={16} />
      </button>

      <div className="h-[1px] w-6 mx-auto bg-[rgba(120,180,200,0.15)] my-0.5" />

      <button
        type="button"
        onClick={onResetView}
        className="h-8 w-8 flex items-center justify-center rounded text-[#8ea8b7] hover:text-cyan-400 hover:bg-[#102631] transition-colors"
        title="Locate Active Vessel"
        aria-label="Locate Active Vessel"
      >
        <Crosshair size={16} />
      </button>

      <button
        type="button"
        onClick={onTogglePerspective}
        className={`h-8 w-8 flex items-center justify-center rounded transition-colors ${
          is3d
            ? "text-cyan-400 bg-cyan-950/40"
            : "text-[#8ea8b7] hover:text-white hover:bg-[#102631]"
        }`}
        title="Toggle Polar Stereo / 3D Grid"
        aria-label="Toggle Polar Stereo"
      >
        <Globe size={16} />
      </button>
    </div>
  );
}

