"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { NavigationMap } from "@/components/map/NavigationMap";
import { MapControls } from "@/components/map/MapControls";
import { MapLayers, LayerVisibilityState } from "@/components/map/MapLayers";
import { SeaIceLegend } from "@/components/map/SeaIceLegend";
import { VesselPanel } from "@/components/panels/VesselPanel";
import { IcebergPanel } from "@/components/panels/IcebergPanel";
import { RiskPanel } from "@/components/panels/RiskPanel";
import {
  ACTIVE_VESSEL,
  VesselTelemetry,
  Iceberg,
  RiskZone,
} from "@/lib/data/antarctic-data";

export default function NavigationPage() {
  const [layers, setLayers] = useState<LayerVisibilityState>({
    coastline: true,
    seaIce: true,
    icebergs: true,
    vesselTrack: true,
    riskZones: true,
    contours: true,
  });

  const [iceOpacity, setIceOpacity] = useState(0.65);
  const [selectedVessel, setSelectedVessel] = useState<VesselTelemetry | null>(null);
  const [selectedIceberg, setSelectedIceberg] = useState<Iceberg | null>(null);
  const [selectedRiskZone, setSelectedRiskZone] = useState<RiskZone | null>(null);

  const handleSelectVessel = (vessel: VesselTelemetry) => {
    setSelectedVessel(vessel);
    setSelectedIceberg(null);
    setSelectedRiskZone(null);
  };

  const handleSelectIceberg = (iceberg: Iceberg) => {
    setSelectedIceberg(iceberg);
    setSelectedVessel(null);
    setSelectedRiskZone(null);
  };

  const handleSelectRiskZone = (zone: RiskZone) => {
    setSelectedRiskZone(zone);
    setSelectedVessel(null);
    setSelectedIceberg(null);
  };

  return (
    <AppShell title="Navigation Map" subtitle="Polar Command Center" hideChromePadding>
      <div className="relative w-full h-full overflow-hidden">
        {/* Full Viewport Tactical Map Canvas */}
        <NavigationMap
          layers={layers}
          iceOpacity={iceOpacity}
          activeRouteId="safest"
          selectedIcebergId={selectedIceberg?.id}
          onSelectVessel={handleSelectVessel}
          onSelectIceberg={handleSelectIceberg}
          onSelectRiskZone={handleSelectRiskZone}
        />

        {/* Top Left Floating Layer Control */}
        <div className="absolute top-4 left-4 z-20">
          <MapLayers
            layers={layers}
            onChange={setLayers}
            iceOpacity={iceOpacity}
            onOpacityChange={setIceOpacity}
          />
        </div>

        {/* Bottom Center Minimal Telemetry Strip */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 hidden md:flex items-center gap-3 px-3 py-1.5 rounded-full bg-[#0B1820]/90 backdrop-blur-md border border-[rgba(120,180,200,0.2)] text-[11px] font-mono text-[#8ea8b7] shadow-xl">
          <button
            type="button"
            onClick={() => handleSelectVessel(ACTIVE_VESSEL)}
            className="flex items-center gap-2 hover:text-cyan-300 transition-colors"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="font-semibold text-white">MV POLAR EXPLORER</span>
          </button>
          <span className="text-[rgba(120,180,200,0.25)]">|</span>
          <span>{"64°49'S 63°30'W"}</span>
          <span className="text-[rgba(120,180,200,0.25)]">|</span>
          <span>HDG 218°</span>
          <span className="text-[rgba(120,180,200,0.25)]">|</span>
          <span>11.4 kn</span>
        </div>

        {/* Progressive Disclosure Floating Drawers (Right Side) */}
        <div className="absolute top-4 right-16 z-30 flex flex-col gap-3 max-h-[92vh] overflow-y-auto">
          {selectedVessel && (
            <VesselPanel
              vessel={selectedVessel}
              onClose={() => setSelectedVessel(null)}
            />
          )}

          {selectedIceberg && (
            <IcebergPanel
              iceberg={selectedIceberg}
              onClose={() => setSelectedIceberg(null)}
            />
          )}

          {selectedRiskZone && (
            <RiskPanel
              zone={selectedRiskZone}
              onClose={() => setSelectedRiskZone(null)}
            />
          )}
        </div>
      </div>
    </AppShell>
  );
}

