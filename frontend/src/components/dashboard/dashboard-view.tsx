"use client";

import React, { useState } from "react";
import {
  Compass,
  Shield,
  Activity,
  Waves,
  Maximize2,
  Minimize2,
  Navigation as NavIcon,
  RefreshCw,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { MissionMap } from "@/components/map/mission-map";
import { SCENARIO } from "@/lib/data/scenarios/drake-to-ross";
import { useRouteStore } from "@/stores/use-route-store";
import { Button } from "@/components/ui/saa-s-template";

export function DashboardView() {
  const [viewMode, setViewMode] = useState<"showcase" | "tactical">("showcase");
  const recalculate = useRouteStore((s) => s.recalculate);
  const routeStatus = useRouteStore((s) => s.status);
  const routeResult = useRouteStore((s) => s.result);

  return (
    <div className="min-h-screen bg-[color:var(--bg-app,#050a14)] text-[color:var(--fg-primary,#e8f1f8)] selection:bg-cyan-500 selection:text-black">
      {/* ------------------------------------------------------------------
       * Sticky Glassmorphism Top Navigation Bar
       * ------------------------------------------------------------------ */}
      <header className="sticky top-0 z-50 w-full border-b border-gray-800/80 bg-[#050a14]/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-500/40 bg-cyan-950/40 text-cyan-400 shadow-sm shadow-cyan-500/20">
              <Compass size={20} />
            </div>
            <div className="flex flex-col">
              <div className="flex items-baseline gap-2">
                <span className="font-sans text-base font-bold tracking-[0.16em] text-white">
                  OFFSHORE
                </span>
                <span className="rounded bg-cyan-950 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-cyan-400 border border-cyan-800/50">
                  v0.1
                </span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">
                Antarctic Maritime Decision Support
              </span>
            </div>
          </div>

          {/* Center Navigation Links */}
          <nav className="hidden lg:flex items-center gap-6 text-xs font-medium text-slate-400">
            <a
              href="#mission-terminal"
              className="hover:text-cyan-300 transition-colors"
              onClick={(e) => {
                if (viewMode !== "showcase") {
                  e.preventDefault();
                  setViewMode("showcase");
                }
              }}
            >
              Mission Map
            </a>
            <a href="#hazards" className="hover:text-cyan-300 transition-colors">
              Hazard Layers
            </a>
            <a href="#routing" className="hover:text-cyan-300 transition-colors">
              A* Pathfinding
            </a>
            <a href="#telemetry" className="hover:text-cyan-300 transition-colors">
              Corridor Telemetry
            </a>
          </nav>

          {/* Right Actions & Layout Switcher */}
          <div className="flex items-center gap-3">
            {/* Active Corridor Pill */}
            <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-gray-800 bg-gray-900/80 px-3 py-1 text-[11px] font-mono text-slate-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Drake → Ross</span>
            </div>

            {/* Recalculate CTA */}
            <button
              type="button"
              onClick={recalculate}
              disabled={routeStatus === "calculating"}
              className="hidden md:flex items-center gap-1.5 rounded-md border border-cyan-500/40 bg-cyan-950/50 px-3 py-1.5 text-xs font-medium text-cyan-300 hover:bg-cyan-900/60 hover:text-white transition-all disabled:opacity-50 cursor-pointer"
              title="Trigger A* risk-optimal route recomputation"
            >
              <RefreshCw
                size={13}
                className={routeStatus === "calculating" ? "animate-spin" : ""}
              />
              <span>Recompute Route</span>
            </button>

            {/* Fullscreen Tactical Mode Toggle */}
            <button
              type="button"
              onClick={() => setViewMode(viewMode === "showcase" ? "tactical" : "showcase")}
              className="flex items-center gap-1.5 rounded-md border border-gray-700 bg-gray-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-gray-700 hover:text-white transition-all cursor-pointer"
            >
              {viewMode === "showcase" ? (
                <>
                  <Maximize2 size={13} className="text-cyan-400" />
                  <span className="hidden sm:inline">Tactical View</span>
                </>
              ) : (
                <>
                  <Minimize2 size={13} className="text-cyan-400" />
                  <span className="hidden sm:inline">Showcase View</span>
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ------------------------------------------------------------------
       * Tactical Fullscreen Mode
       * ------------------------------------------------------------------ */}
      {viewMode === "tactical" && (
        <div className="grid h-[calc(100vh-61px)] w-screen grid-cols-[280px_1fr] overflow-hidden bg-[color:var(--bg-app)]">
          {/* Status rail */}
          <aside className="flex flex-col border-r border-[color:var(--border-subtle)] bg-[color:var(--bg-surface)] p-5 overflow-y-auto">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
                Active Scenario
              </span>
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
            </div>

            <h2 className="mt-1.5 text-base font-semibold text-[color:var(--fg-primary)]">
              {SCENARIO.name}
            </h2>
            <p className="mt-1 text-xs text-[color:var(--fg-secondary)] leading-relaxed">
              {SCENARIO.description}
            </p>

            <div className="mt-6 space-y-3">
              <div className="text-[10px] uppercase tracking-[0.16em] text-[color:var(--fg-muted)]">
                System Status
              </div>
              <ul className="space-y-2 text-xs text-[color:var(--fg-secondary)]">
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-[color:var(--status-safe,#5eead4)]" />
                  <span>Basemap: CARTO Dark Matter</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-[color:var(--status-safe,#5eead4)]" />
                  <span>Sea-Ice Heatmap Active</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-[color:var(--status-safe,#5eead4)]" />
                  <span>Iceberg Clustering Online</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-[color:var(--status-safe,#5eead4)]" />
                  <span>WebGL Flow Particles Active</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-cyan-400" />
                  <span>A* Routing Engine Ready</span>
                </li>
              </ul>
            </div>

            {/* Quick Metrics */}
            {routeResult && (
              <div className="mt-6 rounded-lg border border-cyan-900/50 bg-cyan-950/20 p-3">
                <div className="text-[10px] uppercase tracking-[0.16em] text-cyan-400">
                  Planned Route
                </div>
                <div className="mt-1 font-mono text-xl font-bold text-cyan-300">
                  {Math.round(routeResult.totalNm).toLocaleString()} NM
                </div>
                <div className="mt-0.5 text-xs text-slate-400 font-mono">
                  {routeResult.hours >= 24
                    ? `${(routeResult.hours / 24).toFixed(1)} days @ 14 kn`
                    : `${routeResult.hours.toFixed(1)} hrs @ 14 kn`}
                </div>
              </div>
            )}

            <div className="mt-auto pt-6 border-t border-gray-800 text-[10px] text-[color:var(--fg-muted)]">
              <div>MoES / NCPOR · SIH PS 26059</div>
              <div className="mt-1 text-[9px] text-slate-500 font-mono">
                Coordinates: -66°..-58° Lon | -70°..-60° Lat
              </div>
            </div>
          </aside>

          {/* Interactive Map */}
          <main className="relative h-full w-full">
            <MissionMap />
          </main>
        </div>
      )}

      {/* ------------------------------------------------------------------
       * Modern Showcase & Hero Landing Layout
       * ------------------------------------------------------------------ */}
      {viewMode === "showcase" && (
        <div className="relative">
          {/* Ambient Lighting Background */}
          <div
            className="absolute top-20 left-1/2 -translate-x-1/2 -translate-y-1/4 w-[750px] h-[450px] bg-cyan-500/10 blur-[140px] rounded-full pointer-events-none"
            aria-hidden="true"
          />
          <div
            className="absolute top-96 right-1/4 w-[500px] h-[350px] bg-teal-500/10 blur-[120px] rounded-full pointer-events-none"
            aria-hidden="true"
          />

          {/* Hero Section */}
          <section className="relative mx-auto max-w-7xl px-4 pt-16 pb-12 sm:px-6 lg:pt-20 text-center">
            {/* Pill Announcement */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/40 px-4 py-1.5 text-xs text-cyan-300 backdrop-blur-sm shadow-sm shadow-cyan-500/10">
              <Sparkles size={13} className="text-cyan-400" />
              <span>MoES / NCPOR · Smart India Hackathon PS 26059</span>
              <span className="h-1 w-1 rounded-full bg-cyan-400" />
              <span className="text-slate-400">Antarctic Expedition Safe Passage</span>
            </div>

            {/* Gradient Headline */}
            <h1
              className="mx-auto max-w-5xl text-4xl sm:text-5xl md:text-6xl font-semibold tracking-tight leading-[1.15] mb-6"
              style={{
                background: "linear-gradient(to bottom, #ffffff, #ffffff 60%, rgba(200, 240, 255, 0.7))",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              AI-Powered Antarctic Maritime Navigation <br className="hidden sm:inline" />
              <span className="text-cyan-400">Decision Support Platform</span>
            </h1>

            {/* Subtitle */}
            <p className="mx-auto max-w-2xl text-sm sm:text-base text-slate-400 leading-relaxed mb-8">
              Dynamic multi-source maritime hazard fusion: satellite sea-ice forecasting, YOLO iceberg
              detection & superclustering, WebGL particle flow advection, and A* risk-optimized routing.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-4 mb-14">
              <Button
                type="button"
                variant="gradient"
                size="lg"
                onClick={() => {
                  document.getElementById("mission-terminal")?.scrollIntoView({ behavior: "smooth" });
                }}
                className="flex items-center gap-2"
              >
                <NavIcon size={16} />
                <span>Launch Mission Terminal</span>
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="lg"
                onClick={() => setViewMode("tactical")}
                className="flex items-center gap-2 border border-gray-700 bg-gray-900/90 text-slate-200 hover:bg-gray-800"
              >
                <Maximize2 size={16} />
                <span>Fullscreen Tactical Console</span>
              </Button>
            </div>

            {/* Live Telemetry Chips */}
            <div
              id="telemetry"
              className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-4xl mx-auto text-left"
            >
              <div className="rounded-lg border border-gray-800 bg-gray-950/70 p-3.5 backdrop-blur-sm">
                <div className="text-[10px] uppercase font-mono tracking-wider text-slate-500">
                  Scenario Bounds
                </div>
                <div className="mt-1 text-sm font-semibold text-slate-200">
                  Drake → Ross Corridor
                </div>
                <div className="mt-0.5 text-[11px] font-mono text-cyan-400">
                  -66° to -58° Lon | -70° to -60° Lat
                </div>
              </div>

              <div className="rounded-lg border border-gray-800 bg-gray-950/70 p-3.5 backdrop-blur-sm">
                <div className="text-[10px] uppercase font-mono tracking-wider text-slate-500">
                  Vessel Spec
                </div>
                <div className="mt-1 text-sm font-semibold text-slate-200">
                  Polar Research Vessel
                </div>
                <div className="mt-0.5 text-[11px] font-mono text-cyan-400">
                  Cruise: 14.0 Knots
                </div>
              </div>

              <div className="rounded-lg border border-gray-800 bg-gray-950/70 p-3.5 backdrop-blur-sm">
                <div className="text-[10px] uppercase font-mono tracking-wider text-slate-500">
                  Current Particles
                </div>
                <div className="mt-1 text-sm font-semibold text-slate-200">
                  ACC Flow Simulation
                </div>
                <div className="mt-0.5 text-[11px] font-mono text-teal-400">
                  4,000 WebGL Particles @ 60fps
                </div>
              </div>

              <div className="rounded-lg border border-gray-800 bg-gray-950/70 p-3.5 backdrop-blur-sm">
                <div className="text-[10px] uppercase font-mono tracking-wider text-slate-500">
                  Pathfinding Status
                </div>
                <div className="mt-1 text-sm font-semibold text-slate-200">
                  8-Connected A* Engine
                </div>
                <div className="mt-0.5 text-[11px] font-mono text-emerald-400">
                  {routeResult ? `${Math.round(routeResult.totalNm)} NM Computed` : "Optimal Path Ready"}
                </div>
              </div>
            </div>
          </section>

          {/* ------------------------------------------------------------------
           * Interactive Mission Terminal Showcase
           * ------------------------------------------------------------------ */}
          <section
            id="mission-terminal"
            className="mx-auto max-w-7xl px-4 py-8 sm:px-6 scroll-mt-20"
          >
            <div className="rounded-2xl border border-gray-800/90 bg-[#070d18] shadow-2xl overflow-hidden backdrop-blur-md">
              {/* Terminal Window Header */}
              <div className="flex flex-wrap items-center justify-between border-b border-gray-800 bg-gray-900/70 px-4 py-3 gap-2">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-red-500/80" />
                  <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
                  <span className="h-3 w-3 rounded-full bg-green-500/80" />
                  <span className="ml-2 font-mono text-xs text-slate-400 hidden sm:inline">
                    offshore://antarctica/drake-to-ross/tactical-map
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span>Realtime Simulation</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setViewMode("tactical")}
                    className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-mono cursor-pointer"
                  >
                    <Maximize2 size={12} />
                    <span>Expand Fullscreen</span>
                  </button>
                </div>
              </div>

              {/* Map & Scenario Rail inside Terminal */}
              <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] h-[720px] w-full relative">
                {/* Left Side Info Panel */}
                <div className="hidden lg:flex flex-col border-r border-gray-800/90 bg-[#0a1424] p-5 overflow-y-auto">
                  <div className="text-[10px] uppercase font-mono tracking-[0.16em] text-slate-400">
                    Mission Scenario
                  </div>
                  <h3 className="mt-1 text-base font-semibold text-white">
                    {SCENARIO.name}
                  </h3>
                  <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                    {SCENARIO.description}
                  </p>

                  <div className="mt-6">
                    <div className="text-[10px] uppercase font-mono tracking-[0.16em] text-slate-400">
                      Corridor Hazards
                    </div>
                    <div className="mt-2 space-y-2 text-xs text-slate-300">
                      <div className="rounded-md border border-gray-800 bg-gray-900/60 p-2.5">
                        <div className="flex items-center justify-between text-[11px] font-semibold text-teal-300">
                          <span>Pack Ice Concentration</span>
                          <span>0.25° Grid</span>
                        </div>
                        <p className="mt-1 text-[11px] text-slate-400">
                          Non-rectangular corridor mask with cosine edge-fade.
                        </p>
                      </div>

                      <div className="rounded-md border border-gray-800 bg-gray-900/60 p-2.5">
                        <div className="flex items-center justify-between text-[11px] font-semibold text-sky-300">
                          <span>Iceberg Clusters</span>
                          <span>Supercluster</span>
                        </div>
                        <p className="mt-1 text-[11px] text-slate-400">
                          Click any numbered cluster to zoom and expand members.
                        </p>
                      </div>

                      <div className="rounded-md border border-gray-800 bg-gray-900/60 p-2.5">
                        <div className="flex items-center justify-between text-[11px] font-semibold text-cyan-300">
                          <span>Current Advection</span>
                          <span>WebGL Shaders</span>
                        </div>
                        <p className="mt-1 text-[11px] text-slate-400">
                          Adjust particle density and speed multiplier via HUD.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-auto pt-6 border-t border-gray-800/80 text-[10px] text-slate-500">
                    <div>MoES / NCPOR · SIH PS 26059</div>
                    <div className="mt-0.5 font-mono text-[9px]">
                      A* Heuristic: Haversine + Risk Penalty
                    </div>
                  </div>
                </div>

                {/* Main Interactive Map Component (All tech intact!) */}
                <div className="relative h-full w-full bg-[#050a14]">
                  <MissionMap />
                </div>
              </div>
            </div>
          </section>

          {/* ------------------------------------------------------------------
           * Technical Pillars / Architecture Bento Section
           * ------------------------------------------------------------------ */}
          <section id="hazards" className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <span className="text-xs uppercase tracking-[0.2em] text-cyan-400 font-mono">
                Architecture & Decision Models
              </span>
              <h2 className="mt-2 text-2xl sm:text-3xl font-semibold text-white">
                Multi-Hazard Risk Engine & Navigation Stack
              </h2>
              <p className="mt-2 text-sm text-slate-400">
                OFFSHORE integrates four core subsystems into a unified real-time decision console.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Card 1: Sea-Ice */}
              <div className="rounded-xl border border-gray-800 bg-gray-950/60 p-5 hover:border-cyan-800/60 transition-colors">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-teal-500/30 bg-teal-950/40 text-teal-400 mb-4">
                  <Shield size={20} />
                </div>
                <h3 className="text-base font-semibold text-white">Sea-Ice Heatmap</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  Bilinear spatial interpolation over 0.25° jittered grid points with smooth polygonal
                  envelope clipping and corridor edge-fading.
                </p>
                <div className="mt-4 font-mono text-[11px] text-teal-400">
                  Weight factor: W_ICE = 80 NM
                </div>
              </div>

              {/* Card 2: Iceberg Detection */}
              <div className="rounded-xl border border-gray-800 bg-gray-950/60 p-5 hover:border-cyan-800/60 transition-colors">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-sky-500/30 bg-sky-950/40 text-sky-400 mb-4">
                  <Activity size={20} />
                </div>
                <h3 className="text-base font-semibold text-white">Iceberg Superclustering</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  Dynamic multi-scale aggregation with expansion-zoom ease. Individual detections
                  render size-scaled rings with selection highlighting.
                </p>
                <div className="mt-4 font-mono text-[11px] text-sky-400">
                  Decay: 1.0° linear falloff
                </div>
              </div>

              {/* Card 3: Ocean Currents */}
              <div className="rounded-xl border border-gray-800 bg-gray-950/60 p-5 hover:border-cyan-800/60 transition-colors">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-950/40 text-cyan-400 mb-4">
                  <Waves size={20} />
                </div>
                <h3 className="text-base font-semibold text-white">WebGL Current Flow</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  Custom WebGL shader advecting 4,000 particles at 60 FPS across the Antarctic
                  Circumpolar Current vector field with HUD controls.
                </p>
                <div className="mt-4 font-mono text-[11px] text-cyan-400">
                  Vis factor: 300,000 × m/s
                </div>
              </div>

              {/* Card 4: A* Routing */}
              <div id="routing" className="rounded-xl border border-gray-800 bg-gray-950/60 p-5 hover:border-cyan-800/60 transition-colors">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-amber-500/30 bg-amber-950/40 text-amber-400 mb-4">
                  <Compass size={20} />
                </div>
                <h3 className="text-base font-semibold text-white">8-Connected A* Engine</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  Optimal pathfinding over 1,280 grid cells using King moves, admissible haversine
                  heuristics, and interactive endpoint pulse animations.
                </p>
                <div className="mt-4 font-mono text-[11px] text-amber-400">
                  Latency: &lt;150ms computation
                </div>
              </div>
            </div>
          </section>

          {/* ------------------------------------------------------------------
           * Footer
           * ------------------------------------------------------------------ */}
          <footer className="border-t border-gray-800/80 bg-gray-950 py-10">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <span className="font-bold tracking-wider text-slate-300">OFFSHORE</span>
                <span>·</span>
                <span>Ministry of Earth Sciences (MoES) / NCPOR</span>
                <span>·</span>
                <span>SIH PS 26059</span>
              </div>
              <div className="flex items-center gap-4 text-[11px]">
                <span>Antarctic Maritime Navigation Decision Support System</span>
              </div>
            </div>
          </footer>
        </div>
      )}
    </div>
  );
}

