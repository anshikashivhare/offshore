import { useCallback, useEffect, useRef, useMemo } from "react";
import { Compass, Minus, Plus, RotateCcw } from "lucide-react";
import * as MapLibreGL from "maplibre-gl";
import {
  Map,
  MapRoute,
  MapMarker,
  MarkerContent,
  MarkerLabel,
  useMap,
  type MapRef,
} from "./map-components";
import type {
  Coordinate,
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
  destination: Coordinate;
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

/** Click handler component that registers map click for pick mode */
function MapClickHandler({
  pickMode,
  onPickCoordinate,
}: {
  pickMode: "origin" | "destination" | null;
  onPickCoordinate: (coordinate: Coordinate) => void;
}) {
  const { map } = useMap();

  useEffect(() => {
    if (!map || !pickMode) return;

    const handler = (e: MapLibreGL.MapMouseEvent) => {
      onPickCoordinate({ lat: e.lngLat.lat, lng: e.lngLat.lng });
    };

    map.on("click", handler);
    map.getCanvas().style.cursor = "crosshair";

    return () => {
      map.off("click", handler);
      map.getCanvas().style.cursor = "";
    };
  }, [map, pickMode, onPickCoordinate]);

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
 * Fires exactly once after the map is ready and fits the initial viewport
 * to the bounding box of the supplied route coordinates (origin + destination
 * + waypoints), with comfortable padding and a maximum-zoom cap.
 *
 * A ref guard prevents re-firing after the user manually interacts.
 */
function InitialViewFitter({
  coords,
}: {
  coords: [number, number][];
}) {
  const { map, isLoaded } = useMap();
  const fittedRef = useRef(false);

  useEffect(() => {
    if (!map || !isLoaded || fittedRef.current || coords.length < 2) return;
    fittedRef.current = true;

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
        duration: 0, // instant on first load, no animation jank
      }
    );
  }, [map, isLoaded, coords]);

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
  destination,
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

  // Coords for the initial viewport fit: origin + destination + selected route geometry.
  // Stable reference so InitialViewFitter's effect doesn't re-run on unrelated renders.
  const initialFitCoordsRef = useRef<[number, number][] | null>(null);
  const initialFitCoords = useMemo(() => {
    if (initialFitCoordsRef.current) return initialFitCoordsRef.current;
    const selectedRoute = routes.find((r) => r.id === selectedRouteId) ?? routes[0];
    const pts: [number, number][] = [
      [origin.lng, origin.lat],
      [destination.lng, destination.lat],
      ...(selectedRoute ? selectedRoute.geometry.map(toLngLat) : []),
    ];
    initialFitCoordsRef.current = pts;
    return pts;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally empty — captures first-render values only

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

  // Polar Graticules (Latitude Parallels: 50°S, 60°S, 70°S, 80°S)
  const parallels = useMemo(() => {
    const lats = [-50, -60, -70, -80];
    return lats.map((lat) => {
      const coords: [number, number][] = [];
      for (let lng = -180; lng <= 180; lng += 10) {
        coords.push([lng, lat]);
      }
      return { lat, coords };
    });
  }, []);

  // Polar Meridians (Longitude: -30, 0, 30, 60, 90, 120)
  const meridians = useMemo(() => {
    const lngs = [-30, 0, 30, 60, 90, 120];
    return lngs.map((lng) => {
      const coords: [number, number][] = [
        [lng, -45],
        [lng, -88],
      ];
      return { lng, coords };
    });
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
        <MapClickHandler pickMode={pickMode} onPickCoordinate={onPickCoordinate} />
        {/* Suppress unwanted basemap labels (duplicate ANTARCTICA, RGåbøya, etc.) */}
        <MapLabelSuppressor />
        {/* Fit the initial viewport to the route corridor on first load only */}
        <InitialViewFitter coords={initialFitCoords} />

        {/* ============ POLAR GRATICULES (PARALLELS & MERIDIANS) ============ */}
        {parallels.map(({ lat, coords }) => (
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
        ))}
        {meridians.map(({ lng, coords }) => (
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
            <div className="waypoint-pin origin-pin">
              <span className="waypoint-inner-dot" />
            </div>
          </MarkerContent>
          <MarkerLabel>
            <span className="waypoint-label">Rothera</span>
          </MarkerLabel>
        </MapMarker>

        {/* ============ DESTINATION MARKER (CASEY IN IMAGE 2) ============ */}
        <MapMarker longitude={destination.lng} latitude={destination.lat}>
          <MarkerContent>
            <div className="waypoint-pin destination-pin">
              <span className="waypoint-inner-dot" />
            </div>
          </MarkerContent>
          <MarkerLabel>
            <span className="waypoint-label">Casey</span>
          </MarkerLabel>
        </MapMarker>

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
    </div>
  );
}
