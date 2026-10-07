import React from 'react';
import { OffshoreLogo } from './OffshoreLogo.tsx';

export type OffshoreAnimStyle = 'parallax' | 'tracking' | 'ascent' | 'restrained';

interface OffshoreHeroProps {
  /** Current animation cycle time in seconds (0.0 to 9.6s) */
  currentTime: number;
  /** Total cycle length in seconds */
  cycleDuration?: number;
  /** Whether animation is currently playing */
  isPlaying?: boolean;
  /** Callbacks for interactive elements */
  onNavClick?: (navKey: string) => void;
  onPlanVoyageClick?: () => void;
  /** Mode for clean export / capture */
  isCaptureMode?: boolean;
  /** Whether the OFFSHORE text is positioned behind the mountain peaks (3D depth layer) */
  isBehindMountains?: boolean;
  /** Fine-tune vertical position of OFFSHORE behind the mountain peaks in pixels */
  depthOffset?: number;
  /** Animation preset style for the OFFSHORE text */
  animStyle?: OffshoreAnimStyle;
}

/**
 * Calculates smooth Hermite / smoothstep interpolation
 */
function smoothstep(min: number, max: number, value: number): number {
  const x = Math.max(0, Math.min(1, (value - min) / (max - min)));
  return x * x * (3 - 2 * x);
}

/**
 * Computes exact opacity rhythm for secondary content based on the reference:
 * 0.0 - 2.0s: Full OFFSHORE composition visible (1.0)
 * 2.0 - 2.9s: Secondary content gently fades down (1.0 -> 0.0)
 * 2.9 - 3.2s: Rest at 0.0
 * 3.2 - 4.1s: Softly fades back in (0.0 -> 1.0)
 * 4.1 - 5.2s: Full composition visible (1.0)
 * 5.2 - 6.1s: Gently fades down again (1.0 -> 0.0)
 * 6.1 - 6.4s: Rest at 0.0
 * 6.4 - 7.4s: Content returns (0.0 -> 1.0)
 * 7.4 - 9.6s: Full composition settles (1.0)
 * Seamlessly loops back to 0.0s!
 */
export function getSecondaryOpacity(time: number, duration = 9.6): number {
  const t = time % duration;

  if (t < 2.0) {
    return 1.0;
  } else if (t < 2.9) {
    const p = smoothstep(2.0, 2.9, t);
    return 1.0 - p;
  } else if (t < 3.2) {
    return 0.0;
  } else if (t < 4.1) {
    const p = smoothstep(3.2, 4.1, t);
    return p;
  } else if (t < 5.2) {
    return 1.0;
  } else if (t < 6.1) {
    const p = smoothstep(5.2, 6.1, t);
    return 1.0 - p;
  } else if (t < 6.4) {
    return 0.0;
  } else if (t < 7.4) {
    const p = smoothstep(6.4, 7.4, t);
    return p;
  } else {
    return 1.0;
  }
}

/**
 * Computes dynamic, cinematic animation for the primary OFFSHORE headline
 * Situated in 3D space behind the mountain peaks
 */
export function getOffshoreHeadlineAnimation(
  time: number,
  duration = 9.6,
  style: OffshoreAnimStyle = 'parallax',
  depthOffset = 0
) {
  const t = (time % duration) / duration;
  const cycleRad = t * Math.PI * 2;

  // Secondary content fade timing to correlate the motion
  const secondaryOp = getSecondaryOpacity(time, duration);
  // Quiet moment factor (0 = full UI visible, 1 = secondary UI faded down)
  const quietMomentFactor = 1.0 - secondaryOp;

  let translateY = depthOffset;
  let scale = 1.0;
  let letterSpacing = 0.065;
  let opacity = 0.98;
  let glowIntensity = 0.3;

  switch (style) {
    case 'parallax':
      // Gentle vertical float + quiet moment lift + slow tracking breath
      translateY += Math.sin(cycleRad) * 7 - quietMomentFactor * 8;
      scale = 1.0 + Math.sin(cycleRad) * 0.01 + quietMomentFactor * 0.008;
      letterSpacing = 0.065 + Math.sin(cycleRad) * 0.007 + quietMomentFactor * 0.006;
      opacity = 0.92 + Math.cos(cycleRad) * 0.06 + quietMomentFactor * 0.02;
      glowIntensity = 0.25 + Math.sin(cycleRad) * 0.2 + quietMomentFactor * 0.25;
      break;

    case 'tracking':
      // Expansive letter-spacing breath and luminous icy glow
      translateY += Math.sin(cycleRad) * 4 - quietMomentFactor * 5;
      scale = 1.0 + Math.sin(cycleRad) * 0.006;
      letterSpacing = 0.065 + Math.sin(cycleRad) * 0.014;
      opacity = 0.94 + Math.cos(cycleRad) * 0.06;
      glowIntensity = 0.3 + Math.sin(cycleRad) * 0.3;
      break;

    case 'ascent':
      // Cinematic horizon ascent: begins deeper behind peaks and rises majestically
      const riseProgress = Math.sin((t - 0.25) * Math.PI * 2) * 0.5 + 0.5;
      translateY += (1 - riseProgress) * 18;
      scale = 0.985 + riseProgress * 0.025;
      letterSpacing = 0.062 + riseProgress * 0.01;
      opacity = 0.86 + riseProgress * 0.14;
      glowIntensity = 0.2 + riseProgress * 0.3;
      break;

    case 'restrained':
    default:
      // Minimal luxury motion matching the reference video
      translateY += Math.sin(cycleRad) * 3 - quietMomentFactor * 3;
      scale = 1.0 + Math.sin(cycleRad) * 0.004;
      letterSpacing = 0.065;
      opacity = 0.96 + Math.cos(cycleRad) * 0.04;
      glowIntensity = 0.25;
      break;
  }

  return {
    translateY,
    scale,
    letterSpacing: `${letterSpacing.toFixed(4)}em`,
    opacity,
    textShadow: `0 0 35px rgba(210, 238, 255, ${glowIntensity.toFixed(2)}), 0 0 70px rgba(160, 215, 255, ${(glowIntensity * 0.5).toFixed(2)})`,
  };
}

/**
 * Subtle stable opacity for top header
 */
export function getHeaderOpacity(time: number, duration = 9.6): number {
  const t = (time % duration) / duration;
  return 0.95 + Math.sin(t * Math.PI * 2) * 0.05;
}

export const OffshoreHero: React.FC<OffshoreHeroProps> = ({
  currentTime,
  cycleDuration = 9.6,
  isPlaying = true,
  onNavClick,
  onPlanVoyageClick,
  isCaptureMode = false,
  isBehindMountains = true,
  depthOffset = 0,
  animStyle = 'parallax',
}) => {
  const loopProgress = (currentTime % cycleDuration) / cycleDuration;
  const secondaryOpacity = getSecondaryOpacity(currentTime, cycleDuration);
  const headlineAnim = getOffshoreHeadlineAnimation(currentTime, cycleDuration, animStyle, depthOffset);
  const headerOpacity = getHeaderOpacity(currentTime, cycleDuration);

  // Subtle Y translation tied to opacity fade for cinematic softness (never abrupt)
  const secondaryY = (1 - secondaryOpacity) * 6;



  return (
    <div
      id="offshore-hero-stage"
      className="relative w-full aspect-video min-h-[580px] max-h-[100vh] overflow-hidden select-none bg-[#091b30]"
      style={{
        width: '100%',
      }}
    >
      {/* ======================================================== */}
      {/* LAYER 1: REPLACED WITH THE PROVIDED OFFSHORE HERO IMAGE */}
      {/* The supplied clean Antarctic image is now the sole scene background. */}
      {/* ======================================================== */}
      <img
        id="offshore-hero-background"
        data-offshore-background="true"
        src="/offshore-antarctic-hero-bg.png"
        alt="Antarctic fjord landscape"
        className="absolute inset-0 z-0 h-full w-full object-cover select-none pointer-events-none"
        draggable={false}
        style={{
          transform: `scale(${1 + Math.sin(loopProgress * Math.PI * 2) * 0.002})`,
          transformOrigin: 'center center',
        }}
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 z-[1] pointer-events-none"
        style={{
          background: 'linear-gradient(180deg, rgba(3, 26, 52, 0.02) 0%, rgba(3, 26, 52, 0.06) 100%)',
        }}
      />

      {/* ======================================================== */}
      {/* LAYER 2: PRIMARY "OFFSHORE" HEADLINE (Z: 10 when behind mountains, Z: 25 when in front) */}
      {/* Tucked behind the mountain ridges & faceted central peak */}
      {/* ======================================================== */}
      <div
        className={`absolute top-[16%] sm:top-[18%] md:top-[20%] left-0 right-0 w-full flex items-center justify-center pointer-events-none px-4 transition-all duration-100 ${
          isBehindMountains ? 'z-10' : 'z-25'
        }`}
        style={{
          transform: `translate3d(0, ${headlineAnim.translateY}px, 0) scale(${headlineAnim.scale})`,
          opacity: headlineAnim.opacity,
          letterSpacing: headlineAnim.letterSpacing,
          transition: 'transform 0.08s ease-out, opacity 0.08s ease-out, letter-spacing 0.12s ease-out',
        }}
      >
        <h1
          className="font-montserrat text-white font-[200] leading-none text-center select-none w-full"
          style={{
            fontSize: 'clamp(4.2rem, 15.2vw, 15.2rem)',
            textShadow: headlineAnim.textShadow,
          }}
        >
          OFFSHORE
        </h1>
      </div>

      {/* ======================================================== */}
      {/* LAYER 3: FOREGROUND MOUNTAIN MASK (Z: 20) */}
      {/* This layer provides the transparent cutout of the mountain peaks. */}
      {/* ======================================================== */}
      <img
        src="/offshore-mountains-foreground.png"
        alt=""
        className="absolute inset-0 z-20 h-full w-full object-cover select-none pointer-events-none"
        draggable={false}
        style={{
          transform: `scale(${1 + Math.sin(loopProgress * Math.PI * 2) * 0.002})`,
          transformOrigin: 'center center',
        }}
      />

      {/* ======================================================== */}
      {/* LAYER 4: TOP HEADER & SECONDARY UI (Z: 30) */}
      {/* ======================================================== */}
      <header
        className="absolute top-0 left-0 right-0 z-30 w-full px-6 sm:px-12 md:px-16 pt-6 sm:pt-8 flex items-center justify-between pointer-events-auto"
        style={{
          opacity: headerOpacity,
          transition: 'opacity 0.2s ease-out',
        }}
      >
        {/* Brand Logo & Wordmark */}
        <button
          onClick={() => onNavClick?.('home')}
          className="cursor-pointer text-left focus:outline-none"
          title="OFFSHORE Navigation Intelligence"
        >
          <OffshoreLogo />
        </button>

      </header>

      {/* LAYER 5: SECONDARY CONTENT (ANTARCTIC NAVIGATION + INTELLIGENT MARITIME ROUTING + CTA) */}
      {/* Positioned over the lower fjord water with the exact smooth fade rhythm */}
      <div
        className="absolute bottom-[6%] sm:bottom-[7%] md:bottom-[9%] left-0 right-0 z-30 w-full flex flex-col items-center justify-center text-center px-4"
        style={{
          opacity: secondaryOpacity,
          transform: `translateY(${secondaryY}px)`,
          transition: 'opacity 0.12s cubic-bezier(0.16, 1, 0.3, 1), transform 0.12s cubic-bezier(0.16, 1, 0.3, 1)',
          pointerEvents: secondaryOpacity > 0.1 ? 'auto' : 'none',
        }}
      >
        {/* ANTARCTIC NAVIGATION Title */}
        <h2 className="font-montserrat font-light text-white uppercase text-glow-subtle tracking-[0.14em] leading-tight text-[1.65rem] sm:text-[2.6rem] md:text-[3.5rem] lg:text-[4.2rem]">
          ANTARCTIC NAVIGATION
        </h2>

        {/* INTELLIGENT MARITIME ROUTING Subtitle */}
        <p className="font-montserrat font-light text-white/95 uppercase tracking-[0.22em] text-[10px] sm:text-[14px] md:text-[18px] lg:text-[20px] mt-1 sm:mt-2 mb-5 sm:mb-7 text-glow-subtle">
          INTELLIGENT MARITIME ROUTING
        </p>

        {/* CTA BUTTON GROUP (PLAN A VOYAGE pill button + Circular Arrow button) */}
        <div className="flex items-center justify-center gap-3 sm:gap-3.5">
          {/* Main "PLAN A VOYAGE" Button */}
          <button
            onClick={() => onPlanVoyageClick?.()}
            className="group font-montserrat font-semibold bg-white text-[#0a192f] hover:bg-white/95 active:scale-[0.98] transition-all duration-200 rounded-full px-8 sm:px-11 py-3 sm:py-3.5 text-xs sm:text-[13px] tracking-[0.16em] uppercase btn-ocean-shadow cursor-pointer focus:outline-none flex items-center justify-center"
          >
            <span>PLAN A VOYAGE</span>
          </button>

          {/* Adjacent Circular Arrow Button */}
          <button
            onClick={() => onPlanVoyageClick?.()}
            className="group w-11 sm:w-12 h-11 sm:h-12 rounded-full bg-white hover:bg-white/95 active:scale-[0.98] transition-all duration-200 flex items-center justify-center btn-ocean-shadow cursor-pointer focus:outline-none shrink-0"
            aria-label="Open Voyage Route Navigator"
          >
            {/* Exact diagonal up-right arrow */}
            <svg
              viewBox="0 0 24 24"
              className="w-4 h-4 sm:w-4.5 sm:h-4.5 text-[#0a192f] transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="7" y1="17" x2="17" y2="7" />
              <polyline points="7 7 17 7 17 17" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
