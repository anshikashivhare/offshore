import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bell,
  ChevronDown,
  CircleHelp,
  Globe,
  Map as MapIcon,
  Maximize2,
  PanelRight,
  Route as RouteIcon,
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
 * This is a frontend-only visualization mechanism — NOT a real
 * maritime route optimization. Designed to be replaced by a
 * real routing service/model when available.
 */
function generateMockGeometry(
  origin: Coordinate,
  destination: Coordinate,
  style: "recommended" | "safest" | "fastest" | "fuel"
): Coordinate[] {
  const waypoints: Coordinate[] = [origin];
  const steps = style === "fastest" ? 3 : 4;

  // Offset factor to create visual variety between routes
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
        setOriginLabel(`${coordinate.lat.toFixed(2)}°, ${coordinate.lng.toFixed(2)}°`);
      }
      if (pickMode === "destination") {
        setDestination(coordinate);
        setDestinationLabel(`${coordinate.lat.toFixed(2)}°, ${coordinate.lng.toFixed(2)}°`);
      }
      setPickMode(null);
    },
    [pickMode]
  );

  const handleFocus = useCallback((_coordinate: Coordinate) => {
    /* MapLibre pan/zoom is handled via map controls. Focus hook is API-ready. */
  }, []);

  const handleToggleFullscreen = useCallback(() => {
    setIsFullscreen((v) => !v);
  }, []);

  // Listen for ESC key to exit fullscreen
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      }
    },
    [isFullscreen]
  );

  // Dynamic title from origin/destination labels
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

  return (
    <div className="offshore-app" onKeyDown={handleKeyDown} tabIndex={-1}>
      <AppHeader onMenu={() => setMobileSidebar((value) => !value)} routeLabel={shortRouteTitle} />
      <div className="workspace">
        <div className={`sidebar-drawer ${mobileSidebar ? "open" : ""}`}>
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
        <main className={`map-workspace ${isFullscreen ? "map-fullscreen" : ""}`}>
          <div className="map-header">
            <div>
              <span className="eyebrow">MISSION 08 · ROUTE PLANNING</span>
              <h1>{routeTitle}</h1>
              <p>Risk-aware passage planning · Antarctic Peninsula to Wilkes Land</p>
            </div>
            <div className="map-header-actions">
              <ForecastBadge forecast={forecastMeta} />
              {/* Map/Globe toggle */}
              <div className="view-toggle">
                <button
                  className={`view-toggle-btn ${viewMode === "map" ? "active" : ""}`}
                  onClick={() => setViewMode("map")}
                  aria-label="Map view"
                  title="Map view"
                >
                  <MapIcon size={14} />
                  <span>Map</span>
                </button>
                <button
                  className={`view-toggle-btn ${viewMode === "globe" ? "active" : ""}`}
                  onClick={() => setViewMode("globe")}
                  aria-label="Globe view"
                  title="Globe view"
                >
                  <Globe size={14} />
                  <span>Globe</span>
                </button>
              </div>
              <button className="icon-button" aria-label="Open help">
                <CircleHelp size={16} />
              </button>
              <button className="icon-button" aria-label="Open settings">
                <Settings2 size={16} />
              </button>
              <button
                className={`icon-button ${isFullscreen ? "active" : ""}`}
                aria-label="Fullscreen map"
                onClick={handleToggleFullscreen}
              >
                <Maximize2 size={16} />
              </button>
            </div>
          </div>
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
          <Timeline
            forecast={forecastMeta}
            forecastHours={forecastHours}
            onForecastHoursChange={setForecastHours}
            selectedDate={selectedDate}
            onDateChange={setSelectedDate}
          />
          <KpiStrip forecast={forecastMeta} />
        </main>
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
      <div className="bottom-status">
        <span>
          <i className="status-live" /> Data stream connected
        </span>
        <span>
          Map projection: {viewMode === "globe" ? "Globe" : "Mercator"}
        </span>
        <span>
          Selected alert: {activeAlertId.replace("alert-", "ALERT-")}
        </span>
        <span className="bottom-right">
          <Bell size={13} /> 2 route-relevant alerts <PanelRight size={13} />
          <RouteIcon size={13} /> {selectedRoute.name} selected <ChevronDown size={13} />
        </span>
      </div>
    </div>
  );
}
