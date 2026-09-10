"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Settings, Shield, Sliders, Bell, Check, Save } from "lucide-react";

export default function SettingsPage() {
  const [distanceUnit, setDistanceUnit] = useState<"nm" | "km">("nm");
  const [speedUnit, setSpeedUnit] = useState<"knots" | "ms">("knots");
  const [contrastMode, setContrastMode] = useState("abyss");
  const [cpaThreshold, setCpaThreshold] = useState(15);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <AppShell title="System Settings" subtitle="Bridge Navigation & Sensor Feed Parameters">
      <div className="max-w-4xl mx-auto space-y-6 font-mono text-xs select-none">
        {/* Section 1: Display & Cartography */}
        <div className="p-5 rounded-lg bg-[#0B1820] border border-[rgba(120,180,200,0.15)] shadow-xl space-y-4">
          <div className="flex items-center gap-2 pb-2.5 border-b border-[rgba(120,180,200,0.12)]">
            <Sliders size={15} className="text-cyan-400" />
            <h3 className="font-semibold text-sm text-white tracking-wide font-sans uppercase">
              Display & Cartographic Units
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-[#8ea8b7] block mb-1.5">Distance Measurement Unit</label>
              <div className="flex gap-2">
                {[
                  { id: "nm", label: "Nautical Miles (nm)" },
                  { id: "km", label: "Kilometers (km)" },
                ].map((u) => (
                  <button
                    key={u.id}
                    type="button"
                    onClick={() => setDistanceUnit(u.id as any)}
                    className={`flex-1 py-1.5 px-3 rounded text-center transition-colors ${
                      distanceUnit === u.id
                        ? "bg-cyan-500 text-black font-semibold"
                        : "bg-[#061014] text-[#8ea8b7] border border-[rgba(120,180,200,0.15)] hover:text-white"
                    }`}
                  >
                    {u.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-[#8ea8b7] block mb-1.5">Velocity Unit</label>
              <div className="flex gap-2">
                {[
                  { id: "knots", label: "Knots (kn)" },
                  { id: "ms", label: "Meters/sec (m/s)" },
                ].map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setSpeedUnit(s.id as any)}
                    className={`flex-1 py-1.5 px-3 rounded text-center transition-colors ${
                      speedUnit === s.id
                        ? "bg-cyan-500 text-black font-semibold"
                        : "bg-[#061014] text-[#8ea8b7] border border-[rgba(120,180,200,0.15)] hover:text-white"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Sensor & Satellite Streams */}
        <div className="p-5 rounded-lg bg-[#0B1820] border border-[rgba(120,180,200,0.15)] shadow-xl space-y-4">
          <div className="flex items-center gap-2 pb-2.5 border-b border-[rgba(120,180,200,0.12)]">
            <Shield size={15} className="text-cyan-400" />
            <h3 className="font-semibold text-sm text-white tracking-wide font-sans uppercase">
              Telemetry Feeds & Satellite Assimilation
            </h3>
          </div>

          <div className="space-y-3">
            {[
              {
                title: "Sentinel-1 Synthetic Aperture Radar (SAR)",
                desc: "High-resolution orbital pass updates for polar pack-ice fractures and floe deformation.",
                status: "ACTIVE · 4.8h Revisit",
              },
              {
                title: "US National Ice Center (NIC) Bulletin",
                desc: "Automated tabular iceberg naming, shape boundary tracking, and drift vector assimilation.",
                status: "SYNCED · 06:00 UTC",
              },
              {
                title: "Vessel Class-A AIS Transceiver",
                desc: "Continuous broadcast of ship position, speed over ground, heading, and ice load strain.",
                status: "BROADCASTING (10s interval)",
              },
            ].map((feed, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]"
              >
                <div>
                  <span className="text-white font-semibold block">{feed.title}</span>
                  <span className="text-[#628294] text-[10px] mt-0.5 block">{feed.desc}</span>
                </div>
                <span className="px-2 py-1 rounded bg-[#0B1820] border border-cyan-500/30 text-cyan-300 text-[10px] font-semibold whitespace-nowrap">
                  {feed.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 3: Safety Alarm Thresholds */}
        <div className="p-5 rounded-lg bg-[#0B1820] border border-[rgba(120,180,200,0.15)] shadow-xl space-y-4">
          <div className="flex items-center gap-2 pb-2.5 border-b border-[rgba(120,180,200,0.12)]">
            <Bell size={15} className="text-cyan-400" />
            <h3 className="font-semibold text-sm text-white tracking-wide font-sans uppercase">
              Safety Warning & Alarm Thresholds
            </h3>
          </div>

          <div>
            <div className="flex justify-between text-[#8ea8b7] mb-1">
              <span>Closest Point of Approach (CPA) Proximity Alert Distance</span>
              <span className="text-cyan-300 font-bold">{cpaThreshold} nautical miles</span>
            </div>
            <input
              type="range"
              min="5"
              max="30"
              step="1"
              value={cpaThreshold}
              onChange={(e) => setCpaThreshold(parseInt(e.target.value, 10))}
              className="w-full h-1.5 bg-[#061014] rounded accent-cyan-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-[#526f80] mt-1">
              <span>5 nm (Urgent Close Quarters)</span>
              <span>15 nm (Standard Polar Watch)</span>
              <span>30 nm (Early Tactical Advisory)</span>
            </div>
          </div>
        </div>

        {/* Save Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          {saved && (
            <span className="text-emerald-400 flex items-center gap-1 text-xs">
              <Check size={14} /> Preferences stored in bridge NVRAM
            </span>
          )}
          <button
            type="button"
            onClick={handleSave}
            className="flex items-center gap-2 px-5 py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-xs tracking-wider transition-colors"
          >
            <Save size={14} />
            <span>SAVE CONFIGURATION</span>
          </button>
        </div>
      </div>
    </AppShell>
  );
}

