"use client";

/**
 * IcebergLayer
 * ------------
 * Renders iceberg detection points as either:
 *   - individual circles (when zoomed in past clusterMaxZoom, or when
 *     a detection is far enough from neighbors not to be clustered), or
 *   - clusters (a single circle whose `point_count` represents the
 *     number of icebergs in the neighborhood, with an overlaid text
 *     label showing the abbreviated count).
 *
 * Source-level clustering (maplibre `cluster: true`) does the heavy
 * lifting. The layer paint and click handler are split by the
 * `["has", "point_count"]` filter, so the two cases never mix.
 *
 * Click behavior:
 *   - Click a detection circle → select that iceberg (existing flow,
 *     preserved unchanged).
 *   - Click a cluster circle → ease the camera to the cluster's
 *     expansion zoom (the zoom at which supercluster would split the
 *     cluster into its members). This is the standard maplibre /
 *     mapbox-gl cluster UX.
 *
 * Cursor affordance: hovering over either a detection or a cluster
 * switches the cursor to `pointer`.
 *
 * Color: hsl(195 30% 75%) per spec. Cluster circles stay in the same
 * hue family and only vary in lightness / opacity so the layer reads
 * as a single visual entity at every zoom.
 *
 * Tunables (chosen against the corridor zoom range — see plan §B.2):
 *   - clusterRadius: 50 (≈1° at z3.6)
 *   - clusterMaxZoom: 6 (above z6 the corridor is wide enough on
 *     screen that individual points are visually distinguishable)
 */

import { useEffect } from "react";
import type { FilterSpecification } from "maplibre-gl";
import { MapAdapter } from "@/components/map/map-adapter";
import { useLayerStore } from "@/stores/use-layer-store";
import { useIcebergSelection } from "@/stores/use-iceberg-selection";
import { ICEBERG_GEOJSON } from "@/lib/data/scenarios/drake-to-ross";

export const SOURCE = "iceberg-source";
export const LAYER_DETECTION = "iceberg-detection";
export const LAYER_DETECTION_SELECTED = "iceberg-detection-selected";
export const LAYER_CLUSTER_CIRCLE = "iceberg-cluster-circle";
export const LAYER_CLUSTER_COUNT = "iceberg-cluster-count";

interface Props {
  adapter: MapAdapter;
}

/** Filter expression type for the highlighted selection. */
type IdFilter = FilterSpecification | null;

export function IcebergLayer({ adapter }: Props) {
  const enabled = useLayerStore((s) => s.layers.icebergs.enabled);
  const opacity = useLayerStore((s) => s.layers.icebergs.opacity);
  const select = useIcebergSelection((s) => s.select);
  const selectedId = useIcebergSelection((s) => s.selectedId);

  // Register source + layers exactly once.
  useEffect(() => {
    adapter.onLoad(() => {
      // Source: clustered GeoJSON. supercluster runs in the background
      // and maplibre exposes `point_count` / `cluster` properties on
      // emitted features. We don't need to import supercluster
      // ourselves — maplibre wraps it.
      adapter.addSource(SOURCE, {
        type: "geojson",
        data: ICEBERG_GEOJSON,
        cluster: true,
        clusterRadius: 50,
        clusterMaxZoom: 6,
      });

      // Cluster circle. Sized and shaded by the cluster's point_count.
      // Three tiers: small (2-4), medium (5-14), large (15+).
      // Stays in the iceberg hue family (hsl 195 30 75) — only
      // lightness and alpha shift with cluster size.
      adapter.addLayer({
        id: LAYER_CLUSTER_CIRCLE,
        type: "circle",
        source: SOURCE,
        filter: ["has", "point_count"],
        paint: {
          "circle-radius": [
            "step",
            ["get", "point_count"],
            10, // 2..4
            5, 16,  // 5..14
            15, 22, // 15+
          ],
          "circle-color": [
            "step",
            ["get", "point_count"],
            "hsl(var(--iceberg-hue) var(--iceberg-saturation) var(--iceberg-lightness) / 0.65)", // 2..4
            5, "hsl(var(--iceberg-hue) var(--iceberg-saturation) 70% / 0.95)", // 5..14
            15, "hsl(var(--iceberg-hue) 35% 60% / 1)", // 15+
          ],
          "circle-stroke-color": "hsl(var(--iceberg-hue) 40% 25% / 1)",
          "circle-stroke-width": [
            "case",
            ["<=", ["get", "point_count"], 14],
            0,
            2,
          ],
          "circle-opacity": 0.9,
        },
      });

      // Cluster count label. Sits on top of the circle.
      adapter.addLayer({
        id: LAYER_CLUSTER_COUNT,
        type: "symbol",
        source: SOURCE,
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-size": 12,
          // The CARTO Dark Matter style ships the Open Sans Regular
          // font; its glyph endpoint is reachable from the style url
          // already set in MapAdapter. We use the bare "Open Sans
          // Regular" face name; maplibre resolves it via the style's
          // glyphs URL.
          "text-font": ["Open Sans Regular"],
          "text-allow-overlap": true,
        },
        paint: {
          // maplibre paint expressions expect literal color values, not
          // var() refs. --fg-primary is the ice color #e8f1f8.
          "text-color": "#e8f1f8",
          "text-halo-color": "rgba(5, 10, 20, 0.75)",
          "text-halo-width": 1.2,
        },
      });

      // Base detection layer. The filter `["!", ["has", "point_count"]]`
      // makes this layer render ONLY individual iceberg points (not
      // clusters). Above clusterMaxZoom, all features are unclustered
      // points and the cluster layers show nothing.
      adapter.addLayer({
        id: LAYER_DETECTION,
        type: "circle",
        source: SOURCE,
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-color": "hsl(var(--iceberg-hue) var(--iceberg-saturation) var(--iceberg-lightness) / 0.85)",
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["get", "sizeM"],
            30, 4,
            100, 6,
            250, 9,
            500, 13,
          ],
          "circle-stroke-color": "hsl(var(--iceberg-hue) 40% 30% / 1)",
          "circle-stroke-width": 1,
          "circle-opacity": 0.85,
        },
      });

      // Selected-detection highlight, drawn on top. Filtered to
      // unclustered features only — a cluster never matches.
      adapter.addLayer({
        id: LAYER_DETECTION_SELECTED,
        type: "circle",
        source: SOURCE,
        filter: [
          "all",
          ["!", ["has", "point_count"]],
          ["==", ["get", "id"], ""],
        ] as unknown as FilterSpecification,
        paint: {
          "circle-color": "hsl(var(--iceberg-hue) 80% 70% / 1)",
          "circle-radius": 12,
          "circle-stroke-color": "#e8f1f8",
          "circle-stroke-width": 2,
        },
      });

      // Click on a detection → select that iceberg.
      adapter.on("click", LAYER_DETECTION, (e) => {
        const f = e.features?.[0];
        if (!f) return;
        const id = (f.properties as { id?: string } | null)?.id ?? null;
        if (id) select(id);
      });

      // Click on a cluster → zoom in to its expansion zoom.
      // The cluster feature's `cluster_id` is a number; we ask the
      // GeoJSON source (via the adapter) for the zoom at which the
      // cluster splits into its members, then ease the camera to it.
      adapter.on("click", LAYER_CLUSTER_CIRCLE, async (e) => {
        const f = e.features?.[0];
        if (!f) return;
        const props = f.properties as { cluster_id?: number } | null;
        if (typeof props?.cluster_id !== "number") return;
        if (f.geometry.type !== "Point") return;
        const zoom = await adapter.getClusterExpansionZoom(SOURCE, props.cluster_id);
        adapter.easeTo({
          center: f.geometry.coordinates as [number, number],
          zoom,
          duration: 1200,
        });
      });

      // Cursor affordance on hover (both detections and clusters).
      adapter.on("mouseenter", LAYER_DETECTION, () => {
        document.body.style.cursor = "pointer";
      });
      adapter.on("mouseleave", LAYER_DETECTION, () => {
        document.body.style.cursor = "";
      });
      adapter.on("mouseenter", LAYER_CLUSTER_CIRCLE, () => {
        document.body.style.cursor = "pointer";
      });
      adapter.on("mouseleave", LAYER_CLUSTER_CIRCLE, () => {
        document.body.style.cursor = "";
      });
    });
  }, [adapter, select]);

  // Visibility / opacity sync — now covers the two new cluster layers
  // alongside the existing detection layers.
  useEffect(() => {
    adapter.setLayerVisibility(LAYER_DETECTION, enabled);
    adapter.setLayerVisibility(LAYER_DETECTION_SELECTED, enabled);
    adapter.setLayerVisibility(LAYER_CLUSTER_CIRCLE, enabled);
    adapter.setLayerVisibility(LAYER_CLUSTER_COUNT, enabled);
  }, [adapter, enabled]);

  useEffect(() => {
    adapter.setLayerOpacity(LAYER_DETECTION, opacity);
    adapter.setLayerOpacity(LAYER_CLUSTER_CIRCLE, opacity);
    adapter.setLayerOpacity(LAYER_CLUSTER_COUNT, opacity);
    adapter.setLayerOpacity(LAYER_DETECTION_SELECTED, opacity);
  }, [adapter, opacity]);

  // Selection sync: re-write the filter expression. The filter now
  // includes both the unclustered guard (so a cluster never matches
  // the selected-id test) and the id equality.
  useEffect(() => {
    const filter: IdFilter = selectedId
      ? ([
          "all",
          ["!", ["has", "point_count"]],
          ["==", ["get", "id"], selectedId],
        ] as unknown as FilterSpecification)
      : null;
    adapter.setLayerFilter(LAYER_DETECTION_SELECTED, filter);
  }, [adapter, selectedId]);

  return null;
}
