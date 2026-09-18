import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bell,
  BookOpen,
  ChevronDown,
  CircleHelp,
  Globe,
  Map as MapIcon,
  Maximize2,
  Settings2,
} from "lucide-react";
import DecisionPanel from "@/components/DecisionPanel";
import MissionSidebar from "@/components/MissionSidebar";
import OffshoreMap from "@/components/OffshoreMap";
import { fetchIcebergs, fetchRoutes } from "@/lib/api";
import {
  AppHeader,
  ForecastBadge,
  KpiStrip,
  MapOverlayLegend,
  Timeline,
  fmtForecastDateTime,
} from "@/components/OperationsChrome";
import {
  alerts,
  defaultLayers,
  forecastMeta,
  icebergs,
  locations,
  riskCells,
  routes as staticRoutes,
  tracks,
  trajectories,
  uncertainty,
  vessels,
} from "@/lib/offshore-mock-data";
import type { Coordinate, LayerKey, Priority } from "@/lib/offshore-types";

/**
 * Generates mock route geometry between origin and destination.
 * Visualization mechanism preserving existing algorithm offsets.
 */
function generateMockGeometry(
  origin: Coordinate,
  destination: Coordinate,
  style: "recommended" | "safest" | "fastest" | "fuel"
): Coordinate[] {
  const waypoints: Coordinate[] = [origin];
  const steps = style === "fastest" ? 3 : 4;

  const offsets: Record<string, number> = {
    recommended: 0,
    safest: -1.5,
    fastest: 1.5,
    fuel: 0.8,
  };
  const offset = offsets[style];

  for (let i = 1; i <= steps; i++) {
    const t = i / (steps + 1);
    const lat = origin.lat + (destination.lat - origin.lat) * t + offset * Math.sin(Math.PI * t);
    const lng = origin.lng + (destination.lng - origin.lng) * t + offset * 3 * Math.sin(Math.PI * t * 0.7);
    waypoints.push({ lat, lng });
  }

  waypoints.push(destination);
  return waypoints;
}

const routeStyles = ["recommended", "safest", "fastest", "fuel"] as const;

export default function Home() {
  const [layers, setLayers] = useState(defaultLayers);
  const [selectedRouteId, setSelectedRouteId] = useState(staticRoutes[0].id);
  const [selectedIcebergId, setSelectedIcebergId] = useState<string | null>("IB-221");
  const [selectedVesselId, setSelectedVesselId] = useState(vessels[0].id);
  const [priority, setPriority] = useState<Priority>("Safety First");
  const [origin, setOrigin] = useState<Coordinate>(locations[2].coordinate);
  const [destination, setDestination] = useState<Coordinate>(locations[3].coordinate);
  const [originLabel, setOriginLabel] = useState(locations[2].label);
  const [destinationLabel, setDestinationLabel] = useState(locations[3].label);
  const [pickMode, setPickMode] = useState<"origin" | "destination" | null>(null);
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [activeAlertId, setActiveAlertId] = useState(alerts[0].id);
  const [viewMode, setViewMode] = useState<"map" | "globe">("map");
  const [forecastHours, setForecastHours] = useState(16);
  const [selectedDate, setSelectedDate] = useState(new Date("2026-09-13"));
  const [isFullscreen, setIsFullscreen] = useState(false);

  const [liveIcebergs, setLiveIcebergs] = useState(icebergs);
  const [liveRoutes, setLiveRoutes] = useState(staticRoutes);

  useEffect(() => {
    fetchIcebergs()
      .then((data) => {
        if (data && data.length > 0) setLiveIcebergs(data);
      })
      .catch((err) => console.error("Failed to fetch live icebergs:", err));

    fetchRoutes()
      .then((data) => {
        if (data && data.length > 0) setLiveRoutes(data);
      })
      .catch((err) => console.error("Failed to fetch live routes:", err));
  }, []);

  // Routes with geometry regenerated from current origin/destination
  const routes = useMemo(
    () =>
      liveRoutes.map((route, i) => ({
        ...route,
        geometry: generateMockGeometry(origin, destination, routeStyles[i % routeStyles.length]),
      })),
    [origin, destination, liveRoutes]
  );

  const selectedRoute = useMemo(
    () => routes.find((route) => route.id === selectedRouteId) ?? routes[0],
    [selectedRouteId, routes]
  );

  const handleLocationChange = (kind: "origin" | "destination", label: string) => {
    const location = locations.find((item) => item.label === label);
    if (!location) return;
    if (kind === "origin") {
      setOrigin(location.coordinate);
      setOriginLabel(label);
    } else {
      setDestination(location.coordinate);
      setDestinationLabel(label);
    }
  };

  const handlePickCoordinate = useCallback(
    (coordinate: Coordinate) => {
      if (pickMode === "origin") {
        setOrigin(coordinate);
        setOriginLabel(`${coordinate.lat.toFixed(2)}°S, ${coordinate.lng.toFixed(2)}°W`);
      }
      if (pickMode === "destination") {
        setDestination(coordinate);
        setDestinationLabel(`${coordinate.lat.toFixed(2)}°S, ${coordinate.lng.toFixed(2)}°W`);
      }
      setPickMode(null);
    },
    [pickMode]
  );

  const handleFocus = useCallback((_coordinate: Coordinate) => {
    /* MapLibre focus */
  }, []);

  const handleToggleFullscreen = useCallback(() => {
    setIsFullscreen((v) => !v);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      }
    },
    [isFullscreen]
  );

  const routeTitle = useMemo(() => {
    const o = originLabel.replace(" Research Station", "").replace(" Research Port", "").replace(" Station", "");
    const d = destinationLabel.replace(" Research Station", "").replace(" Research Port", "").replace(" Station", "");
    return `${o} to ${d}`;
  }, [originLabel, destinationLabel]);

  const shortRouteTitle = useMemo(() => {
    const o = originLabel.split(" ")[0];
    const d = destinationLabel.split(" ")[0];
    return `${o} → ${d}`;
  }, [originLabel, destinationLabel]);

  /**
   * The single computed forecast date+time string derived from the user's
   * selected base date and the forecast-hour slider offset.
   * This is the source of truth for all UI elements that display the
   * currently selected forecast date: the header pill and the ForecastBadge.
   */
  const forecastDateTime = useMemo(
    () => fmtForecastDateTime(new Date(selectedDate.getTime() + forecastHours * 60 * 60 * 1000)),
    [selectedDate, forecastHours]
  );

  return (
    <div className="offshore-app" onKeyDown={handleKeyDown} tabIndex={-1}>
      {/* Top Header matching Image 2 */}
      <AppHeader
        onMenu={() => setMobileSidebar((value) => !value)}
        routeLabel={shortRouteTitle}
        forecastDateTime={forecastDateTime}
      />

      <div className="workspace">
        {/* Light Mission Configuration Panel (~270px) matching Image 2 */}
        <div className={`mission-config-wrapper ${mobileSidebar ? "open" : ""}`}>
          <MissionSidebar
            locations={locations}
            vessels={vessels}
            selectedVesselId={selectedVesselId}
            origin={{ label: originLabel, coordinate: origin }}
            destination={{ label: destinationLabel, coordinate: destination }}
            priority={priority}
            layers={layers}
            pickMode={pickMode}
            onVesselChange={setSelectedVesselId}
            onPriorityChange={setPriority}
            onLocationChange={handleLocationChange}
            onPickMode={setPickMode}
            onToggleLayer={(key: LayerKey) =>
              setLayers((current) => ({ ...current, [key]: !current[key] }))
            }
          />
        </div>

        {/* Dominant Map Workspace (Centerpiece) matching Image 2 */}
        <main className={`map-workspace ${isFullscreen ? "map-fullscreen" : ""}`}>
          {/* Map Header */}
          <div className="map-header">
            <div className="map-header-left">
              <span className="eyebrow">MISSION 08 · ROUTE PLANNING</span>
              <h1 className="map-passage-title">{routeTitle}</h1>
              <p className="map-passage-sub">
                Risk-aware passage planning · Antarctic Peninsula to Wilkes Land
              </p>
            </div>

            <div className="map-header-actions">
              <ForecastBadge forecast={forecastMeta} forecastDateTime={forecastDateTime} />

              {/* Map / Globe toggle matching Image 2 */}
              <div className="map-globe-toggle">
                <button
                  className={`toggle-tab-btn ${viewMode === "map" ? "active" : ""}`}
                  onClick={() => setViewMode("map")}
                  aria-label="Map view"
                  title="Map view"
                >
                  <MapIcon size={14} />
                  <span>Map</span>
                </button>
                <button
                  className={`toggle-tab-btn ${viewMode === "globe" ? "active" : ""}`}
                  onClick={() => setViewMode("globe")}
                  aria-label="Globe view"
                  title="Globe view"
                >
                  <Globe size={14} />
                  <span>Globe</span>
                </button>
              </div>

              <button className="control-icon-btn" aria-label="Open help" title="System Help">
                <CircleHelp size={15} />
              </button>
              <button className="control-icon-btn" aria-label="Open settings" title="Map Settings">
                <Settings2 size={15} />
              </button>
              <button
                className={`control-icon-btn ${isFullscreen ? "active" : ""}`}
                aria-label="Fullscreen map"
                title={isFullscreen ? "Exit Fullscreen (Esc)" : "Fullscreen Map"}
                onClick={handleToggleFullscreen}
              >
                <Maximize2 size={15} />
              </button>
            </div>
          </div>

          {/* Map Frame with light polar basemap and legend */}
          <div className={`map-frame ${isFullscreen ? "fullscreen" : ""}`}>
            <OffshoreMap
              layers={layers}
              icebergs={liveIcebergs}
              tracks={tracks}
              trajectories={trajectories}
              uncertainty={uncertainty}
              riskCells={riskCells}
              routes={routes}
              selectedRouteId={selectedRouteId}
              selectedIcebergId={selectedIcebergId}
              origin={origin}
              destination={destination}
              pickMode={pickMode}
              viewMode={viewMode}
              onSelectRoute={setSelectedRouteId}
              onSelectIceberg={setSelectedIcebergId}
              onPickCoordinate={handlePickCoordinate}
              onFocus={handleFocus}
            />
            <MapOverlayLegend />
          </div>

          {/* Time Control Bar matching Image 2 */}
          <Timeline
            forecast={forecastMeta}
            forecastHours={forecastHours}
            onForecastHoursChange={setForecastHours}
            selectedDate={selectedDate}
            onDateChange={setSelectedDate}
          />

          {/* Passage Overview / Environmental Metrics KPI Strip matching Image 2 */}
          <KpiStrip forecast={forecastMeta} />
        </main>

        {/* Right Route Options Panel (~290px) matching Image 2 */}
        <div className="route-options-wrapper">
          <DecisionPanel
            routes={routes}
            selectedRoute={selectedRoute}
            alerts={alerts}
            onSelectRoute={setSelectedRouteId}
            onFocusAlert={(alert) => {
              setActiveAlertId(alert.id);
              handleFocus(alert.location);
            }}
          />
        </div>
      </div>

      {/* Bottom Status Bar matching Image 2 */}
      <footer className="bottom-status-bar" aria-label="Operational status bar">
        <div className="status-bar-left">
          <div className="status-indicator-group">
            <span className="live-status-dot" />
            <span>Data stream connected</span>
          </div>
          <span className="status-v-divider">|</span>
          <span>Map projection: {viewMode === "globe" ? "Polar Orthographic" : "Antarctic Polar Stereographic"}</span>
          <span className="status-v-divider">|</span>
          <span>Selected alert: {activeAlertId.replace("alert-", "ALERT-")}</span>
        </div>

        <div className="status-bar-right">
          <span className="status-item-alert">
            <Bell size={13} /> 2 route-relevant alerts
          </span>
          <button className="status-icon-link" aria-label="Documentation" title="Documentation">
            <BookOpen size={13} />
          </button>
          <button className="status-icon-link" aria-label="Settings" title="Settings">
            <Settings2 size={13} />
          </button>
          <span className="status-active-route">
            {selectedRoute.name} selected <ChevronDown size={12} />
          </span>
        </div>
      </footer>
    </div>
  );
}
