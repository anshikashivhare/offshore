/**
 * useRouteStore — planned-route state for the route layer + panel.
 *
 * Architectural decision (mirrors useIcebergSelection / useOceanCurrentControls):
 *   - useLayerStore is the generic per-LayerId store for things every
 *     layer shares (enabled, opacity). It must NOT grow fields that
 *     are specific to one layer.
 *   - Route calculation is a one-off, expensive side effect
 *     (A* on a 1,280-cell grid). Its result is a single artifact
 *     that the route layer and the route panel both render from.
 *     Putting it in a dedicated store keeps that contract clear
 *     and avoids making useLayerStore carry a `RouteResult` field
 *     that the iceberg, sea-ice, and ocean-current layers don't
 *     care about.
 *
 * State machine:
 *   - `idle`:       no calculation has run yet (initial state).
 *   - `calculating`: A* is in flight. The panel renders a
 *                   "Calculating…" label and disables the
 *                   "Re-calculate" button.
 *   - `ready`:      `result` holds the latest RouteResult. The
 *                   panel renders the metrics, the layer has
 *                   pushed the GeoJSON to the maplibre source.
 *
 * `version` increments on every successful recalculate. Consumers
 * that memoize on `result` should also include `version` so
 * recomputed routes force a re-render even when the result shape
 * is identical.
 */
"use client";

import { create } from "zustand";
import {
  calculateRoute,
  type RouteResult,
} from "@/lib/routing/a-star-router";

export type RouteStatus = "idle" | "calculating" | "ready";

interface RouteStore {
  status: RouteStatus;
  result: RouteResult | null;
  version: number;
  recalculate: () => void;
}

export const useRouteStore = create<RouteStore>((set) => ({
  status: "idle",
  result: null,
  version: 0,
  recalculate: () => {
    // Flip to "calculating" synchronously so the panel can show
    // the in-flight label on the next React render.
    set({ status: "calculating" });
    // Defer the A* to the next tick. calculateRoute() takes
    // ~50-200ms on a 1,280-cell grid; running it inside a
    // setTimeout(0) lets React flush the "Calculating…" state
    // before the main thread blocks. Without the defer, the
    // user would never see the label because the entire
    // recalculate() call would resolve before React repaints.
    setTimeout(() => {
      const result = calculateRoute();
      set((s) => ({
        status: "ready",
        result,
        version: s.version + 1,
      }));
    }, 0);
  },
}));
