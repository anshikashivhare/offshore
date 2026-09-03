/**
 * useOceanCurrentControls — per-layer UI state for the ocean-current
 * CustomLayerInterface.
 *
 * Architectural decision (mirrors the useIcebergSelection pattern):
 *   - useLayerStore is the generic per-LayerId store for things every
 *     layer shares (enabled, opacity). It must NOT grow fields that
 *     are specific to one layer.
 *   - Particle count and speed multiplier are inputs to one layer's
 *     shader + CPU loop. They live here so the layer's useEffects can
 *     react to them; nothing else in the app cares.
 *
 * Defaults are tuned for a 1024×768 viewport at the corridor's
 * default zoom 3.6 — visibly dense, comfortably under 60 fps on
 * integrated GPUs.
 *
 * Why no `colorBy` here:
 *   - The current fragment shader implements a single sequential
 *     speed ramp (glacial → signal → lagoon → alert → hazard). A
 *     second "direction" mode was originally considered but
 *     requires a per-particle hue shader (HSL space) that's a
 *     non-trivial change. Until that's implemented, the panel
 *     exposes only the controls that actually affect the shader.
 */
"use client";

import { create } from "zustand";

interface OceanCurrentControlsState {
  particleCount: number;
  speedMultiplier: number;
  setParticleCount: (n: number) => void;
  setSpeedMultiplier: (m: number) => void;
}

const PARTICLE_MIN = 500;
const PARTICLE_MAX = 10000;
const SPEED_MIN = 0.1;
const SPEED_MAX = 3.0;

export const useOceanCurrentControls = create<OceanCurrentControlsState>(
  (set) => ({
    particleCount: 4000,
    speedMultiplier: 1.0,
    setParticleCount: (n) =>
      set({ particleCount: clamp(n, PARTICLE_MIN, PARTICLE_MAX) }),
    setSpeedMultiplier: (m) =>
      set({ speedMultiplier: clamp(m, SPEED_MIN, SPEED_MAX) }),
  }),
);

export const OCEAN_CURRENT_LIMITS = {
  particleMin: PARTICLE_MIN,
  particleMax: PARTICLE_MAX,
  speedMin: SPEED_MIN,
  speedMax: SPEED_MAX,
} as const;

function clamp(n: number, lo: number, hi: number): number {
  if (Number.isNaN(n)) return lo;
  if (n < lo) return lo;
  if (n > hi) return hi;
  return Math.round(n);
}
