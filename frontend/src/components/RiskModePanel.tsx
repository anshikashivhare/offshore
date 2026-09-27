import React from "react";
import { ShieldAlert, AlertTriangle, Crosshair, Map as MapIcon } from "lucide-react";
import type { Route, Vessel, Iceberg, Coordinate } from "@/lib/offshore-types";

// (Optional) Define NavState locally if not exported from index
type VesselNavState = {
  position: Coordinate;
  heading: number;
  sogKnots: number;
  segmentIndex: number;
  distanceTraveledNm: number;
  distanceRemainingNm: number;
  totalDistanceNm: number;
};

function calcDistKm(c1: Coordinate, c2: Coordinate) {
    const R = 6371; // km
    const dLat = (c2.lat - c1.lat) * Math.PI / 180;
    const dLon = (c2.lng - c1.lng) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) + 
              Math.cos(c1.lat * Math.PI / 180) * Math.cos(c2.lat * Math.PI / 180) * 
              Math.sin(dLon/2) * Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function RiskModePanel({
  onExit,
  routes = [],
  selectedRouteId,
  onSelectRoute,
  vessel,
  icebergs = [],
  navState
}: {
  onExit: () => void;
  routes?: Route[];
  selectedRouteId?: string;
  onSelectRoute?: (id: string) => void;
  vessel?: Vessel | null;
  icebergs?: Iceberg[];
  navState?: VesselNavState | null;
}) {
  const selectedRoute = routes.find(r => r.id === selectedRouteId) || routes[0];
  
  // Vessel Status defaults
  const vesselId = vessel?.vessel_id || "RV-001";
  const vesselName = vessel?.vessel_name || "Unknown Vessel";
  const speed = navState ? navState.sogKnots : (vessel?.cruising_speed || 0);
  
  let heading = navState ? navState.heading : 0;
  let coords = navState?.position || (selectedRoute?.geometry && selectedRoute.geometry.length > 0 ? selectedRoute.geometry[0] : { lat: 0, lng: 0 });

  // If no navState but we have a route, approximate initial heading to next point
  if (!navState && selectedRoute?.geometry && selectedRoute.geometry.length > 1) {
      const start = selectedRoute.geometry[0];
      const next = selectedRoute.geometry[1];
      const y = Math.sin((next.lng - start.lng) * Math.PI/180) * Math.cos(next.lat * Math.PI/180);
      const x = Math.cos(start.lat * Math.PI/180) * Math.sin(next.lat * Math.PI/180) -
                Math.sin(start.lat * Math.PI/180) * Math.cos(next.lat * Math.PI/180) * Math.cos((next.lng - start.lng) * Math.PI/180);
      heading = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  }

  const latStr = `${Math.abs(coords.lat).toFixed(2)}° ${coords.lat >= 0 ? 'N' : 'S'}`;
  const lngStr = `${Math.abs(coords.lng).toFixed(2)}° ${coords.lng >= 0 ? 'E' : 'W'}`;

  const rawRiskScore = selectedRoute?.riskScore ?? 0;
  const riskScore = typeof rawRiskScore === 'number' ? rawRiskScore : 0;
  const riskPct = Math.round(riskScore * 100);
  
  const riskColor = riskScore < 0.25 ? "#22c55e" : riskScore < 0.5 ? "#f59e0b" : "#ef4444";
  const riskLabel = riskScore < 0.25 ? "Low" : riskScore < 0.5 ? "Moderate" : "High";

  let closestIceberg = null;
  let minIceDist = Infinity;
  
  if (icebergs && icebergs.length > 0 && selectedRoute?.geometry) {
     for (let geo of selectedRoute.geometry) {
        for (let ice of icebergs) {
            let dist = calcDistKm(geo, ice.position);
            if (dist < minIceDist) {
                minIceDist = dist;
                closestIceberg = ice;
            }
        }
     }
  }

  return (
    <div className="nav-minimal-dock" style={{ 
      bottom: "12px", 
      left: "12px", 
      transform: "none",
      width: "min(360px, calc(100% - 24px))",
      maxHeight: "calc(100% - 24px)",
      maxWidth: "calc(100% - 24px)",
      minWidth: 0,
      overflowY: "auto",
      overflowX: "hidden",
      padding: "20px", 
      display: "flex", 
      flexDirection: "column", 
      gap: "16px",
      zIndex: 1000,
      justifyContent: "flex-start",
      alignItems: "stretch"
    }} aria-label="Risk Analysis Panel">
      
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <ShieldAlert size={18} color="#ef4444" />
          <span style={{ fontSize: "14px", fontWeight: 600, color: "#fff" }}>Risk Analysis</span>
        </div>
        <button 
          onClick={onExit}
          style={{ 
            background: "rgba(255,255,255,0.1)", 
            border: "1px solid rgba(255,255,255,0.2)", 
            borderRadius: "4px", 
            padding: "4px 8px", 
            fontSize: "11px",
            color: "#fff",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "4px"
          }}
        >
          <MapIcon size={12} />
          Exit Risk Mode
        </button>
      </div>

      {/* Passage Route Selector */}
      {routes && routes.length > 0 && onSelectRoute && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "16px" }}>
          <span className="nav-dock-routes-label">PASSAGE ROUTE</span>
          <div className="nav-dock-routes-chips" style={{ justifyContent: "flex-start" }}>
            {routes.map((r) => {
              const isSelected = r.id === selectedRoute?.id;
              return (
                <button
                  key={r.id}
                  onClick={() => onSelectRoute(r.id)}
                  className={`nav-route-chip ${isSelected ? "active" : ""}`}
                >
                  <span className="nav-route-chip-dot" />
                  <span className="nav-route-chip-name">{r.name.split(" ")[0]}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Vessel Status */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "16px" }}>
         <span className="nav-dock-routes-label">VESSEL STATUS</span>
         <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
               <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 600, marginBottom: "2px" }}>ID / NAME</div>
               <div style={{ fontSize: "12px", color: "#fff", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{vesselId.substring(0, 8)} / {vesselName}</div>
            </div>
            <div>
               <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 600, marginBottom: "2px" }}>HEADING / SPD</div>
               <div style={{ fontSize: "12px", color: "#fff", fontWeight: 600 }}>{Math.round(heading)}° / {speed.toFixed(1)}kn</div>
            </div>
            <div>
               <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 600, marginBottom: "2px" }}>COORDINATES</div>
               <div style={{ fontSize: "11px", color: "#fff", fontWeight: 600, fontFamily: "var(--font-mono)" }}>{latStr}, {lngStr}</div>
            </div>
            <div>
               <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 600, marginBottom: "2px" }}>RISK LEVEL</div>
               <div style={{ fontSize: "13px", color: riskColor, fontWeight: 700 }}>{riskPct}% <span style={{fontSize: "10px", fontWeight: "normal"}}>({riskLabel})</span></div>
            </div>
         </div>
      </div>

      {/* Hazard Proximity */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "6px", padding: "12px", display: "flex", gap: "10px", alignItems: "flex-start" }}>
          <AlertTriangle size={16} color="#ef4444" style={{ marginTop: "2px" }} />
          <div>
            <div style={{ fontSize: "12px", fontWeight: 600, color: "#fff", marginBottom: "4px" }}>Hazard Proximity</div>
            <div style={{ fontSize: "11px", color: "#cbd5e1", lineHeight: 1.4 }}>
              {closestIceberg 
                  ? `Closest known hazard is Iceberg ${closestIceberg.id}, projected passing distance ${(minIceDist).toFixed(1)} km. Encounter Risk: ${closestIceberg.risk?.toUpperCase() || "HIGH"}.`
                  : "No imminent iceberg threats detected along active route geometry."
              }
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", padding: "10px 12px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "6px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <Crosshair size={14} color="#94a3b8" />
            <span style={{ fontSize: "11px", color: "#fff", fontWeight: 600 }}>Future Risk Metrics</span>
          </div>
          {selectedRoute && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginTop: "4px" }}>
                 <div style={{ fontSize: "10px", color: "#94a3b8" }}>Exposure: <strong style={{color:"#fff"}}>{selectedRoute.exposure || "N/A"}</strong></div>
                 <div style={{ fontSize: "10px", color: "#94a3b8" }}>Forecast: <strong style={{color:"#fff"}}>72h</strong></div>
                 <div style={{ fontSize: "10px", color: "#94a3b8" }}>Est Fuel: <strong style={{color:"#fff"}}>{selectedRoute.fuelLitres?.toFixed(0) || "N/A"} L</strong></div>
                 <div style={{ fontSize: "10px", color: "#94a3b8" }}>Dist: <strong style={{color:"#fff"}}>{selectedRoute.distanceKm?.toFixed(0) || "N/A"} km</strong></div>
              </div>
          )}
        </div>
      </div>
    </div>
  );
}
