"use client";

import React, { useState } from "react";
import { Layers, ChevronDown, ChevronUp, Eye, EyeOff } from "lucide-react";

export interface LayerVisibilityState {
  coastline: boolean;
  seaIce: boolean;
  icebergs: boolean;
  vesselTrack: boolean;
  riskZones: boolean;
  contours: boolean;
}

interface MapLayersProps {
  layers: LayerVisibilityState;
  onChange: (layers: LayerVisibilityState) => void;
  iceOpacity?: number;
  onOpacityChange?: (val: number) => void;
}

export function MapLayers({
  layers,
  onChange,
  iceOpacity = 0.65,
  onOpacityChange,
}: MapLayersProps) {
  const [open, setOpen] = useState(false);

  const toggleLayer = (key: keyof LayerVisibilityState) => {
    onChange({ ...layers, [key]: !layers[key] });
  };

  return (
    <div className="relative z-20">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-md bg-[#0B1820]/90 backdrop-blur-md border border-[rgba(120,180,200,0.2)] text-xs font-mono text-[#8ea8b7] hover:text-white shadow-xl transition-all duration-150 active:scale-[0.96] active:bg-[#102631] cursor-pointer"
      >
        <Layers size={14} className="text-cyan-400" />
        <span>LAYERS</span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {open && (
        <div className="absolute top-full mt-2 left-0 w-64 rounded-md bg-[#102631] border border-[rgba(120,180,200,0.25)] shadow-2xl p-3 text-xs font-mono select-none animate-in fade-in-50 zoom-in-95 duration-150">
          <div className="text-[10px] uppercase tracking-wider text-[#628294] font-semibold mb-2">
            Map Overlays & Telemetry
          </div>

          <div className="space-y-1.5">
            {[
              { id: "seaIce", label: "Sea Ice Concentration", color: "#38bdf8" },
              { id: "icebergs", label: "Icebergs & Drift Vectors", color: "#fb923c" },
              { id: "vesselTrack", label: "Vessel Nav Corridor", color: "#22d3ee" },
              { id: "riskZones", label: "Multi-Hazard Risk Zones", color: "#f87171" },
              { id: "contours", label: "Bathymetry Contours", color: "#64748b" },
            ].map((layer) => {
              const active = layers[layer.id as keyof LayerVisibilityState];
              return (
                <button
                  key={layer.id}
                  type="button"
                  onClick={() => toggleLayer(layer.id as keyof LayerVisibilityState)}
                  className="w-full flex items-center justify-between px-2 py-1.5 rounded hover:bg-[#0B1820] text-left transition-all duration-100 active:scale-[0.98] active:bg-cyan-950/30 cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="h-2 w-2 rounded-full transition-colors"
                      style={{ backgroundColor: active ? layer.color : "#475569" }}
                    />
                    <span className={active ? "text-[#e6f4f8] font-medium" : "text-[#628294]"}>
                      {layer.label}
                    </span>
                  </div>
                  {active ? (
                    <Eye size={13} className="text-cyan-400" />
                  ) : (
                    <EyeOff size={13} className="text-[#526f80]" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Ice Overlay Opacity */}
          {onOpacityChange && (
            <div className="mt-3 pt-2.5 border-t border-[rgba(120,180,200,0.15)]">
              <div className="flex justify-between text-[10px] text-[#628294] mb-1">
                <span>Ice Mesh Opacity</span>
                <span>{Math.round(iceOpacity * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={iceOpacity}
                onChange={(e) => onOpacityChange(parseFloat(e.target.value))}
                className="w-full h-1 bg-[#061014] rounded accent-cyan-400 cursor-pointer"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

