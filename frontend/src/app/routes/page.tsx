"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { AppShell } from "@/components/layout/AppShell";

const NavigationMap = dynamic(
  () => import("@/components/map/NavigationMap").then((mod) => mod.NavigationMap),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#061014] text-cyan-400 font-mono">
        <div className="h-12 w-12 rounded-full border border-cyan-500/20 border-t-cyan-400 animate-spin mb-3" />
        <span className="text-xs uppercase tracking-widest text-cyan-300">Calculating A* Optimization Grid…</span>
      </div>
    ),
  }
);
import { ROUTE_OPTIONS, RouteOption } from "@/lib/data/antarctic-data";
import { useRouteStore } from "@/stores/use-route-store";
import { Check, Compass, Shield, Clock, Fuel, CheckCircle2, ChevronRight } from "lucide-react";

export default function RoutesPage() {
  const [destination, setDestination] = useState("Rothera Research Station");
  const [vesselProfile, setVesselProfile] = useState("MV Polar Explorer (PC6)");
  const [selectedRouteId, setSelectedRouteId] = useState<"safest" | "fastest" | "fuel">("safest");
  const [engaged, setEngaged] = useState(false);
  const recalculate = useRouteStore((s) => s.recalculate);

  const activeRoute = ROUTE_OPTIONS.find((r) => r.id === selectedRouteId) || ROUTE_OPTIONS[0];

  const handleEngageRoute = () => {
    recalculate();
    setEngaged(true);
    setTimeout(() => setEngaged(false), 3500);
  };

  return (
    <AppShell title="Route Optimization" subtitle="Autonomous Voyage Planning & Corridor Clearance" hideChromePadding>
      <div className="relative w-full h-full overflow-hidden flex flex-col">
        {/* Step-by-Step Top Wizard Bar */}
        <div className="px-6 py-2.5 bg-[#0B1820]/95 backdrop-blur-md border-b border-[rgba(120,180,200,0.15)] flex flex-wrap items-center justify-between gap-4 z-20 text-xs font-mono select-none">
          <div className="flex flex-wrap items-center gap-4">
            {/* Destination Step */}
            <div className="flex items-center gap-2">
              <span className="text-cyan-400 font-bold">01</span>
              <span className="text-[#628294]">DESTINATION:</span>
              <select
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                className="bg-[#061014] border border-[rgba(120,180,200,0.2)] text-white px-2.5 py-1 rounded focus:outline-none focus:border-cyan-400 cursor-pointer"
              >
                <option value="Rothera Research Station">{"Rothera Station (67°34'S)"}</option>
                <option value="Palmer Station">{"Palmer Station (64°46'S)"}</option>
                <option value="McMurdo Station">{"McMurdo Station (77°50'S)"}</option>
                <option value="King George Island">{"King George Island (62°12'S)"}</option>
              </select>
            </div>

            <ChevronRight size={14} className="text-[#526f80] hidden sm:inline-block" />

            {/* Vessel Step */}
            <div className="flex items-center gap-2">
              <span className="text-cyan-400 font-bold">02</span>
              <span className="text-[#628294]">VESSEL:</span>
              <select
                value={vesselProfile}
                onChange={(e) => setVesselProfile(e.target.value)}
                className="bg-[#061014] border border-[rgba(120,180,200,0.2)] text-white px-2.5 py-1 rounded focus:outline-none focus:border-cyan-400 cursor-pointer"
              >
                <option value="MV Polar Explorer (PC6)">MV Polar Explorer (PC6)</option>
                <option value="RV Sir David Attenborough (PC4)">RV Sir David Attenborough (PC4)</option>
              </select>
            </div>

            <ChevronRight size={14} className="text-[#526f80] hidden sm:inline-block" />

            {/* Optimization Priority */}
            <div className="flex items-center gap-1.5">
              <span className="text-cyan-400 font-bold">03</span>
              <span className="text-[#628294] mr-1">STRATEGY:</span>
              {ROUTE_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => {
                    setSelectedRouteId(opt.id);
                    recalculate();
                  }}
                  className={`px-3 py-1 rounded text-xs font-semibold tracking-wider transition-colors ${
                    selectedRouteId === opt.id
                      ? "bg-cyan-500 text-black shadow-md"
                      : "bg-[#061014] text-[#8ea8b7] border border-[rgba(120,180,200,0.15)] hover:text-white"
                  }`}
                >
                  {opt.id.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Action Button */}
          <div>
            <button
              type="button"
              onClick={handleEngageRoute}
              className={`flex items-center gap-2 px-4 py-1.5 rounded font-semibold text-xs tracking-wider transition-all duration-200 ${
                engaged
                  ? "bg-emerald-500 text-black shadow-[0_0_15px_rgba(52,211,153,0.5)]"
                  : "bg-cyan-500 hover:bg-cyan-400 text-black"
              }`}
            >
              {engaged ? (
                <>
                  <Check size={15} />
                  <span>ROUTE ENGAGED TO AUTONOMOUS PILOT</span>
                </>
              ) : (
                <>
                  <Compass size={15} />
                  <span>ENGAGE ROUTE IN AUTOPILOT</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Route Map & Progressive Telemetry Drawer */}
        <div className="relative flex-1 w-full h-full overflow-hidden">
          <NavigationMap
            layers={{
              coastline: true,
              seaIce: true,
              icebergs: true,
              vesselTrack: true,
              riskZones: true,
              contours: true,
            }}
            activeRouteId={selectedRouteId}
          />

          {/* Right Floating Route Analysis Card */}
          <div className="absolute top-4 right-4 z-20 w-84 rounded-lg bg-[#102631]/95 backdrop-blur-md border border-[rgba(120,180,200,0.25)] shadow-2xl p-4 text-xs font-mono select-none animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-2 border-b border-[rgba(120,180,200,0.15)]">
              <div>
                <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider">
                  Corridor Telemetry
                </span>
                <h3 className="font-semibold text-sm text-white tracking-wide font-sans">
                  {activeRoute.title}
                </h3>
              </div>
              <span
                className="px-2 py-0.5 rounded text-[10px] font-bold"
                style={{ backgroundColor: `${activeRoute.color}20`, color: activeRoute.color }}
              >
                {activeRoute.riskLabel} Risk
              </span>
            </div>

            <p className="text-[11px] text-[#8ea8b7] my-3 leading-relaxed">
              {activeRoute.summary}
            </p>

            {/* Key Comparison Grid */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)] text-center">
                <span className="text-[9px] text-[#628294] block">DISTANCE</span>
                <span className="text-white font-bold text-xs">{activeRoute.distanceNm} nm</span>
              </div>
              <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)] text-center">
                <span className="text-[9px] text-[#628294] block">EST. TIME</span>
                <span className="text-white font-bold text-xs">{activeRoute.etaHours}h</span>
              </div>
              <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)] text-center">
                <span className="text-[9px] text-[#628294] block">FUEL BURN</span>
                <span className="text-cyan-300 font-bold text-xs">{activeRoute.fuelBurnTons} MT</span>
              </div>
            </div>

            {/* Polar Class Assessment */}
            <div className="p-2 rounded bg-[#0B1820] border border-[rgba(120,180,200,0.12)] space-y-1 text-[11px] text-[#8ea8b7]">
              <div className="flex justify-between">
                <span>Avg Ice Concentration:</span>
                <span className="text-white font-bold">{activeRoute.avgIceConcentration}%</span>
              </div>
              <div className="flex justify-between">
                <span>Max Corridor Risk Index:</span>
                <span className="text-orange-400 font-bold">{activeRoute.maxRiskScore}/100</span>
              </div>
              <div className="flex justify-between">
                <span>Planned Waypoints:</span>
                <span className="text-white font-bold">{activeRoute.waypointsCount} Geodetic Fixes</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

