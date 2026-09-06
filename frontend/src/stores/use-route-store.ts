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
  ROUTE_START,
  ROUTE_GOAL,
} from "@/lib/routing/a-star-router";

export type RouteStatus = "idle" | "calculating" | "ready";

export interface Coordinates {
  lat: number;
  lon: number;
}

interface RouteStore {
  status: RouteStatus;
  result: RouteResult | null;
  version: number;
  origin: Coordinates;
  destination: Coordinates;
  pendingSelection: "origin" | "destination" | null;
  setPendingSelection: (sel: "origin" | "destination" | null) => void;
  setEndpoints: (origin: Coordinates, destination: Coordinates) => void;
  setOrigin: (origin: Coordinates) => void;
  setDestination: (destination: Coordinates) => void;
  recalculate: () => void;
}

export const useRouteStore = create<RouteStore>((set, get) => ({
  status: "idle",
  result: null,
  version: 0,
  origin: ROUTE_START,
  destination: ROUTE_GOAL,
  pendingSelection: null,
  setPendingSelection: (pendingSelection) => set({ pendingSelection }),
  setEndpoints: (origin: Coordinates, destination: Coordinates) => {
    set({ origin, destination });
    get().recalculate();
  },
  setOrigin: (origin: Coordinates) => {
    set({ origin, pendingSelection: null });
    get().recalculate();
  },
  setDestination: (destination: Coordinates) => {
    set({ destination, pendingSelection: null });
    get().recalculate();
  },
  recalculate: () => {
    set({ status: "calculating" });
    const { origin, destination } = get();
    setTimeout(() => {
      const result = calculateRoute(origin, destination);
      set((s) => ({
        status: "ready",
        result,
        version: s.version + 1,
      }));
    }, 0);
  },
}));
