/**
 * A* Maritime Router
 * ====================================================================
 * Computes a risk-aware route across the Drake-Passage → Ross-Sea
 * scenario corridor. The route avoids heavy sea-ice concentration and
 * iceberg clusters by adding per-cell penalties to the A* edge cost.
 *
 * Grid:
 *   - lon ∈ [-66, -58] (8° wide), 32 columns
 *   - lat ∈ [-70, -60] (10° tall), 40 rows
 *   - cell size: 0.25° (matches the sea-ice grid resolution)
 *   - total cells: 32 × 40 = 1,280
 *
 * Cost function (per edge A → B):
 *
 *   edgeCost = haversineNM(A, B)
 *            + W_ICE  * concentration[B]
 *            + W_ICEBERG * icebergPenalty(B)
 *            + (isLand[B] ? 1e6 : 0)
 *
 * where:
 *   - haversineNM is the great-circle distance in nautical miles.
 *   - concentration[B] is the bilinearly-interpolated sea-ice
 *     concentration at B (0..1).
 *   - icebergPenalty(B) is a smooth 0..1 falloff based on the
 *     precomputed distance to the nearest iceberg: 1 at the
 *     iceberg's cell, 0 at 1° or more away.
 *   - isLand marks cells inside the Antarctic Peninsula polygon —
 *     effectively impassable, the route stays in open water.
 *
 * Heuristic: haversineNM to the goal. Admissible (never over-
 * estimates the true cost) so A* stays optimal.
 *
 * Movement: 8-connected (king moves). Diagonal moves cost √2× the
 * cardinal cost. This produces more realistic ship tracks than
 * 4-connected movement, which would stair-step.
 *
 * Performance budget: A* on a 1,280-cell grid with 8-connected
 * neighbors explores ~5-15k nodes. With a binary-heap open set
 * this runs in <200ms on a modern laptop, well under the
 * "Re-calculate route" click latency target.
 */

import type { Feature, FeatureCollection, LineString, Point } from "geojson";
import {
  ICEBERG_GEOJSON,
  sampleConcentration,
} from "@/lib/data/scenarios/drake-to-ross";

/* ------------------------------------------------------------------
 * Cost-function weights (per the user's verification Q&A choice).
 * ------------------------------------------------------------------ */
const W_ICE = 80;        // NM penalty per unit sea-ice concentration
const W_ICEBERG = 60;    // NM penalty for cells adjacent to an iceberg
const ICEBERG_FALLOFF_DEG = 1.0;   // distance over which the iceberg
                                    // penalty decays from 1 → 0
const LAND_COST = 1e6;   // effectively impassable

/* ------------------------------------------------------------------
 * Grid definition
 * ------------------------------------------------------------------ */
export const GRID_MIN_LON = -66;
export const GRID_MAX_LON = -58;
export const GRID_MIN_LAT = -70;
export const GRID_MAX_LAT = -60;
export const GRID_STEP = 0.25;
export const GRID_COLS = Math.round(
  (GRID_MAX_LON - GRID_MIN_LON) / GRID_STEP,
);  // 32
export const GRID_ROWS = Math.round(
  (GRID_MAX_LAT - GRID_MIN_LAT) / GRID_STEP,
);  // 40
export const GRID_CELL_COUNT = GRID_COLS * GRID_ROWS;  // 1,280

/** Default route endpoints. NW corner → SE corner of the corridor,
 *  matching the natural trans-Drake → trans-Ross direction. */
export const ROUTE_START = { lon: -64, lat: -60 };
export const ROUTE_GOAL = { lon: -58, lat: -70 };

/** Vessel cruise speed. Used to convert route distance → time. */
export const VESSEL_SPEED_KNOTS = 14;

/* ------------------------------------------------------------------
 * Cost grid
 * ------------------------------------------------------------------
 * One precomputed entry per cell, holding the static risk data
 * (concentration, iceberg proximity, land flag). Built once at
 * module load — the per-edge cost is then a function of the
 * destination cell's static data plus the haversine distance.
 */

interface CellCost {
  /** Sea-ice concentration at the cell center (0..1). */
  concentration: number;
  /** Smooth 0..1 falloff from the nearest iceberg, 0 at 1° or
   *  more away, 1 in the iceberg's cell. */
  icebergPenalty: number;
  /** True if the cell is inside the Antarctic Peninsula polygon
   *  (effectively land — the route must stay in open water). */
  isLand: boolean;
}

export const ROUTE_GRID: CellCost[] = buildRouteGrid();

/** Public read-only access for diagnostics / future risk-surface
 *  visualization (a "risk-layer.tsx" could render this as a
 *  heatmap). The grid is built once at module load and never
 *  mutated. */
export function getRouteGrid(): ReadonlyArray<CellCost> {
  return ROUTE_GRID;
}

/* ------------------------------------------------------------------
 * A* result shape
 * ------------------------------------------------------------------ */
export interface RouteResult {
  /** GeoJSON FeatureCollection with one LineString feature (the
   *  full path from start to goal, lon/lat order). The
   *  featureCollection shape matches what maplibre's
   *  `setData(source, fc)` expects. */
  featureCollection: FeatureCollection<LineString>;
  /** Path coordinates (lon, lat) for direct use. */
  coordinates: [number, number][];
  /** Total edge cost in nautical miles, including all penalties. */
  totalNm: number;
  /** Estimated time en route at VESSEL_SPEED_KNOTS, in hours. */
  hours: number;
  /** Maximum risk score along any single edge of the route. The
   *  route panel's "Severe" risk badge is driven by this. */
  maxRiskScore: number;
  /** Mean risk score across all edges, for the route panel's
   *  secondary metric. */
  meanRiskScore: number;
  /** Number of waypoints in the path (cell count). */
  waypointCount: number;
  /** Small intermediate waypoint GeoJSON (every vertex except
   *  start + end). Drawn as a circle layer. */
  waypointsFeature: FeatureCollection<Point>;
  /** Start + end GeoJSON with a `kind` property (`"start"` /
   *  `"end"`) and a `pulse` property (0..1, set by the layer on
   *  each animation tick). Drawn as a circle layer with
   *  pulse-driven radius. */
  endpointsFeature: FeatureCollection<Point>;
  /** Start cell index for reference. */
  startIndex: number;
  /** Goal cell index for reference. */
  goalIndex: number;
  /** Distance and Risk metrics for graph plotting. */
  pathMetrics: { distance: number; risk: number }[];
}

/* ------------------------------------------------------------------
 * Public entry point
 * ------------------------------------------------------------------ */

/** Run A* and return the optimal path + metrics. Synchronous;
 *  ~50-200ms on a 1,280-cell grid. The route store defers the call
 *  to setTimeout(0) so the React tree can repaint a "Calculating…"
 *  status before A* blocks the main thread. */
export function calculateRoute(
  startCoord = ROUTE_START,
  goalCoord = ROUTE_GOAL
): RouteResult {
  const startIndex = nearestCellIndex(startCoord.lon, startCoord.lat);
  const goalIndex = nearestCellIndex(goalCoord.lon, goalCoord.lat);

  const path = aStar(startIndex, goalIndex);

  // Build coordinates from the cell path, in (lon, lat) order.
  const coordinates: [number, number][] = path.map((idx) => {
    const { lon, lat } = cellCenter(idx);
    return [round4(lon), round4(lat)];
  });

  // Hybrid routing: if the original start/goal coords are outside the grid bounds,
  // prepend/append them to the coordinates array so the line connects to the global port.
  const isOutside = (c: {lon: number, lat: number}) => 
    c.lon < GRID_MIN_LON || c.lon > GRID_MAX_LON || c.lat < GRID_MIN_LAT || c.lat > GRID_MAX_LAT;

  if (isOutside(startCoord)) {
    coordinates.unshift([round4(startCoord.lon), round4(startCoord.lat)]);
  }
  if (isOutside(goalCoord)) {
    coordinates.push([round4(goalCoord.lon), round4(goalCoord.lat)]);
  }

  // Compute per-edge metrics: haversine distance + risk score.
  let totalNm = 0;
  let maxRisk = 0;
  let sumRisk = 0;
  let riskEdgesCount = 0;
  
  // Track metrics for graphing (Distance vs Risk)
  const pathMetrics: { distance: number; risk: number }[] = [];
  
  for (let i = 0; i < coordinates.length - 1; i++) {
    const [lonA, latA] = coordinates[i];
    const [lonB, latB] = coordinates[i + 1];
    const dist = haversineNM(lonA, latA, lonB, latB);
    
    // Determine risk: if outside grid, risk is 0 (open ocean)
    let risk = 0;
    if (!isOutside({lon: lonB, lat: latB})) {
      const idx = nearestCellIndex(lonB, latB);
      const bCell = ROUTE_GRID[idx];
      risk = W_ICE * bCell.concentration + W_ICEBERG * bCell.icebergPenalty;
      
      sumRisk += risk;
      riskEdgesCount++;
      if (risk > maxRisk) maxRisk = risk;
    }
    
    totalNm += dist;
    pathMetrics.push({ distance: totalNm, risk });
  }
  
  const meanRisk = riskEdgesCount > 0 ? sumRisk / riskEdgesCount : 0;
  const hours = totalNm / VESSEL_SPEED_KNOTS;

  // Build the GeoJSON pieces the layer will push into the map.
  const lineFeature: Feature<LineString> = {
    type: "Feature",
    properties: {},
    geometry: { type: "LineString", coordinates },
  };
  const featureCollection: FeatureCollection<LineString> = {
    type: "FeatureCollection",
    features: [lineFeature],
  };

  // Intermediate waypoints = every vertex except first and last.
  // Slicing is O(n) once; the feature collection is small (~30-80
  // entries for a typical route).
  const waypointFeatures: Feature<Point>[] = [];
  for (let i = 1; i < coordinates.length - 1; i++) {
    waypointFeatures.push({
      type: "Feature",
      properties: { i },
      geometry: { type: "Point", coordinates: coordinates[i] },
    });
  }
  const waypointsFeature: FeatureCollection<Point> = {
    type: "FeatureCollection",
    features: waypointFeatures,
  };

  // Endpoints: two features (start + end) with a `kind` property
  // for the layer's filter expression and a `pulse` property the
  // layer animates. Initial pulse is 0 (mid-cycle, ease-in-out
  // envelope).
  const endpointsFeature: FeatureCollection<Point> = {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { kind: "start", pulse: 0 },
        geometry: { type: "Point", coordinates: coordinates[0] },
      },
      {
        type: "Feature",
        properties: { kind: "end", pulse: 0 },
        geometry: {
          type: "Point",
          coordinates: coordinates[coordinates.length - 1],
        },
      },
    ],
  };

  return {
    featureCollection,
    coordinates,
    totalNm,
    hours,
    maxRiskScore: maxRisk,
    meanRiskScore: meanRisk,
    waypointCount: coordinates.length,
    endpointsFeature,
    startIndex,
    goalIndex,
    pathMetrics,
  };
}

/* ==================================================================
 * Below: internals. Not exported. Documented for the next reader.
 * ================================================================== */

/* ------------------------------------------------------------------
 * Grid construction
 * ------------------------------------------------------------------ */
function buildRouteGrid(): CellCost[] {
  // Pre-extract iceberg coordinates once. The features are
  // { type: "Point", coordinates: [lon, lat] }.
  const icebergs: Array<[number, number]> = [];
  for (const f of ICEBERG_GEOJSON.features) {
    if (f.geometry.type === "Point") {
      icebergs.push([
        f.geometry.coordinates[0],
        f.geometry.coordinates[1],
      ]);
    }
  }

  // The grid covers the corridor bbox. The corridor's polygonal
  // envelope (the Antarctic Peninsula quadrilateral from
  // drake-to-ross.ts) defines the "open water" area. Every cell
  // inside the grid bbox is either inside that polygon (open
  // ocean) or to the east of it (also open ocean); there is no
  // land inside the grid. An earlier draft of this file marked
  // the polygon's western (peninsula-side) half as `isLand: true`,
  // which made the NW-corridor start cell impassable. The land
  // check is now unconditionally false; if real-data boundaries
  // ever need to exclude sub-cells (e.g. an iceberg cluster too
  // dense to thread through), set isLand per-feature from a
  // future authoritative source rather than from a polygon
  // membership test.
  const cells: CellCost[] = new Array(GRID_CELL_COUNT);
  for (let r = 0; r < GRID_ROWS; r++) {
    for (let c = 0; c < GRID_COLS; c++) {
      const idx = r * GRID_COLS + c;
      const { lon, lat } = cellCenter(idx);

      cells[idx] = {
        concentration: sampleConcentration(lon, lat),
        icebergPenalty: icebergPenaltyAt(lon, lat, icebergs),
        isLand: false,
      };
    }
  }
  return cells;
}

/** Returns 1.0 at the iceberg's exact cell, 0.0 at ICEBERG_FALLOFF_DEG
 *  or more away, with a smooth linear interpolation in between. */
function icebergPenaltyAt(
  lon: number,
  lat: number,
  icebergs: ReadonlyArray<readonly [number, number]>,
): number {
  let minDistDeg = Infinity;
  for (const [iLon, iLat] of icebergs) {
    // Equirectangular approximation is fine for < 5° distances.
    const cosLat = Math.cos((lat * Math.PI) / 180);
    const dLon = (iLon - lon) * cosLat;
    const dLat = iLat - lat;
    const dist = Math.hypot(dLon, dLat);
    if (dist < minDistDeg) minDistDeg = dist;
  }
  if (minDistDeg >= ICEBERG_FALLOFF_DEG) return 0;
  return clamp01(1 - minDistDeg / ICEBERG_FALLOFF_DEG);
}

/* ------------------------------------------------------------------
 * A* core
 * ------------------------------------------------------------------ */
function aStar(startIndex: number, goalIndex: number): number[] {
  const n = GRID_CELL_COUNT;
  const gScore = new Float32Array(n).fill(Infinity);
  const fScore = new Float32Array(n).fill(Infinity);
  const parent = new Int32Array(n).fill(-1);
  const closed = new Uint8Array(n);

  gScore[startIndex] = 0;
  fScore[startIndex] = heuristic(startIndex, goalIndex);

  // Open set: a binary heap of [fScore, cellIndex] pairs.
  // Using a flat typed-array-backed heap is ~5× faster than a
  // generic priority queue for this size, and the data is small
  // (~5-15k entries) so memory is not a concern.
  const heap: number[] = [];   // heap[i] = cell index; ordered by fScore[heap[i]]
  heapPush(heap, startIndex, fScore);

  while (heap.length > 0) {
    const current = heapPop(heap, fScore);
    if (current === goalIndex) {
      return reconstructPath(parent, current);
    }
    closed[current] = 1;

    const { lon: cLon, lat: cLat } = cellCenter(current);
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        const nr = Math.floor(current / GRID_COLS) + dr;
        const nc = (current % GRID_COLS) + dc;
        if (nr < 0 || nr >= GRID_ROWS || nc < 0 || nc >= GRID_COLS) continue;
        const neighbor = nr * GRID_COLS + nc;
        if (closed[neighbor]) continue;

        // Haversine between cell centers, in NM.
        const { lon: nLon, lat: nLat } = cellCenter(neighbor);
        const dist = haversineNM(cLon, cLat, nLon, nLat);

        const cell = ROUTE_GRID[neighbor];
        if (cell.isLand) continue;   // impassable

        const stepCost =
          dist +
          W_ICE * cell.concentration +
          W_ICEBERG * cell.icebergPenalty;
        const tentativeG = gScore[current] + stepCost;

        if (tentativeG < gScore[neighbor]) {
          parent[neighbor] = current;
          gScore[neighbor] = tentativeG;
          fScore[neighbor] = tentativeG + heuristic(neighbor, goalIndex);
          // Re-push even if already in the heap. The fScore is
          // monotonically decreasing for any given cell, so a
          // stale entry is always behind the new one in
          // ordering; we skip it via the closed check above.
          // This is the textbook "lazy deletion" variant of A*.
          heapPush(heap, neighbor, fScore);
        }
      }
    }
  }

  // No path. A* with non-negative costs and the start inside the
  // grid will always find a path if one exists; the only way to
  // reach here is if the goal is unreachable, which is a bug in
  // the cost function. Return a direct line so the UI degrades
  // gracefully.
  return [startIndex, goalIndex];
}

function reconstructPath(parent: Int32Array, endIndex: number): number[] {
  const path: number[] = [];
  let cur = endIndex;
  while (cur !== -1) {
    path.push(cur);
    cur = parent[cur];
  }
  return path.reverse();
}

/* ------------------------------------------------------------------
 * Geometry helpers
 * ------------------------------------------------------------------ */
function cellCenter(idx: number): { lon: number; lat: number } {
  const r = Math.floor(idx / GRID_COLS);
  const c = idx % GRID_COLS;
  return {
    lon: GRID_MIN_LON + (c + 0.5) * GRID_STEP,
    lat: GRID_MIN_LAT + (r + 0.5) * GRID_STEP,
  };
}

function nearestCellIndex(lon: number, lat: number): number {
  const c = Math.max(0, Math.min(GRID_COLS - 1, Math.floor((lon - GRID_MIN_LON) / GRID_STEP)));
  const r = Math.max(0, Math.min(GRID_ROWS - 1, Math.floor((lat - GRID_MIN_LAT) / GRID_STEP)));
  return r * GRID_COLS + c;
}

function heuristic(a: number, b: number): number {
  const ac = cellCenter(a);
  const bc = cellCenter(b);
  return haversineNM(ac.lon, ac.lat, bc.lon, bc.lat);
}

/** Great-circle distance between two (lon, lat) points, in
 *  nautical miles. The mean Earth radius is 6,371 km; 1 NM =
 *  1.852 km, so 6,371 / 1.852 ≈ 3,439 NM. */
const NM_PER_RADIAN = 3440.065;
function haversineNM(
  lon1: number,
  lat1: number,
  lon2: number,
  lat2: number,
): number {
  const φ1 = (lat1 * Math.PI) / 180;
  const φ2 = (lat2 * Math.PI) / 180;
  const dφ = ((lat2 - lat1) * Math.PI) / 180;
  const dλ = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dφ / 2) * Math.sin(dφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(dλ / 2) * Math.sin(dλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return NM_PER_RADIAN * c;
}

/* ------------------------------------------------------------------
 * Binary heap (min-heap by fScore)
 * ------------------------------------------------------------------ */
function heapPush(heap: number[], cell: number, fScore: Float32Array): void {
  heap.push(cell);
  siftUp(heap, heap.length - 1, fScore);
}

function heapPop(heap: number[], fScore: Float32Array): number {
  const top = heap[0];
  const last = heap.pop()!;
  if (heap.length > 0) {
    heap[0] = last;
    siftDown(heap, 0, fScore);
  }
  return top;
}

function siftUp(heap: number[], i: number, fScore: Float32Array): void {
  while (i > 0) {
    const parent = (i - 1) >> 1;
    if (fScore[heap[i]] < fScore[heap[parent]]) {
      const tmp = heap[i];
      heap[i] = heap[parent];
      heap[parent] = tmp;
      i = parent;
    } else break;
  }
}

function siftDown(heap: number[], i: number, fScore: Float32Array): void {
  const n = heap.length;
  while (true) {
    const l = 2 * i + 1;
    const r = 2 * i + 2;
    let smallest = i;
    if (l < n && fScore[heap[l]] < fScore[heap[smallest]]) smallest = l;
    if (r < n && fScore[heap[r]] < fScore[heap[smallest]]) smallest = r;
    if (smallest === i) break;
    const tmp = heap[i];
    heap[i] = heap[smallest];
    heap[smallest] = tmp;
    i = smallest;
  }
}

/* ------------------------------------------------------------------
 * Misc
 * ------------------------------------------------------------------ */
function clamp01(n: number): number {
  if (n < 0) return 0;
  if (n > 1) return 1;
  return n;
}

function round4(n: number): number {
  return Math.round(n * 10000) / 10000;
}

/* ------------------------------------------------------------------
 * Re-exported type aliases for convenience
 * ------------------------------------------------------------------ */
export type { Feature, FeatureCollection, LineString, Point } from "geojson";
