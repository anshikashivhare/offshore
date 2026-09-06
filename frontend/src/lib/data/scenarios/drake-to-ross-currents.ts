/**
 * drake-to-ross-currents — MOCK DATA.
 * ====================================================================
 * !!!! PLACEHOLDER / PROTOTYPE DATA — NOT REAL HYCOM / OSCAR INPUT !!!!
 *
 * Mock surface-current vector field for the Drake Passage → Ross Sea
 * corridor. Sibling to drake-to-ross.ts; the same scenario, a separate
 * data product.
 *
 * Real data will arrive later from:
 *   - HYCOM (HYbrid Coordinate Ocean Model) or OSCAR (Ocean Surface
 *     Current Analyses Real-time) — server-side resampling to a
 *     regular lon/lat grid, then exposed via the backend API.
 *
 * Pattern to reuse (matches the sea-ice generator in drake-to-ross.ts):
 *   - A 1° control grid of vector components `(u, v)` is bilinearly
 *     interpolated at any (lon, lat) by `sampleFlow`.
 *   - Speeds in the controls are HAND-ASSIGNED to a plausible
 *     Antarctic regime (NOT tropical reference values):
 *       - Body of the Antarctic Circumpolar Current (ACC): 0.05–0.15 m/s
 *       - ACC jets (where the corridor crosses a streamline
 *         concentration): 0.20–0.30 m/s
 *       - Ross Gyre northern limb: 0.05–0.15 m/s
 *   - Direction is east-going across the Drake, with a southward
 *     deflection as the ACC approaches the Ross Sea. NOT
 *     climatological truth; this is a smoke-test field.
 *
 * Why a regular grid (not a sparse point set):
 *   - The ocean-current layer advects thousands of particles via
 *     bilinear interpolation, so the CPU side needs O(1) per-particle
 *     lookup. A 1° grid (interpolated to 0.5° if needed) is the
 *     shape that the real backend will hand us.
 *   - The existing sea-ice scenario already established the
 *     control-grid + interpolator pattern. We mirror it here.
 */

/* ------------------------------------------------------------------
 * 1° control grid of u (east, m/s) and v (north, m/s)
 * ------------------------------------------------------------------ */
/** u-component (east-positive). One row per latitude (south-to-north). */
const CURRENT_U: ReadonlyArray<ReadonlyArray<number>> = [
  // lon   -66    -65    -64    -63    -62    -61    -60    -59    -58
  /* -70 */ [ 0.20,  0.22,  0.24,  0.25,  0.24,  0.22,  0.20,  0.18,  0.16],
  /* -68 */ [ 0.18,  0.20,  0.22,  0.23,  0.22,  0.20,  0.18,  0.16,  0.14],
  /* -66 */ [ 0.14,  0.16,  0.18,  0.20,  0.20,  0.18,  0.16,  0.14,  0.12],
  /* -64 */ [ 0.10,  0.12,  0.15,  0.18,  0.20,  0.18,  0.15,  0.12,  0.10],
  /* -62 */ [ 0.08,  0.10,  0.12,  0.15,  0.18,  0.18,  0.15,  0.10,  0.08],
  /* -60 */ [ 0.05,  0.07,  0.09,  0.12,  0.15,  0.15,  0.12,  0.09,  0.06],
];

/** v-component (north-positive, i.e. *negative* = southward in SH). */
const CURRENT_V: ReadonlyArray<ReadonlyArray<number>> = [
  // lon   -66    -65    -64    -63    -62    -61    -60    -59    -58
  /* -70 */ [-0.05, -0.06, -0.07, -0.07, -0.06, -0.05, -0.04, -0.03, -0.02],
  /* -68 */ [-0.04, -0.05, -0.06, -0.06, -0.05, -0.04, -0.03, -0.02, -0.02],
  /* -66 */ [-0.03, -0.04, -0.04, -0.04, -0.04, -0.03, -0.03, -0.02, -0.02],
  /* -64 */ [-0.02, -0.02, -0.03, -0.03, -0.03, -0.02, -0.02, -0.02, -0.01],
  /* -62 */ [-0.01, -0.01, -0.02, -0.02, -0.02, -0.02, -0.01, -0.01, -0.01],
  /* -60 */ [ 0.00,  0.00, -0.01, -0.01, -0.01, -0.01,  0.00,  0.00,  0.00],
];

/** Maximum speed anywhere on the control grid. Used by the shader
 *  to normalize `vSpeed` into the color-ramp input. Computed once
 *  at module load — small array, this is cheap. */
function computeMaxSpeed(): number {
  let max = 0;
  for (let i = 0; i < CURRENT_U.length; i++) {
    for (let j = 0; j < CURRENT_U[i].length; j++) {
      const u = CURRENT_U[i][j];
      const v = CURRENT_V[i][j];
      const s = Math.hypot(u, v);
      if (s > max) max = s;
    }
  }
  // Round up to a tidy 0.05 m/s tick for the legend.
  return Math.ceil(max * 20) / 20;
}

export const CURRENT_LON_AXIS = [-66, -65, -64, -63, -62, -61, -60, -59, -58];
export const CURRENT_LAT_AXIS = [-70, -68, -66, -64, -62, -60]; // south-to-north
export const CURRENT_MAX_SPEED_MS = computeMaxSpeed();

/** Particle-spawn bounds. Particles that advect outside this box
 *  are respawned at a random position inside it.
 *
 *  Why wider than the data grid:
 *    - The u/v control grid (above) is the authoritative mock data and
 *      is anchored to the drake-to-ross corridor (8°×10°). But the
 *      CustomLayerInterface's particles are visible at every zoom, and
 *      the user can pan/zoom the basemap to adjacent regions.
 *    - For the default view (center [-62, -65], zoom 3.6, 1024×768),
 *      maplibre shows roughly 50° of longitude and 17° of latitude
 *      on screen. A corridor-only spawn box would leave the rest of
 *      the visible area empty when the layer is enabled.
 *    - Widening SPAWN_BOUNDS without widening the data grid is safe:
 *      sampleFlow() clamps out-of-grid lookups to the nearest corner,
 *      so particles outside the data grid simply resample the
 *      boundary (u, v) value. They still advect — they just take the
 *      boundary direction. That looks fine for placeholder data.
 *
 *    This is intentional: when the real HYCOM/OSCAR grid arrives, it
 *    will be much wider than the corridor and SPAWN_BOUNDS can be
 *    extended again to match. Today we want the visible viewport to
 *    never be empty of particles.
 */
export const SPAWN_BOUNDS = {
  // 22° wide — wider than the corridor (8°) but inside the typical
  // visible map width at z3.6 (≈50°), so panning ±7° east/west still
  // shows particles at the edge of the screen.
  lonMin: -72,
  lonMax: -50,
  // 17° tall — matches the typical visible map height at z3.6
  // around -65°S (≈17°), so particles cover top-to-bottom of the
  // default view. The corridor's lat axis is -70..-60; this extends
  // 2° south and 5° north to fill the screen on the Ross-Sea side.
  latMin: -72,
  latMax: -55,
} as const;

/* ------------------------------------------------------------------
 * Bilinear interpolation (mirrors the sea-ice sampler)
 * ------------------------------------------------------------------ */
function bracket(axis: ReadonlyArray<number>, v: number): number {
  if (v <= axis[0]) return 0;
  if (v >= axis[axis.length - 1]) return axis.length - 2;
  for (let i = 0; i < axis.length - 1; i++) {
    if (v >= axis[i] && v <= axis[i + 1]) return i;
  }
  return axis.length - 2;
}

export interface FlowSample {
  /** East-component (m/s). Positive = eastward. */
  u: number;
  /** North-component (m/s). Positive = northward. */
  v: number;
  /** Magnitude (m/s), sqrt(u² + v²). */
  speed: number;
}

/** Bilinear lookup of (u, v) at any (lon, lat) inside the corridor.
 *  Values outside the grid are clamped to the nearest corner. */
export function sampleFlow(lon: number, lat: number): FlowSample {
  const li = bracket(CURRENT_LON_AXIS, lon);
  const ai = bracket(CURRENT_LAT_AXIS, lat);
  const lon0 = CURRENT_LON_AXIS[li];
  const lon1 = CURRENT_LON_AXIS[li + 1];
  const lat0 = CURRENT_LAT_AXIS[ai];
  const lat1 = CURRENT_LAT_AXIS[ai + 1];
  // CORNERS arrays are south-to-north: ai = southern row.
  const uSW = CURRENT_U[ai][li];
  const uSE = CURRENT_U[ai][li + 1];
  const uNW = CURRENT_U[ai + 1][li];
  const uNE = CURRENT_U[ai + 1][li + 1];
  const vSW = CURRENT_V[ai][li];
  const vSE = CURRENT_V[ai][li + 1];
  const vNW = CURRENT_V[ai + 1][li];
  const vNE = CURRENT_V[ai + 1][li + 1];

  const tx = lon1 === lon0 ? 0 : (lon - lon0) / (lon1 - lon0);
  // lat is negative; lat0 < lat1, so (lat - lat0) / (lat1 - lat0) works
  // for SH just like NH.
  const ty = lat1 === lat0 ? 0 : (lat - lat0) / (lat1 - lat0);

  const u = (uSW + (uSE - uSW) * tx) + (((uNW + (uNE - uNW) * tx)) - (uSW + (uSE - uSW) * tx)) * ty;
  const v = (vSW + (vSE - vSW) * tx) + (((vNW + (vNE - vNW) * tx)) - (vSW + (vSE - vSW) * tx)) * ty;
  return { u, v, speed: Math.hypot(u, v) };
}

/* ------------------------------------------------------------------
 * Test surface — exported so a quick smoke-check can be done from
 * devtools / a node script. Not consumed by the layer.
 * ------------------------------------------------------------------ */
export const CURRENT_FIELD = {
  lonAxis: CURRENT_LON_AXIS,
  latAxis: CURRENT_LAT_AXIS,
  maxSpeedMs: CURRENT_MAX_SPEED_MS,
  sample: sampleFlow,
} as const;
