"use client";

/**
 * RouteLayer
 * ----------
 * Renders the planned route produced by `useRouteStore` as four
 * maplibre sublayers:
 *
 *   - LAYER_LINE_GLOW:  a soft, wide, low-opacity line that sits
 *                       below the main line as a bloom halo.
 *   - LAYER_LINE:       the main cyan polyline.
 *   - LAYER_WAYPOINTS:  small intermediate waypoint dots along
 *                       the polyline (excludes start + end).
 *   - LAYER_ENDPOINTS:  pulsing cyan circles at start + end.
 *
 * Conventions (per the layer pattern from iceberg-layer.tsx and
 * ocean-current-layer.tsx):
 *   - 'use client', takes { adapter: MapAdapter }, renders null.
 *   - SOURCE / LAYER_* exports are the source + layer ids every
 *     other module references.
 *   - Source + layer registration happens exactly once inside
 *     one useEffect → adapter.onLoad(...).
 *   - Visibility / opacity sync follow the iceberg-layer pattern
 *     (a single useEffect per axis; setLayerVisibility and
 *     setLayerOpacity cover all four sublayers).
 *   - Layer components never import maplibre-gl directly except
 *     for type-only imports. The route layer's runtime uses
 *     only the adapter's API.
 *
 * Why a separate panel file?
 *   The route panel (route-panel.tsx) reads from useRouteStore
 *   too. Co-locating the panel render with the layer would
 *   couple the two files; keeping them separate lets future
 *   refactors extract the panel without touching the layer's
 *   maplibre wiring.
 *
 * Endpoint pulse animation:
 *   Maplibre paint expressions don't have a built-in time
 *   variable for `circle-radius`. We drive the pulse by
 *   re-uploading the source data once per ~250ms with a fresh
 *   `pulse` property (0..1) per feature, and the layer's
 *   `circle-radius` expression reads from it:
 *     radius = 6 + 4 * pulse
 *   This is the standard "pulsing dot" pattern for maplibre.
 *   The two features (start + end) pulse in phase; the
 *   underlying sine produces a smooth ease-in-out envelope.
 */

import { useEffect, useRef } from "react";
import type {
  FeatureCollection,
  LineString,
  Point,
} from "geojson";
import { MapAdapter } from "@/components/map/map-adapter";
import { useLayerStore } from "@/stores/use-layer-store";
import { useRouteStore } from "@/stores/use-route-store";
import { RoutePanel } from "@/components/map/route-panel";

/* ------------------------------------------------------------------
 * Layer + source ids (exported for tests, future debug tools, and
 * the map-legend / future refactors).
 * ------------------------------------------------------------------ */
export const SOURCE = "route-source";
export const SOURCE_WAYPOINTS = "route-waypoints-source";
export const SOURCE_ENDPOINTS = "route-endpoints-source";

export const LAYER_LINE = "route-line";
export const LAYER_LINE_GLOW = "route-line-glow";
export const LAYER_WAYPOINTS = "route-waypoints";
export const LAYER_ENDPOINTS = "route-endpoints";

/* ------------------------------------------------------------------
 * Color constants
 * ------------------------------------------------------------------
 * Maplibre paint expressions expect literal CSS values, not
 * `var()` references. The `--accent-route` CSS variable is for
 * the panel; the maplibre side hard-codes the equivalent hex.
 * Keep these in sync if either is changed in tokens.css.
 */
const ROUTE_COLOR = "#22d3ee";   // matches --color-cyan
const ROUTE_COLOR_GLOW = "rgba(34, 211, 238, 0.35)";  // 35% alpha

/* ------------------------------------------------------------------
 * Empty initial feature collections
 * ------------------------------------------------------------------
 * The sources need a real FeatureCollection (not null) at
 * registration time, otherwise maplibre logs a warning on the
 * first `setData` call. We seed with empty ones and let the
 * useEffect below push the real data once A* completes.
 */
const EMPTY_LINE: FeatureCollection<LineString> = {
  type: "FeatureCollection",
  features: [],
};
const EMPTY_POINTS: FeatureCollection<Point> = {
  type: "FeatureCollection",
  features: [],
};

/* ------------------------------------------------------------------
 * Component
 * ------------------------------------------------------------------ */
interface Props {
  adapter: MapAdapter;
}

export function RouteLayer({ adapter }: Props) {
  const enabled = useLayerStore((s) => s.layers.route.enabled);
  const opacity = useLayerStore((s) => s.layers.route.opacity);
  const status = useRouteStore((s) => s.status);
  const result = useRouteStore((s) => s.result);

  // Latest data + a ref to it for the pulse ticker. The ref
  // exists so the setInterval callback always sees the current
  // result without needing to be in the effect's deps (which
  // would restart the interval on every result).
  const resultRef = useRef(result);
  resultRef.current = result;

  // Source + layer registration, exactly once.
  useEffect(() => {
    adapter.onLoad(() => {
      // Three sources, four layers.
      adapter.addSource(SOURCE, { type: "geojson", data: EMPTY_LINE });
      adapter.addSource(SOURCE_WAYPOINTS, { type: "geojson", data: EMPTY_POINTS });
      adapter.addSource(SOURCE_ENDPOINTS, { type: "geojson", data: EMPTY_POINTS });

      // Glow halo. Wider + dimmer than the main line. Drawn
      // BELOW the main line so the main line's stroke sits on
      // top of the bloom.
      adapter.addLayer({
        id: LAYER_LINE_GLOW,
        type: "line",
        source: SOURCE,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ROUTE_COLOR,
          "line-width": 8,
          "line-opacity": 0.25,
          "line-blur": 4,
        },
      });

      // Main route line. Cyan, 2.5px, drawn on top of the glow.
      adapter.addLayer({
        id: LAYER_LINE,
        type: "line",
        source: SOURCE,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ROUTE_COLOR,
          "line-width": 2.5,
          "line-opacity": 1,
        },
      });

      // Intermediate waypoints. Small cyan dots at every polyline
      // vertex except the first and last (which are the
      // endpoints, drawn as larger pulsing circles on a separate
      // layer).
      adapter.addLayer({
        id: LAYER_WAYPOINTS,
        type: "circle",
        source: SOURCE_WAYPOINTS,
        paint: {
          "circle-radius": 3,
          "circle-color": ROUTE_COLOR,
          "circle-stroke-color": "#0a1424",  // --color-deep: a
                                              // subtle dark ring
                                              // to lift the dot
                                              // off the line.
          "circle-stroke-width": 0.5,
          "circle-opacity": 0.85,
        },
      });

      // Endpoints. Each feature has a `pulse` property (0..1)
      // that the layer's radius expression reads to drive the
      // pulse animation. `kind` distinguishes start from end
      // (currently only used to color them differently if we
      // want to in the future; today both are the same cyan).
      adapter.addLayer({
        id: LAYER_ENDPOINTS,
        type: "circle",
        source: SOURCE_ENDPOINTS,
        paint: {
          // radius = 6 + 4 * pulse; pulse runs 0..1
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["get", "pulse"],
            0, 6,
            1, 10,
          ],
          "circle-color": ROUTE_COLOR,
          "circle-stroke-color": "#e8f1f8",  // --color-ice
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.95,
        },
      });
    });

    // Cleanup: remove sources + layers on unmount. Sources and
    // layers are idempotent under addSource / addLayer
    // (MapAdapter guards against duplicates), but on unmount we
    // want a clean slate.
    return () => {
      for (const id of [LAYER_ENDPOINTS, LAYER_WAYPOINTS, LAYER_LINE, LAYER_LINE_GLOW]) {
        adapter.removeLayer(id);
      }
      for (const id of [SOURCE_ENDPOINTS, SOURCE_WAYPOINTS, SOURCE]) {
        adapter.removeSource(id);
      }
    };
  }, [adapter]);

  // Click handler for dynamic routing
  useEffect(() => {
    // We can't put pendingSelection in the deps array without re-binding the event 
    // on every click, which is fine, but cleaner to just fetch it on click via the store.
    const handleClick = (e: any) => {
      const state = useRouteStore.getState();
      if (state.pendingSelection) {
        const { lng, lat } = e.lngLat;
        if (state.pendingSelection === "origin") {
          state.setOrigin({ lon: lng, lat });
        } else if (state.pendingSelection === "destination") {
          state.setDestination({ lon: lng, lat });
        }
      }
    };
    
    // Add event
    adapter.on("click", handleClick);
    
    // NOTE: MapAdapter doesn't expose a global `off` that takes a handler in its types,
    // but maplibregl.Map does. 
    return () => {
      adapter.getRawMap().off("click", handleClick);
    };
  }, [adapter]);

  // Push the A* result into the three sources when it becomes
  // available. This effect depends on `status` and `result`
  // (not on `version` — version is for memoization by
  // consumers, not for triggering a re-push).
  useEffect(() => {
    if (status !== "ready" || !result) return;
    adapter.setData(SOURCE, result.featureCollection as unknown as GeoJSON.FeatureCollection);
    adapter.setData(SOURCE_WAYPOINTS, result.waypointsFeature as unknown as GeoJSON.FeatureCollection);
    adapter.setData(SOURCE_ENDPOINTS, result.endpointsFeature as unknown as GeoJSON.FeatureCollection);
  }, [adapter, status, result]);

  // Visibility sync. All four sublayers toggle together.
  useEffect(() => {
    adapter.setLayerVisibility(LAYER_LINE, enabled);
    adapter.setLayerVisibility(LAYER_LINE_GLOW, enabled);
    adapter.setLayerVisibility(LAYER_WAYPOINTS, enabled);
    adapter.setLayerVisibility(LAYER_ENDPOINTS, enabled);
  }, [adapter, enabled]);

  // Opacity sync. Apply the slider's value to the main line
  // and the waypoints; the glow and endpoints are styled
  // semi-transparent in their paint expressions so a full-
  // range slider on the user side wouldn't push them to
  // imperceptibility. We do still let the user dim the line
  // itself all the way to 0.
  useEffect(() => {
    adapter.setLayerOpacity(LAYER_LINE, opacity);
    adapter.setLayerOpacity(LAYER_WAYPOINTS, opacity);
  }, [adapter, opacity]);

  // Pulse ticker. Runs at ~4 Hz while the layer is enabled and
  // a result is loaded. The tick walks the pulse value along a
  // sine curve and rewrites the two endpoint features. Cost:
  // ~0.05ms per tick (two feature objects, single setData
  // call) — comfortably under the per-frame budget.
  useEffect(() => {
    if (!enabled) return;
    if (status !== "ready" || !result) return;
    const PULSE_PERIOD_MS = 1500;
    let raf = 0;
    const startedAt = performance.now();
    const tick = () => {
      const t = (performance.now() - startedAt) / PULSE_PERIOD_MS;
      // sin → 0..1 envelope with a soft phase shift so the
      // pulse is at "max" around t=0.5 and "min" around t=0/1.
      const phase = (Math.sin(t * 2 * Math.PI) + 1) / 2;
      const cur = resultRef.current;
      if (cur) {
        const fc: FeatureCollection<Point> = {
          type: "FeatureCollection",
          features: cur.endpointsFeature.features.map((f) => ({
            ...f,
            properties: {
              ...(f.properties as Record<string, unknown> | null),
              pulse: phase,
            },
          })),
        };
        adapter.setData(
          SOURCE_ENDPOINTS,
          fc as unknown as GeoJSON.FeatureCollection,
        );
      }
      raf = window.requestAnimationFrame(tick);
    };
    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [adapter, enabled, status, result]);

  return <RoutePanel enabled={enabled} />;
}
