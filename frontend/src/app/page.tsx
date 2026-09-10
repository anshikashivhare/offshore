"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Compass, ArrowRight } from "lucide-react";

export default function LandingPage() {
  const router = useRouter();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

useEffect(() => {
  if (videoRef.current) {
    videoRef.current.playbackRate = 1.25;
  }
}, []);

  const handleEnterCommandCenter = () => {
    setIsTransitioning(true);

    setTimeout(() => {
      router.push("/navigation");
    }, 650);
  };

  return (
    <div
      className={`relative h-screen w-screen overflow-hidden bg-[#061014] text-[#e6f4f8] select-none flex flex-col justify-between transition-all duration-700 ${
        isTransitioning ? "scale-110 opacity-0" : "scale-100 opacity-100"
      }`}
    >
      {/* ================================================================
          BACKGROUND VIDEO
         ================================================================ */}
      <video
  ref={videoRef}
  autoPlay
  muted
  loop
  playsInline
  preload="auto"
  className="absolute inset-0 z-0 h-full w-full object-cover"
>
      <source src="/videos/iceberg.mp4" type="video/mp4" />
    </video>

      {/* ================================================================
          DARK OVERLAY
         ================================================================ */}
      <div className="absolute inset-0 z-[1] bg-[#061014]/45 pointer-events-none" />

     {/* ================================================================
    CURVED SATELLITE ORBIT LINES - TOP RIGHT
================================================================ */}
<svg
  className="absolute top-0 right-0 w-[650px] h-[420px] pointer-events-none opacity-80"
  viewBox="0 0 650 420"
  fill="none"
>
  <defs>
    <filter id="satelliteGlow">
      <feGaussianBlur stdDeviation="2" result="coloredBlur" />
      <feMerge>
        <feMergeNode in="coloredBlur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  {/* ============================================================
      FIRST CURVED DOTTED ORBIT
  ============================================================ */}
  <path
    d="M 120 20 C 180 150, 320 210, 650 250"
    stroke="#22d3ee"
    strokeWidth="2"
    strokeDasharray="3 12"
    strokeLinecap="round"
    opacity="0.85"
  >
    <animate
      attributeName="stroke-dashoffset"
      values="0;-80"
      dur="4s"
      repeatCount="indefinite"
    />
  </path>

</svg>

  {/* ================================================================
    CURVED SATELLITE ORBIT LINES - TOP RIGHT
================================================================ */}
<svg
  className="absolute top-0 right-0 w-[620px] h-[400px] pointer-events-none z-[2]"
  viewBox="0 0 620 400"
  fill="none"
>
  {/* FIRST CURVED DOTTED LINE */}
  <path
    d="M 80 20 Q 230 260 620 300"
    stroke="#22d3ee"
    strokeWidth="2"
    strokeDasharray="4 12"
    strokeLinecap="round"
    opacity="0.75"
  >
    <animate
      attributeName="stroke-dashoffset"
      from="0"
      to="-80"
      dur="4s"
      repeatCount="indefinite"
    />
  </path>

  {/* SECOND CURVED DOTTED LINE */}
  <path
    d="M 180 10 Q 330 180 620 210"
    stroke="#22d3ee"
    strokeWidth="2"
    strokeDasharray="4 12"
    strokeLinecap="round"
    opacity="0.7"
  >
    <animate
      attributeName="stroke-dashoffset"
      from="0"
      to="-80"
      dur="5s"
      repeatCount="indefinite"
    />
  </path>

  {/* ============================================================
      SATELLITE - PLACED ON SECOND CURVED LINE
  ============================================================ */}
  <g transform="translate(470 175) rotate(15)">

    {/* LEFT SOLAR PANEL */}
    <rect
      x="-26"
      y="-6"
      width="14"
      height="12"
      fill="rgba(6,16,20,0.8)"
      stroke="#22d3ee"
      strokeWidth="1.5"
    />

    {/* CONNECTION LEFT */}
    <line
      x1="-12"
      y1="0"
      x2="-7"
      y2="0"
      stroke="#22d3ee"
      strokeWidth="1.5"
    />

    {/* SATELLITE BODY */}
    <rect
      x="-7"
      y="-7"
      width="14"
      height="14"
      rx="2"
      fill="#0B1820"
      stroke="#22d3ee"
      strokeWidth="1.8"
    />

    {/* CONNECTION RIGHT */}
    <line
      x1="7"
      y1="0"
      x2="12"
      y2="0"
      stroke="#22d3ee"
      strokeWidth="1.5"
    />

    {/* RIGHT SOLAR PANEL */}
    <rect
      x="12"
      y="-6"
      width="14"
      height="12"
      fill="rgba(6,16,20,0.8)"
      stroke="#22d3ee"
      strokeWidth="1.5"
    />

    {/* SMALL ANTENNA */}
    <line
      x1="0"
      y1="-7"
      x2="0"
      y2="-13"
      stroke="#22d3ee"
      strokeWidth="1.5"
    />

    <circle
      cx="0"
      cy="-15"
      r="2"
      fill="#22d3ee"
    />
  </g>

  {/* SMALL GLOWING ORBIT POINTS */}
  <circle cx="320" cy="150" r="3" fill="#22d3ee">
    <animate
      attributeName="opacity"
      values="0.3;1;0.3"
      dur="2s"
      repeatCount="indefinite"
    />
  </circle>

  <circle cx="540" cy="225" r="3" fill="#22d3ee">
    <animate
      attributeName="opacity"
      values="1;0.3;1"
      dur="2.5s"
      repeatCount="indefinite"
    />
  </circle>
</svg>

      {/* ================================================================
          GEOSPATIAL BACKGROUND GRID
         ================================================================ */}
      <div className="absolute inset-0 z-[2] geo-grid-pattern pointer-events-none opacity-40" />

      {/* ================================================================
          OCEAN VIGNETTE
         ================================================================ */}
      <div className="absolute inset-0 z-[2] ocean-vignette pointer-events-none" />

      {/* ================================================================
          CYAN ATMOSPHERIC GLOW
         ================================================================ */}
      <div
        className="absolute z-[2] top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-cyan-500/5 blur-[160px] rounded-full pointer-events-none"
        aria-hidden="true"
      />

      {/* ================================================================
          BACKGROUND ANTARCTIC VECTOR GEOMETRY
         ================================================================ */}
      <svg
        className="absolute inset-0 z-[2] w-full h-full pointer-events-none opacity-35"
        viewBox="0 0 1200 800"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <linearGradient
            id="landingRouteGradient"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="100%"
          >
            <stop
              offset="0%"
              stopColor="#38bdf8"
              stopOpacity="0.8"
            />

            <stop
              offset="100%"
              stopColor="#22d3ee"
              stopOpacity="0.8"
            />
          </linearGradient>
        </defs>

        {/* Faint Latitude Parallels */}
        {[200, 360, 520, 680].map((y, idx) => (
          <g key={`lat-${idx}`}>
            <line
              x1="0"
              y1={y}
              x2="1200"
              y2={y}
              stroke="rgba(120, 180, 200, 0.12)"
              strokeDasharray="2 6"
            />

            <text
              x="30"
              y={y - 6}
              fill="#324b59"
              fontSize="10"
              fontFamily="monospace"
            >
              6{idx + 1}°00&apos;S
            </text>
          </g>
        ))}

        {/* Faint Longitude Meridians */}
        {[250, 500, 750, 1000].map((x, idx) => (
          <g key={`lon-${idx}`}>
            <line
              x1={x}
              y1="0"
              x2={x}
              y2="800"
              stroke="rgba(120, 180, 200, 0.12)"
              strokeDasharray="2 6"
            />

            <text
              x={x + 8}
              y="35"
              fill="#324b59"
              fontSize="10"
              fontFamily="monospace"
            >
              6{idx * 2}°00&apos;W
            </text>
          </g>
        ))}

        {/* Animated Navigation Route */}
<polyline
  points="260,120 370,260 460,390 540,540 620,680"
  fill="none"
  stroke="url(#landingRouteGradient)"
  strokeWidth="1.75"
  className="animate-route-dash"
/>

        {/* ============================================================
            ICEBERG MARKERS
           ============================================================ */}
        <g opacity="0.6">
          <circle
            cx="480"
            cy="280"
            r="3"
            fill="#38bdf8"
          />

          <circle
            cx="480"
            cy="280"
            r="10"
            fill="none"
            stroke="#38bdf8"
            strokeWidth="0.5"
            strokeDasharray="2 2"
          />

          <text
            x="495"
            y="284"
            fill="#526f80"
            fontSize="9"
            fontFamily="monospace"
          >
            B-102
          </text>

          <circle
            cx="720"
            cy="410"
            r="4"
            fill="#38bdf8"
          />

          <circle
            cx="720"
            cy="410"
            r="12"
            fill="none"
            stroke="#38bdf8"
            strokeWidth="0.5"
            strokeDasharray="2 2"
          />

          <text
            x="735"
            y="414"
            fill="#526f80"
            fontSize="9"
            fontFamily="monospace"
          >
            A-68A
          </text>

          <circle
            cx="340"
            cy="510"
            r="2.5"
            fill="#38bdf8"
          />

          <text
            x="352"
            y="514"
            fill="#526f80"
            fontSize="9"
            fontFamily="monospace"
          >
            C-19B
          </text>
        </g>

        {/* ============================================================
            VESSEL MARKER
           ============================================================ */}
        <g transform="translate(460, 390)">
          <circle
            cx="0"
            cy="0"
            r="18"
            fill="none"
            stroke="#22d3ee"
            strokeWidth="0.75"
            className="animate-radar-ping"
          />

          <polygon
            points="0,-7 5,3 0,1 -5,3"
            fill="#22d3ee"
            transform="rotate(128)"
          />

          <text
            x="14"
            y="4"
            fill="#22d3ee"
            fontSize="9"
            fontFamily="monospace"
            fontWeight="bold"
          >
            MV POLAR EXPLORER · 15.2 kn
          </text>
        </g>
      </svg>

      {/* ================================================================
          HEADER
         ================================================================ */}
      <header className="relative z-10 p-6 sm:p-8 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-[#0B1820]/90 border border-[rgba(120,180,200,0.25)] flex items-center justify-center text-cyan-400">
            <Compass size={16} />
          </div>

          <span className="font-sans text-sm font-bold tracking-[0.25em] text-white">
            OFFSHORE
          </span>
        </div>

        {/* System Status */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#0B1820]/90 border border-[rgba(120,180,200,0.2)] text-xs font-mono text-[#8ea8b7]">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)] animate-pulse" />

          <span className="tracking-wider">
            SYSTEM ONLINE
          </span>
        </div>
      </header>

      {/* ================================================================
          MAIN CONTENT
         ================================================================ */}
      <main className="relative z-10 max-w-3xl mx-auto px-6 text-center my-auto">
        <h1
          className="font-sans text-6xl sm:text-7xl md:text-8xl font-bold tracking-[0.22em] uppercase leading-none mb-4"
          style={{
            background:
              "linear-gradient(180deg, #FFFFFF 0%, #D4E8F2 65%, rgba(140, 200, 225, 0.4) 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          OFFSHORE
        </h1>

        {/* Tagline */}
        <p className="text-xl sm:text-2xl font-light text-cyan-300 tracking-[0.16em] mb-4">
          Navigate the Unknown.
        </p>

        {/* Description */}
        <p className="max-w-md mx-auto text-xs sm:text-sm text-[#b0c6d0] font-sans leading-relaxed mb-10">
          AI-powered intelligence for Antarctic maritime navigation.
        </p>

        {/* CTA */}
        <button
          type="button"
          onClick={handleEnterCommandCenter}
          className="group inline-flex items-center gap-3 px-7 py-3.5 rounded-lg bg-[#0B1820]/90 hover:bg-[#102631] text-cyan-300 hover:text-white border border-cyan-500/40 hover:border-cyan-400 text-xs sm:text-sm font-semibold tracking-wider transition-all duration-300 shadow-[0_0_24px_rgba(34,211,238,0.15)] hover:shadow-[0_0_32px_rgba(34,211,238,0.3)] cursor-pointer"
        >
          <span>ENTER COMMAND CENTER</span>

          <ArrowRight
            size={16}
            className="group-hover:translate-x-1 transition-transform"
          />
        </button>
      </main>

      {/* ================================================================
          FOOTER
         ================================================================ */}
      <footer className="relative z-10 p-6 sm:p-8 flex items-center justify-between text-[10px] font-mono text-[#7894a2] border-t border-[rgba(120,180,200,0.12)]">
        <div>
          <span>
            ANTARCTIC PENINSULA CORRIDOR: 64°49&apos;S, 63°29&apos;W
          </span>
        </div>

        <div className="hidden sm:flex items-center gap-4">
          <span>OPERATIONS: NCPOR / MoES</span>
          <span>·</span>
          <span>POLAR CLASS 6 ASSIST</span>
        </div>
      </footer>
    </div>
  );
}