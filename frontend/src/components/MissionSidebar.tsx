import React, { useState, useMemo, useEffect, useRef, useCallback } from "react";
import {
  Calendar,
  ChevronDown,
  Clock,
  Layers,
  MapPin,
  Settings2,
  Shield,
  Ship,
} from "lucide-react";
import type { AppLocation, LayerKey, Priority, Vessel } from "@/lib/offshore-types";
import { searchPorts } from "@/lib/api";

function SearchablePortSelect({
  id,
  value,
  locations,
  onChange,
}: {
  id: string;
  value: string;
  locations: AppLocation[];
  onChange: (loc: AppLocation) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<AppLocation[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced backend search
  const doSearch = useCallback((term: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!term.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }
    setIsSearching(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchPorts(term, 0, 100);
        if (data && data.data) {
          setSearchResults(
            data.data.map((p: any) => ({
              label: `${p.name}, ${p.country}`,
              coordinate: { lat: p.lat, lng: p.lon },
              country: p.country,
            }))
          );
        }
      } catch (err) {
        console.error("Port search failed:", err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 250);
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value;
    setSearchTerm(term);
    doSearch(term);
  };

  // Show backend results when searching, otherwise show local locations
  const displayList = searchTerm.trim() ? searchResults : locations;

  const displayValue = useMemo(() => {
    const loc = locations.find((l) => l.label === value);
    if (!loc) return value;
    return loc.country === "Antarctica" ? `${loc.label} {Antarctica}` : loc.label;
  }, [value, locations]);

  return (
    <div className="select-wrapper searchable-select-container" ref={containerRef} style={{ position: "relative" }}>
      <div
        id={id}
        className="field-select"
        style={{ cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between" }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {displayValue}
        </span>
        <ChevronDown size={14} style={{ opacity: 0.5 }} />
      </div>

      {isOpen && (
        <div
          className="searchable-dropdown-menu"
          style={{
            position: "absolute", top: "100%", left: 0, right: 0, zIndex: 50,
            backgroundColor: "#F3F1EA", border: "1px solid #DCE5E5", borderRadius: "6px",
            marginTop: "4px", boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
            display: "flex", flexDirection: "column", maxHeight: "250px",
          }}
        >
          <div style={{ padding: "8px", borderBottom: "1px solid #DCE5E5" }}>
            <input
              type="text"
              placeholder="Search all 5,400+ ports..."
              value={searchTerm}
              onChange={handleSearchChange}
              onClick={(e) => e.stopPropagation()}
              autoFocus
              style={{
                width: "100%", padding: "6px 8px", fontSize: "13px",
                border: "1px solid #DCE5E5", borderRadius: "4px",
                backgroundColor: "#FFFFFF", color: "#183B43",
              }}
            />
          </div>
          <div style={{ overflowY: "auto", padding: "4px 0" }}>
            {isSearching && (
              <div style={{ padding: "8px 12px", fontSize: "13px", color: "#8A9B9D" }}>Searching...</div>
            )}
            {!isSearching && !searchTerm.trim() && (
              <div style={{ padding: "4px 12px 8px 12px", fontSize: "11px", color: "#8A9B9D", fontWeight: 600, letterSpacing: "0.5px", textTransform: "uppercase" }}>
                Showing 50 of {locations.length.toLocaleString()} ports — type to search
              </div>
            )}
            {!isSearching && searchTerm.trim() && displayList.length > 0 && (
              <div style={{ padding: "4px 12px 8px 12px", fontSize: "11px", color: "#8A9B9D", fontWeight: 600, letterSpacing: "0.5px", textTransform: "uppercase" }}>
                {displayList.length} results for '{searchTerm}'
              </div>
            )}
            
            {!isSearching && (searchTerm.trim() ? displayList : displayList.slice(0, 50)).map((loc) => {
              const display = loc.country === "Antarctica" ? `${loc.label} {Antarctica}` : loc.label;
              return (
                <div
                  key={loc.label}
                  onClick={() => {
                    onChange(loc);
                    setIsOpen(false);
                    setSearchTerm("");
                    setSearchResults([]);
                  }}
                  style={{
                    padding: "6px 12px", fontSize: "13px", cursor: "pointer",
                    backgroundColor: loc.label === value ? "#DCE5E5" : "transparent",
                    color: "#183B43"
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#DCE5E5")}
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor = loc.label === value ? "#DCE5E5" : "transparent")
                  }
                >
                  {display}
                </div>
              );
            })}
            {!isSearching && displayList.length === 0 && searchTerm.trim() && (
              <div style={{ padding: "8px 12px", fontSize: "13px", color: "#8A9B9D" }}>No ports found</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

type MissionSidebarProps = {
  locations: AppLocation[];
  vessels: Vessel[];
  selectedVesselId: string;
  origin: AppLocation;
  destination: AppLocation;
  priority: Priority;
  layers: Record<LayerKey, boolean>;
  pickMode: "origin" | "destination" | null;
  onVesselChange: (id: string) => void;
  onPriorityChange: (priority: Priority) => void;
  onLocationChange: (kind: "origin" | "destination", loc: AppLocation) => void;
  onPickMode: (mode: "origin" | "destination" | null) => void;
  onToggleLayer: (key: LayerKey) => void;
  isCalculating?: boolean;
  onCalculateRoute?: () => void;
  routeError?: string | null;
  customVesselConfig?: Vessel | null;
  onCustomVesselConfigChange: (config: Vessel | null) => void;
};

const layerRows: Array<{ key: LayerKey; label: string; color: string }> = [
  { key: "seaIce", label: "Sea-ice concentration", color: "#527C78" },
  { key: "forecast", label: "Forecast model · 72h", color: "#6C8E91" },
  { key: "icebergs", label: "Iceberg detections", color: "#C66B45" },
  { key: "tracks", label: "Historical tracks", color: "#596A6D" },
  { key: "trajectories", label: "Predicted trajectories", color: "#3B5F66" },
  { key: "uncertainty", label: "Uncertainty boundary", color: "#8A9B9D" },
  { key: "risk", label: "Dynamic risk surface", color: "#C66B45" },
  { key: "routes", label: "Candidate routes", color: "#527C78" },
  { key: "vessel", label: "Vessel position", color: "#183B43" },
];

export default function MissionSidebar({
  locations,
  vessels,
  selectedVesselId,
  origin,
  destination,
  priority,
  layers,
  pickMode,
  onVesselChange,
  onPriorityChange,
  onLocationChange,
  onPickMode,
  onToggleLayer,
  isCalculating,
  onCalculateRoute,
  routeError,
  customVesselConfig,
  onCustomVesselConfigChange,
}: MissionSidebarProps) {
  const [openMissionSetup, setOpenMissionSetup] = useState(true);
  const [openVesselProfile, setOpenVesselProfile] = useState(false);
  const [openMapLayers, setOpenMapLayers] = useState(false);

  const currentVessel = vessels.find((item) => item.vessel_id === selectedVesselId) ?? vessels[0];

  return (
    <aside className="mission-config-panel" aria-label="Mission Configuration">
      {/* Eyebrow & Main Title matching Image 2 */}
      <div className="config-header">
        <span className="config-eyebrow">MISSION CONFIGURATION</span>
        <h2 className="config-title">Plan a passage</h2>
        <p className="config-desc">
          Set the operating context before comparing route recommendations.
        </p>
      </div>

      <div className="config-body">
        {/* Accordion 1: Mission setup (Expanded by default) */}
        <section className="config-section">
          <button
            type="button"
            className="section-header-btn"
            onClick={() => setOpenMissionSetup(!openMissionSetup)}
            aria-expanded={openMissionSetup}
          >
            <div className="section-header-left">
              <Settings2 size={14} className="section-icon" />
              <span>Mission setup</span>
            </div>
            <ChevronDown
              size={14}
              className={`chevron-icon ${openMissionSetup ? "rotated" : ""}`}
            />
          </button>

          {openMissionSetup && (
            <div className="section-content">
              {/* Origin */}
              <div className="field-group">
                <label htmlFor="origin-select" className="field-label">
                  Origin
                </label>
                <SearchablePortSelect
                  id="origin-select"
                  value={origin.label}
                  locations={locations}
                  onChange={(loc) => onLocationChange("origin", loc)}
                />
                <div className="pick-row">
                  <button
                    type="button"
                    className={`pick-map-btn ${pickMode === "origin" ? "active" : ""}`}
                    onClick={() => onPickMode(pickMode === "origin" ? null : "origin")}
                  >
                    <MapPin size={12} />
                    <span>Pick on map</span>
                  </button>
                </div>
              </div>

              {/* Destination */}
              <div className="field-group">
                <label htmlFor="dest-select" className="field-label">
                  Destination
                </label>
                <SearchablePortSelect
                  id="dest-select"
                  value={destination.label}
                  locations={locations}
                  onChange={(loc) => onLocationChange("destination", loc)}
                />
                <div className="pick-row">
                  <button
                    type="button"
                    className={`pick-map-btn ${pickMode === "destination" ? "active" : ""}`}
                    onClick={() => onPickMode(pickMode === "destination" ? null : "destination")}
                  >
                    <MapPin size={12} />
                    <span>Pick on map</span>
                  </button>
                </div>
              </div>

              {/* Departure & UTC Time */}
              <div className="split-fields-row">
                <div className="field-group flex-1">
                  <label htmlFor="dep-date" className="field-label">
                    Departure
                  </label>
                  <div className="input-icon-box">
                    <input
                      id="dep-date"
                      type="date"
                      defaultValue="2026-09-13"
                      className="field-input"
                    />
                    <Calendar size={13} className="field-input-icon" />
                  </div>
                </div>

                <div className="field-group flex-1">
                  <label htmlFor="dep-time" className="field-label">
                    UTC time
                  </label>
                  <div className="input-icon-box">
                    <input
                      id="dep-time"
                      type="time"
                      defaultValue="12:00"
                      className="field-input"
                    />
                    <Clock size={13} className="field-input-icon" />
                  </div>
                </div>
              </div>

              {/* Navigation priority */}
              <div className="field-group">
                <label htmlFor="priority-select" className="field-label">
                  Navigation priority
                </label>
                <div className="select-wrapper">
                  <select
                    id="priority-select"
                    className="field-select"
                    value={priority}
                    onChange={(e) => onPriorityChange(e.target.value as Priority)}
                  >
                    <option value="Safety First">Safety First</option>
                    <option value="Balanced">Balanced</option>
                    <option value="Fuel Efficient">Fuel Efficient</option>
                    <option value="Time Efficient">Time Efficient</option>
                  </select>
                </div>

                {/* Light green callout box matching Image 2 */}
                <div className="priority-callout-box">
                  <Shield size={14} className="callout-icon" />
                  <span className="callout-text">
                    {priority === "Safety First" && "Minimizes predicted environmental risk."}
                    {priority === "Balanced" && "Balances transit schedule with sea ice exposure."}
                    {priority === "Fuel Efficient" && "Emphasizes minimum fuel consumption curve."}
                    {priority === "Time Efficient" && "Prioritizes direct navigational corridor."}
                  </span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Accordion 2: Vessel profile */}
        <section className="config-section">
          <button
            type="button"
            className="section-header-btn"
            onClick={() => setOpenVesselProfile(!openVesselProfile)}
            aria-expanded={openVesselProfile}
          >
            <div className="section-header-left">
              <Ship size={14} className="section-icon" />
              <span>Vessel profile</span>
            </div>
            <ChevronDown
              size={14}
              className={`chevron-icon ${openVesselProfile ? "rotated" : ""}`}
            />
          </button>

          {openVesselProfile && (
            <div className="section-content">
              <div className="field-group">
                <label htmlFor="vessel-select" className="field-label">
                  Selected Vessel
                </label>
                <div className="select-wrapper">
                  <select
                    id="vessel-select"
                    className="field-select"
                    value={selectedVesselId}
                    onChange={(e) => onVesselChange(e.target.value)}
                  >
                    {vessels.length === 0 ? (
                      <option value="" disabled>
                        No vessels available
                      </option>
                    ) : (
                      vessels.map((v) => (
                        <option key={v.vessel_id} value={v.vessel_id}>
                          {v.vessel_name}
                        </option>
                      ))
                    )}
                  </select>
                </div>
              </div>

              {currentVessel && (
                <div className="vessel-specs-strip">
                  <div className="vessel-spec-cell">
                    <span className="spec-tag">ICE CLASS</span>
                    <span className="spec-val">{currentVessel.ice_capability || "N/A"}</span>
                  </div>
                  <div className="vessel-spec-cell">
                    <span className="spec-tag">CRUISING</span>
                    <span className="spec-val">{customVesselConfig ? customVesselConfig.cruising_speed : currentVessel.cruising_speed} kn</span>
                  </div>
                  <div className="vessel-spec-cell">
                    <span className="spec-tag">BURN RATE</span>
                    <span className="spec-val">{(customVesselConfig ? customVesselConfig.fuel_consumption : currentVessel.fuel_consumption).toLocaleString()} t/d</span>
                  </div>
                </div>
              )}

              {currentVessel && (
                <div className="field-group" style={{ marginTop: "12px" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px" }}>
                    <input 
                      type="checkbox" 
                      checked={!!customVesselConfig}
                      onChange={(e) => {
                        if (e.target.checked) {
                          onCustomVesselConfigChange({ ...currentVessel });
                        } else {
                          onCustomVesselConfigChange(null);
                        }
                      }}
                    />
                    Enable Custom Overrides
                  </label>
                  
                  {customVesselConfig && (
                    <div style={{ marginTop: "8px", padding: "10px", backgroundColor: "#fff8e6", border: "1px solid #f59e0b", borderRadius: "4px" }}>
                      <div style={{ color: "#d97706", fontSize: "11px", fontWeight: "bold", marginBottom: "8px" }}>
                        ⚠️ {currentVessel.vessel_name} — simulated configuration
                      </div>
                      <div className="split-fields-row">
                        <div className="field-group flex-1">
                          <label className="field-label" style={{ fontSize: "11px" }}>Speed (kn)</label>
                          <input 
                            type="number" 
                            className="field-input" 
                            value={customVesselConfig.cruising_speed} 
                            onChange={(e) => onCustomVesselConfigChange({ ...customVesselConfig, cruising_speed: parseFloat(e.target.value) || 0 })}
                          />
                        </div>
                        <div className="field-group flex-1">
                          <label className="field-label" style={{ fontSize: "11px" }}>Fuel (t/d)</label>
                          <input 
                            type="number" 
                            className="field-input" 
                            value={customVesselConfig.fuel_consumption} 
                            onChange={(e) => onCustomVesselConfigChange({ ...customVesselConfig, fuel_consumption: parseFloat(e.target.value) || 0 })}
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </section>

        {/* Accordion 3: Map layers */}
        <section className="config-section">
          <button
            type="button"
            className="section-header-btn"
            onClick={() => setOpenMapLayers(!openMapLayers)}
            aria-expanded={openMapLayers}
          >
            <div className="section-header-left">
              <Layers size={14} className="section-icon" />
              <span>Map layers</span>
            </div>
            <ChevronDown
              size={14}
              className={`chevron-icon ${openMapLayers ? "rotated" : ""}`}
            />
          </button>

          {openMapLayers && (
            <div className="section-content">
              <div className="layer-options-list">
                {layerRows.map((row) => (
                  <label key={row.key} className="layer-row-item">
                    <span
                      className="layer-row-swatch"
                      style={{ backgroundColor: row.color }}
                    />
                    <span className="layer-row-title">{row.label}</span>
                    <input
                      type="checkbox"
                      className="layer-checkbox"
                      checked={layers[row.key]}
                      onChange={() => onToggleLayer(row.key)}
                    />
                  </label>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>

      <div style={{ padding: "16px", marginTop: "auto" }}>
        {routeError && (
          <div style={{ color: "#ef4444", fontSize: "12px", marginBottom: "8px", padding: "8px", backgroundColor: "#fef2f2", borderRadius: "4px" }}>
            {routeError}
          </div>
        )}
        <button
          onClick={onCalculateRoute}
          disabled={isCalculating}
          style={{
            width: "100%",
            padding: "12px",
            backgroundColor: isCalculating ? "#6C8E91" : "#183B43",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: isCalculating ? "not-allowed" : "pointer",
            fontWeight: "bold"
          }}
        >
          {isCalculating ? "Calculating Route..." : "Calculate Route"}
        </button>
      </div>
    </aside>
  );
}
