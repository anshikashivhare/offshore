import React from "react";
import { ShieldAlert, AlertTriangle, Crosshair, Map as MapIcon, ChevronRight } from "lucide-react";

export function RiskModePanel({
  onExit,
}: {
  onExit: () => void;
}) {
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
      zIndex: 1000
    }} aria-label="Risk Analysis Panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-hairline)", paddingBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <ShieldAlert size={18} color="#ef4444" />
          <span style={{ fontSize: "14px", fontWeight: 600, color: "var(--deep-fjord)" }}>Risk Analysis</span>
        </div>
        <button 
          onClick={onExit}
          style={{ 
            background: "var(--ice-paper-surface)", 
            border: "1px solid var(--border-hairline)", 
            borderRadius: "4px", 
            padding: "4px 8px", 
            fontSize: "11px",
            color: "var(--graphite-muted)",
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

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "6px", padding: "12px", display: "flex", gap: "10px", alignItems: "flex-start" }}>
          <AlertTriangle size={16} color="#ef4444" style={{ marginTop: "2px" }} />
          <div>
            <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--deep-fjord)", marginBottom: "4px" }}>Hazard Proximity</div>
            <div style={{ fontSize: "11px", color: "var(--graphite-muted)", lineHeight: 1.4 }}>
              Active scanning for predicted encounters, collision vectors, and dynamic hazards along the selected route.
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", background: "var(--ice-paper-surface)", border: "1px solid var(--border-hairline)", borderRadius: "6px", opacity: 0.7 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Crosshair size={14} color="var(--graphite-muted)" />
            <span style={{ fontSize: "11px", color: "var(--graphite-muted)" }}>Future Risk Metrics</span>
          </div>
          <ChevronRight size={14} color="var(--graphite-muted)" />
        </div>
      </div>
    </div>
  );
}
