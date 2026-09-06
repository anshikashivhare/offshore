"use client";

import { useEffect, useState } from "react";
import type { FeatureCollection, Point } from "geojson";
import { MapAdapter } from "@/components/map/map-adapter";
import { useLayerStore } from "@/stores/use-layer-store";
import { ROUTE_GRID, GRID_COLS } from "@/lib/routing/a-star-router";

export const SOURCE_RISK = "risk-source";
export const LAYER_RISK = "risk-layer";

interface Props {
  adapter: MapAdapter;
}

export function RiskLayer({ adapter }: Props) {
  const enabled = useLayerStore((s) => s.layers.risk.enabled);
  const opacity = useLayerStore((s) => s.layers.risk.opacity);
  const [data, setData] = useState<FeatureCollection<Point> | null>(null);

  useEffect(() => {
    if (!enabled || data) return;
    
    // Generate risk heatmap data from the static A* routing grid
    const features: GeoJSON.Feature<Point>[] = [];
    for (let i = 0; i < ROUTE_GRID.length; i++) {
      const cell = ROUTE_GRID[i];
      // Only include points with actual risk to avoid a flat heatmap
      const totalRisk = (cell.concentration * 80) + (cell.icebergPenalty * 60);
      if (totalRisk > 10 && !cell.isLand) {
        // Reverse engineer lat/lon from index (from a-star-router grid math)
        // lon = GRID_MIN_LON + (x + 0.5) * GRID_STEP
        // lat = GRID_MIN_LAT + (y + 0.5) * GRID_STEP
        const x = i % GRID_COLS;
        const y = Math.floor(i / GRID_COLS);
        const lon = -66 + (x + 0.5) * 0.25;
        const lat = -70 + (y + 0.5) * 0.25;
        
        features.push({
          type: "Feature",
          geometry: { type: "Point", coordinates: [lon, lat] },
          properties: { risk: totalRisk }
        });
      }
    }
    
    setData({
      type: "FeatureCollection",
      features,
    } as unknown as FeatureCollection<Point>);
  }, [enabled, data]);

  // Mount source & layer
  useEffect(() => {
    adapter.onLoad(() => {
      adapter.addSource(SOURCE_RISK, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] }
      });

      adapter.addLayer({
        id: LAYER_RISK,
        type: "heatmap",
        source: SOURCE_RISK,
        paint: {
          "heatmap-weight": [
            "interpolate",
            ["linear"],
            ["get", "risk"],
            0, 0,
            100, 1
          ],
          "heatmap-intensity": 1,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0, "rgba(0, 0, 0, 0)",
            0.2, "rgba(253, 224, 71, 0.4)",  // yellow-300
            0.5, "rgba(249, 115, 22, 0.6)",  // orange-500
            0.8, "rgba(239, 68, 68, 0.8)",   // red-500
            1, "rgba(153, 27, 27, 0.9)"      // red-800
          ],
          "heatmap-radius": 30,
          "heatmap-opacity": 0.7,
        }
      });
    });

    return () => {
      adapter.removeLayer(LAYER_RISK);
      adapter.removeSource(SOURCE_RISK);
    };
  }, [adapter]);

  useEffect(() => {
    adapter.setLayerVisibility(LAYER_RISK, enabled);
  }, [adapter, enabled]);

  useEffect(() => {
    adapter.setLayerOpacity(LAYER_RISK, opacity);
  }, [adapter, opacity]);

  useEffect(() => {
    if (data) adapter.setData(SOURCE_RISK, data);
  }, [adapter, data]);

  return null;
}
