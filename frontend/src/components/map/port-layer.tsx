"use client";

import { useEffect, useRef } from "react";
import type { MapMouseEvent } from "maplibre-gl";
import maplibregl from "maplibre-gl";
import { MapAdapter } from "@/components/map/map-adapter";
import { usePortStore } from "@/stores/use-port-store";
import { useRouteStore } from "@/stores/use-route-store";

interface Props {
  adapter: MapAdapter;
}

export function PortLayer({ adapter }: Props) {
  const ports = usePortStore((s) => s.ports);
  const fetchPorts = usePortStore((s) => s.fetchPorts);
  
  const origin = useRouteStore((s) => s.origin);
  const destination = useRouteStore((s) => s.destination);
  const pendingSelection = useRouteStore((s) => s.pendingSelection);
  const setPendingSelection = useRouteStore((s) => s.setPendingSelection);
  const setOrigin = useRouteStore((s) => s.setOrigin);
  const setDestination = useRouteStore((s) => s.setDestination);
  
  // Fetch ports on mount
  useEffect(() => {
    fetchPorts();
  }, [fetchPorts]);

  // Keep a ref to the map for popup handling and bounds
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);

  useEffect(() => {
    adapter.onLoad((map) => {
      mapRef.current = map;
      
      // Add source for ports
      adapter.addSource("ports-source", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      // Layer for all unselected ports (small dots)
      adapter.addLayer({
        id: "ports-layer",
        type: "circle",
        source: "ports-source",
        paint: {
          "circle-radius": 3,
          "circle-color": "rgba(148, 163, 184, 0.6)",
          "circle-stroke-width": 1,
          "circle-stroke-color": "rgba(255, 255, 255, 0.3)",
        },
      });
      
      // Layer for selected Origin/Destination
      adapter.addLayer({
        id: "ports-selected-layer",
        type: "circle",
        source: "ports-source",
        filter: ["has", "selectionType"],
        paint: {
          "circle-radius": 6,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#fff",
          "circle-color": [
            "match",
            ["get", "selectionType"],
            "origin", "#10b981", // Green for origin
            "destination", "#ef4444", // Red for destination
            "#3b82f6" // fallback blue
          ]
        },
      });

      // Hover Tooltip logic
      popupRef.current = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
        className: "port-tooltip",
      });

      map.on("mouseenter", "ports-layer", (e) => {
        if (!e.features || e.features.length === 0) return;
        map.getCanvas().style.cursor = "pointer";
        const feature = e.features[0];
        const coordinates = (feature.geometry as any).coordinates.slice();
        
        const name = feature.properties?.name;
        const country = feature.properties?.country;
        
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
          coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        popupRef.current
          ?.setLngLat(coordinates as [number, number])
          .setHTML(`<div style="padding: 4px; font-family: monospace; font-size: 11px;">
            <strong>${name}</strong><br/>
            <span style="color: #64748b">${country}</span>
          </div>`)
          .addTo(map);
      });

      map.on("mouseleave", "ports-layer", () => {
        map.getCanvas().style.cursor = "";
        popupRef.current?.remove();
      });
      
      // Click logic to select port
      map.on("click", "ports-layer", (e: MapMouseEvent & { features?: maplibregl.MapboxGeoJSONFeature[] }) => {
        if (!e.features || e.features.length === 0) return;
        const feature = e.features[0];
        
        // Prevent default route-layer click logic from overriding this if pendingSelection is active
        e.preventDefault(); 
        
        const coords = (feature.geometry as any).coordinates;
        const portName = feature.properties?.name;
        
        // If user is actively placing A or B, satisfy that
        const currentPending = useRouteStore.getState().pendingSelection;
        if (currentPending === "origin") {
          setOrigin(coords[1], coords[0]);
          setPendingSelection(null);
        } else if (currentPending === "destination") {
          setDestination(coords[1], coords[0]);
          setPendingSelection(null);
        } else {
          // If no pending selection, click defaults to setting Origin, 
          // or Destination if Origin is already set (and not clicking the same origin)
          const currOrigin = useRouteStore.getState().origin;
          
          // Check if clicking close to current origin
          const isOrigin = Math.abs(currOrigin.lat - coords[1]) < 0.1 && Math.abs(currOrigin.lon - coords[0]) < 0.1;
          
          if (isOrigin) {
            // Unset origin? Or just ignore. Let's ignore.
          } else {
            // Set as destination
            setDestination(coords[1], coords[0]);
          }
        }
      });
    });
    
    // NOTE: cleanup function for port layer
    return () => {
      adapter.removeLayer("ports-selected-layer");
      adapter.removeLayer("ports-layer");
      adapter.removeSource("ports-source");
    };
  }, [adapter, setOrigin, setDestination, setPendingSelection]);

  // Update GeoJSON data when ports or selection changes
  useEffect(() => {
    const features: GeoJSON.Feature<GeoJSON.Point>[] = ports.map((p) => {
      // Determine if this port is the origin or destination
      let selectionType = null;
      if (Math.abs(p.lat - origin.lat) < 0.01 && Math.abs(p.lon - origin.lon) < 0.01) {
        selectionType = "origin";
      } else if (Math.abs(p.lat - destination.lat) < 0.01 && Math.abs(p.lon - destination.lon) < 0.01) {
        selectionType = "destination";
      }

      return {
        type: "Feature",
        properties: {
          name: p.name,
          country: p.country,
          ...(selectionType && { selectionType })
        },
        geometry: {
          type: "Point",
          coordinates: [p.lon, p.lat],
        },
      };
    });

    adapter.setData("ports-source", {
      type: "FeatureCollection",
      features,
    });
  }, [ports, origin, destination, adapter]);
  
  // Pan and zoom when both origin and destination change
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;
    
    // Calculate distance to see if we should pan
    const dx = destination.lon - origin.lon;
    const dy = destination.lat - origin.lat;
    const dist = Math.sqrt(dx*dx + dy*dy);
    
    if (dist > 5) {
      // Create a bounding box covering both points
      const bounds = new maplibregl.LngLatBounds(
        [origin.lon, origin.lat],
        [destination.lon, destination.lat]
      );
      
      map.fitBounds(bounds, {
        padding: 100,
        maxZoom: 6,
        duration: 2000
      });
    }
  }, [origin, destination]);

  return null;
}
