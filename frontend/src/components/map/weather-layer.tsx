"use client";

import { useEffect, useState } from "react";
import type { FeatureCollection, Point } from "geojson";
import { MapAdapter } from "@/components/map/map-adapter";
import { useLayerStore } from "@/stores/use-layer-store";
import { GRID_MIN_LON, GRID_MAX_LON, GRID_MIN_LAT, GRID_MAX_LAT } from "@/lib/routing/a-star-router";

export const SOURCE_WEATHER = "weather-source";
export const LAYER_WEATHER = "weather-layer";

interface Props {
  adapter: MapAdapter;
}

export function WeatherLayer({ adapter }: Props) {
  const enabled = useLayerStore((s) => s.layers.weather.enabled);
  const opacity = useLayerStore((s) => s.layers.weather.opacity);
  const [data, setData] = useState<FeatureCollection<Point> | null>(null);

  // Fetch real Open-Meteo weather data when enabled for the first time
  useEffect(() => {
    if (!enabled || data) return;
    
    // We fetch a 4x4 grid of coordinates across our map bounds to visualize wind/weather
    const lons = [GRID_MIN_LON, GRID_MIN_LON + 2.5, GRID_MIN_LON + 5, GRID_MAX_LON];
    const lats = [GRID_MIN_LAT, GRID_MIN_LAT + 3, GRID_MIN_LAT + 6, GRID_MAX_LAT];
    
    const latParams = lats.flatMap(lat => lons.map(() => lat)).join(",");
    const lonParams = lats.flatMap(() => lons).join(",");
    
    // Fetch wind speed and direction from open-meteo
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${latParams}&longitude=${lonParams}&current=wind_speed_10m,wind_direction_10m`;
    
    fetch(url)
      .then(res => res.json())
      .then(json => {
        if (!Array.isArray(json)) return;
        
        const features = json.map((res: any) => ({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [res.longitude, res.latitude],
          },
          properties: {
            windSpeed: res.current.wind_speed_10m,
            windDir: res.current.wind_direction_10m,
          }
        }));
        
        setData({
          type: "FeatureCollection",
          features,
        } as unknown as FeatureCollection<Point>);
      })
      .catch(console.error);
  }, [enabled, data]);

  // Mount source & layer
  useEffect(() => {
    adapter.onLoad(() => {
      adapter.addSource(SOURCE_WEATHER, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] }
      });

      adapter.addLayer({
        id: LAYER_WEATHER,
        type: "symbol",
        source: SOURCE_WEATHER,
        layout: {
          "text-field": [
            "format",
            ["get", "windSpeed"], " km/h\n",
            {"font-scale": 0.8},
            "▼", {"font-scale": 0.8}
          ],
          "text-rotate": ["get", "windDir"],
          "text-size": 12,
          "text-allow-overlap": false,
        },
        paint: {
          "text-color": "#fbbf24", // yellow-400
          "text-halo-color": "#1e293b",
          "text-halo-width": 2,
        }
      });
    });

    return () => {
      adapter.removeLayerSafe(LAYER_WEATHER);
      adapter.removeSourceSafe(SOURCE_WEATHER);
    };
  }, [adapter]);

  useEffect(() => {
    adapter.setLayerVisibility(LAYER_WEATHER, enabled);
  }, [adapter, enabled]);

  useEffect(() => {
    adapter.setLayerOpacity(LAYER_WEATHER, opacity);
  }, [adapter, opacity]);

  useEffect(() => {
    if (data) adapter.setData(SOURCE_WEATHER, data);
  }, [adapter, data]);

  return null;
}
