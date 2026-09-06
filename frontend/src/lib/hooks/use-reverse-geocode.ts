import { useState, useEffect } from "react";
import type { Coordinates } from "@/stores/use-route-store";
import { usePortStore } from "@/stores/use-port-store";

export interface GeocodeResult {
  primary: string;
  secondary?: string;
}

// Simple memory cache to avoid hitting rate limits when re-clicking the same general area
const cache = new Map<string, GeocodeResult>();

export function useReverseGeocode(coords: Coordinates): GeocodeResult {
  const [result, setResult] = useState<GeocodeResult>({ primary: "Loading..." });
  
  useEffect(() => {
    // Check local ports first
    const ports = usePortStore.getState().ports;
    const matchedPort = ports.find(
      (p) => Math.abs(p.lat - coords.lat) < 0.01 && Math.abs(p.lon - coords.lon) < 0.01
    );

    if (matchedPort) {
      setResult({ primary: matchedPort.name, secondary: matchedPort.country });
      return;
    }

    // Round to 2 decimals for caching (~1km resolution)
    const cacheKey = `${coords.lat.toFixed(2)},${coords.lon.toFixed(2)}`;
    
    if (cache.has(cacheKey)) {
      setResult(cache.get(cacheKey)!);
      return;
    }

    setResult({ primary: "Resolving..." });
    
    const url = `https://nominatim.openstreetmap.org/reverse?lat=${coords.lat}&lon=${coords.lon}&format=jsonv2`;
    
    fetch(url, {
      headers: {
        // Nominatim requires a User-Agent
        "User-Agent": "OffshoreRoutingDashboard/1.0"
      }
    })
      .then(res => res.json())
      .then(data => {
        let locationName = "Open Ocean";
        
        if (data.address) {
          // Priority for maritime/coastal features
          locationName = 
            data.name || 
            data.address.port || 
            data.address.bay || 
            data.address.sea || 
            data.address.ocean || 
            data.address.island || 
            data.address.city || 
            data.address.county || 
            data.address.state || 
            "Open Ocean";
        }
        
        const finalResult = { 
          primary: locationName, 
          secondary: data.address?.country 
        };
        cache.set(cacheKey, finalResult);
        setResult(finalResult);
      })
      .catch(err => {
        console.error("Geocoding failed:", err);
        setResult({ primary: "Unknown location" });
      });
      
  }, [coords.lat, coords.lon]);

  return result;
}
