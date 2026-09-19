import React, { useCallback, useEffect, useRef, useMemo, useState } from "react";
import { Compass, Minus, Plus, RotateCcw } from "lucide-react";
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
  RiskCell,
  Route,
  UncertaintyRegion,
} from "@/lib/offshore-types";

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
  origin: Coordinate;
  originLabel?: string;
  destination: Coordinate;
  destinationLabel?: string;
  locations?: AppLocation[];
  pickMode: "origin" | "destination" | null;
  viewMode: "map" | "globe";
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

// Fallback center/zoom used by the Reset View button.
// Placed midway along the Rothera → Casey southern corridor.
const DEFAULT_CENTER: [number, number] = [21, -67];
const DEFAULT_ZOOM = 2.2;

/** Custom Light Map Controls matching Image 2 top-left controls */
function NauticalMapControls({ onReset }: { onReset: () => void }) {
  const { map } = useMap();

  const handleZoomIn = () => map?.zoomIn({ duration: 300 });
  const handleZoomOut = () => map?.zoomOut({ duration: 300 });
  const handleResetNorth = () => map?.resetNorth({ duration: 500 });

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
      <button onClick={onReset} aria-label="Reset View" title="Reset to Antarctic Passage">
        <RotateCcw size={14} />
      </button>
    </div>
  );
}

/** Interaction handler component that registers map click for pick mode and pointer coordinates */
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

/**
 * Hides basemap symbol layers that are unwanted in the Antarctic polar view:
 *  - place_continent: the basemap's own continent label (duplicate of our custom ANTARCTICA marker)
 *  - small place name layers that produce stray labels like "RGåbøya" at certain zoom levels
 * Re-applies on every style reload so it survives theme switches and projection changes.
 */
const SUPPRESSED_BASEMAP_LAYERS = [
  // Continent label — we render our own ANTARCTICA marker; hiding this removes the duplicate
  "place_continent",
  // Small-settlement and city layers irrelevant to the Antarctic polar view
  "place_hamlet",
  "place_suburbs",
  "place_villages",
  "place_town",
  "place_city_r6",
  "place_city_r5",
  "place_city_dot_r7",
];

function MapLabelSuppressor() {
  const { map, isLoaded } = useMap();

  useEffect(() => {
    if (!map || !isLoaded) return;

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
  }, [map, isLoaded]);

  return null;
}

/**
 * Fits the viewport to the bounding box of the supplied route coordinates 
 * whenever they change (e.g., origin/dest changes, or new route calculated).
 */
function DynamicViewFitter({
  coords,
}: {
  coords: [number, number][];
}) {
  const { map, isLoaded } = useMap();

  useEffect(() => {
    if (!map || !isLoaded || coords.length < 2) return;

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
      }
    );
  }, [map, isLoaded, coords]);

  return null;
}

function PortsLayer({
  locations,
  originLabel,
  destinationLabel,
}: {
  locations: any[];
  originLabel: string;
  destinationLabel: string;
}) {
  const { map, isLoaded } = useMap();

  useEffect(() => {
    if (!map || !isLoaded) return;

    const sourceId = "offshore-ports";
    const layerId = "offshore-ports-circle";

    const features = locations
      .filter((loc) => loc.label !== originLabel && loc.label !== destinationLabel)
      .map((loc) => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [loc.coordinate.lng, loc.coordinate.lat],
        },
        properties: {
          label: loc.label.split(",")[0],
        },
      }));

    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features,
        } as any,
      });
    } else {
      (map.getSource(sourceId) as any).setData({
        type: "FeatureCollection",
        features,
      });
    }

    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: "circle",
        source: sourceId,
        paint: {
          "circle-color": "#8A9B9D",
          "circle-radius": 3.5,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#FFFFFF",
        },
      });
    }
  }, [map, isLoaded, locations, originLabel, destinationLabel]);

  return null;
}

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
  onSelectRoute,
  onSelectIceberg,
  onPickCoordinate,
  onFocus,
}: OffshoreMapProps) {
  const mapRef = useRef<MapRef>(null);

  const projection = useMemo(
    () => (viewMode === "globe" ? { type: "globe" as const } : { type: "mercator" as const }),
    [viewMode]
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

  // Coords for viewport fit: origin + destination + selected route geometry.
  // Re-calculates (and therefore re-fits) when these inputs change.
  const fitCoords = useMemo(() => {
    const selectedRoute = routes.find((r) => r.id === selectedRouteId) ?? routes[0];
    const pts: [number, number][] = [
      [origin.lng, origin.lat],
      [destination.lng, destination.lat],
      ...(selectedRoute ? selectedRoute.geometry.map(toLngLat) : []),
    ];
    return pts;
  }, [origin.lng, origin.lat, destination.lng, destination.lat, selectedRouteId, routes]);

  // Convert route coordinates to [lng, lat] tuples
  const routeCoordArrays = useMemo(
    () =>
      routes.map((route) => ({
        route,
        coords: route.geometry.map(toLngLat),
      })),
    [routes]
  );

  // Convert tracks to route coordinates
  const trackCoordArrays = useMemo(
    () =>
      tracks.map((track) => ({
        id: track.icebergId,
        coords: track.history.map(toLngLat),
      })),
    [tracks]
  );

  // Convert trajectories to route coordinates
  const trajectoryCoordArrays = useMemo(
    () =>
      trajectories.map((traj) => ({
        id: traj.icebergId,
        coords: traj.prediction.map(toLngLat),
      })),
    [trajectories]
  );

  // Global Parallels (Latitude: -80 to 80, every 10 or 20 degrees)
  const parallels = useMemo(() => {
    const lats = [];
    for (let lat = -80; lat <= 80; lat += 20) {
      if (lat !== 0) lats.push(lat); // Skip equator if desired, or keep it. Let's keep it.
    }
    lats.push(0);
    return lats.map((lat) => {
      const coords: [number, number][] = [];
      for (let lng = -180; lng <= 180; lng += 10) {
        coords.push([lng, lat]);
      }
      return { lat, coords };
    });
  }, []);

  // Global Meridians (Longitude: -180 to 180, every 30 degrees)
  const meridians = useMemo(() => {
    const lngs = [];
    for (let lng = -180; lng < 180; lng += 30) {
      lngs.push(lng);
    }
    return lngs.map((lng) => {
      const coords: [number, number][] = [
        [lng, -88],
        [lng, 88],
      ];
      return { lng, coords };
    });
  }, []);

  const [pointerCoord, setPointerCoord] = useState<Coordinate | null>(null);
  const [clickedCoord, setClickedCoord] = useState<Coordinate | null>(null);

  const handlePointerClick = useCallback((coord: Coordinate) => {
    setClickedCoord(coord);
  }, []);

  return (
    <div className={`map-stage ${pickMode ? "is-picking" : ""}`}>
      {/* Light Positron Basemap matching Image 2 */}
      <Map
        ref={mapRef}
        theme="light"
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        projection={projection}
        className="offshore-maplibre light-polar-map"
        attributionControl={false}
      >
        <MapInteractionsHandler 
          pickMode={pickMode} 
          onPickCoordinate={onPickCoordinate} 
          onPointerMove={setPointerCoord}
          onPointerClick={handlePointerClick}
        />
        {/* Suppress unwanted basemap labels (duplicate ANTARCTICA, RGåbøya, etc.) */}
        <MapLabelSuppressor />
        {/* Fits the viewport to the route corridor whenever origin/dest/route changes */}
        <DynamicViewFitter coords={fitCoords} />

        {/* ============ POLAR GRATICULES (PARALLELS & MERIDIANS) ============ */}
        {parallels.map(({ lat, coords }) => (
          <React.Fragment key={`parallel-group-${lat}`}>
            <MapRoute
              key={`parallel-${lat}`}
              id={`graticule-parallel-${lat}`}
              coordinates={coords}
              color="#A8C2CA"
              width={0.8}
              opacity={0.5}
              dashArray={[3, 4]}
              interactive={false}
            />
            {/* Label at longitude 0 */}
            <MapMarker longitude={0} latitude={lat}>
              <MarkerContent>
                <div style={{ color: "#7A8F92", fontSize: "10px", fontFamily: "var(--font-mono)", padding: "2px", fontWeight: 600, transform: "translateY(-10px)", pointerEvents: "none" }}>
                  {Math.abs(lat)}° S
                </div>
              </MarkerContent>
            </MapMarker>
          </React.Fragment>
        ))}
        {meridians.map(({ lng, coords }) => (
          <React.Fragment key={`meridian-group-${lng}`}>
            <MapRoute
              key={`meridian-${lng}`}
              id={`graticule-meridian-${lng}`}
              coordinates={coords}
              color="#A8C2CA"
              width={0.8}
              opacity={0.4}
              dashArray={[3, 4]}
              interactive={false}
            />
            {/* Label at latitude -45 (outer edge) */}
            <MapMarker longitude={lng} latitude={-45}>
              <MarkerContent>
                <div style={{ color: "#7A8F92", fontSize: "10px", fontFamily: "var(--font-mono)", padding: "2px", fontWeight: 600, pointerEvents: "none" }}>
                  {Math.abs(lng)}° {lng >= 0 ? "E" : "W"}
                </div>
              </MarkerContent>
            </MapMarker>
          </React.Fragment>
        ))}

        {/* ============ CANDIDATE & SELECTED ROUTES (RULE 5 & 6) ============ */}
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

        {/* ============ PREDICTED RISK ZONES (HATCHED AREAS IN IMAGE 2) ============ */}
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

        {/* ============ ICEBERGS (TRIANGLE NAUTICAL MARKERS IN IMAGE 2) ============ */}
        {layers.icebergs &&
          icebergs.map((iceberg) => {
            const isActive = iceberg.id === selectedIcebergId;
            return (
              <MapMarker
                key={iceberg.id}
                longitude={iceberg.position.lng}
                latitude={iceberg.position.lat}
                onClick={() => {
                  onSelectIceberg(iceberg.id);
                  onFocus(iceberg.position);
                }}
              >
                <MarkerContent>
                  <div className={`iceberg-triangle-marker ${isActive ? "active" : ""}`}>
                    <svg width="16" height="16" viewBox="0 0 16 16">
                      <polygon
                        points="8,2 14,14 2,14"
                        fill="#FFFFFF"
                        stroke="#527C78"
                        strokeWidth="1.5"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                </MarkerContent>
              </MapMarker>
            );
          })}

        {/* ============ ORIGIN MARKER (ROTHERA IN IMAGE 2) ============ */}
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

        {/* ============ DESTINATION MARKER (CASEY IN IMAGE 2) ============ */}
        <MapMarker longitude={destination.lng} latitude={destination.lat}>
          <MarkerContent>
            <div className="waypoint-pin destination-pin" title="Destination">
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

        {/* ============ ALL AVAILABLE PORTS (except origin/dest) ============ */}


        {/* ============ GEOGRAPHIC LABELS (ANTARCTICA, WEDDELL SEA, ROSS SEA) ============ */}
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

        {/* ============ PORT LAYER ============ */}
        <PortsLayer locations={locations} originLabel={originLabel} destinationLabel={destinationLabel} />

        {/* ============ NAUTICAL MAP CONTROLS (TOP-LEFT) ============ */}
        <NauticalMapControls onReset={handleReset} />
      </Map>

      {/* Nautical Scale Bar (Bottom-Left in Image 2) */}
      <div className="nautical-scale-bar" aria-label="Nautical scale">
        <div className="scale-marks">
          <span>0</span>
          <span>250</span>
          <span>500</span>
          <span>1,000 km</span>
        </div>
        <div className="scale-line" />
      </div>

      {/* Live Coordinate Readout (Bottom-Left, above scale bar) */}
      {(pointerCoord || clickedCoord) && (
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
