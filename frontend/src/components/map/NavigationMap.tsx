"use client";

/**
 * NavigationMap
 * -------------
 * Powers the tactical map views across OFFSHORE.
 * Hosts the original MissionMap (MapLibre GL with CARTO Dark Matter basemap,
 * SeaIceLayer, IcebergLayer with clustering, OceanCurrentLayer with WebGL particles,
 * and RouteLayer with A* calculated path).
 *
 * Adds live synchronization with:
 *   - useIcebergSelection: triggers iceberg inspection drawer on click
 *   - useLayerStore: controls MapLibre layer visibility & opacity
 *   - useRouteStore: controls A* route recalculation & display
 */

import React, { useEffect } from "react";
import { MissionMap } from "./mission-map";
import {
  ACTIVE_VESSEL,
  TRACKED_ICEBERGS,
  RISK_ZONES,
  VesselTelemetry,
  Iceberg,
  RiskZone,
} from "@/lib/data/antarctic-data";
import { useIcebergSelection } from "@/stores/use-iceberg-selection";
import { useLayerStore } from "@/stores/use-layer-store";
import { useRouteStore } from "@/stores/use-route-store";
import { LayerVisibilityState } from "./MapLayers";
import { Compass, Navigation as NavIcon, Radio } from "lucide-react";

interface NavigationMapProps {
  layers?: LayerVisibilityState;
  iceOpacity?: number;
  activeRouteId?: "safest" | "fastest" | "fuel";
  selectedIcebergId?: string | null;
  onSelectVessel?: (vessel: VesselTelemetry) => void;
  onSelectIceberg?: (iceberg: Iceberg) => void;
  onSelectRiskZone?: (zone: RiskZone) => void;
  highlightZoneId?: string | null;
  showLegend?: boolean;
}

export function NavigationMap({
  layers,
  iceOpacity = 0.65,
  activeRouteId = "safest",
  selectedIcebergId,
  onSelectVessel,
  onSelectIceberg,
  onSelectRiskZone,
  highlightZoneId,
  showLegend = true,
}: NavigationMapProps) {
  const storeIcebergId = useIcebergSelection((s) => s.selectedId);
  const selectStoreIceberg = useIcebergSelection((s) => s.select);
  const setLayerEnabled = useLayerStore((s) => s.setEnabled);
  const setLayerOpacity = useLayerStore((s) => s.setOpacity);
  const recalculateRoute = useRouteStore((s) => s.recalculate);
  const routeResult = useRouteStore((s) => s.result);

  // Sync external selectedIcebergId into store if provided
  useEffect(() => {
    if (selectedIcebergId && selectedIcebergId !== storeIcebergId) {
      selectStoreIceberg(selectedIcebergId);
    }
  }, [selectedIcebergId, storeIcebergId, selectStoreIceberg]);

  // Sync store selection to parent callback
  useEffect(() => {
    if (storeIcebergId && onSelectIceberg) {
      const found = TRACKED_ICEBERGS.find((b) => b.id === storeIcebergId);
      if (found) {
        onSelectIceberg(found);
      }
    }
  }, [storeIcebergId, onSelectIceberg]);

  // Sync layer states into useLayerStore
  useEffect(() => {
    if (layers) {
      setLayerEnabled("seaIce", layers.seaIce);
      setLayerEnabled("icebergs", layers.icebergs);
      setLayerEnabled("route", layers.vesselTrack);
      setLayerEnabled("oceanCurrents", layers.contours);
    }
  }, [layers, setLayerEnabled]);

  useEffect(() => {
    if (iceOpacity !== undefined) {
      setLayerOpacity("seaIce", iceOpacity);
    }
  }, [iceOpacity, setLayerOpacity]);

  // Automatically compute A* route if not yet calculated
  useEffect(() => {
    if (!routeResult) {
      recalculateRoute();
    }
  }, [routeResult, recalculateRoute]);

  return (
    <div className="relative w-full h-full overflow-hidden bg-[#061014]">
      {/* Original Real MapLibre Engine (CARTO Dark Matter + SeaIce + Icebergs + WebGL Ocean Particles + Route) */}
      <MissionMap showLegend={showLegend} className="w-full h-full">
        {/* Active Vessel HUD Indicator Overlay */}
        <div className="absolute top-20 left-4 z-10 pointer-events-auto">
          <button
            type="button"
            onClick={() => onSelectVessel?.(ACTIVE_VESSEL)}
            className="group flex items-center gap-2.5 px-3 py-1.5 rounded-md bg-[#0B1820]/90 backdrop-blur-md border border-[rgba(120,180,200,0.2)] hover:border-cyan-400 text-xs font-mono text-[#8ea8b7] shadow-xl transition-all"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-400" />
            </span>
            <div className="text-left">
              <div className="text-[10px] uppercase tracking-wider text-[#628294] font-semibold">
                Active Flagship
              </div>
              <div className="text-white font-bold group-hover:text-cyan-300">
                MV POLAR EXPLORER · 11.4 kn
              </div>
            </div>
          </button>
        </div>

        {/* Tactical Coordinate HUD Badge */}
        <div className="absolute bottom-4 right-4 z-10 hidden sm:flex items-center gap-3 px-3 py-1.5 rounded bg-[#0B1820]/80 backdrop-blur-md border border-[rgba(120,180,200,0.15)] text-[10px] font-mono text-[#628294] pointer-events-none">
          <span>ANTARCTIC SECTOR: DRAKE → ROSS CORRIDOR</span>
          <span>·</span>
          <span className="text-cyan-400">CARTO DARK MATTER GL</span>
          <span>·</span>
          <span>WEBGL FLOW PARTICLES</span>
        </div>
      </MissionMap>
    </div>
  );
}
