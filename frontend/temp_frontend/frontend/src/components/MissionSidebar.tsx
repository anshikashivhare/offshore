import { useState } from "react";
import { Anchor, ChevronDown, Crosshair, Layers3, MapPin, Radio, ShipWheel, SlidersHorizontal } from "lucide-react";
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
  { key: "seaIce", label: "Current sea ice", color: "#65c4b7" }, { key: "forecast", label: "Forecast · 72 h", color: "#73b9d8" }, { key: "icebergs", label: "Iceberg detections", color: "#f4b979" }, { key: "tracks", label: "Historical tracks", color: "#a4aeb8" }, { key: "trajectories", label: "Predicted trajectories", color: "#d59ce2" }, { key: "uncertainty", label: "Uncertainty envelope", color: "#c08fd0" }, { key: "risk", label: "Dynamic risk surface", color: "#ee7f69" }, { key: "routes", label: "Candidate routes", color: "#66d2c3" }, { key: "vessel", label: "Vessel position", color: "#e5f4ee" },
];

export default function MissionSidebar({ locations, vessels, selectedVesselId, origin, destination, priority, layers, pickMode, onVesselChange, onPriorityChange, onLocationChange, onPickMode, onToggleLayer }: MissionSidebarProps) {
  const [openSection, setOpenSection] = useState<"mission" | "layers" | "vessel">("mission");
  const vessel = vessels.find((item) => item.id === selectedVesselId) ?? vessels[0];
  const toggleSection = (section: "mission" | "layers" | "vessel") => setOpenSection(openSection === section ? "mission" : section);
  return (
    <aside className="mission-sidebar">
      <div className="sidebar-intro"><span className="eyebrow">MISSION CONFIGURATION</span><h2>Plan a passage</h2><p>Set the operating context before comparing route recommendations.</p></div>
      <section className="side-section"><button className="section-heading" onClick={() => toggleSection("mission")}><span><Crosshair size={15} /> Mission setup</span><ChevronDown size={14} className={openSection === "mission" ? "rotated" : ""} /></button>{openSection === "mission" && <div className="section-body mission-form">
        <label>Origin<select value={origin.label} onChange={(event) => onLocationChange("origin", event.target.value)}>{locations.map((location) => <option key={location.label}>{location.label}</option>)}</select></label><button className={`map-pick ${pickMode === "origin" ? "active" : ""}`} onClick={() => onPickMode(pickMode === "origin" ? null : "origin")}><MapPin size={13} /> Pick on map</button>
        <label>Destination<select value={destination.label} onChange={(event) => onLocationChange("destination", event.target.value)}>{locations.map((location) => <option key={location.label}>{location.label}</option>)}</select></label><button className={`map-pick ${pickMode === "destination" ? "active" : ""}`} onClick={() => onPickMode(pickMode === "destination" ? null : "destination")}><MapPin size={13} /> Pick on map</button>
        <div className="field-grid"><label>Departure<input type="date" defaultValue="2026-09-13" /></label><label>UTC time<input type="time" defaultValue="12:00" /></label></div>
        <label>Navigation priority<select value={priority} onChange={(event) => onPriorityChange(event.target.value as Priority)}><option>Safety First</option><option>Balanced</option><option>Fuel Efficient</option><option>Time Efficient</option></select></label>
        <div className="priority-note"><SlidersHorizontal size={13} /><span>{priority === "Safety First" ? "Minimizes predicted environmental risk." : priority === "Fuel Efficient" ? "Emphasizes estimated fuel consumption." : priority === "Time Efficient" ? "Emphasizes total transit time." : "Balances time, fuel and predicted risk."}</span></div>
      </div>}</section>
      <section className="side-section"><button className="section-heading" onClick={() => toggleSection("vessel")}><span><ShipWheel size={15} /> Vessel profile</span><ChevronDown size={14} className={openSection === "vessel" ? "rotated" : ""} /></button>{openSection === "vessel" && <div className="section-body vessel-form"><label>Selected vessel<select value={selectedVesselId} onChange={(event) => onVesselChange(event.target.value)}>{vessels.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><div className="vessel-summary"><div className="vessel-icon"><Anchor size={18} /></div><div><strong>{vessel.type}</strong><span>{vessel.iceClass}</span></div></div><div className="vessel-specs"><span><b>{vessel.cruisingSpeedKn}</b> kn<span>cruising</span></span><span><b>{vessel.fuelBurnLph.toLocaleString()}</b> L/h<span>fuel burn</span></span></div></div>}</section>
      <section className="side-section"><button className="section-heading" onClick={() => toggleSection("layers")}><span><Layers3 size={15} /> Map layers</span><ChevronDown size={14} className={openSection === "layers" ? "rotated" : ""} /></button>{openSection === "layers" && <div className="section-body layer-list">{layerRows.map((row) => <label className="layer-row" key={row.key}><span className="layer-name"><i style={{ background: row.color }} />{row.label}</span><input type="checkbox" checked={layers[row.key]} onChange={() => onToggleLayer(row.key)} /></label>)}</div>}</section>
      <div className="sidebar-foot"><Radio size={13} /><span>Mock data mode</span><em>API-ready</em></div>
    </aside>
  );
}
