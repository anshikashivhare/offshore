"use client";

import { useEffect, useRef } from "react";
import type { FeatureCollection, Point } from "geojson";
import { MapAdapter } from "@/components/map/map-adapter";
import { useLayerStore } from "@/stores/use-layer-store";
import { useRouteStore } from "@/stores/use-route-store";
import * as turf from "@turf/turf";

export const SOURCE_VESSEL = "vessel-source";
export const LAYER_VESSEL = "vessel-layer";

interface Props {
  adapter: MapAdapter;
}

export function VesselLayer({ adapter }: Props) {
  const enabled = useLayerStore((s) => s.layers.vessel.enabled);
  const opacity = useLayerStore((s) => s.layers.vessel.opacity);
  const status = useRouteStore((s) => s.status);
  const result = useRouteStore((s) => s.result);

  const resultRef = useRef(result);
  resultRef.current = result;

  // Mount source & layer
  useEffect(() => {
    adapter.onLoad(() => {
      adapter.addSource(SOURCE_VESSEL, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] }
      });

      adapter.addLayer({
        id: LAYER_VESSEL,
        type: "symbol",
        source: SOURCE_VESSEL,
        layout: {
          // 'rocket-15' or 'triangle-15' are built-in MapLibre sprites
          "icon-image": "triangle-15",
          "icon-size": 1.5,
          "icon-rotate": ["get", "bearing"],
          "icon-rotation-alignment": "map",
          "icon-allow-overlap": true,
        },
        paint: {
          "icon-color": "hsl(0 0% 90%)",
          "icon-opacity": 1,
        }
      });
    });

    return () => {
      adapter.removeLayer(LAYER_VESSEL);
      adapter.removeSource(SOURCE_VESSEL);
    };
  }, [adapter]);

  useEffect(() => {
    adapter.setLayerVisibility(LAYER_VESSEL, enabled);
  }, [adapter, enabled]);

  useEffect(() => {
    adapter.setLayerOpacity(LAYER_VESSEL, opacity);
  }, [adapter, opacity]);

  // Animation Loop
  useEffect(() => {
    if (!enabled || status !== "ready" || !result) return;
    
    // Convert coordinate list to Turf LineString
    const line = turf.lineString(result.coordinates);
    const totalDistance = turf.length(line, { units: "kilometers" });
    if (totalDistance === 0) return;

    let raf = 0;
    const speedKmPerMs = 0.05; // speed of animation
    let lastTime = performance.now();
    let currentDistance = 0;

    const tick = (time: number) => {
      const dt = time - lastTime;
      lastTime = time;

      currentDistance += speedKmPerMs * dt;
      if (currentDistance > totalDistance) {
        currentDistance = 0; // loop back to start
      }

      // Calculate new position
      const currentPos = turf.along(line, currentDistance, { units: "kilometers" });
      
      // Calculate bearing by taking a point slightly ahead
      const nextDistance = Math.min(currentDistance + 1, totalDistance);
      const nextPos = turf.along(line, nextDistance, { units: "kilometers" });
      const currentBearing = turf.bearing(currentPos, nextPos);

      const fc: FeatureCollection<Point> = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            geometry: currentPos.geometry,
            properties: { bearing: currentBearing }
          }
        ]
      };
      adapter.setData(SOURCE_VESSEL, fc as unknown as GeoJSON.FeatureCollection);
      raf = window.requestAnimationFrame(tick);
    };
    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [adapter, enabled, status, result]);

  return null;
}
