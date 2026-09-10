"use client";

import React from "react";
import { Iceberg } from "@/lib/data/antarctic-data";
import { X, Mountain, AlertCircle, Compass, Clock, Navigation } from "lucide-react";
import Link from "next/link";

interface IcebergPanelProps {
  iceberg: Iceberg;
  onClose: () => void;
  onProjectDrift?: () => void;
}

export function IcebergPanel({ iceberg, onClose, onProjectDrift }: IcebergPanelProps) {
  const isHighRisk = iceberg.riskLevel === "High" || iceberg.riskLevel === "Critical";

  return (
    <div className="w-80 rounded-lg bg-[#102631]/95 backdrop-blur-md border border-[rgba(120,180,200,0.25)] shadow-2xl p-4 text-xs font-mono select-none z-30 animate-in fade-in slide-in-from-right-2 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-[rgba(120,180,200,0.15)]">
        <div>
          <div className="flex items-center gap-1.5">
            <Mountain size={14} className={isHighRisk ? "text-orange-400" : "text-cyan-400"} />
            <h3 className="font-semibold text-sm text-white tracking-wide font-sans">
              {iceberg.name}
            </h3>
          </div>
          <span className="text-[10px] text-[#628294]">
            {iceberg.classification} · {iceberg.firstDetected}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded text-[#8ea8b7] hover:text-white hover:bg-[#0B1820]"
          aria-label="Close Iceberg Panel"
        >
          <X size={15} />
        </button>
      </div>

      {/* Primary Threat Banner */}
      <div
        className={`my-3 p-2.5 rounded border flex items-center justify-between ${
          isHighRisk
            ? "bg-orange-950/40 border-orange-800/60 text-orange-200"
            : "bg-[#061014] border-[rgba(120,180,200,0.15)] text-[#9cb6c5]"
        }`}
      >
        <div className="flex items-center gap-2">
          <AlertCircle size={15} className={isHighRisk ? "text-orange-400" : "text-cyan-400"} />
          <div>
            <div className="text-[10px] text-[#8ea8b7]">COLLISION THREAT LEVEL</div>
            <div className="font-bold text-white uppercase tracking-wider">
              {iceberg.riskLevel} PRIORITY
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-[#8ea8b7]">CPA DISTANCE</div>
          <div className="font-bold text-white">{iceberg.cpaDistanceNm} nm</div>
        </div>
      </div>

      {/* Physical Dimensions */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
          <span className="text-[10px] text-[#628294]">DIMENSIONS</span>
          <div className="text-white font-bold mt-0.5">
            {iceberg.lengthKm} × {iceberg.widthKm} km
          </div>
          <span className="text-[9px] text-[#8ea8b7]">Freeboard: {iceberg.freeboardM}m</span>
        </div>

        <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)]">
          <span className="text-[10px] text-[#628294]">EST. MASS</span>
          <div className="text-white font-bold mt-0.5">{iceberg.estimatedMassMt} Mt</div>
          <span className="text-[9px] text-[#8ea8b7]">Bulk: Tabular Core</span>
        </div>
      </div>

      {/* Drift Trajectory Vector */}
      <div className="p-2 rounded bg-[#061014] border border-[rgba(120,180,200,0.1)] space-y-1.5 mb-3 text-[11px] text-[#8ea8b7]">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[#628294]">
            <Compass size={12} /> Drift Heading
          </span>
          <span className="text-white">
            {iceberg.driftHeading}° ({iceberg.driftDirLabel})
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[#628294]">
            <Navigation size={12} /> Velocity
          </span>
          <span className="text-white">{iceberg.driftSpeedKnots} knots</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[#628294]">
            <Clock size={12} /> Intercept Horizon
          </span>
          <span className="text-amber-300 font-semibold">{iceberg.cpaTimeHours} hours</span>
        </div>
      </div>

      {/* Progressive Actions */}
      <div className="space-y-1.5">
        {onProjectDrift && (
          <button
            type="button"
            onClick={onProjectDrift}
            className="w-full py-1.5 rounded bg-[#0B1820] hover:bg-[#153243] border border-[rgba(120,180,200,0.2)] text-[#8ea8b7] hover:text-white transition-colors"
          >
            PROJECT 48-HOUR DRIFT TRAJECTORY
          </button>
        )}
        <Link
          href="/icebergs"
          className="block w-full py-1.5 rounded bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-center text-xs tracking-wider transition-colors"
        >
          VIEW IN ICEBERG INTELLIGENCE →
        </Link>
      </div>
    </div>
  );
}

