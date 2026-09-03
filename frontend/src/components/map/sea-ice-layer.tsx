"use client";

/**
 * SeaIceLayer
 * -----------
 * Renders the sea-ice concentration grid from the drake-to-ross scenario
 * as a heatmap layer. Source is intentionally a plain (non-clustered)
 * GeoJSON source of Point features; clustering is not appropriate for a
 * regular grid.
 *
 * Convention (must be followed by all future layer components):
 *   1. Export a `SOURCE` constant — the maplibre source id. This is the
 *      string every other layer / debug tool references.
 *   2. Export a `LAYER_*` constant for each maplibre layer id.
 *   3. Subscribe to useLayerStore for `enabled` + `opacity`; push
 *      changes into the adapter (don't duplicate state locally).
 *   4. All maplibre interaction goes through the MapAdapter. Do not
 *      import maplibregl directly from a layer component.
 *
 * Style choice — heatmap, not a fill grid:
 *   - We have ~1° point samples, not polygons. A heatmap renders the
 *     concentration gradient naturally and avoids ugly "blocky" cells
 *     while the dataset is small.
 *   - When the real data arrives (polygon grid from NSIDC), this file
 *     will be replaced with a `fill` paint expression driving color
 *     from the same `concentration` property.
 */

import { useEffect } from "react";
import { MapAdapter } from "@/components/map/map-adapter";
import { useLayerStore } from "@/stores/use-layer-store";
import { SEA_ICE_GEOJSON } from "@/lib/data/scenarios/drake-to-ross";

export const SOURCE = "sea-ice-source";
export const LAYER_HEATMAP = "sea-ice-heatmap";

interface Props {
  adapter: MapAdapter;
}

export function SeaIceLayer({ adapter }: Props) {
  const enabled = useLayerStore((s) => s.layers.seaIce.enabled);
  const opacity = useLayerStore((s) => s.layers.seaIce.opacity);

  // Register source + layer exactly once.
  useEffect(() => {
    adapter.onLoad((map) => {
      adapter.addSource(SOURCE, { type: "geojson", data: SEA_ICE_GEOJSON });

      adapter.addLayer({
        id: LAYER_HEATMAP,
        type: "heatmap",
        source: SOURCE,
        maxzoom: 9,
        paint: {
          // Linear 0..1 weight, so high-concentration cells produce
          // the strongest density. The concentration field is
          // already smooth (0 outside the corridor polygon, 0..0.98
          // inside, sampled at jittered positions and softened by
          // a cosine edge-fade), so the heatmap is naturally a
          // smooth field that contours along the corridor rather
          // than reading as a hard rectangle.
          "heatmap-weight": [
            "interpolate",
            ["linear"],
            ["get", "concentration"],
            0, 0,
            1, 1,
          ],
          // Glacial-teal → pack-ice ramp. Density=0 is fully
          // transparent so the basemap shows through. The ramp
          // reaches 60% alpha at the high end, not 95% — the
          // polygon mask + edge-fade + lat gradient already do the
          // spatial work, so the ramp just needs to read as "ice"
          // without becoming an opaque block that hides adjacent
          // layers. The top color is amber (not red): red reads as
          // a hazard/alert semantic elsewhere in the design
          // system, and the pack-ice body isn't an alert — it's a
          // baseline navigational fact.
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,    "rgba(127, 209, 211, 0)",
            0.08, "rgba(127, 209, 211, 0.30)",
            0.25, "rgba(127, 209, 211, 0.45)",
            0.50, "rgba(94, 234, 212, 0.50)",
            0.75, "rgba(58, 169, 179, 0.55)",
            1,    "rgba(251, 191, 36, 0.55)",
          ],
          // Radius tuned to 20-30 px across the corridor's zoom
          // range (z3-z5). The smaller radius (down from the
          // previous 25-35 px) is what the user spec asked for
          // and is the key reason the heatmap no longer expands
          // into a solid rectangle: a 24-px radius on a 0.25°
          // jittered grid (~5 px between points at z3.6) gives
          // ~4-5× overlap — enough for blend, small enough that
          // the polygon's straight edges don't bleed into a hard
          // rectangle. The radius still grows modestly with zoom
          // so the field is detailed at high zoom and reads as a
          // single wash at low zoom.
          "heatmap-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1, 14,
            3, 20,
            4, 24,
            5, 30,
            7, 36,
          ],
          // Intensity tuned to keep the field at organic density
          // with the smaller radius. With a 20-30 px radius
          // (down from 25-35), we reduce intensity proportionally
          // so the total heatmap density at the field's center
          // stays in the 0.6-0.75 band — high enough to read as
          // a clear "ice body" but low enough that the polygon's
          // edge-fade band (where concentrations are already
          // dropping) is not pushed to a hard saturated edge.
          "heatmap-intensity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1, 0.55,
            3, 0.65,
            5, 0.75,
          ],
          "heatmap-opacity": 0.75,
        },
      });
    });
  }, [adapter]);

  // React to enabled / opacity changes without re-creating the layer.
  useEffect(() => {
    adapter.setLayerVisibility(LAYER_HEATMAP, enabled);
  }, [adapter, enabled]);

  useEffect(() => {
    adapter.setLayerOpacity(LAYER_HEATMAP, opacity);
  }, [adapter, opacity]);

  return null;
}
