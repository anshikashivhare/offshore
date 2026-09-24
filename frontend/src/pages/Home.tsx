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
import {
  fetchIcebergs,
  fetchLiveRouteEnvironment,
  fetchGlobalPorts,
  fetchRoutes,
  planRoute,
  fetchVessels,
} from "@/lib/api";
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
} from "@/lib/offshore-mock-data";
import type { AppLocation, Coordinate, LayerKey, Priority, Vessel } from "@/lib/offshore-types";

// Mock geometry generation removed in favor of actual backend calculation

export default function Home() {
  const [layers, setLayers] = useState(defaultLayers);
  const [selectedRouteId, setSelectedRouteId] = useState(staticRoutes[0].id);
  const [selectedIcebergId, setSelectedIcebergId] = useState<string | null>("IB-221");
  const [selectedVesselId, setSelectedVesselId] = useState<string>("");
  const [priority, setPriority] = useState<Priority>("Safety First");
  const [origin, setOrigin] = useState<Coordinate>(locations[2].coordinate);
  const [destination, setDestination] = useState<Coordinate>(locations[3].coordinate);
  const [originLabel, setOriginLabel] = useState(locations[2].label);
  const [destinationLabel, setDestinationLabel] = useState(locations[3].label);
  const [pickMode, setPickMode] = useState<"origin" | "destination" | null>(null);
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [activeAlertId, setActiveAlertId] = useState(alerts[0].id);
  // Globe is the safe default for Antarctic interpretation; Mercator remains
  // available for familiar navigation interaction but visibly distorts scale.
  const [viewMode, setViewMode] = useState<"map" | "globe">("globe");
  const [forecastHours, setForecastHours] = useState(16);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isFullscreen, setIsFullscreen] = useState(false);

  const [liveIcebergs, setLiveIcebergs] = useState(icebergs);
  const [liveRoutes, setLiveRoutes] = useState<typeof staticRoutes>([]);
  const [liveLocations, setLiveLocations] = useState<AppLocation[]>([]);
  const [liveVessels, setLiveVessels] = useState<Vessel[]>([]);
  const [customVesselConfig, setCustomVesselConfig] = useState<Vessel | null>(null);
  const [liveEnvironment, setLiveEnvironment] = useState<any>(null);
  const [liveEnvError, setLiveEnvError] = useState<string | null>(null);
  const [routeValidationError, setRouteValidationError] = useState<string | null>(null);

  useEffect(() => {
    // REGRESSION GUARD: Never generate mock geometry (like straight lines) here.
    // Ensure that liveRoutes remains empty until a successful backend route response 
    // is received from POST /api/v1/routes/plan via handleCalculateRoute.
    setLiveRoutes([]);
    setRouteValidationError(null);
  }, [origin, destination]);

  useEffect(() => {
    fetchGlobalPorts()
      .then((data) => {
        if (data && data.data && data.data.length > 0) {
          const ports = data.data.map((p: any) => ({
            label: `${p.name}, ${p.country}`,
            coordinate: { lat: p.lat, lng: p.lon },
            country: p.country
          }));
          // MapLibre is highly performant with thousands of points, so we can load them all
          setLiveLocations(ports);
        }
      })
      .catch((err) => console.error("Failed to fetch all ports:", err));

    fetchIcebergs()
      .then((data) => {
        if (data && data.features && data.features.length > 0) {
          const mapped = data.features.map((f: any) => ({
            id: f.properties.iceberg_id.split("-")[0].toUpperCase(),
            position: { lat: f.geometry.coordinates[1], lng: f.geometry.coordinates[0] },
            sizeKm: f.properties.estimated_size / 1000,
            timestamp: f.properties.timestamp,
            confidence: f.properties.confidence,
            drift: "NNW",
            risk: "moderate"
          }));
          setLiveIcebergs(mapped);
        }
      })
      .catch((err) => console.error("Failed to fetch live icebergs:", err));

    fetchRoutes()
      .then((data) => {
        if (data && data.length > 0) setLiveRoutes(data);
      })
      .catch((err) => console.error("Failed to fetch live routes:", err));

    fetchVessels()
      .then((res) => {
        const items = res.data;
        if (items && items.length > 0) {
          setLiveVessels(items);
          setSelectedVesselId(items[0].vessel_id);
          setRouteValidationError("");
        } else {
          setLiveVessels([]);
          setSelectedVesselId("");
          setRouteValidationError("No vessels available. Please check database connection or demo mode configuration.");
        }
      })
      .catch((err) => {
        console.error("Failed to fetch vessels:", err);
        setLiveVessels([]);
        setSelectedVesselId("");
        setRouteValidationError(err.message || "Failed to fetch vessels.");
      });
  }, []);

  const [isCalculating, setIsCalculating] = useState(false);

  // Directly use liveRoutes which will now contain backend results
  const routes = liveRoutes;

  const handleCalculateRoute = useCallback(async () => {
    if (routeValidationError) return;
    if (!selectedVesselId) {
      setLiveEnvError("No vessel selected.");
      return;
    }
    
    setIsCalculating(true);
    setLiveEnvError(null);
    try {
      const requestPayload = {
        vessel_id: selectedVesselId,
        origin: `${origin.lng},${origin.lat}`,
        destination: `${destination.lng},${destination.lat}`,
        departure_time: new Date(selectedDate.getTime() + forecastHours * 60 * 60 * 1000).toISOString(),
        objective_type: priority === "Time Efficient" ? "fastest" 
                        : priority === "Fuel Efficient" ? "fuel_efficient" 
                        : "safest",
        custom_vessel_config: customVesselConfig
      };
      
      const feature = await planRoute(requestPayload);
      
      const distNm = feature.properties.distance || 0;
      const etaDays = feature.properties.eta 
        ? (new Date(feature.properties.eta).getTime() - new Date(feature.properties.departure_time).getTime()) / (1000 * 3600 * 24)
        : 0;

      const mappedRoute = {
        id: feature.properties.route_id,
        name: `${priority} Route (${new Date().toLocaleTimeString()})`,
        objective: priority === "Time Efficient" ? "Fastest" as const 
                 : priority === "Fuel Efficient" ? "Fuel Efficient" as const 
                 : priority === "Safety First" ? "Safest" as const 
                 : "Recommended" as const,
        distanceNm: distNm,
        distanceKm: distNm * 1.852,
        etaHours: etaDays * 24,
        fuelLitres: feature.properties.estimated_fuel || 0,
        estimatedDays: etaDays,
        riskScore: feature.properties.risk_score || 0,
        exposure: `${Math.round(etaDays)} days`,
        status: "Calculated",
        accent: "#2563eb",
        geometry: feature.geometry.coordinates.map((c: number[]) => ({ lat: c[1], lng: c[0] })),
        data_provenance: feature.properties.waypoints?.map((w: any) => w.data_provenance) || [],
        risk_data_status: feature.properties.risk_data_status,
        ml_prediction_status: feature.properties.ml_prediction_status,
        warnings: feature.properties.warnings
      };

      setLiveRoutes([mappedRoute]);
      setSelectedRouteId(mappedRoute.id);
    } catch (err: any) {
      console.error(err);
      setLiveEnvError(err.message || "Route calculation failed");
      setLiveRoutes([]);
      setSelectedRouteId("");
    } finally {
      setIsCalculating(false);
    }
  }, [selectedVesselId, origin, destination, selectedDate, forecastHours, priority, routeValidationError]);

  const selectedRoute = useMemo(
    () => liveRoutes.find((route) => route.id === selectedRouteId) ?? liveRoutes[0],
    [selectedRouteId, liveRoutes]
  );

  useEffect(() => {
    if (!selectedRoute) return;
    const fetchEnv = async () => {
      try {
        const targetEta = new Date(selectedDate.getTime() + forecastHours * 60 * 60 * 1000).toISOString();
        const waypoints = selectedRoute.geometry.map(c => ({ lat: c.lat, lon: c.lng, eta: targetEta }));
        const subset = waypoints.length > 50 ? waypoints.filter((_, i) => i % Math.ceil(waypoints.length/50) === 0).slice(0, 50) : waypoints;
        const res = await fetchLiveRouteEnvironment(subset);
        setLiveEnvironment(res);
        setLiveEnvError(null);
      } catch (err: any) {
        setLiveEnvError(err.message || "Failed to fetch live environment.");
      }
    };
    fetchEnv();
    const interval = setInterval(fetchEnv, 60000);
    return () => clearInterval(interval);
  }, [selectedRoute, selectedDate, forecastHours]);

  const handleLocationChange = (kind: "origin" | "destination", loc: AppLocation) => {
    if (kind === "origin") {
      setOrigin(loc.coordinate);
      setOriginLabel(loc.label);
    } else {
      setDestination(loc.coordinate);
      setDestinationLabel(loc.label);
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
            locations={liveLocations}
            vessels={liveVessels}
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
            isCalculating={isCalculating}
            onCalculateRoute={handleCalculateRoute}
            routeError={routeValidationError || liveEnvError}
            customVesselConfig={customVesselConfig}
            onCustomVesselConfigChange={setCustomVesselConfig}
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
              originLabel={originLabel}
              destination={destination}
              destinationLabel={destinationLabel}
              locations={liveLocations}
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
            <span className={`live-status-dot ${routeValidationError || liveEnvError ? "error" : "success"}`} style={{ backgroundColor: routeValidationError || liveEnvError ? "#ef4444" : "#10b981" }} />
            <span>
              {routeValidationError
                ? `VALIDATION ERROR: ${routeValidationError}`
                : (liveEnvError 
                    ? `STALE DATA: ${liveEnvError}` 
                    : (liveEnvironment 
                        ? `Live Retrieval: Success (Forecast: ${liveEnvironment.waypoints[0]?.weather_status?.latest_forecast_time || "N/A"})` 
                        : "Connecting live stream..."))}
            </span>
          </div>
          <span className="status-v-divider">|</span>
          <span className={selectedRoute?.ml_prediction_status === "unavailable" ? "text-red-500" : ""}>
            ML Prediction: {!selectedRoute ? "Pending" : selectedRoute.ml_prediction_status === "unavailable" ? "Unavailable" : "Active (XGBoost)"}
          </span>
          <span className="status-v-divider">|</span>
          <span>Map projection: {viewMode === "globe" ? "WGS84 globe" : "Web Mercator — distorted near poles"}</span>
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
            {selectedRoute ? `${selectedRoute.name} selected` : "No route selected"} <ChevronDown size={12} />
          </span>
        </div>
      </footer>
    </div>
  );
}
