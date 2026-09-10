"use client";

import React, { useState } from "react";
import { Bell, ShieldCheck, User } from "lucide-react";

interface TopbarProps {
  title: string;
  subtitle: string;
}

export function Topbar({ title, subtitle }: TopbarProps) {
  const [showNotifications, setShowNotifications] = useState(false);

  const notifications = [
    {
      id: "n-1",
      type: "warning",
      title: "Iceberg B-102 Drift Alert",
      text: "CPA adjusted to 14.2 nm in 9.4 hours (Bearing 284° WNW).",
      time: "4m ago",
    },
    {
      id: "n-2",
      type: "info",
      title: "Sentinel-1 SAR Feed Sync",
      text: "New polar synthetic aperture radar swath assimilated (25m res).",
      time: "18m ago",
    },
    {
      id: "n-3",
      type: "safe",
      title: "Corridor Clearance Confirmed",
      text: "Safe waypoint corridor telemetry verified by NAVAREA X.",
      time: "42m ago",
    },
  ];

  return (
    <header className="h-14 px-6 bg-[#061014] border-b border-[rgba(120,180,200,0.15)] flex items-center justify-between z-30 select-none">
      {/* Title & Context */}
      <div className="flex items-baseline gap-3 min-w-0">
        <h1 className="text-sm font-semibold tracking-wide text-white uppercase truncate font-sans">
          {title}
        </h1>
        <span className="hidden sm:inline-block text-xs text-[#628294] font-mono truncate">
          / {subtitle}
        </span>
      </div>

      {/* Right Actions & Status Indicators */}
      <div className="flex items-center gap-4 text-xs font-mono">
        {/* System Online Badge */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#0B1820] border border-[rgba(120,180,200,0.2)] text-[#8ea8b7]">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-[11px] font-medium tracking-wider text-emerald-300">
            SYSTEM ONLINE
          </span>
        </div>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-1.5 rounded text-[#8ea8b7] hover:text-white hover:bg-[#102631] transition-colors relative"
            aria-label="Toggle notifications"
          >
            <Bell size={16} />
            <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-cyan-400" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-lg bg-[#102631] border border-[rgba(120,180,200,0.25)] shadow-2xl z-50 p-3 text-left">
              <div className="flex items-center justify-between pb-2 border-b border-[rgba(120,180,200,0.12)]">
                <span className="text-xs font-semibold text-white uppercase tracking-wider">
                  Operational Alerts
                </span>
                <span className="text-[10px] text-cyan-400 font-mono">3 Active</span>
              </div>
              <div className="divide-y divide-[rgba(120,180,200,0.1)] mt-1 max-h-60 overflow-y-auto custom-scrollbar">
                {notifications.map((n) => (
                  <div key={n.id} className="py-2.5 px-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-white">{n.title}</span>
                      <span className="text-[10px] text-[#628294]">{n.time}</span>
                    </div>
                    <p className="text-[11px] text-[#9cb6c5] mt-1 leading-snug">{n.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Vessel Badge */}
        <div className="hidden md:flex items-center gap-2 pl-2 border-l border-[rgba(120,180,200,0.15)] text-[#9cb6c5]">
          <ShieldCheck size={15} className="text-cyan-400" />
          <span className="text-[11px] font-semibold text-white tracking-wider">
            PC6 EXPLORER
          </span>
        </div>

        {/* User Avatar */}
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#102631] border border-[rgba(120,180,200,0.25)] text-cyan-300">
          <User size={13} />
        </div>
      </div>
    </header>
  );
}

