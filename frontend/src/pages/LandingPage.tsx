import React from 'react';
import { useLocation } from "wouter";
import { Compass, ArrowRight } from "lucide-react";

export default function LandingPage() {
  const [, setLocation] = useLocation();

  return (
    <div className="relative min-h-screen w-full bg-[#071526] text-white flex flex-col overflow-hidden font-jakarta select-none">
      
      {/* Background Video */}
      <div className="absolute inset-0 z-0">
        <video 
          autoPlay 
          loop 
          muted 
          playsInline 
          className="w-full h-full object-cover opacity-80"
          src="/iceberg.mp4"
        />
        {/* Subtle dark overlay for contrast */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#020b14]/40 via-transparent to-[#020b14]/60 mix-blend-multiply" />
      </div>

      {/* Decorative HUD Elements */}
      <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden">
        {/* Faint Grid Lines */}
        <svg className="absolute top-[20%] left-0 w-full h-1 overflow-visible" style={{ transform: 'rotate(-5deg)' }}>
          <line x1="0" y1="0" x2="100%" y2="0" stroke="currentColor" strokeWidth="1" strokeDasharray="4 8" className="text-white/10 animate-dash-flow-reverse" />
        </svg>
        <svg className="absolute top-[45%] left-0 w-full h-1 overflow-visible" style={{ transform: 'rotate(-5deg)' }}>
          <line x1="0" y1="0" x2="100%" y2="0" stroke="currentColor" strokeWidth="1" strokeDasharray="4 8" className="text-white/10 animate-dash-flow" />
        </svg>
        <svg className="absolute top-[70%] left-0 w-full h-1 overflow-visible" style={{ transform: 'rotate(-5deg)' }}>
          <line x1="0" y1="0" x2="100%" y2="0" stroke="currentColor" strokeWidth="1" strokeDasharray="4 8" className="text-white/10 animate-dash-flow-slow" />
        </svg>

        {/* Latitude Markers (Left edge) */}
        <div className="absolute left-8 top-[18%] text-[10px] tracking-widest text-white/30">61°00'S</div>
        <div className="absolute left-8 top-[43%] text-[10px] tracking-widest text-white/30">62°00'S</div>
        <div className="absolute left-8 top-[68%] text-[10px] tracking-widest text-white/30">63°00'S</div>
        <div className="absolute left-8 bottom-8 text-[10px] tracking-widest text-white/30">-64°00'S</div>

        {/* Right side orbit / satellite arc */}
        <svg className="absolute top-0 right-0 w-1/2 h-full opacity-20" viewBox="0 0 1000 1000" fill="none">
          <path d="M 1000,100 C 600,150 400,300 200,600" stroke="white" strokeWidth="1" strokeDasharray="4 8" className="animate-dash-flow" />
          <path d="M 1000,0 C 700,50 500,200 250,500" stroke="white" strokeWidth="1" strokeDasharray="4 8" className="animate-dash-flow-slow" />
          <rect x="750" y="240" width="12" height="12" fill="white" stroke="rgba(255,255,255,0.5)" strokeWidth="4" transform="rotate(30 750 240)" />
        </svg>

        {/* Tracking Points */}
        <div className="absolute top-[28%] left-[42%] flex items-center gap-2 text-white/40 text-[10px] tracking-widest">
          <span className="w-1.5 h-1.5 rounded-full bg-white/60 shadow-[0_0_4px_rgba(255,255,255,0.8)]" />
          B-102
        </div>
        
        <div className="absolute top-[48%] left-[45%] flex items-center gap-2 text-white/40 text-[10px] tracking-widest">
          <span className="w-1.5 h-1.5 rounded-full bg-white/60 shadow-[0_0_4px_rgba(255,255,255,0.8)]" />
          MV POLAR EXPLORER - 13.2 kn
        </div>

        <div className="absolute bottom-[30%] left-[28%] flex items-center gap-2 text-white/40 text-[10px] tracking-widest">
          <span className="w-1.5 h-1.5 rounded-full bg-white/60 shadow-[0_0_4px_rgba(255,255,255,0.8)]" />
          C-109
        </div>
      </div>

      {/* Header */}
      <header className="relative z-20 flex justify-between items-center px-8 py-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center bg-white/5 backdrop-blur-sm">
            <Compass size={16} className="text-white/80" />
          </div>
          <span className="font-bold tracking-[0.2em] text-sm text-white/90">OFFSHORE</span>
        </div>
        
        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)] animate-pulse" />
          <span className="text-[10px] tracking-widest text-white/70 font-medium">SYSTEM ONLINE</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-20 flex-1 flex flex-col justify-center items-center text-center mt-[-4rem]">
        <h1 
          className="font-montserrat font-bold text-white leading-none tracking-wide text-glow-subtle mb-4"
          style={{ fontSize: 'clamp(5rem, 10vw, 9rem)', textShadow: '0 8px 32px rgba(0, 15, 30, 0.6), 0 0 60px rgba(200, 240, 255, 0.2)' }}
        >
          OFFSHORE
        </h1>
        
        <h2 className="text-2xl sm:text-3xl font-light tracking-wide text-white/90 mb-3">
          Navigate the Unknown.
        </h2>
        
        <p className="text-sm sm:text-base text-white/60 tracking-wider font-light max-w-lg mb-10">
          AI-powered intelligence for Antarctic maritime navigation.
        </p>
        
        <button 
          onClick={() => setLocation("/dashboard")}
          className="group relative flex items-center gap-3 px-8 py-3.5 rounded-full border border-white/30 bg-white/5 backdrop-blur-md hover:bg-white/10 hover:border-white/50 transition-all duration-300"
        >
          <span className="text-xs font-semibold tracking-[0.15em] text-white">ENTER DASHBOARD</span>
          <ArrowRight size={14} className="text-white/70 group-hover:text-white transition-colors duration-300 group-hover:translate-x-1" />
        </button>
      </main>

      {/* Footer */}
      <footer className="relative z-20 flex justify-between items-end px-8 pb-8 text-[10px] tracking-[0.15em] text-white/40">
        <div>
          ANTARCTIC PENINSULA CORRIDOR: 64°49'S, 63°29'W
        </div>
        <div>
          OPERATIONS: NCPOR / MoES · POLAR CLASS 6 ASSIST
        </div>
      </footer>
    </div>
  );
}
