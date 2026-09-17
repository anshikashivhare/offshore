import { useCallback, useEffect, useRef, useMemo } from "react";
import { RotateCcw } from "lucide-react";
import * as MapLibreGL from "maplibre-gl";
import {
  Map,
  MapRoute,
  MapMarker,
  MarkerContent,
  MarkerLabel,
  MapControls,
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

/** Convert an Offshore Coordinate to [lng, lat] tuple for mapcn */
function toLngLat(c: Coordinate): [number, number] {
  return [c.lng, c.lat];
}

/** Route accent color map matching existing Offshore CSS color scheme */
const ROUTE_COLORS: Record<string, string> = {
  teal: "#6dd4c0",
  blue: "#75b9db",
  amber: "#e4ae6b",
  violet: "#c48fd2",
};

const DEFAULT_CENTER: [number, number] = [20, -67];
const DEFAULT_ZOOM = 2.2;

/** Reset viewport button — uses the MapLibre map instance via useMap() */
function ResetButton({ onReset }: { onReset: () => void }) {
  return (
    <div className="map-reset-btn">
      <button onClick={onReset} aria-label="Reset map view" title="Reset map view">
        <RotateCcw size={15} />
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

  const handleRecenter = useCallback(() => {
    // Center between origin and destination
    const centerLng = (origin.lng + destination.lng) / 2;
    const centerLat = (origin.lat + destination.lat) / 2;
    mapRef.current?.flyTo({
      center: [centerLng, centerLat],
      zoom: 3,
      duration: 1200,
    });
  }, [origin, destination]);

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

  return (
    <div className={`map-stage ${pickMode ? "is-picking" : ""}`}>
      <Map
        ref={mapRef}
        theme="dark"
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        projection={projection}
        className="offshore-maplibre"
      >
        {/* Map click handler for pick mode */}
        <MapClickHandler pickMode={pickMode} onPickCoordinate={onPickCoordinate} />

        {/* ============ ROUTE LAYERS ============ */}
        {layers.routes &&
          routeCoordArrays.map(({ route, coords }) => (
            <MapRoute
              key={route.id}
              id={`offshore-route-${route.id}`}
              coordinates={coords}
              color={ROUTE_COLORS[route.accent] || "#6dd4c0"}
              width={route.id === selectedRouteId ? 4 : 2.5}
              opacity={route.id === selectedRouteId ? 1 : 0.55}
              dashArray={route.id === selectedRouteId ? undefined : [6, 4]}
              active={route.id === selectedRouteId}
              activeColor={ROUTE_COLORS[route.accent] || "#6dd4c0"}
              activeWidth={4.5}
              activeOpacity={1}
              onClick={() => onSelectRoute(route.id)}
              interactive
            />
          ))}

        {/* ============ TRACK LAYERS ============ */}
        {layers.tracks &&
          trackCoordArrays.map(({ id, coords }) => (
            <MapRoute
              key={`track-${id}`}
              id={`offshore-track-${id}`}
              coordinates={coords}
              color="#8c9b9f"
              width={1.6}
              opacity={0.52}
              dashArray={[2, 4]}
              interactive={false}
            />
          ))}

        {/* ============ TRAJECTORY LAYERS ============ */}
        {layers.trajectories &&
          trajectoryCoordArrays.map(({ id, coords }) => (
            <MapRoute
              key={`traj-${id}`}
              id={`offshore-traj-${id}`}
              coordinates={coords}
              color="#c993d2"
              width={2}
              opacity={0.9}
              dashArray={[5, 7]}
              interactive={false}
            />
          ))}

        {/* ============ ICEBERG MARKERS ============ */}
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
                  <div className={`iceberg-map-marker ${isActive ? "active" : ""}`}>
                    <svg width="20" height="20" viewBox="0 0 20 20">
                      <polygon
                        points="6,17 8,5 11,2 15,17"
                        fill="#f4e5ca"
                        stroke="#fff0d3"
                        strokeWidth="1"
                      />
                      <circle cx="10" cy="10" r="2" fill="#e9bb7d" />
                    </svg>
                  </div>
                </MarkerContent>
                <MarkerLabel position="top">
                  <span className="iceberg-label">{iceberg.id}</span>
                </MarkerLabel>
              </MapMarker>
            );
          })}

        {/* ============ VESSEL MARKER ============ */}
        {layers.vessel && (
          <MapMarker longitude={origin.lng} latitude={origin.lat}>
            <MarkerContent>
              <div className="vessel-map-marker">
                <div className="vessel-pulse-ring" />
                <div className="vessel-dot" />
              </div>
            </MarkerContent>
            <MarkerLabel position="top">
              <span className="vessel-label">RV AURORA</span>
            </MarkerLabel>
          </MapMarker>
        )}

        {/* ============ ORIGIN MARKER ============ */}
        <MapMarker longitude={origin.lng} latitude={origin.lat}>
          <MarkerContent>
            <div className="endpoint-marker origin" />
          </MarkerContent>
          <MarkerLabel position="bottom">
            <span className="endpoint-label">ORIGIN</span>
          </MarkerLabel>
        </MapMarker>

        {/* ============ DESTINATION MARKER ============ */}
        <MapMarker longitude={destination.lng} latitude={destination.lat}>
          <MarkerContent>
            <div className="endpoint-marker destination" />
          </MarkerContent>
          <MarkerLabel position="bottom">
            <span className="endpoint-label">DESTINATION</span>
          </MarkerLabel>
        </MapMarker>

        {/* ============ MAPCN CONTROLS ============ */}
        <MapControls
          position="top-left"
          showZoom={true}
          showCompass={true}
          showLocate={false}
          showFullscreen={true}
        />

        {/* Reset button (custom, not in mapcn) */}
        <ResetButton onReset={handleReset} />
      </Map>

      {/* Map mode indicator */}
      <div className="map-mode">
        {pickMode ? (
          <>
            <span className="mode-dot" /> Click map to place {pickMode}
          </>
        ) : (
          <>{viewMode === "globe" ? "Globe projection" : "Mercator projection"} · MapLibre</>
        )}
      </div>
    </div>
  );
}
