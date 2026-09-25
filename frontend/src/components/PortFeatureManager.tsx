import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  Anchor,
  X,
  Compass,
  Navigation,
  MapPin,
  Search,
  Ship,
  Triangle,
  ChevronRight,
  ExternalLink,
  Crosshair,
} from "lucide-react";
import { useMap } from "./map-components";
import type { AppLocation, Coordinate, PortRecord, Vessel, Iceberg } from "@/lib/offshore-types";
import { searchPorts } from "@/lib/api";

// ─── HELPERS ─────────────────────────────────────────────────────────

export function formatNauticalCoords(lat: number, lon: number): string {
  const latDir = lat >= 0 ? "N" : "S";
  const lonDir = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lon).toFixed(4)}° ${lonDir}`;
}

export function formatPortName(name: string): string {
  if (!name) return "";
  // If all caps, convert to clean Title Case
  if (name === name.toUpperCase()) {
    return name
      .toLowerCase()
      .split(" ")
      .map((word) => {
        if (["rrs", "usns", "hms", "rv", "fsv"].includes(word)) return word.toUpperCase();
        return word.charAt(0).toUpperCase() + word.slice(1);
      })
      .join(" ");
  }
  return name;
}

export function getPortType(name: string, country: string): string {
  const upperName = (name || "").toUpperCase();
  const upperCountry = (country || "").toUpperCase();
  if (
    upperCountry.includes("ANTARCTICA") ||
    upperName.includes("STATION") ||
    upperName.includes("BASE") ||
    upperName.includes("RESEARCH")
  ) {
    return "Polar Research Station";
  }
  if (upperName.includes("TERMINAL") || upperName.includes("OFFSHORE")) {
    return "Offshore Marine Terminal";
  }
  return "Commercial Seaport";
}

// ─── HOVER POPUP CARD ─────────────────────────────────────────────────

export interface HoveredPortInfo {
  port: PortRecord;
  x: number;
  y: number;
}

export function PortHoverCard({ info }: { info: HoveredPortInfo | null }) {
  if (!info) return null;
  const { port, x, y } = info;
  const displayName = formatPortName(port.name);
  const portType = getPortType(port.name, port.country);
  const coordsFormatted = formatNauticalCoords(port.lat, port.lon);

  // Position smartly so it doesn't overflow screen
  const left = Math.min(Math.max(x + 12, 12), window.innerWidth - 240);
  const top = Math.max(y - 110, 16);

  return (
    <div
      className="port-hover-card"
      style={{
        position: "fixed",
        left: `${left}px`,
        top: `${top}px`,
        zIndex: 9999,
        pointerEvents: "none",
      }}
    >
      <div className="port-hover-inner">
        <div className="port-hover-header">
          <div className="port-hover-badge">
            <Anchor size={11} className="text-[#00F0FF]" />
            <span>PORT</span>
          </div>
          <span className="port-hover-type">{portType}</span>
        </div>

        <div className="port-hover-title">{displayName}</div>
        <div className="port-hover-country">{port.country || "International Waters"}</div>

        <div className="port-hover-coords">
          <MapPin size={10} className="text-[#7dd3fc]" />
          <span>{coordsFormatted}</span>
        </div>
      </div>
    </div>
  );
}

// ─── FULL PORT DETAILS CARD / PANEL ───────────────────────────────────

export function PortDetailCard({
  port,
  onClose,
  onCenter,
  onSetOrigin,
  onSetDestination,
}: {
  port: PortRecord | null;
  onClose: () => void;
  onCenter?: (port: PortRecord) => void;
  onSetOrigin?: (port: PortRecord) => void;
  onSetDestination?: (port: PortRecord) => void;
}) {
  if (!port) return null;

  const displayName = formatPortName(port.name);
  const portType = getPortType(port.name, port.country);
  const coordsFormatted = formatNauticalCoords(port.lat, port.lon);
  const isPolar = port.country === "Antarctica" || portType === "Polar Research Station";

  return (
    <div
      className="port-detail-panel"
      aria-label="Port Details Modal"
    >
      <div className="port-detail-header">
        <div className="port-detail-title-group">
          <div className="port-detail-icon-box">
            <Anchor size={17} className="text-[#00F0FF]" />
          </div>
          <div>
            <div className="port-detail-tag">INFRASTRUCTURE · MARITIME NODE</div>
            <h3 className="port-detail-name">{displayName}</h3>
          </div>
        </div>
        <button
          onClick={onClose}
          className="port-detail-close-btn"
          aria-label="Close port details"
          title="Close details"
        >
          <X size={15} />
        </button>
      </div>

      <div className="port-detail-body">
        <div className="port-detail-meta-row">
          <span className="port-detail-country-pill">{port.country || "International"}</span>
          <span className={`port-detail-type-pill ${isPolar ? "polar" : ""}`}>{portType}</span>
          {port.code && <span className="port-detail-code-pill">UN/LOCODE: {port.code}</span>}
        </div>

        <div className="port-detail-info-grid">
          <div className="port-info-cell">
            <span className="port-info-label">COORDINATES</span>
            <span className="port-info-val mono">{coordsFormatted}</span>
          </div>
          <div className="port-info-cell">
            <span className="port-info-label">LATITUDE / LONGITUDE</span>
            <span className="port-info-val mono">
              {port.lat.toFixed(4)}°, {port.lon.toFixed(4)}°
            </span>
          </div>
          <div className="port-info-cell">
            <span className="port-info-label">MARITIME REGION</span>
            <span className="port-info-val">
              {isPolar ? "Antarctic Polar Sector" : "Southern Ocean Gateway"}
            </span>
          </div>
          <div className="port-info-cell">
            <span className="port-info-label">OPERATIONAL STATUS</span>
            <span className="port-info-val text-[#10b981] flex items-center gap-1.5">
              <span className="port-status-dot" /> Active Harbor
            </span>
          </div>
        </div>

        {/* Quick Route Planning Actions */}
        <div className="port-detail-actions">
          {onCenter && (
            <button
              onClick={() => onCenter(port)}
              className="port-btn port-btn-center"
              title="Center camera on this port"
            >
              <Crosshair size={13} />
              <span>Center on Port</span>
            </button>
          )}

          {onSetOrigin && (
            <button
              onClick={() => onSetOrigin(port)}
              className="port-btn port-btn-secondary"
              title="Set this port as origin in mission planner"
            >
              <span>Set as Departure</span>
            </button>
          )}

          {onSetDestination && (
            <button
              onClick={() => onSetDestination(port)}
              className="port-btn port-btn-secondary"
              title="Set this port as destination in mission planner"
            >
              <span>Set as Target</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── UNIFIED SEARCH BAR (PORTS, VESSELS, ICEBERGS) ───────────────────

export interface SearchResultItem {
  id: string;
  type: "port" | "vessel" | "iceberg";
  title: string;
  subtitle: string;
  lat: number;
  lon: number;
  raw: any;
}

export function UnifiedSearchBar({
  ports = [],
  vessels = [],
  icebergs = [],
  onSelectPort,
  onSelectVessel,
  onSelectIceberg,
}: {
  ports: AppLocation[] | PortRecord[];
  vessels?: Vessel[];
  icebergs?: Iceberg[];
  onSelectPort: (port: PortRecord) => void;
  onSelectVessel?: (vesselId: string, coord: Coordinate) => void;
  onSelectIceberg?: (icebergId: string, coord: Coordinate) => void;
}) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [remotePorts, setRemotePorts] = useState<PortRecord[]>([]);
  const [isSearchingRemote, setIsSearchingRemote] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  // Normalize local ports array for instant sub-millisecond search
  const normalizedLocalPorts = useMemo<PortRecord[]>(() => {
    return ports.map((p: any, idx) => {
      if ("lon" in p && "lat" in p) {
        return {
          id: p.id || `port-${idx}`,
          name: p.name,
          country: p.country || "",
          lat: p.lat,
          lon: p.lon,
        };
      }
      return {
        id: `port-${idx}`,
        name: p.label.split(",")[0],
        country: p.country || (p.label.split(",")[1] || "").trim(),
        lat: p.coordinate.lat,
        lon: p.coordinate.lng,
      };
    });
  }, [ports]);

  // Debounced API search for comprehensive results
  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setRemotePorts([]);
      setIsSearchingRemote(false);
      return;
    }

    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    debounceTimerRef.current = setTimeout(async () => {
      setIsSearchingRemote(true);
      try {
        const res = await searchPorts(query.trim(), 0, 30);
        if (res && res.data) {
          setRemotePorts(
            res.data.map((item: any, idx: number) => ({
              id: `remote-${idx}-${item.name}`,
              name: item.name,
              country: item.country,
              lat: item.lat,
              lon: item.lon,
            }))
          );
        }
      } catch (err) {
        console.warn("Port API search error:", err);
      } finally {
        setIsSearchingRemote(false);
      }
    }, 200);

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [query]);

  // Combined matching results
  const results = useMemo<SearchResultItem[]>(() => {
    const qLower = query.toLowerCase().trim();
    const list: SearchResultItem[] = [];

    // If query is empty, show key Antarctic Research Stations & Major Gateway Ports as recommendations
    if (!qLower) {
      const priorityNames = [
        "cape town", "mcmurdo", "rothera", "casey", "ushuaia", "punta arenas",
        "hobart", "christchurch", "fremantle", "stanley", "dumont", "palmer"
      ];
      const seen = new Set<string>();

      for (const target of priorityNames) {
        const match = normalizedLocalPorts.find(
          (p) => p.name.toLowerCase().includes(target) || p.country.toLowerCase().includes(target)
        );
        if (match && !seen.has(match.id)) {
          seen.add(match.id);
          list.push({
            id: match.id,
            type: "port",
            title: formatPortName(match.name),
            subtitle: `${match.country || "Seaport"} · ${formatNauticalCoords(match.lat, match.lon)}`,
            lat: match.lat,
            lon: match.lon,
            raw: match,
          });
        }
      }

      for (const p of normalizedLocalPorts) {
        if (!seen.has(p.id)) {
          seen.add(p.id);
          list.push({
            id: p.id,
            type: "port",
            title: formatPortName(p.name),
            subtitle: `${p.country || "Seaport"} · ${formatNauticalCoords(p.lat, p.lon)}`,
            lat: p.lat,
            lon: p.lon,
            raw: p,
          });
        }
        if (list.length >= 8) break;
      }

      return list;
    }

    // 1. Matched Ports (combine remote search and instant local matches)
    const seenNames = new Set<string>();

    for (const p of remotePorts) {
      const key = `${p.name}-${p.country}`.toLowerCase();
      if (!seenNames.has(key)) {
        seenNames.add(key);
        list.push({
          id: p.id,
          type: "port",
          title: formatPortName(p.name),
          subtitle: `${p.country || "Seaport"} · ${formatNauticalCoords(p.lat, p.lon)}`,
          lat: p.lat,
          lon: p.lon,
          raw: p,
        });
      }
    }

    for (const p of normalizedLocalPorts) {
      if (
        p.name.toLowerCase().includes(qLower) ||
        p.country.toLowerCase().includes(qLower)
      ) {
        const key = `${p.name}-${p.country}`.toLowerCase();
        if (!seenNames.has(key)) {
          seenNames.add(key);
          list.push({
            id: p.id,
            type: "port",
            title: formatPortName(p.name),
            subtitle: `${p.country || "Seaport"} · ${formatNauticalCoords(p.lat, p.lon)}`,
            lat: p.lat,
            lon: p.lon,
            raw: p,
          });
        }
      }
      if (list.length >= 35) break;
    }

    // 2. Matched Vessels
    for (const v of vessels) {
      const vName = v.vessel_name || "";
      const vIce = v.ice_capability || "";
      const vFlag = v.flag_country || "";
      if (
        vName.toLowerCase().includes(qLower) ||
        vIce.toLowerCase().includes(qLower) ||
        vFlag.toLowerCase().includes(qLower)
      ) {
        list.push({
          id: v.vessel_id,
          type: "vessel",
          title: v.vessel_name,
          subtitle: `${v.vessel_type || "Vessel"} · ${vIce || "Polar"} · ${v.cruising_speed} kn`,
          lat: 0,
          lon: 0,
          raw: v,
        });
      }
    }

    // 3. Matched Icebergs
    for (const berg of icebergs) {
      if (berg.id.toLowerCase().includes(qLower)) {
        list.push({
          id: berg.id,
          type: "iceberg",
          title: `Iceberg ${berg.id}`,
          subtitle: `Size ${berg.sizeKm.toFixed(1)} km · Risk ${berg.risk}`,
          lat: berg.position.lat,
          lon: berg.position.lng,
          raw: berg,
        });
      }
    }

    return list.slice(0, 30);
  }, [query, remotePorts, normalizedLocalPorts, vessels, icebergs]);

  const handleSelect = (item: SearchResultItem) => {
    setIsOpen(false);
    setQuery("");
    if (item.type === "port") {
      onSelectPort(item.raw as PortRecord);
    } else if (item.type === "vessel" && onSelectVessel) {
      onSelectVessel(item.id, { lat: item.lat, lng: item.lon });
    } else if (item.type === "iceberg" && onSelectIceberg) {
      onSelectIceberg(item.id, { lat: item.lat, lng: item.lon });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => (prev - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[activeIndex]) {
        handleSelect(results[activeIndex]);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  return (
    <div className="unified-search-container" ref={containerRef}>
      <div className="unified-search-input-box">
        <Search size={14} className="search-icon-dim" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
            setActiveIndex(0);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search ports (e.g. Cape Town, Hobart, McMurdo)..."
          className="unified-search-input"
          aria-label="Search ports, vessels, or icebergs"
        />
        {query && (
          <button
            onClick={() => {
              setQuery("");
              inputRef.current?.focus();
            }}
            className="search-clear-btn"
            title="Clear search"
          >
            <X size={12} />
          </button>
        )}
      </div>

      {isOpen && (
        <div className="unified-search-dropdown">
          <div className="search-section-header">
            {!query.trim()
              ? "SUGGESTED ANTARCTIC GATEWAYS & PORTS"
              : `MATCHING PORTS & TARGETS (${results.length})`}
          </div>

          {isSearchingRemote && (
            <div className="search-status-bar">
              <span className="search-spinner" />
              <span>Querying 5,400+ world ports database...</span>
            </div>
          )}

          {results.length === 0 && !isSearchingRemote && query.trim() && (
            <div className="search-empty-state">
              <span>No ports found matching "{query}"</span>
            </div>
          )}

          {results.map((item, index) => {
            const isSelected = index === activeIndex;
            return (
              <div
                key={`${item.type}-${item.id}`}
                className={`search-result-row ${isSelected ? "selected" : ""}`}
                onClick={() => handleSelect(item)}
                onMouseEnter={() => setActiveIndex(index)}
              >
                <div className="search-row-icon">
                  {item.type === "port" && <Anchor size={14} className="text-[#38bdf8]" />}
                  {item.type === "vessel" && <Ship size={14} className="text-[#22c55e]" />}
                  {item.type === "iceberg" && <Triangle size={14} className="text-[#f59e0b]" />}
                </div>

                <div className="search-row-text">
                  <div className="search-row-title">
                    <span>{item.title}</span>
                    <span className={`search-type-tag ${item.type}`}>
                      {item.type.toUpperCase()}
                    </span>
                  </div>
                  <div className="search-row-subtitle">{item.subtitle}</div>
                </div>

                <ChevronRight size={13} className="search-row-arrow" />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── HIGH PERFORMANCE MAPLIBRE PORT LAYER ─────────────────────────────

export function PortsMapLayer({
  ports = [],
  visible = true,
  isNavMode = false,
  selectedPort,
  onHoverPort,
  onClickPort,
}: {
  ports: AppLocation[] | PortRecord[];
  visible?: boolean;
  isNavMode?: boolean;
  selectedPort: PortRecord | null;
  onHoverPort: (info: HoveredPortInfo | null) => void;
  onClickPort: (port: PortRecord) => void;
}) {
  const { map, isLoaded } = useMap();

  const sourceId = "offshore-global-ports-source";
  const glowLayerId = "offshore-global-ports-glow";
  const circleLayerId = "offshore-global-ports-circle";
  const symbolLayerId = "offshore-global-ports-symbol";
  const selectedPulseLayerId = "offshore-global-ports-selected";

  // Build GeoJSON FeatureCollection with memoization
  const geojson = useMemo(() => {
    const features = ports
      .map((p: any, idx) => {
        let lat: number;
        let lon: number;
        let name: string;
        let country: string;

        if ("lon" in p && "lat" in p) {
          lat = Number(p.lat);
          lon = Number(p.lon);
          name = p.name;
          country = p.country || "";
        } else if (p.coordinate) {
          lat = Number(p.coordinate.lat);
          lon = Number(p.coordinate.lng);
          name = p.label.split(",")[0];
          country = p.country || (p.label.split(",")[1] || "").trim();
        } else {
          return null;
        }

        if (isNaN(lat) || isNaN(lon)) return null;

        return {
          type: "Feature",
          id: idx,
          geometry: {
            type: "Point",
            coordinates: [lon, lat],
          },
          properties: {
            id: p.id || `port-${idx}`,
            name: name,
            country: country,
            lat: lat,
            lon: lon,
            type: getPortType(name, country),
            code: p.code || "",
          },
        };
      })
      .filter(Boolean);

    return {
      type: "FeatureCollection",
      features,
    };
  }, [ports]);

  const [styleEpoch, setStyleEpoch] = useState(0);

  // Re-sync layer when map style changes (e.g. Navigation vector map vs Polar Ocean map)
  useEffect(() => {
    if (!map) return;
    const handleStyleLoad = () => {
      setStyleEpoch((v) => v + 1);
    };
    map.on("style.load", handleStyleLoad);
    return () => {
      map.off("style.load", handleStyleLoad);
    };
  }, [map]);

  // Setup / Update layers on map
  useEffect(() => {
    if (!map || !isLoaded) return;

    // 1. Source
    const existingSource = map.getSource(sourceId) as any;
    if (!existingSource) {
      map.addSource(sourceId, {
        type: "geojson",
        data: geojson as any,
      });
    } else {
      existingSource.setData(geojson);
    }

    // 2. Halo Glow Layer
    if (!map.getLayer(glowLayerId)) {
      map.addLayer({
        id: glowLayerId,
        type: "circle",
        source: sourceId,
        paint: {
          "circle-color": isNavMode ? "#3B82F6" : "#00F0FF",
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1, 4,
            4, 7,
            8, 11,
            12, 15,
          ],
          "circle-opacity": isNavMode ? 0.35 : 0.22,
          "circle-blur": 0.8,
        },
      });
    } else {
      map.setPaintProperty(glowLayerId, "circle-color", isNavMode ? "#3B82F6" : "#00F0FF");
      map.setPaintProperty(glowLayerId, "circle-opacity", isNavMode ? 0.35 : 0.22);
    }

    // 3. Port Core Circle Layer - BLUE in navigation mode
    if (!map.getLayer(circleLayerId)) {
      map.addLayer({
        id: circleLayerId,
        type: "circle",
        source: sourceId,
        paint: {
          "circle-color": isNavMode
            ? "#2563EB"
            : [
                "case",
                ["==", ["get", "type"], "Polar Research Station"],
                "#38BDF8", // Cyan for polar research station
                "#0284C7", // Ocean blue for commercial harbor
              ],
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1, 2.5,
            4, 4.5,
            7, 6.5,
            12, isNavMode ? 7.5 : 9,
          ],
          "circle-stroke-width": isNavMode ? 2 : 1.5,
          "circle-stroke-color": "#FFFFFF",
        },
      });
    } else {
      map.setPaintProperty(
        circleLayerId,
        "circle-color",
        isNavMode
          ? "#2563EB"
          : [
              "case",
              ["==", ["get", "type"], "Polar Research Station"],
              "#38BDF8",
              "#0284C7",
            ]
      );
      map.setPaintProperty(circleLayerId, "circle-radius", [
        "interpolate",
        ["linear"],
        ["zoom"],
        1, 2.5,
        4, 4.5,
        7, 6.5,
        12, isNavMode ? 7.5 : 9,
      ]);
      map.setPaintProperty(circleLayerId, "circle-stroke-width", isNavMode ? 2 : 1.5);
      map.setPaintProperty(circleLayerId, "circle-stroke-color", "#FFFFFF");
    }

    // 4. Label Symbol Layer (at higher zoom levels)
    if (!map.getLayer(symbolLayerId)) {
      map.addLayer({
        id: symbolLayerId,
        type: "symbol",
        source: sourceId,
        minzoom: 5.5,
        layout: {
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Regular", "Arial Unicode MS Regular"],
          "text-size": [
            "interpolate",
            ["linear"],
            ["zoom"],
            5.5, 9,
            9, 12,
          ],
          "text-offset": [0, 1.3],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#F0F9FF",
          "text-halo-color": "#081426",
          "text-halo-width": 2,
        },
      });
    }

    // 5. Visibility
    const visibility = visible ? "visible" : "none";
    if (map.getLayer(glowLayerId)) map.setLayoutProperty(glowLayerId, "visibility", visibility);
    if (map.getLayer(circleLayerId)) map.setLayoutProperty(circleLayerId, "visibility", visibility);
    if (map.getLayer(symbolLayerId)) map.setLayoutProperty(symbolLayerId, "visibility", visibility);
  }, [map, isLoaded, geojson, visible, isNavMode, styleEpoch]);

  // Selected Port Highlight Ring
  useEffect(() => {
    if (!map || !isLoaded) return;

    const highlightSourceId = "offshore-selected-port-source";

    if (!selectedPort) {
      if (map.getLayer(selectedPulseLayerId)) map.removeLayer(selectedPulseLayerId);
      if (map.getSource(highlightSourceId)) map.removeSource(highlightSourceId);
      return;
    }

    const highlightGeojson = {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [selectedPort.lon, selectedPort.lat],
          },
          properties: selectedPort,
        },
      ],
    };

    if (!map.getSource(highlightSourceId)) {
      map.addSource(highlightSourceId, {
        type: "geojson",
        data: highlightGeojson as any,
      });
    } else {
      (map.getSource(highlightSourceId) as any).setData(highlightGeojson);
    }

    if (!map.getLayer(selectedPulseLayerId)) {
      map.addLayer({
        id: selectedPulseLayerId,
        type: "circle",
        source: highlightSourceId,
        paint: {
          "circle-color": "transparent",
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1, 8,
            6, 14,
            12, 20,
          ],
          "circle-stroke-width": 3,
          "circle-stroke-color": "#00F0FF",
          "circle-stroke-opacity": 0.9,
        },
      });
    }
  }, [map, isLoaded, selectedPort]);

  // Event Listeners: Mouseenter / Mouseleave / Click
  useEffect(() => {
    if (!map || !isLoaded || !visible) return;

    const handleMouseEnter = (e: any) => {
      map.getCanvas().style.cursor = "pointer";
      if (e.features && e.features.length > 0) {
        const feat = e.features[0];
        const props = feat.properties;
        const coords = feat.geometry.coordinates;

        onHoverPort({
          port: {
            id: props.id || String(props.name),
            name: props.name,
            country: props.country,
            lat: Number(props.lat || coords[1]),
            lon: Number(props.lon || coords[0]),
            port_type: props.type,
            code: props.code,
          },
          x: e.point.x,
          y: e.point.y,
        });
      }
    };

    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
      onHoverPort(null);
    };

    const handleCanvasMouseOut = (e: MouseEvent) => {
      if (!e.relatedTarget) {
        handleMouseLeave();
      }
    };

    const handleMapMouseMove = (e: any) => {
      const features = map.queryRenderedFeatures(e.point, { layers: [circleLayerId] });
      if (!features || features.length === 0) {
        handleMouseLeave();
      }
    };

    const handleMapClick = (e: any) => {
      const features = map.queryRenderedFeatures(e.point, { layers: [circleLayerId] });
      if (!features || features.length === 0) {
        onClickPort(null as any);
      }
    };

    const handleClick = (e: any) => {
      if (e.features && e.features.length > 0) {
        const feat = e.features[0];
        const props = feat.properties;
        const coords = feat.geometry.coordinates;

        const portRecord: PortRecord = {
          id: props.id || String(props.name),
          name: props.name,
          country: props.country,
          lat: Number(props.lat || coords[1]),
          lon: Number(props.lon || coords[0]),
          port_type: props.type,
          code: props.code,
        };

        onClickPort(portRecord);
      }
    };

    map.on("mouseenter", circleLayerId, handleMouseEnter);
    map.on("mouseleave", circleLayerId, handleMouseLeave);
    map.on("click", circleLayerId, handleClick);
    map.on("mousemove", handleMapMouseMove);
    map.on("movestart", handleMouseLeave);
    map.on("zoomstart", handleMouseLeave);
    map.on("click", handleMapClick);

    const canvas = map.getCanvas();
    canvas.addEventListener("mouseleave", handleMouseLeave);
    canvas.addEventListener("mouseout", handleCanvasMouseOut);

    return () => {
      map.off("mouseenter", circleLayerId, handleMouseEnter);
      map.off("mouseleave", circleLayerId, handleMouseLeave);
      map.off("click", circleLayerId, handleClick);
      map.off("mousemove", handleMapMouseMove);
      map.off("movestart", handleMouseLeave);
      map.off("zoomstart", handleMouseLeave);
      map.off("click", handleMapClick);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
      canvas.removeEventListener("mouseout", handleCanvasMouseOut);
      map.getCanvas().style.cursor = "";
    };
  }, [map, isLoaded, visible, onHoverPort, onClickPort]);

  return null;
}
