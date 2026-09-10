"use client";

import React from "react";
import { ArrowRight, Menu, X, Compass, Shield, Activity, Waves } from "lucide-react";

// Inline Button Component
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost" | "gradient";
  size?: "default" | "sm" | "lg";
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "default", size = "default", className = "", children, ...props }, ref) => {
    const baseStyles =
      "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer";

    const variants = {
      default: "bg-white text-black hover:bg-gray-100",
      secondary: "bg-gray-800 text-white hover:bg-gray-700",
      ghost: "hover:bg-gray-800/50 text-white",
      gradient:
        "bg-gradient-to-b from-white via-white/95 to-white/60 text-black hover:scale-105 active:scale-95 shadow-lg shadow-white/10",
    };

    const sizes = {
      default: "h-10 px-4 py-2 text-sm",
      sm: "h-9 px-4 text-xs",
      lg: "h-12 px-8 text-base",
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

// Navigation Component
export const Navigation = React.memo(() => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <header className="fixed top-0 w-full z-50 border-b border-gray-800/50 bg-black/80 backdrop-blur-md">
      <nav className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <Compass size={18} />
            </div>
            <span className="text-xl font-bold tracking-wider text-white">OFFSHORE</span>
          </div>

          <div className="hidden md:flex items-center justify-center gap-8 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
            <a
              href="#mission"
              className="text-sm text-white/60 hover:text-white transition-colors"
            >
              Mission
            </a>
            <a
              href="#layers"
              className="text-sm text-white/60 hover:text-white transition-colors"
            >
              Layers
            </a>
            <a
              href="#routing"
              className="text-sm text-white/60 hover:text-white transition-colors"
            >
              A* Routing
            </a>
            <a
              href="#documentation"
              className="text-sm text-white/60 hover:text-white transition-colors"
            >
              Documentation
            </a>
          </div>

          <div className="hidden md:flex items-center gap-4">
            <Button type="button" variant="ghost" size="sm">
              Telemetry
            </Button>
            <Button type="button" variant="default" size="sm">
              Launch App
            </Button>
          </div>

          <button
            type="button"
            className="md:hidden text-white cursor-pointer"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>

      {mobileMenuOpen && (
        <div className="md:hidden bg-black/95 backdrop-blur-md border-t border-gray-800/50">
          <div className="px-6 py-4 flex flex-col gap-4">
            <a
              href="#mission"
              className="text-sm text-white/60 hover:text-white transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Mission
            </a>
            <a
              href="#layers"
              className="text-sm text-white/60 hover:text-white transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Layers
            </a>
            <a
              href="#routing"
              className="text-sm text-white/60 hover:text-white transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              A* Routing
            </a>
            <a
              href="#documentation"
              className="text-sm text-white/60 hover:text-white transition-colors py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Documentation
            </a>
            <div className="flex flex-col gap-2 pt-4 border-t border-gray-800/50">
              <Button type="button" variant="ghost" size="sm">
                Telemetry
              </Button>
              <Button type="button" variant="default" size="sm">
                Launch App
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
});

Navigation.displayName = "Navigation";

// Hero Component
export const Hero = React.memo(() => {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-start px-6 py-24 md:py-28">
      {/* Ambient background glow */}
      <div
        className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-cyan-500/15 blur-[120px] rounded-full pointer-events-none"
        aria-hidden="true"
      />

      <aside className="mb-8 inline-flex flex-wrap items-center justify-center gap-2 px-4 py-2 rounded-full border border-cyan-500/30 bg-cyan-950/40 backdrop-blur-sm max-w-full">
        <span className="text-xs text-center whitespace-nowrap text-cyan-300">
          MoES / NCPOR · SIH PS 26059
        </span>
        <a
          href="#mission"
          className="flex items-center gap-1 text-xs text-cyan-400 hover:text-white transition-all active:scale-95 whitespace-nowrap"
          aria-label="Explore mission corridor"
        >
          Explore corridor
          <ArrowRight size={12} />
        </a>
      </aside>

      <h1
        className="text-4xl md:text-5xl lg:text-6xl font-semibold text-center max-w-4xl px-6 leading-tight mb-6 tracking-tight"
        style={{
          background: "linear-gradient(to bottom, #ffffff, #ffffff, rgba(255, 255, 255, 0.65))",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        }}
      >
        Antarctic Maritime Navigation <br />Decision Support System
      </h1>

      <p className="text-sm md:text-base text-center max-w-2xl px-6 mb-10 text-slate-400">
        AI-enabled navigation combining real-time sea-ice forecasting, YOLO iceberg detection,
        ocean-current advection, and A* risk-optimized routing across Antarctic corridors.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-4 relative z-10 mb-14">
        <Button
          type="button"
          variant="gradient"
          size="lg"
          className="rounded-lg flex items-center justify-center"
          aria-label="Get started with the platform"
          onClick={() => {
            document.getElementById("mission-map-container")?.scrollIntoView({ behavior: "smooth" });
          }}
        >
          Inspect Mission Map
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="lg"
          className="rounded-lg border border-gray-700/80 bg-gray-900/80 hover:bg-gray-800"
          onClick={() => {
            window.location.href = "#routing";
          }}
        >
          View A* Routing
        </Button>
      </div>

      {/* Feature Pills */}
      <div className="flex flex-wrap items-center justify-center gap-3 max-w-3xl mb-16 text-xs text-slate-300">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-800 bg-gray-900/60">
          <Shield size={14} className="text-teal-400" />
          <span>Sea-Ice Heatmap</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-800 bg-gray-900/60">
          <Activity size={14} className="text-sky-400" />
          <span>Iceberg Superclustering</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-800 bg-gray-900/60">
          <Waves size={14} className="text-cyan-400" />
          <span>WebGL Particle Advection</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-800 bg-gray-900/60">
          <Compass size={14} className="text-amber-400" />
          <span>A* Multi-Objective Routing</span>
        </div>
      </div>

      {/* Visual Showcase Card with High-Tech Preview */}
      <div className="w-full max-w-5xl relative pb-20">
        <div
          className="absolute left-1/2 w-[95%] pointer-events-none z-0"
          style={{
            top: "-20%",
            transform: "translateX(-50%)",
          }}
          aria-hidden="true"
        >
          <div className="w-full h-48 bg-gradient-to-r from-cyan-500/20 via-teal-500/20 to-blue-500/20 blur-3xl opacity-60" />
        </div>

        <div className="relative z-10 rounded-xl border border-gray-800 bg-gray-950/80 shadow-2xl overflow-hidden backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-gray-800/80 bg-gray-900/60 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-red-500/80" />
              <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <span className="h-3 w-3 rounded-full bg-green-500/80" />
              <span className="ml-2 font-mono text-xs text-slate-400">
                offshore://antarctica/drake-to-ross-corridor
              </span>
            </div>
            <span className="font-mono text-xs text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2.5 py-0.5 rounded-full">
              LIVE TELEMETRY
            </span>
          </div>

          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?auto=format&fit=crop&w=1600&q=80"
            alt="Antarctic maritime navigation and iceberg surveillance"
            className="w-full h-[420px] object-cover filter contrast-125 brightness-90"
            loading="eager"
          />
        </div>
      </div>
    </section>
  );
});

Hero.displayName = "Hero";

// Main Component
export default function SaaSComponent() {
  return (
    <main className="min-h-screen bg-black text-white selection:bg-cyan-500 selection:text-black">
      <Navigation />
      <Hero />
    </main>
  );
}

