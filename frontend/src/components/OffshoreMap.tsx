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

function toLngLat(c: Coordinate): [number, number] {
  return [c.lng, c.lat];
}

const ROUTE_COLORS: Record<string, string> = {
  teal: "#527C78",
  blue: "#456E78",
  amber: "#C66B45",
  violet: "#6E7778",
};

const DEFAULT_CENTER: [number, number] = [20, -67];
const DEFAULT_ZOOM = 2.2;

function ResetButton({ onReset }: { onReset: () => void }) {
  return (
    <div className="map-reset-btn">
      <button onClick={onReset} aria-label="Reset map view" title="Reset map view">
        <RotateCcw size={15} />
      </button>
    </div>
  );
}

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
  riskCells: _riskCells,
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

  const routeCoordArrays = useMemo(
    () => routes.map((route) => ({ route, coords: route.geometry.map(toLngLat) })),
    [routes]
  );
  const trackCoordArrays = useMemo(
    () => tracks.map((track) => ({ id: track.icebergId, coords: track.history.map(toLngLat) })),
    [tracks]
  );
  const trajectoryCoordArrays = useMemo(
    () => trajectories.map((traj) => ({ id: traj.icebergId, coords: traj.prediction.map(toLngLat) })),
    [trajectories]
  );

  return (
    <div className={`map-stage ${pickMode ? "is-picking" : ""}`}>
      <Map
        ref={mapRef}
        theme="light"
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        projection={projection}
        className="offshore-maplibre"
      >
        <MapClickHandler pickMode={pickMode} onPickCoordinate={onPickCoordinate} />

        {layers.routes && routeCoordArrays.map(({ route, coords }) => (
          <MapRoute
            key={route.id}
            id={`offshore-route-${route.id}`}
            coordinates={coords}
            color={ROUTE_COLORS[route.accent] || ROUTE_COLORS.teal}
            width={route.id === selectedRouteId ? 4 : 2.25}
            opacity={route.id === selectedRouteId ? 0.98 : 0.48}
            dashArray={route.id === selectedRouteId ? undefined : [6, 4]}
            active={route.id === selectedRouteId}
            activeColor={ROUTE_COLORS[route.accent] || ROUTE_COLORS.teal}
            activeWidth={4.5}
            activeOpacity={1}
            onClick={() => onSelectRoute(route.id)}
            interactive
          />
        ))}

        {layers.tracks && trackCoordArrays.map(({ id, coords }) => (
          <MapRoute
            key={`track-${id}`}
            id={`offshore-track-${id}`}
            coordinates={coords}
            color="#7B898A"
            width={1.4}
            opacity={0.48}
            dashArray={[2, 4]}
            interactive={false}
          />
        ))}

        {layers.trajectories && trajectoryCoordArrays.map(({ id, coords }) => (
          <MapRoute
            key={`traj-${id}`}
            id={`offshore-traj-${id}`}
            coordinates={coords}
            color="#527C78"
            width={2}
            opacity={0.9}
            dashArray={[5, 7]}
            interactive={false}
          />
        ))}

        {layers.icebergs && icebergs.map((iceberg) => {
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
                  <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
                    <polygon points="7,18 8.5,6 12,2.5 16,18" fill="#F3F1EA" stroke="#183B43" strokeWidth="1.2" />
                    <circle cx="11" cy="11.5" r="2.2" fill="#C66B45" />
                  </svg>
                </div>
              </MarkerContent>
              <MarkerLabel position="top">
                <span className="iceberg-label">{iceberg.id}</span>
              </MarkerLabel>
            </MapMarker>
          );
        })}

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

        <MapMarker longitude={origin.lng} latitude={origin.lat}>
          <MarkerContent><div className="endpoint-marker origin" /></MarkerContent>
          <MarkerLabel position="bottom"><span className="endpoint-label">ORIGIN</span></MarkerLabel>
        </MapMarker>

        <MapMarker longitude={destination.lng} latitude={destination.lat}>
          <MarkerContent><div className="endpoint-marker destination" /></MarkerContent>
          <MarkerLabel position="bottom"><span className="endpoint-label">DESTINATION</span></MarkerLabel>
        </MapMarker>

        <MapControls position="top-left" showZoom={true} showCompass={true} showLocate={false} showFullscreen={true} />
        <ResetButton onReset={handleReset} />
      </Map>

      <div className="map-mode">
        {pickMode ? (
          <><span className="mode-dot" /> Click map to place {pickMode}</>
        ) : (
          <>{viewMode === "globe" ? "Globe projection" : "Mercator projection"} · MapLibre</>
        )}
      </div>
    </div>
  );
}
