"use client";

/**
 * MissionMap — top-level composer.
 *
 * Responsibilities:
 *   - Owns the <div> container that MapLibre mounts into.
 *   - Owns the MapAdapter instance (one per mount).
 *   - Mounts the layer components and passes the adapter down.
 *   - Cleans up the map on unmount.
 *
 * Note: layer components are children but communicate with the map
 * ONLY through the adapter. They render null. This keeps the React
 * tree small (re-renders here don't repaint the map) and matches
 * the convention that every layer is an imperative plugin to the
 * adapter rather than a wrapper around the map.
 */

import { useEffect, useRef, useState } from "react";
import { MapAdapter } from "@/components/map/map-adapter";
import { SeaIceLayer } from "@/components/map/sea-ice-layer";
import { IcebergLayer } from "@/components/map/iceberg-layer";
import { OceanCurrentLayer } from "@/components/map/ocean-current-layer";
import { RouteLayer } from "@/components/map/route-layer";
import { MapLegend } from "@/components/map/map-legend";

export function MissionMap() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [adapter, setAdapter] = useState<MapAdapter | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const a = new MapAdapter(containerRef.current);
    setAdapter(a);
    return () => {
      a.destroy();
      setAdapter(null);
    };
  }, []);

  return (
    <div className="relative h-full w-full">
      <div
        ref={containerRef}
        className="absolute inset-0"
        aria-label="Antarctic navigation map"
        role="application"
      />
      {adapter ? (
        <>
          <SeaIceLayer adapter={adapter} />
          <IcebergLayer adapter={adapter} />
          <OceanCurrentLayer adapter={adapter} />
          <RouteLayer adapter={adapter} />
        </>
      ) : null}
      <MapLegend />
    </div>
  );
}
