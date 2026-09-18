import { useState } from "react";
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
  onLocationChange: (kind: "origin" | "destination", label: string) => void;
  onPickMode: (mode: "origin" | "destination" | null) => void;
  onToggleLayer: (key: LayerKey) => void;
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
}: MissionSidebarProps) {
  const [openMissionSetup, setOpenMissionSetup] = useState(true);
  const [openVesselProfile, setOpenVesselProfile] = useState(false);
  const [openMapLayers, setOpenMapLayers] = useState(false);

  const currentVessel = vessels.find((item) => item.id === selectedVesselId) ?? vessels[0];

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
                <div className="select-wrapper">
                  <select
                    id="origin-select"
                    className="field-select"
                    value={origin.label}
                    onChange={(e) => onLocationChange("origin", e.target.value)}
                  >
                    {locations.map((loc) => (
                      <option key={loc.label} value={loc.label}>
                        {loc.label}
                      </option>
                    ))}
                  </select>
                </div>
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
                <div className="select-wrapper">
                  <select
                    id="dest-select"
                    className="field-select"
                    value={destination.label}
                    onChange={(e) => onLocationChange("destination", e.target.value)}
                  >
                    {locations.map((loc) => (
                      <option key={loc.label} value={loc.label}>
                        {loc.label}
                      </option>
                    ))}
                  </select>
                </div>
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
                    {vessels.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="vessel-specs-strip">
                <div className="vessel-spec-cell">
                  <span className="spec-tag">ICE CLASS</span>
                  <span className="spec-val">{currentVessel.iceClass}</span>
                </div>
                <div className="vessel-spec-cell">
                  <span className="spec-tag">CRUISING</span>
                  <span className="spec-val">{currentVessel.cruisingSpeedKn} kn</span>
                </div>
                <div className="vessel-spec-cell">
                  <span className="spec-tag">BURN RATE</span>
                  <span className="spec-val">{currentVessel.fuelBurnLph.toLocaleString()} L/h</span>
                </div>
              </div>
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
    </aside>
  );
}
