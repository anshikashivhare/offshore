/**
 * drake-to-ross scenario — MOCK DATA.
 * ====================================================================
 * !!!! PLACEHOLDER / PROTOTYPE DATA — NOT REAL SATELLITE / NSIDC INPUT !!!!
 *
 * This module is the single source of mock data for the Drake Passage →
 * Ross Sea corridor. It exists so that sea-ice and iceberg layers have
 * something to render during early frontend development, before the
 * backend's data ingestion + risk_engine pipelines are online.
 *
 * Real data will arrive later from:
 *   - NSIDC sea-ice concentration rasters (backend preprocessing → GeoJSON)
 *   - ML iceberg detection (YOLO/CV pipeline) writing to database
 *
 * Pattern to reuse:
 *   - Each scenario exports a `SEA_ICE_GEOJSON` and an `ICEBERG_GEOJSON`
 *     feature collection. The shape (FeatureCollection of Points / Polygons
 *     with consistent property names) is what layer components will
 *     read against.
 *   - A future `oceanCurrents` scenario should follow the same shape:
 *     export a single FeatureCollection where each feature represents
 *     a vector arrow (LineString of length 1, or Point with `u`/`v`
 *     properties for arrow-drawing in a CustomLayer).
 *   - When the backend is online, the layer components will swap from
 *     `import { ICEBERG_GEOJSON } from "@/lib/data/scenarios/..."` to
 *     `fetch('/api/icebergs?...')` returning the same GeoJSON shape.
 *     The layer code does not change.
 *
 * Why hand-authored here instead of a generator:
 *   - The mock data is small (one concentration grid + a handful of
 *     detections). A PRNG-based "generator" would only obscure the
 *     shape we want the layer code to learn against. The intent of
 *     this scenario is a reference implementation, not volume.
 */

import type { Feature, FeatureCollection, Point } from "geojson";

export interface SeaIceFeatureProps {
  /** 0..1, fraction of grid cell covered by ice. */
  concentration: number;
}

export interface IcebergFeatureProps {
  id: string;
  /** Major-axis length in metres. Placeholder. */
  sizeM: number;
  /** 0..1 detector confidence. Placeholder. */
  confidence: number;
  /** ISO-8601 UTC. Placeholder detection timestamp. */
  detectedAt: string;
}

export type SeaIceFeature = Feature<Point, SeaIceFeatureProps>;
export type IcebergFeature = Feature<Point, IcebergFeatureProps>;

/* ------------------------------------------------------------------
 * Sea-ice concentration field
 * ------------------------------------------------------------------
 * Emits a 0.25° JITTERED point grid over a POLYGON-shaped envelope
 * that follows the Antarctic Peninsula corridor — not a rectangular
 * coordinate box, and not a perfectly regular grid.
 *
 * Three reasons it's not a regular grid:
 *
 *   1. Polygon envelope. The corridor is a quadrilateral whose
 *      western edge runs diagonally (the peninsula itself) and whose
 *      interior holds a poleward-increasing concentration gradient
 *      (open water in the Drake, pack ice in the Ross / Weddell).
 *      Points outside the polygon are dropped, so the heatmap
 *      renders the polygon's organic shape instead of a hard box.
 *
 *   2. Position jitter. Each grid cell's point is offset by up to
 *      half a step in each axis (mulberry32-seeded for stability).
 *      A regular grid produces faint row/column artefacts in the
 *      heatmap no matter what radius is chosen, because every
 *      point lies on the same lat-line and same lon-line. Jitter
 *      breaks that structure so the gaussian-falloff halos blend
 *      into a single organic field.
 *
 *   3. Concentration sampled at the jittered point. The
 *      concentration value is the bilinearly-interpolated field
 *      value at the *jittered* (lon, lat), not at the grid cell
 *      center. This means the field is smooth at the per-point
 *      level, not just at the per-cell level.
 *
 * Why 0.25° resolution (vs the previous 0.5°):
 *   - At z3.6 the 0.5° grid was ~10 px between points. Even with a
 *     heatmap radius of 25 px, the row structure was visible as
 *     "horizontal stripes" because each row's points fall in a
 *     narrow vertical band. 0.25° halves the spacing to ~5 px and
 *     a heatmap radius of ~30 px gives ~6× overlap, so points
 *     blend smoothly into a continuous field.
 *   - Total point count: 40 lat × 32 lon × ~0.7 (polygon fill
 *     ratio) ≈ 900 features. Well within the heatmap's budget.
 *
 * The hand-authored control grid is the *same shape* as before
 * (a lat-increasing gradient with mild east-increasing structure),
 * but the polygon mask + jitter clip it to the Antarctic
 * Peninsula shape with organic, non-grid-aligned point positions.
 * When the real NSIDC raster arrives, the same polygon-mask
 * preprocessor will run server-side before GeoJSON emission; the
 * jitter step is moot in the real-data path (the raster is dense
 * enough that jitter is unnecessary).
 */

/* Antarctic Peninsula corridor — quadrilateral, lon-decreasing
 * (peninsula on the west). Polygon's western edge is the diagonal
 * from (-64, -60) (northern tip of peninsula) to (-66, -70) (the
 * peninsula's southern coast at the corridor's SW corner). The
 * eastern edge is the open-ocean side at lon = -58.
 *
 *   NW (-64, -60)            NE (-58, -60)
 *        *-------------------------*
 *        |                       / |
 *        |                     /   |
 *        |                   /     |
 *        |                 /       |
 *        |               /         |
 *        |             /           |
 *        *-------------------------*
 *   SW (-66, -70)            SE (-58, -70)
 */
const POLY_NW_LON = -64;
const POLY_NW_LAT = -60;
const POLY_NE_LON = -58;
const POLY_SE_LAT = -70;
const POLY_SW_LON = -66;
const POLY_LAT_MIN = -70; // south
const POLY_LAT_MAX = -60; // north
const POLY_LON_MAX = -58; // east

/** Western boundary of the polygon at a given latitude. Linear
 *  interpolation between NW and SW corners. */
function westLonAt(lat: number): number {
  // At lat=-60, west=-64. At lat=-70, west=-66. Slope: -0.2 per degree.
  const t = (lat - POLY_LAT_MAX) / (POLY_LAT_MIN - POLY_LAT_MAX); // 0 at north, 1 at south
  return POLY_NW_LON + (POLY_SW_LON - POLY_NW_LON) * t;
}

/** True if (lon, lat) is inside the corridor polygon. The polygon
 *  is bounded on the west by the peninsula diagonal, on the east
 *  by the open-ocean line, and on the north/south by the lat range. */
function insideCorridor(lon: number, lat: number): boolean {
  if (lat > POLY_LAT_MAX || lat < POLY_LAT_MIN) return false;
  if (lon > POLY_LON_MAX) return false;
  if (lon < westLonAt(lat)) return false;
  return true;
}

/** Bilinear concentration field over the corridor. Uses a 1° control
 *  grid for the gradient shape, then masks the result to 0 outside
 *  the polygon. The control grid is the same lat-increasing /
 *  lon-increasing pattern the layer has had since the placeholder
 *  was first introduced; this is the documented reference behavior
 *  for swapping in real NSIDC data later.
 *
 *  Exported so the A* router (lib/routing/a-star-router.ts) can
 *  sample the same field for its cost function. Reusing the
 *  bilinear sampler here means the route's risk surface and the
 *  sea-ice layer's heatmap will always agree — there's no risk of
 *  the router using a slightly different control grid than the
 *  visualization. */
const SEA_ICE_CORNERS: ReadonlyArray<ReadonlyArray<number>> = [
  // lon   -66    -65    -64    -63    -62    -61    -60    -59    -58
  /* -70 */ [0.80, 0.88, 0.92, 0.94, 0.95, 0.96, 0.97, 0.97, 0.98],
  /* -68 */ [0.60, 0.75, 0.85, 0.90, 0.92, 0.94, 0.95, 0.96, 0.97],
  /* -66 */ [0.40, 0.55, 0.70, 0.80, 0.85, 0.90, 0.92, 0.94, 0.95],
  /* -64 */ [0.20, 0.35, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90],
  /* -62 */ [0.10, 0.20, 0.30, 0.40, 0.50, 0.55, 0.60, 0.65, 0.70],
  /* -60 */ [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45],
];
const SEA_ICE_LON_AXIS = [-66, -65, -64, -63, -62, -61, -60, -59, -58];
const SEA_ICE_LAT_AXIS = [-70, -68, -66, -64, -62, -60]; // south-to-north
const SEA_ICE_STEP = 0.25; // output resolution (degrees) — finer than
                           // before so the heatmap reads as a
                           // continuous field, not row-banding.

/** Bilinear interpolation over a 1°-spaced regular grid, clamped
 *  outside the grid to the nearest corner. Exported for reuse by
 *  the A* router's cost function (see lib/routing/a-star-router.ts). */
export function sampleConcentration(lon: number, lat: number): number {
  const lonIdx = bracket(SEA_ICE_LON_AXIS, lon);
  const latIdx = bracket(SEA_ICE_LAT_AXIS, lat);
  const lon0 = SEA_ICE_LON_AXIS[lonIdx];
  const lon1 = SEA_ICE_LON_AXIS[lonIdx + 1];
  const lat0 = SEA_ICE_LAT_AXIS[latIdx];
  const lat1 = SEA_ICE_LAT_AXIS[latIdx + 1];

  // CORNERS is south-to-north: latIdx is the southern row,
  // latIdx + 1 is the northern row.
  const vSouthWest = SEA_ICE_CORNERS[latIdx][lonIdx];
  const vSouthEast = SEA_ICE_CORNERS[latIdx][lonIdx + 1];
  const vNorthWest = SEA_ICE_CORNERS[latIdx + 1][lonIdx];
  const vNorthEast = SEA_ICE_CORNERS[latIdx + 1][lonIdx + 1];

  const tx = lon1 === lon0 ? 0 : (lon - lon0) / (lon1 - lon0);
  const ty = lat1 === lat0 ? 0 : (lat - lat0) / (lat1 - lat0);

  const south = vSouthWest + (vSouthEast - vSouthWest) * tx;
  const north = vNorthWest + (vNorthEast - vNorthWest) * tx;
  return clamp01(south + (north - south) * ty);
}

function bracket(axis: ReadonlyArray<number>, v: number): number {
  if (v <= axis[0]) return 0;
  if (v >= axis[axis.length - 1]) return axis.length - 2;
  for (let i = 0; i < axis.length - 1; i++) {
    if (v >= axis[i] && v <= axis[i + 1]) return i;
  }
  return axis.length - 2;
}

function clamp01(n: number): number {
  if (n < 0) return 0;
  if (n > 1) return 1;
  return n;
}

function buildSeaIce(): FeatureCollection<Point, SeaIceFeatureProps> {
  const features: SeaIceFeature[] = [];
  let id = 0;
  // Sweep a STRIDED jittered grid over the corridor polygon's
  // bounding box, but only emit a point if (lon, lat) lands inside
  // the polygon. The jitter (random offset up to half the grid step
  // in each axis) is the key step: a perfectly regular grid shows
  // up in the heatmap as a faint row/column pattern no matter how
  // big the radius, because every point falls on the same lat-line
  // and same lon-line. With jitter, points are scattered around the
  // polygon's interior, and the heatmap's gaussian falloff blurs
  // them into a single organic field.
  //
  // Two layers of filtering keep the field shape organic rather
  // than reading as a rigid rectangle:
  //
  //   1. Polygon membership: points outside the corridor polygon
  //      are dropped. The polygon's western edge follows the
  //      Antarctic Peninsula diagonal (not a straight vertical
  //      line), so the visible "left" boundary curves with the
  //      peninsula.
  //
  //   2. EDGE_FADE_DEG margin: points within EDGE_FADE_DEG of the
  //      polygon boundary have their concentration multiplied by a
  //      smooth 0..1 fadeout (cosine, raised to the 1.5 power for a
  //      softer falloff). This means a heatmap that uses these
  //      values as weights will have a soft gradient at the
  //      polygon's edges — not a hard rectangle. At z3.6, 0.6°
  //      ≈ 67px ≈ 2× the 30px heatmap radius, so the gaussian
  //      falloff reads as a smooth boundary rather than a sharp
  //      polygon edge.
  const lonMinBox = POLY_SW_LON;
  const lonMaxBox = POLY_LON_MAX;
  const latMinBox = POLY_LAT_MIN;
  const latMaxBox = POLY_LAT_MAX;
  // Use a deterministic PRNG (mulberry32 seeded from a constant) so
  // the jitter pattern is stable across HMR / page reloads — a
  // re-render should produce the same points, not a different
  // "organic" pattern each time.
  const rand = mulberry32(0xcea1ce5);
  const jitterRange = SEA_ICE_STEP * 0.55; // ±0.55 × step ≈ ±0.14° at 0.25° step
  for (let lat = latMinBox; lat <= latMaxBox + 1e-9; lat += SEA_ICE_STEP) {
    for (let lon = lonMinBox; lon <= lonMaxBox + 1e-9; lon += SEA_ICE_STEP) {
      // Jitter each point within half a step in each axis. This
      // breaks the regular grid pattern while keeping points
      // inside their cell's neighborhood.
      const jLat = lat + (rand() * 2 - 1) * jitterRange;
      const jLon = lon + (rand() * 2 - 1) * jitterRange;
      if (!insideCorridor(jLon, jLat)) continue;
      const rawConcentration = sampleConcentration(jLon, jLat);
      // Apply the edge-fade so the heatmap's gaussian falloff at
      // the polygon boundary reads as a soft gradient instead of a
      // hard edge. If the point is well inside the corridor, this
      // is 1.0 (no effect).
      const edgeFade = edgeFadeFactor(jLon, jLat);
      const concentration = rawConcentration * edgeFade;
      // Drop points whose concentration is effectively zero (would
      // not contribute to the heatmap). This prevents the heatmap
      // from rendering a faint halo at the polygon's edge that
      // would read as a rectangular outline.
      if (concentration < 0.02) continue;
      features.push({
        type: "Feature",
        id: id++,
        geometry: { type: "Point", coordinates: [round2(jLon), round2(jLat)] },
        properties: { concentration: round3(concentration) },
      });
    }
  }
  return { type: "FeatureCollection", features };
}

/** Width of the edge-fade band, in degrees. Inside this distance
 *  from the polygon boundary, the concentration is multiplied by a
 *  smooth fadeout so the heatmap's outer gaussian ring has a soft
 *  falloff rather than a hard cut. Beyond this distance, the
 *  fadeout is 1.0 (no effect). */
const EDGE_FADE_DEG = 0.6;

/** Smooth cosine-based fadeout based on the point's distance to the
 *  nearest polygon edge. Returns 1.0 deep inside the corridor and
 *  0.0 at the boundary. Exponent of 1.5 gives a softer drop near
 *  the edge than a pure cosine, so the heatmap's outer halo is a
 *  smooth gradient rather than a sharp cutoff. */
function edgeFadeFactor(lon: number, lat: number): number {
  const distToWest = lon - westLonAt(lat);
  const distToEast = POLY_LON_MAX - lon;
  const distToNorth = lat - POLY_LAT_MAX;
  const distToSouth = POLY_LAT_MIN - lat;
  const minDist = Math.min(distToWest, distToEast, distToNorth, distToSouth);
  if (minDist >= EDGE_FADE_DEG) return 1.0;
  if (minDist <= 0) return 0.0;
  // Cosine taper: 1.0 at the interior (d = EDGE_FADE_DEG), 0.0 at
  // the boundary (d = 0), with a smooth bell shape in between.
  const t = minDist / EDGE_FADE_DEG; // 0 at edge, 1 at interior
  const taper = 0.5 - 0.5 * Math.cos(Math.PI * t);
  return Math.pow(taper, 1.5);
}

/** Mulberry32 — small, fast, deterministic PRNG. Seeded with a
 *  constant so the jitter pattern is stable across reloads. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
function round3(n: number): number {
  return Math.round(n * 1000) / 1000;
}

/* ------------------------------------------------------------------
 * Iceberg detections
 * ------------------------------------------------------------------
 * A handful of representative detection points scattered along the
 * same corridor. Sizes and confidences are illustrative.
 */
const ICEBERG_ROWS: ReadonlyArray<Omit<IcebergFeature, "type">> = [
  { id: "ice-001", geometry: { type: "Point", coordinates: [-63.4, -61.8] }, properties: { id: "ice-001", sizeM: 120, confidence: 0.82, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-002", geometry: { type: "Point", coordinates: [-62.1, -62.3] }, properties: { id: "ice-002", sizeM: 240, confidence: 0.91, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-003", geometry: { type: "Point", coordinates: [-61.0, -63.1] }, properties: { id: "ice-003", sizeM: 60,  confidence: 0.55, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-004", geometry: { type: "Point", coordinates: [-60.2, -64.0] }, properties: { id: "ice-004", sizeM: 380, confidence: 0.95, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-005", geometry: { type: "Point", coordinates: [-59.4, -65.0] }, properties: { id: "ice-005", sizeM: 95,  confidence: 0.70, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-006", geometry: { type: "Point", coordinates: [-58.7, -66.2] }, properties: { id: "ice-006", sizeM: 510, confidence: 0.97, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-007", geometry: { type: "Point", coordinates: [-59.9, -67.4] }, properties: { id: "ice-007", sizeM: 30,  confidence: 0.48, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-008", geometry: { type: "Point", coordinates: [-61.2, -68.1] }, properties: { id: "ice-008", sizeM: 200, confidence: 0.88, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-009", geometry: { type: "Point", coordinates: [-60.0, -69.0] }, properties: { id: "ice-009", sizeM: 150, confidence: 0.80, detectedAt: "2026-09-01T08:14:00Z" } },
  { id: "ice-010", geometry: { type: "Point", coordinates: [-58.9, -70.0] }, properties: { id: "ice-010", sizeM: 90,  confidence: 0.65, detectedAt: "2026-09-01T08:14:00Z" } },
];

function buildIcebergs(): FeatureCollection<Point, IcebergFeatureProps> {
  return {
    type: "FeatureCollection",
    features: ICEBERG_ROWS.map((f) => ({ ...f, type: "Feature" })) as IcebergFeature[],
  };
}

/** Scenario metadata. Used by the dashboard header / scenario picker later. */
export const SCENARIO = {
  id: "drake-to-ross",
  name: "Drake Passage → Ross Sea",
  // Centroid of the corridor (lon, lat) and zoom chosen to frame the
  // corridor with a small margin at typical viewport sizes. Must stay
  // in sync with MapAdapter's DEFAULT_CENTER/DEFAULT_ZOOM.
  center: [-62, -65] as [number, number],
  zoom: 3.6,
  description:
    "Reference corridor from the tip of South America across the Drake Passage and into the Ross Sea. Used for sea-ice and iceberg layer smoke-testing.",
} as const;

export const SEA_ICE_GEOJSON: FeatureCollection<Point, SeaIceFeatureProps> = buildSeaIce();
export const ICEBERG_GEOJSON: FeatureCollection<Point, IcebergFeatureProps> = buildIcebergs();
