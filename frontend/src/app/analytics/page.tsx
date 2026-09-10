"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { AnalyticsChart } from "@/components/charts/AnalyticsChart";
import { BarChart3, Layers, Mountain, Gauge, ChevronDown, ChevronUp, Download } from "lucide-react";

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<"seaIce" | "icebergs" | "performance">("seaIce");
  const [showDetails, setShowDetails] = useState(false);

  return (
    <AppShell title="Maritime Analytics" subtitle="Operational Telemetry & Climatology Baseline">
      <div className="max-w-6xl mx-auto space-y-6 font-mono text-xs select-none">
        {/* Top Filter Strip */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-lg bg-[#0B1820] border border-[rgba(120,180,200,0.15)]">
          <div className="flex items-center gap-3">
            <span className="text-[#628294]">DATA SET:</span>
            <div className="flex items-center gap-1.5">
              {[
                { id: "seaIce", label: "Sea Ice Trends", icon: Layers },
                { id: "icebergs", label: "Iceberg Activity", icon: Mountain },
                { id: "performance", label: "Transit Performance", icon: Gauge },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-semibold tracking-wider transition-colors ${
                      isActive
                        ? "bg-cyan-500 text-black shadow-md"
                        : "bg-[#061014] text-[#8ea8b7] border border-[rgba(120,180,200,0.15)] hover:text-white"
                    }`}
                  >
                    <Icon size={14} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-[#628294]">TIMEFRAME:</span>
            <select className="bg-[#061014] border border-[rgba(120,180,200,0.2)] text-white px-2.5 py-1 rounded cursor-pointer">
              <option>Last 12 Months (2024-2025)</option>
              <option>5-Year Climatology Mean</option>
              <option>Voyage History (Current Season)</option>
            </select>
          </div>
        </div>

        {/* Primary Analytic Visualization Card */}
        <div className="p-5 rounded-lg bg-[#0B1820] border border-[rgba(120,180,200,0.2)] shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-[rgba(120,180,200,0.12)]">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-wide font-sans uppercase">
                {activeTab === "seaIce" && "Monthly Sea Ice Concentration vs. 10-Year Climatology Baseline"}
                {activeTab === "icebergs" && "Weekly Radar/SAR Iceberg Detection Volume & Hazard Rate"}
                {activeTab === "performance" && "Polar Passage Safety Index & Hydrodynamic Fuel Efficiency"}
              </h3>
              <span className="text-[10px] text-[#526f80]">
                {activeTab === "seaIce" && "Sensor Assimilation: AMSR2, Sentinel-1 SAR, SMOS Thin Ice Model"}
                {activeTab === "icebergs" && "Data Source: US National Ice Center (NIC) & High-Resolution SAR Feeds"}
                {activeTab === "performance" && "Vessel Engine Telemetry & Polar Code Risk Margin Analytics"}
              </span>
            </div>

            <button
              type="button"
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#061014] border border-[rgba(120,180,200,0.2)] text-[#8ea8b7] hover:text-white text-[11px]"
            >
              <Download size={13} />
              <span>EXPORT CSV</span>
            </button>
          </div>

          <div className="mt-4">
            <AnalyticsChart type={activeTab} />
          </div>
        </div>

        {/* Progressive Disclosure Section: Details & Sensor Health */}
        <div className="p-4 rounded-lg bg-[#0B1820] border border-[rgba(120,180,200,0.15)]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400" />
              <span className="text-xs font-semibold text-white uppercase tracking-wider">
                Telemetry Provenance & Sensor Reliability
              </span>
            </div>
            <button
              type="button"
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 text-xs font-semibold"
            >
              <span>{showDetails ? "HIDE DETAILS" : "VIEW DETAILED BREAKDOWN"}</span>
              {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>

          {showDetails && (
            <div className="mt-4 pt-3 border-t border-[rgba(120,180,200,0.12)] grid grid-cols-1 md:grid-cols-3 gap-4 text-[11px]">
              <div className="p-3 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
                <span className="text-[#628294] block uppercase font-bold text-[10px]">SAR Constellation</span>
                <span className="text-white font-semibold mt-1 block">Sentinel-1A / 1B C-Band</span>
                <p className="text-[#8ea8b7] mt-1">Revisit interval: 4.8 hours. Dual-polarization HH+HV radar imagery.</p>
              </div>

              <div className="p-3 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
                <span className="text-[#628294] block uppercase font-bold text-[10px]">Altimetry Stream</span>
                <span className="text-white font-semibold mt-1 block">CryoSat-2 SIRAL-2</span>
                <p className="text-[#8ea8b7] mt-1">Sea ice freeboard and thickness retrieval accuracy within ±0.12m.</p>
              </div>

              <div className="p-3 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
                <span className="text-[#628294] block uppercase font-bold text-[10px]">AIS Ground Stations</span>
                <span className="text-white font-semibold mt-1 block">Palmer & Rothera Repeater Network</span>
                <p className="text-[#8ea8b7] mt-1">99.8% uptime with satellite AIS constellation failover support.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

