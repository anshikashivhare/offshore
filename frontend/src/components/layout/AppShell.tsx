"use client";

import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { Menu, X } from "lucide-react";

interface AppShellProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  hideChromePadding?: boolean;
}

export function AppShell({
  title,
  subtitle,
  children,
  hideChromePadding = false,
}: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#061014] text-[#e6f4f8]">
      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Desktop / Mobile Drawer */}
      <div
        className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-[250ms] ease-[cubic-bezier(0.22,1,0.36,1)] lg:relative lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Sidebar />
      </div>

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        {/* Topbar with mobile hamburger toggle */}
        <div className="relative flex items-center">
          <button
            type="button"
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden p-3 text-[#8ea8b7] hover:text-white bg-[#061014] border-b border-[rgba(120,180,200,0.15)] z-40"
            aria-label="Toggle Navigation"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="flex-1 min-w-0">
            <Topbar title={title} subtitle={subtitle} />
          </div>
        </div>

        {/* View Content */}
        <main
          className={`flex-1 min-w-0 relative overflow-hidden animate-content-enter ${
            hideChromePadding ? "p-0" : "p-4 sm:p-6 overflow-y-auto custom-scrollbar"
          }`}
        >
          {children}
        </main>
      </div>
    </div>
  );
}

