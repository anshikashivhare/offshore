import React, { useCallback, useEffect, useRef, useMemo, useState } from "react";
import { Compass, Minus, Plus, RotateCcw, Globe2, Crosshair, Info, ChevronDown, ChevronUp } from "lucide-react";
import * as MapLibreGL from "maplibre-gl";
import {
  Map,
  MapRoute,
  MapMarker,
  MarkerContent,
  MarkerLabel,
  MapGeoJSON,
  useMap,
  type MapRef,
} from "./map-components";
import type {
  Coordinate,
  AppLocation,
  Iceberg,
  IcebergTrack,
  IcebergTrajectory,
  LayerKey,
  PortRecord,
  RiskCell,
  Route,
  UncertaintyRegion,
  Vessel,
  ViewMode,
} from "@/lib/offshore-types";
import {
  PortsMapLayer,
  PortHoverCard,
  PortDetailCard,
  type HoveredPortInfo,
} from "./PortFeatureManager";
import {
  NavigationModeController,
  VesselMarker,
  NavigationProminentRoute,
  NavigationHUD,
  NavigationZoomControls,
  IcebergDetailCard,
  IcebergHoverTooltip,
  calculateDistanceNm,
  type VesselNavState,
} from "./NavigationMode";
import {
  GEBCO_SOURCE_ID,
  GEBCO_LAYER_ID,
  getGebcoSourceConfig,
  getGebcoLayerConfig,
} from "@/services/map/gebco";
import {
  SEA_ICE_SOURCE_ID,
  SEA_ICE_LAYER_ID,
  getSeaIceSourceConfig,
  getSeaIceLayerConfig,
  getSeaIceTileUrl,
  type SeaIceDateMode,
  resolveSeaIceDate,
} from "@/services/map/nasaGibs";

type OffshoreMapProps = {
  layers: Record<LayerKey, boolean>;
  icebergs: Iceberg[];
  tracks: IcebergTrack[];
  trajectories: IcebergTrajectory[];
  uncertainty: UncertaintyRegion[];
  riskCells: RiskCell[];
  routes: Route[];
  selectedRouteId: string;
  selectedIcebergId: string | null;
  origin: Coordinate | null;
  originLabel?: string;
  destination: Coordinate | null;
  destinationLabel?: string;
  locations?: AppLocation[];
  pickMode: "origin" | "destination" | null;
  viewMode: ViewMode;
  selectedVessel?: Vessel | null;
  selectedPort?: PortRecord | null;
  onSelectPort?: (port: PortRecord | null) => void;
  onSetOriginPort?: (port: PortRecord) => void;
  onSetDestinationPort?: (port: PortRecord) => void;
  liveEnvironment?: any;
  onExitNavigation?: () => void;
  seaIceOpacity: number;
  seaIceDateMode: SeaIceDateMode;
  seaIceCustomDate?: string;
  onSelectRoute: (id: string) => void;
  onSelectIceberg: (id: string) => void;
  onPickCoordinate: (coordinate: Coordinate) => void;
  onFocus: (coordinate: Coordinate) => void;
};

/** Convert an Offshore Coordinate to [lng, lat] tuple for MapLibre */
function toLngLat(c: Coordinate): [number, number] {
  return [c.lng, c.lat];
}

/** Format coordinates into scientific notation */
function formatCoordinate(lat: number, lng: number): string {
  const latStr = `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? "N" : "S"}`;
  const lngStr = `${Math.abs(lng).toFixed(4)}° ${lng >= 0 ? "E" : "W"}`;
  return `${latStr} · ${lngStr}`;
}

// Global initial view (world-level)
const DEFAULT_CENTER: [number, number] = [0, 0];
const DEFAULT_ZOOM = 1.8;

// Antarctica focus
const ANTARCTICA_CENTER: [number, number] = [0, -72];
const ANTARCTICA_ZOOM = 3.0;

/**
 * Dark-ocean base style used instead of Carto — GEBCO tiles paint over it.
 */
const oceanBaseStyle: MapLibreGL.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#0a1628" },
    },
  ],
};

// ─── GEBCO RASTER LAYER ───────────────────────────────────────────────
function GebcoLayer({ visible, isNavMode = false }: { visible: boolean; isNavMode?: boolean }) {
  const { map, isLoaded } = useMap();
  const [status, setStatus] = useState<"loading" | "loaded" | "error">("loading");

  useEffect(() => {
    if (!map || !isLoaded) return;

    const sourceId = GEBCO_SOURCE_ID;
    const layerId = GEBCO_LAYER_ID;

    try {
      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, getGebcoSourceConfig());
      }

      if (!map.getLayer(layerId)) {
        // Insert at the very bottom — above the background only
        const layers = map.getStyle().layers || [];
        const firstNonBgLayer = layers.find((l) => l.id !== "background");
        map.addLayer(getGebcoLayerConfig(), firstNonBgLayer?.id);
      }

      setStatus("loaded");

      // Listen for tile errors
      const handleError = (e: any) => {
        if (e.sourceId === sourceId) setStatus("error");
      };
      map.on("error", handleError);

      return () => {
        map.off("error", handleError);
        try {
          if (map.getLayer(layerId)) map.removeLayer(layerId);
          if (map.getSource(sourceId)) map.removeSource(sourceId);
        } catch {
          /* ignore */
        }
      };
    } catch {
      setStatus("error");
    }
  }, [map, isLoaded]);

  // Visibility & opacity toggle (no source re-creation)
  useEffect(() => {
    if (!map || !isLoaded) return;
    try {
      if (map.getLayer(GEBCO_LAYER_ID)) {
        map.setLayoutProperty(GEBCO_LAYER_ID, "visibility", visible ? "visible" : "none");
        // In navigation mode, keep GEBCO subtle so sea ice is the prominent layer
        map.setPaintProperty(GEBCO_LAYER_ID, "raster-opacity", isNavMode ? 0.35 : 1.0);
      }
    } catch {
      /* ignore */
    }
  }, [map, isLoaded, visible, isNavMode]);

  return (
    <>
      {status === "error" && (
        <div className="map-layer-status-msg" aria-live="polite">
          GEBCO layer unavailable
        </div>
      )}
    </>
  );
}

// ─── SEA ICE CONCENTRATION RASTER LAYER ───────────────────────────────
function SeaIceLayer({
  visible,
  opacity,
  dateMode,
  customDate,
}: {
  visible: boolean;
  opacity: number;
  dateMode: SeaIceDateMode;
  customDate?: string;
}) {
  const { map, isLoaded } = useMap();
  const [status, setStatus] = useState<"loading" | "loaded" | "error">("loading");
  const currentDateRef = useRef<string>("");

  const resolvedDate = useMemo(
    () => resolveSeaIceDate(dateMode, customDate),
    [dateMode, customDate],
  );

  // Add source + layer on mount
  useEffect(() => {
    if (!map || !isLoaded) return;

    const sourceId = SEA_ICE_SOURCE_ID;
    const layerId = SEA_ICE_LAYER_ID;

    try {
      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, getSeaIceSourceConfig(resolvedDate));
        currentDateRef.current = resolvedDate;
      }

      if (!map.getLayer(layerId)) {
        // Insert above GEBCO but below all vector layers
        // Find the first non-raster, non-background layer to insert before
        const layers = map.getStyle().layers || [];
        let insertBefore: string | undefined;
        for (const l of layers) {
          if (l.id !== "background" && l.id !== GEBCO_LAYER_ID) {
            insertBefore = l.id;
            break;
          }
        }
        map.addLayer(getSeaIceLayerConfig(opacity), insertBefore);
      }

      setStatus("loaded");

      const handleError = (e: any) => {
        if (e.sourceId === sourceId) setStatus("error");
      };
      map.on("error", handleError);

      return () => {
        map.off("error", handleError);
        try {
          if (map.getLayer(layerId)) map.removeLayer(layerId);
          if (map.getSource(sourceId)) map.removeSource(sourceId);
        } catch {
          /* ignore */
        }
      };
    } catch {
      setStatus("error");
    }
  }, [map, isLoaded]);

  // Date change — update source tiles without re-creating
  useEffect(() => {
    if (!map || !isLoaded) return;
    if (currentDateRef.current === resolvedDate) return;

    try {
      const source = map.getSource(SEA_ICE_SOURCE_ID);
      if (source && "setTiles" in source) {
        (source as any).setTiles([getSeaIceTileUrl(resolvedDate)]);
        currentDateRef.current = resolvedDate;
        setStatus("loaded");
      }
    } catch {
      setStatus("error");
    }
  }, [map, isLoaded, resolvedDate]);

  // Opacity change — paint property only
  useEffect(() => {
    if (!map || !isLoaded) return;
    try {
      if (map.getLayer(SEA_ICE_LAYER_ID)) {
        map.setPaintProperty(SEA_ICE_LAYER_ID, "raster-opacity", opacity);
      }
    } catch {
      /* ignore */
    }
  }, [map, isLoaded, opacity]);

  // Visibility toggle
  useEffect(() => {
    if (!map || !isLoaded) return;
    try {
      if (map.getLayer(SEA_ICE_LAYER_ID)) {
        map.setLayoutProperty(SEA_ICE_LAYER_ID, "visibility", visible ? "visible" : "none");
      }
    } catch {
      /* ignore */
    }
  }, [map, isLoaded, visible]);

  return (
    <>
      {status === "error" && visible && (
        <div className="map-layer-status-msg" aria-live="polite">
          Sea-ice data temporarily unavailable
        </div>
      )}
    </>
  );
}

// ─── MAP CONTROLS ─────────────────────────────────────────────────────
function NauticalMapControls({ onReset }: { onReset: () => void }) {
  const { map } = useMap();

  const handleZoomIn = () => map?.zoomIn({ duration: 300 });
  const handleZoomOut = () => map?.zoomOut({ duration: 300 });
  const handleResetNorth = () => map?.resetNorth({ duration: 500 });

  const handleFocusAntarctica = () =>
    map?.flyTo({
      center: ANTARCTICA_CENTER,
      zoom: ANTARCTICA_ZOOM,
      duration: 2000,
    });

  const handleResetGlobal = () =>
    map?.flyTo({
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      bearing: 0,
      pitch: 0,
      duration: 1500,
    });

  return (
    <div className="nautical-map-controls" aria-label="Map Navigation Controls">
      <button onClick={handleZoomIn} aria-label="Zoom in" title="Zoom in">
        <Plus size={15} />
      </button>
      <button onClick={handleZoomOut} aria-label="Zoom out" title="Zoom out">
        <Minus size={15} />
      </button>
      <button onClick={handleResetNorth} aria-label="Reset North" title="Orient to North">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <polygon points="12 2 19 21 12 17 5 21 12 2" fill="currentColor" />
        </svg>
      </button>
      <button
        onClick={handleFocusAntarctica}
        aria-label="Focus Antarctica"
        title="Focus Antarctica"
        className="btn-focus-antarctica"
      >
        <Crosshair size={13} />
      </button>
      <button
        onClick={handleResetGlobal}
        aria-label="Reset Global View"
        title="Reset Global View"
        className="btn-reset-global"
      >
        <Globe2 size={13} />
      </button>
      <button onClick={onReset} aria-label="Reset View" title="Reset to default view">
        <RotateCcw size={14} />
      </button>
    </div>
  );
}

// ─── MAP INTERACTION HANDLER ──────────────────────────────────────────
function MapInteractionsHandler({
  pickMode,
  onPickCoordinate,
  onPointerMove,
  onPointerClick,
}: {
  pickMode: "origin" | "destination" | null;
  onPickCoordinate: (coordinate: Coordinate) => void;
  onPointerMove: (coordinate: Coordinate | null) => void;
  onPointerClick: (coordinate: Coordinate) => void;
}) {
  const { map } = useMap();

  useEffect(() => {
    if (!map) return;

    const clickHandler = (e: MapLibreGL.MapMouseEvent) => {
      if (pickMode) {
        onPickCoordinate({ lat: e.lngLat.lat, lng: e.lngLat.lng });
      } else {
        onPointerClick({ lat: e.lngLat.lat, lng: e.lngLat.lng });
      }
    };

    const moveHandler = (e: MapLibreGL.MapMouseEvent) => {
      onPointerMove({ lat: e.lngLat.lat, lng: e.lngLat.lng });
    };

    const leaveHandler = () => {
      onPointerMove(null);
    };

    map.on("click", clickHandler);
    map.on("mousemove", moveHandler);
    map.on("mouseout", leaveHandler);

    if (pickMode) {
      map.getCanvas().style.cursor = "crosshair";
    }

    return () => {
      map.off("click", clickHandler);
      map.off("mousemove", moveHandler);
      map.off("mouseout", leaveHandler);
      map.getCanvas().style.cursor = "";
    };
  }, [map, pickMode, onPickCoordinate, onPointerMove, onPointerClick]);

  return null;
}

// ─── LABEL SUPPRESSOR ─────────────────────────────────────────────────
/**
 * Hides basemap symbol layers that are unwanted in the Antarctic polar view:
 *  - place_continent: the basemap's own continent label (duplicate of our custom ANTARCTICA marker)
 *  - small place name layers that produce stray labels like "RGåbøya" at certain zoom levels
 * Re-applies on every style reload so it survives theme switches and projection changes.
 */
const SUPPRESSED_BASEMAP_LAYERS = [
  "place_continent",
  "place_hamlet",
  "place_suburbs",
  "place_villages",
  "place_town",
  "place_city_r6",
  "place_city_r5",
  "place_city_dot_r7",
];

function MapLabelSuppressor({ enabled = true }: { enabled?: boolean }) {
  const { map, isLoaded } = useMap();

  useEffect(() => {
    if (!map || !isLoaded || !enabled) return;

    const apply = () => {
      SUPPRESSED_BASEMAP_LAYERS.forEach((layerId) => {
        try {
          if (map.getLayer(layerId)) {
            map.setLayoutProperty(layerId, "visibility", "none");
          }
        } catch {
          // Layer may not exist in all style variants — silently ignore
        }
      });
    };

    // Apply immediately (style already loaded when isLoaded becomes true)
    apply();

    // Re-apply after any future style reloads (e.g. theme switch)
    map.on("style.load", apply);
    return () => {
      map.off("style.load", apply);
    };
  }, [map, isLoaded, enabled]);

  return null;
}

// ─── DYNAMIC VIEW FITTER ──────────────────────────────────────────────
function DynamicViewFitter({ coords, enabled = true }: { coords: [number, number][]; enabled?: boolean }) {
  const { map, isLoaded } = useMap();

  useEffect(() => {
    if (!map || !isLoaded || !enabled || coords.length < 2) return;

    const lngs = coords.map((c) => c[0]);
    const lats = coords.map((c) => c[1]);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);

    map.fitBounds(
      [
        [minLng, minLat],
        [maxLng, maxLat],
      ],
      {
        padding: { top: 80, bottom: 80, left: 60, right: 80 },
        maxZoom: 3.5,
        duration: 1000,
      },
    );
  }, [map, isLoaded, coords, enabled]);

  return null;
}


// ─── COMPACT LEGEND ───────────────────────────────────────────────────
function SeaIceLegend() {
  const [collapsed, setCollapsed] = useState(true);

  return (
    <div className="sea-ice-legend" aria-label="Sea Ice Concentration Legend">
      <button
        className="sea-ice-legend-toggle"
        onClick={() => setCollapsed(!collapsed)}
        aria-label={collapsed ? "Expand sea ice legend" : "Collapse sea ice legend"}
        title="Sea Ice Concentration Legend"
      >
        <span className="sea-ice-legend-title">SEA ICE</span>
        {collapsed ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
      </button>
      {!collapsed && (
        <div className="sea-ice-legend-body">
          <div className="sea-ice-legend-bar">
            <div className="sea-ice-gradient" />
            <div className="sea-ice-legend-labels">
              <span>0%</span>
              <span>25%</span>
              <span>50%</span>
              <span>75%</span>
              <span>100%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── COMPACT ATTRIBUTION ──────────────────────────────────────────────
function DataAttribution({
  seaIceDate,
}: {
  seaIceDate: string;
}) {
  const [showDetail, setShowDetail] = useState(false);

  return (
    <div className="map-data-attribution" aria-label="Data source attribution">
      <button
        className="attribution-toggle"
        onClick={() => setShowDetail(!showDetail)}
        aria-label="Data sources"
        title="Data sources"
      >
        <Info size={12} />
        <span className="attribution-label">Sources</span>
      </button>
      {showDetail && (
        <div className="attribution-detail">
          <div className="attribution-row">
            <span className="attribution-source">GEBCO</span>
            <span className="attribution-desc">GEBCO 2026 Grid</span>
          </div>
          <div className="attribution-row">
            <span className="attribution-source">NASA GIBS</span>
            <span className="attribution-desc">Sea Ice · {seaIceDate}</span>
          </div>
          <div className="attribution-row">
            <span className="attribution-source">OFFSHORE</span>
            <span className="attribution-desc">Operational data</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── DATA STATUS INDICATOR ────────────────────────────────────────────
function DataStatusIndicator({
  seaIceDate,
  gebcoVisible,
  seaIceVisible,
}: {
  seaIceDate: string;
  gebcoVisible: boolean;
  seaIceVisible: boolean;
}) {
  return (
    <div className="map-data-status" aria-label="Layer data status">
      {seaIceVisible && (
        <div className="data-status-row">
          <span className="data-status-dot" />
          <span className="data-status-text">SEA ICE · {seaIceDate}</span>
        </div>
      )}
      {gebcoVisible && (
        <div className="data-status-row">
          <span className="data-status-dot" />
          <span className="data-status-text">GEBCO 2026 Grid</span>
        </div>
      )}
    </div>
  );
}

// ─── OPTIMIZED CONSOLIDATED POLAR GRATICULES LAYER ────────────────────
function PolarGraticulesLayer() {
  const { map, isLoaded } = useMap();

  useEffect(() => {
    if (!map || !isLoaded) return;
    const sourceId = "polar-graticules-source";
    const layerId = "polar-graticules-layer";

    if (!map.getSource(sourceId)) {
      const features: any[] = [];
      for (let lat = -80; lat <= 80; lat += 20) {
        const coords: [number, number][] = [];
        for (let lng = -180; lng <= 180; lng += 10) coords.push([lng, lat]);
        features.push({
          type: "Feature",
          geometry: { type: "LineString", coordinates: coords },
        });
      }
      for (let lng = -180; lng < 180; lng += 30) {
        features.push({
          type: "Feature",
          geometry: {
            type: "LineString",
            coordinates: [
              [lng, -88],
              [lng, 88],
            ],
          },
        });
      }

      map.addSource(sourceId, {
        type: "geojson",
        data: { type: "FeatureCollection", features },
      });

      map.addLayer({
        id: layerId,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": "#A8C2CA",
          "line-width": 0.8,
          "line-opacity": 0.35,
          "line-dasharray": [3, 4],
        },
      });
    }

    return () => {
      try {
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      } catch {
        /* ignore */
      }
    };
  }, [map, isLoaded]);

  return null;
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────
export default function OffshoreMap({
  layers,
  icebergs,
  tracks,
  trajectories,
  uncertainty,
  riskCells,
  routes,
  selectedRouteId,
  selectedIcebergId,
  origin,
  originLabel = "Origin",
  destination,
  destinationLabel = "Destination",
  locations = [],
  pickMode,
  viewMode,
  selectedVessel,
  selectedPort,
  onSelectPort,
  onSetOriginPort,
  onSetDestinationPort,
  liveEnvironment,
  onExitNavigation,
  seaIceOpacity,
  seaIceDateMode,
  seaIceCustomDate,
  onSelectRoute,
  onSelectIceberg,
  onPickCoordinate,
  onFocus,
}: OffshoreMapProps) {
  const mapRef = useRef<MapRef>(null);

  // Port hover popup state
  const [hoveredPortInfo, setHoveredPortInfo] = useState<HoveredPortInfo | null>(null);

  // Center on port handler
  const handleCenterPort = useCallback((port: PortRecord) => {
    if (mapRef.current) {
      mapRef.current.flyTo({
        center: [port.lon, port.lat],
        zoom: Math.max(mapRef.current.getZoom(), 7.5),
        duration: 1200,
        essential: true,
      });
    }
  }, []);

  // When selectedPort changes, fly camera to it smoothly
  useEffect(() => {
    if (!selectedPort || !mapRef.current) return;
    mapRef.current.flyTo({
      center: [selectedPort.lon, selectedPort.lat],
      zoom: Math.max(mapRef.current.getZoom(), 7.5),
      duration: 1400,
      essential: true,
    });
  }, [selectedPort]);

  // Navigation mode tracking and playback state
  const [isFollowing, setIsFollowing] = useState(true);
  const [isPlaying, setIsPlaying] = useState(true);
  const [speedMultiplier, setSpeedMultiplier] = useState(5);
  const [navState, setNavState] = useState<VesselNavState | null>(null);

  // Iceberg selection & hover tooltip state (Navigation Mode)
  const [selectedIceberg, setSelectedIceberg] = useState<Iceberg | null>(null);
  const [hoveredIcebergInfo, setHoveredIcebergInfo] = useState<{
    iceberg: Iceberg;
    x: number;
    y: number;
    distanceNm?: number;
  } | null>(null);

  useEffect(() => {
    if (viewMode === "navigation") {
      setIsFollowing(true);
      setIsPlaying(true);
    }
  }, [viewMode]);

  const projection = useMemo(
    () => (viewMode === "globe" ? { type: "globe" as const } : { type: "mercator" as const }),
    [viewMode],
  );

  const handleReset = useCallback(() => {
    mapRef.current?.flyTo({
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      bearing: 0,
      pitch: 0,
      duration: 1200,
    });
  }, []);

  const selectedRoute = useMemo(
    () => routes.find((route) => route.id === selectedRouteId) ?? routes[0],
    [routes, selectedRouteId],
  );

  // A port's catalogue point can lie on land, while a route ends at its
  // navigable water approach.  They are rendered as distinct entities: the
  // destination pin always remains at the selected port.
  const destinationApproach =
    selectedRoute?.geometry[selectedRoute.geometry.length - 1] ?? destination;
  const hasSeparateDestinationApproach =
    selectedRoute !== undefined && destination !== null && destinationApproach !== null &&
    (Math.abs(destinationApproach.lng - destination.lng) > 0.0001 ||
      Math.abs(destinationApproach.lat - destination.lat) > 0.0001);

  // Coords for viewport fit: origin + destination + selected route geometry.
  const fitCoords = useMemo(() => {
    const pts: [number, number][] = [];
    if (origin) pts.push([origin.lng, origin.lat]);
    if (destination) pts.push([destination.lng, destination.lat]);
    if (selectedRoute) {
      pts.push(...selectedRoute.geometry.map(toLngLat));
    }
    return pts;
  }, [origin?.lng, origin?.lat, destination?.lng, destination?.lat, selectedRouteId, routes]);

  // Convert route coordinates to [lng, lat] tuples
  const routeCoordArrays = useMemo(
    () =>
      routes.map((route) => ({
        route,
        coords: route.geometry.map(toLngLat),
      })),
    [routes],
  );

  // Convert tracks to route coordinates
  const trackCoordArrays = useMemo(
    () =>
      tracks.map((track) => ({
        id: track.icebergId,
        coords: track.history.map(toLngLat),
      })),
    [tracks],
  );

  // Convert trajectories to route coordinates
  const trajectoryCoordArrays = useMemo(
    () =>
      trajectories.map((traj) => ({
        id: traj.icebergId,
        coords: traj.prediction.map(toLngLat),
      })),
    [trajectories],
  );


  const [pointerCoord, setPointerCoord] = useState<Coordinate | null>(null);
  const [clickedCoord, setClickedCoord] = useState<Coordinate | null>(null);

  const handlePointerClick = useCallback((coord: Coordinate) => {
    setClickedCoord(coord);
  }, []);

  // Resolved sea-ice date for display
  const resolvedSeaIceDate = useMemo(
    () => resolveSeaIceDate(seaIceDateMode, seaIceCustomDate),
    [seaIceDateMode, seaIceCustomDate]
  );

  // Normal vector basemap (like Google Maps) for Navigation Mode
  const NAVIGATION_BASEMAP_STYLE = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

  const currentMapStyles = useMemo(() => {
    if (viewMode === "navigation") {
      return {
        light: NAVIGATION_BASEMAP_STYLE,
        dark: NAVIGATION_BASEMAP_STYLE,
      };
    }
    return {
      light: oceanBaseStyle,
      dark: oceanBaseStyle,
    };
  }, [viewMode]);

  // Smooth Zoom In/Out handlers for Navigation Controls
  const handleZoomIn = useCallback(() => {
    if (!mapRef.current) return;
    const current = mapRef.current.getZoom();
    const next = Math.min(18, Math.round(current + 1));
    mapRef.current.easeTo({ zoom: next, duration: 250 });
  }, []);

  const handleZoomOut = useCallback(() => {
    if (!mapRef.current) return;
    const current = mapRef.current.getZoom();
    const next = Math.max(1, Math.round(current - 1));
    mapRef.current.easeTo({ zoom: next, duration: 250 });
  }, []);

  // When viewMode changes (e.g. entering/exiting full navigation view), trigger canvas resize
  useEffect(() => {
    const t1 = setTimeout(() => mapRef.current?.resize(), 60);
    const t2 = setTimeout(() => mapRef.current?.resize(), 300);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [viewMode]);

  return (
    <div className={`map-stage ${pickMode ? "is-picking" : ""}`}>
      {/* Dynamic basemap: Normal vector map for Navigation; polar dark-ocean for Map/Globe */}
      <Map
        ref={mapRef}
        styles={currentMapStyles}
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        projection={projection}
        className={`offshore-maplibre ${viewMode === "navigation" ? "navigation-normal-map" : "gebco-polar-map"}`}
        attributionControl={false}
      >
        <MapInteractionsHandler
          pickMode={pickMode}
          onPickCoordinate={onPickCoordinate}
          onPointerMove={setPointerCoord}
          onPointerClick={handlePointerClick}
        />
        <MapLabelSuppressor enabled={viewMode !== "navigation"} />
        <DynamicViewFitter coords={fitCoords} enabled={viewMode !== "navigation"} />

        {/* ============ NAVIGATION MODE CONTROLLER & PROMINENT ROUTE ============ */}
        <NavigationModeController
          enabled={viewMode === "navigation"}
          vessel={selectedVessel}
          route={selectedRoute}
          origin={origin}
          destination={destination}
          isFollowing={isFollowing}
          isPlaying={isPlaying}
          speedMultiplier={speedMultiplier}
          onUserPanned={() => setIsFollowing(false)}
          onNavStateChange={setNavState}
        />
        <NavigationProminentRoute
          route={selectedRoute}
          origin={origin}
          destination={destination}
          enabled={viewMode === "navigation"}
        />

        {/* ============ VESSEL 3D MARKER ============ */}
        {navState && (
          <VesselMarker
            position={navState.position}
            heading={navState.heading}
            sogKnots={navState.sogKnots}
            vesselName={selectedVessel?.vessel_name || "RRS Sir David Attenborough"}
            mapBearing={mapRef.current?.getBearing() ?? navState.heading}
          />
        )}

        {/* ============ LAYER 1: GEBCO BATHYMETRY BASEMAP (Disabled in Navigation mode to prevent blurry pixels) ============ */}
        <GebcoLayer visible={viewMode !== "navigation" && layers.gebco !== false} />

        {/* ============ LAYER 2: SEA ICE CONCENTRATION OVERLAY ============ */}
        <SeaIceLayer
          visible={layers.seaIceConcentration !== false}
          opacity={viewMode === "navigation" ? Math.min(seaIceOpacity, 0.65) : seaIceOpacity}
          dateMode={seaIceDateMode}
          customDate={seaIceCustomDate}
        />

        {/* ============ POLAR GRATICULES (Hidden in navigation mode) ============ */}
        {viewMode !== "navigation" && <PolarGraticulesLayer />}

        {/* ============ CANDIDATE & SELECTED ROUTES ============ */}
        {layers.routes &&
          routeCoordArrays.map(({ route, coords }) => {
            const isSelected = route.id === selectedRouteId;
            const isRust = route.riskScore >= 0.45 || route.objective === "Fastest";
            const isSafest = route.objective === "Safest";

            let routeColor = "#7A8F92";
            if (isSelected) {
              routeColor = isRust ? "#C66B45" : "#527C78";
            } else if (isSafest) {
              routeColor = "#596A6D";
            } else if (isRust) {
              routeColor = "#C66B45";
            }

            return (
              <MapRoute
                key={route.id}
                id={`offshore-route-${route.id}`}
                coordinates={coords}
                color={routeColor}
                width={isSelected ? 4 : 2}
                opacity={isSelected ? 1 : 0.6}
                dashArray={isSelected ? undefined : [6, 4]}
                active={isSelected}
                activeColor={routeColor}
                activeWidth={4.5}
                activeOpacity={1}
                onClick={() => onSelectRoute(route.id)}
                interactive
              />
            );
          })}

        {/* ============ OBSERVED TRACKS (SOLID/DOTTED NEUTRAL) ============ */}
        {layers.tracks &&
          trackCoordArrays.map(({ id, coords }) => (
            <MapRoute
              key={`track-${id}`}
              id={`offshore-track-${id}`}
              coordinates={coords}
              color="#596A6D"
              width={1.4}
              opacity={0.55}
              dashArray={[2, 3]}
              interactive={false}
            />
          ))}

        {/* ============ PREDICTED TRAJECTORIES (DASHED FORECAST) ============ */}
        {layers.trajectories &&
          trajectoryCoordArrays.map(({ id, coords }) => (
            <MapRoute
              key={`traj-${id}`}
              id={`offshore-traj-${id}`}
              coordinates={coords}
              color="#3B5F66"
              width={2}
              opacity={0.8}
              dashArray={[5, 6]}
              interactive={false}
            />
          ))}

        {/* ============ PREDICTED RISK ZONES ============ */}
        {layers.risk && (
          <>
            {/* Weddell Sea Risk Zone */}
            <MapMarker longitude={-20} latitude={-63}>
              <MarkerContent>
                <div className="risk-hatched-box" title="Predicted High Risk Zone · Dense Multiyear Ice">
                  <svg width="70" height="42" viewBox="0 0 70 42">
                    <polygon
                      points="10,2 65,8 55,38 8,32"
                      fill="rgba(198, 107, 69, 0.18)"
                      stroke="#C66B45"
                      strokeWidth="1.5"
                      strokeDasharray="4 2"
                    />
                    <line x1="15" y1="5" x2="30" y2="35" stroke="#C66B45" strokeWidth="1" opacity="0.6" />
                    <line x1="28" y1="6" x2="43" y2="36" stroke="#C66B45" strokeWidth="1" opacity="0.6" />
                    <line x1="41" y1="7" x2="56" y2="37" stroke="#C66B45" strokeWidth="1" opacity="0.6" />
                  </svg>
                </div>
              </MarkerContent>
            </MapMarker>

            {/* Indian Ocean Margin Risk Zone */}
            <MapMarker longitude={72} latitude={-64}>
              <MarkerContent>
                <div className="risk-hatched-box" title="Predicted Risk Zone · Calving Margins">
                  <svg width="60" height="40" viewBox="0 0 60 40">
                    <polygon
                      points="8,4 52,10 44,36 4,30"
                      fill="rgba(198, 107, 69, 0.18)"
                      stroke="#C66B45"
                      strokeWidth="1.5"
                      strokeDasharray="4 2"
                    />
                    <line x1="14" y1="6" x2="26" y2="34" stroke="#C66B45" strokeWidth="1" opacity="0.6" />
                    <line x1="28" y1="8" x2="40" y2="35" stroke="#C66B45" strokeWidth="1" opacity="0.6" />
                  </svg>
                </div>
              </MarkerContent>
            </MapMarker>
          </>
        )}

        {/* ============ ICEBERGS ============ */}
        {layers.icebergs &&
          icebergs.map((iceberg) => {
            const isNav = viewMode === "navigation";
            const isActive = iceberg.id === selectedIcebergId || iceberg.id === selectedIceberg?.id;

            return (
              <MapMarker
                key={iceberg.id}
                longitude={iceberg.position.lng}
                latitude={iceberg.position.lat}
                onClick={() => {
                  if (isNav) {
                    setSelectedIceberg(iceberg);
                  } else {
                    onSelectIceberg(iceberg.id);
                    onFocus(iceberg.position);
                  }
                }}
              >
                <MarkerContent>
                  <div
                    className={`iceberg-red-dot-marker ${isActive ? "active" : ""}`}
                    onMouseEnter={(e) => {
                      const distNm = navState?.position
                        ? calculateDistanceNm(navState.position, iceberg.position)
                        : undefined;
                      setHoveredIcebergInfo({
                        iceberg,
                        x: e.clientX,
                        y: e.clientY,
                        distanceNm: distNm,
                      });
                    }}
                    onMouseMove={(e) => {
                      const distNm = navState?.position
                        ? calculateDistanceNm(navState.position, iceberg.position)
                        : undefined;
                      setHoveredIcebergInfo({
                        iceberg,
                        x: e.clientX,
                        y: e.clientY,
                        distanceNm: distNm,
                      });
                    }}
                    onMouseLeave={() => setHoveredIcebergInfo(null)}
                    onTouchStart={(e) => {
                      const touch = e.touches[0];
                      const distNm = navState?.position
                        ? calculateDistanceNm(navState.position, iceberg.position)
                        : undefined;
                      setHoveredIcebergInfo({
                        iceberg,
                        x: touch.clientX,
                        y: touch.clientY,
                        distanceNm: distNm,
                      });
                    }}
                    onTouchEnd={() => setHoveredIcebergInfo(null)}
                    title={`Iceberg ${iceberg.id}`}
                  >
                    <div className="iceberg-pulse-halo" />
                    <div className="iceberg-dot-core" />
                  </div>
                </MarkerContent>
              </MapMarker>
            );
          })}

        {/* ============ ORIGIN MARKER (ROTHERA IN IMAGE 2) ============ */}
        {origin && (
          <MapMarker longitude={origin.lng} latitude={origin.lat}>
            <MarkerContent>
              <div className="waypoint-pin origin-pin" title="Origin">
                O
              </div>
            </MarkerContent>
            <MarkerLabel>
              <div className="waypoint-label" style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <span>{originLabel.split(",")[0]}</span>
                <span style={{ fontSize: "9px", opacity: 0.7 }}>{formatCoordinate(origin.lat, origin.lng)}</span>
              </div>
            </MarkerLabel>
          </MapMarker>
        )}

        {/* The destination always identifies the selected port location. */}
        {destination && (
          <MapMarker longitude={destination.lng} latitude={destination.lat}>
            <MarkerContent>
              <div className="waypoint-pin destination-pin" title="Destination port">
                D
              </div>
            </MarkerContent>
            <MarkerLabel>
              <div className="waypoint-label" style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <span>{destinationLabel.split(",")[0]}</span>
                <span style={{ fontSize: "9px", opacity: 0.7 }}>{formatCoordinate(destination.lat, destination.lng)}</span>
              </div>
            </MarkerLabel>
          </MapMarker>
        )}

        {hasSeparateDestinationApproach && (
          <MapMarker longitude={destinationApproach.lng} latitude={destinationApproach.lat}>
            <MarkerContent>
              <div
                className="waypoint-pin"
                title="Navigable approach: calculated route ends here"
                style={{ background: "#527C78", fontSize: "10px" }}
              >
                A
              </div>
            </MarkerContent>
            <MarkerLabel>
              <div className="waypoint-label" style={{ fontSize: "9px" }}>
                Navigable approach
              </div>
            </MarkerLabel>
          </MapMarker>
        )}

        {/* ============ PORTS INFRASTRUCTURE LAYER (BLUE in navigation mode) ============ */}
        <PortsMapLayer
          ports={locations}
          visible={layers.ports !== false}
          isNavMode={viewMode === "navigation"}
          selectedPort={selectedPort ?? null}
          onHoverPort={setHoveredPortInfo}
          onClickPort={(port) => onSelectPort?.(port)}
        />

        {/* ============ GEOGRAPHIC LABELS (Hidden in Navigation mode) ============ */}
        {viewMode !== "navigation" && (
          <>
            <MapMarker longitude={0} latitude={-82}>
              <MarkerContent>
                <span className="geo-label-continent">ANTARCTICA</span>
              </MarkerContent>
            </MapMarker>
            <MapMarker longitude={-45} latitude={-72}>
              <MarkerContent>
                <span className="geo-label-sea">WEDDELL<br />SEA</span>
              </MarkerContent>
            </MapMarker>
            <MapMarker longitude={-175} latitude={-75}>
              <MarkerContent>
                <span className="geo-label-sea">ROSS SEA</span>
              </MarkerContent>
            </MapMarker>
            <MapMarker longitude={85} latitude={-55}>
              <MarkerContent>
                <span className="geo-label-ocean">INDIAN<br />OCEAN</span>
              </MarkerContent>
            </MapMarker>
          </>
        )}

        {/* ============ NAUTICAL MAP CONTROLS (TOP-LEFT) ============ */}
        {viewMode !== "navigation" && <NauticalMapControls onReset={handleReset} />}
      </Map>

      {/* ============ NAVIGATION HUD (Clean bottom Google Maps dock) ============ */}
      {viewMode === "navigation" && navState && (
        <NavigationHUD
          vessel={selectedVessel}
          navState={navState}
          route={selectedRoute}
          routes={routes}
          selectedRouteId={selectedRouteId}
          onSelectRoute={onSelectRoute}
          icebergs={icebergs}
          isFollowing={isFollowing}
          isPlaying={isPlaying}
          speedMultiplier={speedMultiplier}
          onTogglePlay={() => setIsPlaying((p) => !p)}
          onSpeedChange={(spd) => setSpeedMultiplier(spd)}
          onRecenter={() => {
            setIsFollowing(true);
            if (mapRef.current && navState) {
              const paddingTop = typeof window !== "undefined" ? Math.min(window.innerHeight * 0.44, 300) : 220;
              mapRef.current.easeTo({
                center: [navState.position.lng, navState.position.lat],
                bearing: navState.heading,
                pitch: 48,
                zoom: mapRef.current.getZoom() || 11.5,
                padding: { top: paddingTop, bottom: 0, left: 0, right: 0 },
                duration: 600,
              });
            }
          }}
          onExit={() => onExitNavigation?.()}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
        />
      )}

      {/* Floating Zoom Controls (Google Maps Style + and - buttons on the right side) */}
      {viewMode === "navigation" && (
        <NavigationZoomControls
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onRecenter={() => {
            setIsFollowing(true);
            if (mapRef.current && navState) {
              const paddingTop = typeof window !== "undefined" ? Math.min(window.innerHeight * 0.44, 300) : 220;
              mapRef.current.easeTo({
                center: [navState.position.lng, navState.position.lat],
                bearing: navState.heading,
                pitch: 48,
                zoom: mapRef.current.getZoom() || 11.5,
                padding: { top: paddingTop, bottom: 0, left: 0, right: 0 },
                duration: 600,
              });
            }
          }}
          isFollowing={isFollowing}
        />
      )}

      {/* Floating Hover Information Card */}
      <PortHoverCard info={hoveredPortInfo} />

      {/* Selected Port Details Modal / Panel */}
      {selectedPort && (
        <PortDetailCard
          port={selectedPort}
          onClose={() => onSelectPort?.(null)}
          onCenter={handleCenterPort}
          onSetOrigin={onSetOriginPort}
          onSetDestination={onSetDestinationPort}
        />
      )}

      {/* Real Iceberg Satellite Image Detail Card (Navigation Mode) */}
      <IcebergDetailCard
        iceberg={selectedIceberg}
        vesselPosition={navState?.position}
        onClose={() => setSelectedIceberg(null)}
      />

      {/* Real Iceberg Hover Tooltip */}
      <IcebergHoverTooltip info={hoveredIcebergInfo} />

      {/* Sea Ice Legend (Bottom-Right, compact - hidden in navigation) */}
      {viewMode !== "navigation" && layers.seaIceConcentration !== false && <SeaIceLegend />}

      {/* Data Attribution (Bottom-Right, below legend - hidden in navigation) */}
      {viewMode !== "navigation" && <DataAttribution seaIceDate={resolvedSeaIceDate} />}

      {/* Data Status (Top-Right, compact - hidden in navigation) */}
      {viewMode !== "navigation" && (
        <DataStatusIndicator
          seaIceDate={resolvedSeaIceDate}
          gebcoVisible={layers.gebco !== false}
          seaIceVisible={layers.seaIceConcentration !== false}
        />
      )}

      {/* Nautical Scale Bar (Bottom-Left - hidden in navigation) */}
      {viewMode !== "navigation" && (
        <div className="nautical-scale-bar" aria-label="Nautical scale">
          <div className="scale-marks">
            <span>0</span>
            <span>250</span>
            <span>500</span>
            <span>1,000 km</span>
          </div>
          <div className="scale-line" />
        </div>
      )}

      {/* Live Coordinate Readout (Bottom-Left, above scale bar - hidden in navigation) */}
      {viewMode !== "navigation" && (pointerCoord || clickedCoord) && (
        <div style={{
          position: "absolute",
          bottom: "48px",
          left: "16px",
          background: "var(--deep-fjord, #1e293b)",
          color: "#f8fafc",
          padding: "8px 12px",
          borderRadius: "6px",
          fontSize: "12px",
          fontFamily: "var(--font-mono)",
          fontWeight: 600,
          boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)",
          border: "1px solid rgba(255,255,255,0.1)",
          zIndex: 10,
          pointerEvents: "none",
          display: "flex",
          flexDirection: "column",
          gap: "4px"
        }}>
          {pointerCoord && (
            <div>
              <span style={{ opacity: 0.7, marginRight: "8px", fontSize: "10px" }}>CURSOR</span>
              {formatCoordinate(pointerCoord.lat, pointerCoord.lng)}
            </div>
          )}
          {clickedCoord && (
            <div style={{ borderTop: pointerCoord ? "1px solid rgba(255,255,255,0.1)" : "none", paddingTop: pointerCoord ? "4px" : "0" }}>
              <span style={{ opacity: 0.7, marginRight: "8px", fontSize: "10px" }}>PINNED</span>
              {formatCoordinate(clickedCoord.lat, clickedCoord.lng)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
