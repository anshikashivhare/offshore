"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  Layers,
  Mountain,
  AlertTriangle,
  Route,
  BarChart3,
  Settings,
  LucideIcon,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const PRIMARY_NAV: NavItem[] = [
  { label: "Navigation", href: "/navigation", icon: Compass },
  { label: "Sea Ice", href: "/sea-ice", icon: Layers },
  { label: "Icebergs", href: "/icebergs", icon: Mountain },
  { label: "Risk Map", href: "/risk", icon: AlertTriangle },
  { label: "Routes", href: "/routes", icon: Route },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 h-screen bg-[#061014] border-r border-[rgba(120,180,200,0.15)] flex flex-col justify-between select-none z-40">
      {/* Brand Header */}
      <div>
        <div className="px-5 py-5 border-b border-[rgba(120,180,200,0.12)]">
          <Link href="/" className="group flex flex-col">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
              <span className="font-sans text-sm font-bold tracking-[0.22em] text-white group-hover:text-cyan-300 transition-colors">
                OFFSHORE
              </span>
            </div>
            <span className="mt-1 text-[10px] font-mono tracking-wider text-[#526f80] uppercase">
              Antarctic Command Center
            </span>
          </Link>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1 mt-2">
          {PRIMARY_NAV.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 px-3 py-2.5 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? "bg-[#0B1820] text-cyan-300 shadow-sm"
                    : "text-[#8ea8b7] hover:text-[#e6f4f8] hover:bg-[#0B1820]/60"
                }`}
              >
                {/* Thin cyan active accent */}
                {isActive && (
                  <span
                    className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-cyan-400 rounded-r shadow-[0_0_6px_rgba(34,211,238,0.6)]"
                    aria-hidden="true"
                  />
                )}

                <Icon
                  size={16}
                  className={isActive ? "text-cyan-400" : "text-[#526f80] group-hover:text-[#8ea8b7]"}
                />
                <span className="tracking-wide">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Settings Link */}
      <div className="p-3 border-t border-[rgba(120,180,200,0.12)]">
        <Link
          href="/settings"
          className={`relative flex items-center gap-3 px-3 py-2.5 rounded-md text-xs font-medium transition-all ${
            pathname === "/settings"
              ? "bg-[#0B1820] text-cyan-300"
              : "text-[#8ea8b7] hover:text-[#e6f4f8] hover:bg-[#0B1820]/60"
          }`}
        >
          {pathname === "/settings" && (
            <span
              className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-cyan-400 rounded-r shadow-[0_0_6px_rgba(34,211,238,0.6)]"
              aria-hidden="true"
            />
          )}
          <Settings
            size={16}
            className={pathname === "/settings" ? "text-cyan-400" : "text-[#526f80]"}
          />
          <span className="tracking-wide">Settings</span>
        </Link>
      </div>
    </aside>
  );
}

