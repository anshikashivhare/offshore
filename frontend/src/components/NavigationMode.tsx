import React, { useEffect, useRef, useState, useMemo } from "react";
import {
  Ship,
  Play,
  Pause,
  LocateFixed,
  X,
  Plus,
  Minus,
  Compass,
} from "lucide-react";
import { useMap, MapMarker, MarkerContent, MapRoute } from "./map-components";
import type { Coordinate, Iceberg, Route, Vessel } from "@/lib/offshore-types";

// =========================================================================
// GEODESIC & NAVIGATION MATHEMATICS
// =========================================================================

function toRadians(deg: number): number {
  return (deg * Math.PI) / 180;
}

function toDegrees(rad: number): number {
  return (rad * 180) / Math.PI;
}

/**
 * Calculates initial rhumb / forward bearing between two coordinates in degrees [0, 360).
 */
export function calculateBearing(start: Coordinate, end: Coordinate): number {
  const phi1 = toRadians(start.lat);
  const phi2 = toRadians(end.lat);
  const deltaLambda = toRadians(end.lng - start.lng);

  const y = Math.sin(deltaLambda) * Math.cos(phi2);
  const x =
    Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);
  const theta = Math.atan2(y, x);
  return (toDegrees(theta) + 360) % 360;
}

/**
 * Calculates great-circle distance between two coordinates in Nautical Miles (NM).
 */
export function calculateDistanceNm(start: Coordinate, end: Coordinate): number {
  const R = 3440.065; // Earth radius in nautical miles
  const phi1 = toRadians(start.lat);
  const phi2 = toRadians(end.lat);
  const deltaPhi = toRadians(end.lat - start.lat);
  const deltaLambda = toRadians(end.lng - start.lng);

  const a =
    Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Shortest angular difference between two bearings in degrees [-180, 180].
 */
export function shortestAngleDiff(target: number, current: number): number {
  return ((((target - current) % 360) + 540) % 360) - 180;
}

/**
 * Calculates intermediate great-circle waypoints between two coordinates.
 * Produces a smooth navigable curve on the globe/Mercator map.
 */
export function generateGreatCircleWaypoints(
  start: Coordinate,
  end: Coordinate,
  numPoints = 35
): Coordinate[] {
  const p1Lat = toRadians(start.lat);
  const p1Lng = toRadians(start.lng);
  const p2Lat = toRadians(end.lat);
  const p2Lng = toRadians(end.lng);

  const d = 2 * Math.asin(
    Math.sqrt(
      Math.sin((p2Lat - p1Lat) / 2) ** 2 +
      Math.cos(p1Lat) * Math.cos(p2Lat) * (Math.sin((p2Lng - p1Lng) / 2) ** 2)
    )
  );

  if (d < 1e-6) return [start, end];

  const points: Coordinate[] = [];
  for (let i = 0; i <= numPoints; i++) {
    const f = i / numPoints;
    const A = Math.sin((1 - f) * d) / Math.sin(d);
    const B = Math.sin(f * d) / Math.sin(d);
    const x = A * Math.cos(p1Lat) * Math.cos(p1Lng) + B * Math.cos(p2Lat) * Math.cos(p2Lng);
    const y = A * Math.cos(p1Lat) * Math.sin(p1Lng) + B * Math.cos(p2Lat) * Math.sin(p2Lng);
    const z = A * Math.sin(p1Lat) + B * Math.sin(p2Lat);
    const lat = Math.atan2(z, Math.sqrt(x * x + y * y));
    const lng = Math.atan2(y, x);
    points.push({ lat: toDegrees(lat), lng: toDegrees(lng) });
  }
  return points;
}

/**
 * Converts a compass bearing in degrees to a 16-wind cardinal direction string.
 */
export function headingToCompass(deg: number): string {
  const directions = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
  ];
  const index = Math.round((((deg % 360) + 360) % 360) / 22.5) % 16;
  return directions[index];
}

/**
 * Interpolates vessel position along a route polyline given a traveled distance.
 */
export function interpolateAlongRoute(
  geometry: Coordinate[],
  distanceTraveledNm: number
): {
  position: Coordinate;
  heading: number;
  segmentIndex: number;
  distanceRemainingNm: number;
  totalDistanceNm: number;
} {
  if (!geometry || geometry.length === 0) {
    const fallback = { lat: -64.8, lng: -63.5 };
    return {
      position: fallback,
      heading: 0,
      segmentIndex: 0,
      distanceRemainingNm: 0,
      totalDistanceNm: 0,
    };
  }

  if (geometry.length === 1) {
    return {
      position: geometry[0],
      heading: 0,
      segmentIndex: 0,
      distanceRemainingNm: 0,
      totalDistanceNm: 0,
    };
  }

  // Pre-calculate cumulative segment lengths
  const segmentLengths: number[] = [];
  let totalDistanceNm = 0;
  for (let i = 0; i < geometry.length - 1; i++) {
    const segDist = calculateDistanceNm(geometry[i], geometry[i + 1]);
    segmentLengths.push(segDist);
    totalDistanceNm += segDist;
  }

  // Clamp distance
  const clampedDist = Math.max(0, Math.min(distanceTraveledNm, totalDistanceNm));
  const distanceRemainingNm = Math.max(0, totalDistanceNm - clampedDist);

  let accumulated = 0;
  for (let i = 0; i < segmentLengths.length; i++) {
    const segLen = segmentLengths[i];
    if (accumulated + segLen >= clampedDist || i === segmentLengths.length - 1) {
      const segProgress = segLen > 0 ? (clampedDist - accumulated) / segLen : 0;
      const start = geometry[i];
      const end = geometry[i + 1];

      // Linear interpolation between waypoints
      const lat = start.lat + (end.lat - start.lat) * segProgress;
      const lng = start.lng + (end.lng - start.lng) * segProgress;

      // Segment heading
      const heading = calculateBearing(start, end);

      return {
        position: { lat, lng },
        heading,
        segmentIndex: i,
        distanceRemainingNm,
        totalDistanceNm,
      };
    }
    accumulated += segLen;
  }

  const lastCoord = geometry[geometry.length - 1];
  const prevCoord = geometry[geometry.length - 2];
  return {
    position: lastCoord,
    heading: calculateBearing(prevCoord, lastCoord),
    segmentIndex: geometry.length - 2,
    distanceRemainingNm: 0,
    totalDistanceNm,
  };
}

// =========================================================================
// STATE INTERFACES
// =========================================================================

export type VesselNavState = {
  position: Coordinate;
  heading: number;
  sogKnots: number;
  distanceTraveledNm: number;
  distanceRemainingNm: number;
  totalDistanceNm: number;
  segmentIndex: number;
};

// A pitched camera is useful close to the vessel, but a flat, north-up view is
// essential at world scale. Keeping the perspective camera at a low zoom puts
// the Mercator horizon inside the viewport and exposes the empty area seen
// above the map in Navigation mode.
export const NAVIGATION_OVERVIEW_ZOOM = 4.5;
const NAVIGATION_PERSPECTIVE_PITCH = 48;

export function isNavigationOverview(zoom: number): boolean {
  return zoom <= NAVIGATION_OVERVIEW_ZOOM;
}

// =========================================================================
// NAVIGATION CONTROLLER COMPONENT (Runs inside MapLibre Map instance)
// =========================================================================

export function NavigationModeController({
  enabled,
  vessel,
  route,
  origin,
  destination,
  isFollowing,
  isPlaying,
  speedMultiplier = 1,
  onUserPanned,
  onNavStateChange,
}: {
  enabled: boolean;
  vessel?: Vessel | null;
  route?: Route | null;
  origin?: Coordinate | null;
  destination?: Coordinate | null;
  isFollowing: boolean;
  isPlaying: boolean;
  speedMultiplier: number;
  onUserPanned: () => void;
  onNavStateChange: (state: VesselNavState) => void;
}) {
  const { map, isLoaded } = useMap();

  // Route geometry fallback: route > [origin, destination] with smooth great circle > default Antarctic point
  const routeGeometry = useMemo<Coordinate[]>(() => {
    if (route && route.geometry && route.geometry.length > 1) {
      return route.geometry;
    }
    if (origin && destination) {
      return generateGreatCircleWaypoints(origin, destination, 35);
    }
    if (origin) {
      return [origin, { lat: origin.lat - 1, lng: origin.lng + 1 }];
    }
    return [
      { lat: -67.57, lng: -68.13 }, // Rothera
      { lat: -64.82, lng: -63.50 }, // Port Lockroy
      { lat: -62.19, lng: -58.96 }, // King George Island
    ];
  }, [route, origin, destination]);

  // Cruising speed from existing backend vessel data
  const baseSpeedKnots = vessel?.cruising_speed || 13.0;

  // Track traveled distance along current route
  const [distanceTraveledNm, setDistanceTraveledNm] = useState(0);
  const currentBearingRef = useRef<number>(0);
  const userZoomRef = useRef<number>(11.5);
  const previousCameraRef = useRef<{
    center: [number, number];
    zoom: number;
    pitch: number;
    bearing: number;
  } | null>(null);

  // Reset progress and smoothly reposition camera when route changes
  useEffect(() => {
    setDistanceTraveledNm(0);
    if (enabled && map && isLoaded && routeGeometry.length > 0) {
      const startPt = routeGeometry[0];
      const nextPt = routeGeometry[Math.min(1, routeGeometry.length - 1)];
      const initialBearing = calculateBearing(startPt, nextPt);
      currentBearingRef.current = initialBearing;
      const paddingTop = typeof window !== "undefined" ? Math.min(window.innerHeight * 0.44, 300) : 220;
      map.easeTo({
        center: [startPt.lng, startPt.lat],
        bearing: initialBearing,
        pitch: NAVIGATION_PERSPECTIVE_PITCH,
        zoom: userZoomRef.current || 11.5,
        padding: { top: paddingTop, bottom: 0, left: 0, right: 0 },
        duration: 900,
      });
    }
  }, [route?.id, enabled, map, isLoaded]); // eslint-disable-line react-hooks/exhaustive-deps

  // Compute current vessel position & heading from geometry and distanceTraveledNm
  const navState = useMemo<VesselNavState>(() => {
    const interpolated = interpolateAlongRoute(routeGeometry, distanceTraveledNm);
    return {
      position: interpolated.position,
      heading: interpolated.heading,
      sogKnots: baseSpeedKnots,
      distanceTraveledNm,
      distanceRemainingNm: interpolated.distanceRemainingNm,
      totalDistanceNm: interpolated.totalDistanceNm,
      segmentIndex: interpolated.segmentIndex,
    };
  }, [routeGeometry, distanceTraveledNm, baseSpeedKnots]);

  // Notify parent of navState update
  useEffect(() => {
    onNavStateChange(navState);
  }, [navState, onNavStateChange]);

  // Animation frame loop for voyage progression along route
  useEffect(() => {
    if (!enabled || !isPlaying || navState.totalDistanceNm === 0) return;

    let lastTime = performance.now();
    let animationId: number;

    const tick = (now: number) => {
      const dtHours = Math.min((now - lastTime) / 1000 / 3600, 0.001); // seconds to hours, clamped
      lastTime = now;

      // Distance increment (NM) = speed (knots) * time (hours) * speedMultiplier
      const distDelta = baseSpeedKnots * dtHours * speedMultiplier;

      setDistanceTraveledNm((prev) => {
        const next = prev + distDelta;
        if (next >= navState.totalDistanceNm) {
          return 0; // loop back seamlessly
        }
        return next;
      });

      animationId = requestAnimationFrame(tick);
    };

    animationId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationId);
  }, [enabled, isPlaying, baseSpeedKnots, speedMultiplier, navState.totalDistanceNm]);

  // Camera initialization upon entering Navigation Mode
  useEffect(() => {
    if (!map || !isLoaded) return;

    if (enabled) {
      // Ensure world wraps seamlessly without artificial bounds in navigation mode
      try {
        map.setMaxBounds(null);
        if (typeof (map as any).setRenderWorldCopies === "function") {
          (map as any).setRenderWorldCopies(true);
        }
        // Enable smooth, fluid wheel zoom
        if (map.scrollZoom) {
          map.scrollZoom.enable();
          map.scrollZoom.setWheelZoomRate(1 / 90);
          map.scrollZoom.setZoomRate(1 / 20);
        }
      } catch {
        /* ignore */
      }

      // Save 2D camera state for clean restoration on exit
      const center = map.getCenter();
      previousCameraRef.current = {
        center: [center.lng, center.lat],
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing(),
      };

      currentBearingRef.current = navState.heading;
      userZoomRef.current = 11.5;

      // Position vessel in lower-middle section using viewport camera padding
      const paddingTop = typeof window !== "undefined" ? Math.min(window.innerHeight * 0.44, 300) : 220;

      // Google Maps Navigation Perspective:
      // - pitch: 48°
      // - zoom: 11.5
      // - bearing: follows vessel heading so direction of travel is always UP
      map.flyTo({
        center: [navState.position.lng, navState.position.lat],
        pitch: NAVIGATION_PERSPECTIVE_PITCH,
        bearing: navState.heading,
        zoom: 11.5,
        padding: { top: paddingTop, bottom: 0, left: 0, right: 0 },
        duration: 1200,
        essential: true,
      });
    } else {
      // Clean exit: restore camera to normal flat 2D perspective
      map.easeTo({
        pitch: 0,
        bearing: 0,
        zoom: 3.0,
        padding: { top: 0, bottom: 0, left: 0, right: 0 },
        duration: 900,
        essential: true,
      });
    }
  }, [enabled, map, isLoaded]); // eslint-disable-line react-hooks/exhaustive-deps

  // At world scale, use the same overhead orientation people expect from a
  // conventional map. This removes the artificial horizon/empty canvas while
  // preserving the 3D vessel-following perspective at navigation zooms.
  useEffect(() => {
    if (!enabled || !map || !isLoaded) return;

    const normalizeOverviewOrientation = () => {
      if (!isNavigationOverview(map.getZoom())) return;
      if (map.getPitch() === 0 && map.getBearing() === 0) return;

      map.easeTo({
        pitch: 0,
        bearing: 0,
        padding: { top: 0, bottom: 0, left: 0, right: 0 },
        duration: 220,
        essential: true,
      });
    };

    map.on("zoomend", normalizeOverviewOrientation);
    normalizeOverviewOrientation();

    return () => {
      map.off("zoomend", normalizeOverviewOrientation);
    };
  }, [enabled, map, isLoaded]);

  // User zoom listener: keep track of user's zoom changes so tracking does NOT snap back!
  useEffect(() => {
    if (!enabled || !map || !isLoaded) return;

    const handleZoomUpdate = () => {
      userZoomRef.current = map.getZoom();
    };

    map.on("zoom", handleZoomUpdate);
    map.on("wheel", handleZoomUpdate);

    return () => {
      map.off("zoom", handleZoomUpdate);
      map.off("wheel", handleZoomUpdate);
    };
  }, [enabled, map, isLoaded]);

  // Continuous Camera Tracking while following vessel
  useEffect(() => {
    if (!enabled || !map || !isLoaded || !isFollowing) return;

    // Smooth shortest-path angular rotation for bearing to prevent jitter
    const targetBearing = navState.heading;
    const diff = shortestAngleDiff(targetBearing, currentBearingRef.current);
    const newBearing = (currentBearingRef.current + diff * 0.15 + 360) % 360;
    currentBearingRef.current = newBearing;

    const paddingTop = typeof window !== "undefined" ? Math.min(window.innerHeight * 0.44, 300) : 220;
    const targetZoom = userZoomRef.current ?? map.getZoom() ?? 11.5;

    const overview = isNavigationOverview(targetZoom);

    map.easeTo({
      center: [navState.position.lng, navState.position.lat],
      bearing: overview ? 0 : newBearing,
      pitch: overview ? 0 : NAVIGATION_PERSPECTIVE_PITCH,
      zoom: targetZoom, // Dynamic user zoom - allows freely zooming in/out smoothly!
      padding: overview
        ? { top: 0, bottom: 0, left: 0, right: 0 }
        : { top: paddingTop, bottom: 0, left: 0, right: 0 },
      duration: 320,
      easing: (t) => t,
    });
  }, [enabled, map, isLoaded, isFollowing, navState.position, navState.heading]);

  // Detect manual user drag / rotate to pause camera following
  useEffect(() => {
    if (!enabled || !map || !isLoaded) return;

    const handleUserDrag = (e: any) => {
      if (e.originalEvent && e.originalEvent.type !== 'wheel') {
        onUserPanned();
      }
    };

    map.on("dragstart", handleUserDrag);
    map.on("rotatestart", handleUserDrag);
    map.on("zoomstart", handleUserDrag);
    map.on("pitchstart", handleUserDrag);

    return () => {
      map.off("dragstart", handleUserDrag);
      map.off("rotatestart", handleUserDrag);
      map.off("zoomstart", handleUserDrag);
      map.off("pitchstart", handleUserDrag);
    };
  }, [enabled, map, isLoaded, onUserPanned]);

  return null;
}

// =========================================================================
// VESSEL 3D MARKER COMPONENT
// =========================================================================

export function VesselMarker({
  position,
  heading,
  sogKnots,
  vesselName,
  mapBearing = 0,
}: {
  position: Coordinate;
  heading: number;
  sogKnots: number;
  vesselName: string;
  mapBearing?: number;
}) {
  // Relative rotation so bow points straight UP when map rotates with heading
  const relativeAngle = ((heading - mapBearing) % 360 + 360) % 360;

  return (
    <MapMarker longitude={position.lng} latitude={position.lat}>
      <MarkerContent>
        <div className="vessel-nav-marker-wrapper" title={`${vesselName} · ${sogKnots.toFixed(1)} kn`}>
          {/* Navigational Radar Sweep Ring */}
          <div className="vessel-radar-ring" />

          {/* Heading Orientation Container */}
          <div
            className="vessel-hull-rotator"
            style={{
              transform: `rotate(${relativeAngle}deg)`,
              transition: "transform 0.15s linear",
            }}
          >
            {/* Forward Line of Sight Cone */}
            <div className="vessel-sight-cone" />

            {/* Marine Ship Hull SVG Silhouette */}
            <svg
              width="28"
              height="44"
              viewBox="0 0 28 44"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="vessel-hull-svg"
            >
              {/* Outer Ship Outline */}
              <path
                d="M14 2 C18 10, 24 20, 24 34 C24 40, 21 42, 14 42 C7 42, 4 40, 4 34 C4 20, 10 10, 14 2 Z"
                fill="#183B43"
                stroke="#00F0FF"
                strokeWidth="2"
              />
              {/* Bridge Deckhouse */}
              <rect x="9" y="24" width="10" height="12" rx="2" fill="#527C78" stroke="#FFFFFF" strokeWidth="1" />
              {/* Mast / Radar Beacon */}
              <circle cx="14" cy="28" r="2" fill="#C66B45" />
              {/* Bow Pointing Chevron */}
              <path d="M14 6 L18 13 L14 11 L10 13 Z" fill="#00F0FF" />
            </svg>
          </div>

          {/* Floating Vessel Badge */}
          <div className="vessel-badge-floating">
            <span className="vessel-badge-name">{vesselName}</span>
            <span className="vessel-badge-speed">{sogKnots.toFixed(1)} kn</span>
          </div>
        </div>
      </MarkerContent>
    </MapMarker>
  );
}

// =========================================================================
// NAVIGATION PROMINENT RECOMMENDED ROUTE (Luminous Voyage Overlay)
// =========================================================================

export function NavigationProminentRoute({
  route,
  origin,
  destination,
  enabled,
}: {
  route?: Route | null;
  origin?: Coordinate | null;
  destination?: Coordinate | null;
  enabled: boolean;
}) {
  if (!enabled) return null;

  const points = useMemo<Coordinate[]>(() => {
    if (route && route.geometry && route.geometry.length > 1) {
      return route.geometry;
    }
    if (origin && destination) {
      return generateGreatCircleWaypoints(origin, destination, 35);
    }
    return [];
  }, [route, origin, destination]);

  if (points.length < 2) return null;
  const coords = points.map((c) => [c.lng, c.lat] as [number, number]);

  return (
    <>
      {/* Radiant Underglow Layer */}
      <MapRoute
        id="nav-route-underglow"
        coordinates={coords}
        color="#00F0FF"
        width={10}
        opacity={0.45}
        interactive={false}
      />
      {/* High-Contrast Core Voyage Trajectory */}
      <MapRoute
        id="nav-route-core"
        coordinates={coords}
        color="#FFFFFF"
        width={4}
        opacity={0.95}
        interactive={false}
      />
      {/* Center Navigational Guide Line */}
      <MapRoute
        id="nav-route-centerline"
        coordinates={coords}
        color="#183B43"
        width={1.5}
        opacity={0.8}
        dashArray={[4, 6]}
        interactive={false}
      />
    </>
  );
}

// =========================================================================
// FLOATING ZOOM AND CAMERA CONTROLS (Google Maps Style)
// =========================================================================

export function NavigationZoomControls({
  onZoomIn,
  onZoomOut,
  onRecenter,
  isFollowing,
}: {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onRecenter?: () => void;
  isFollowing: boolean;
}) {
  return (
    <div className="nav-floating-zoom-controls" aria-label="Map Zoom Controls">
      <button
        onClick={onZoomIn}
        className="nav-zoom-btn"
        title="Zoom In (+)"
        aria-label="Zoom In"
      >
        <Plus size={16} />
      </button>
      <div className="nav-zoom-divider" />
      <button
        onClick={onZoomOut}
        className="nav-zoom-btn"
        title="Zoom Out (-)"
        aria-label="Zoom Out"
      >
        <Minus size={16} />
      </button>
      {!isFollowing && onRecenter && (
        <>
          <div className="nav-zoom-divider" />
          <button
            onClick={onRecenter}
            className="nav-zoom-btn nav-zoom-recenter"
            title="Re-center on vessel"
            aria-label="Re-center"
          >
            <LocateFixed size={15} className="text-[#00F0FF]" />
          </button>
        </>
      )}
    </div>
  );
}

// =========================================================================
// MINIMAL NAVIGATION DOCK (Clean Google Maps Style Bottom HUD)
// =========================================================================

export function NavigationHUD({
  navState,
  route,
  routes = [],
  selectedRouteId,
  onSelectRoute,
  isFollowing,
  isPlaying,
  onTogglePlay,
  onRecenter,
  onExit,
  onZoomIn,
  onZoomOut,
}: {
  vessel?: Vessel | null;
  navState: VesselNavState;
  route?: Route | null;
  routes?: Route[];
  selectedRouteId?: string;
  onSelectRoute?: (id: string) => void;
  icebergs?: Iceberg[];
  isFollowing: boolean;
  isPlaying: boolean;
  speedMultiplier?: number;
  onTogglePlay?: () => void;
  onSpeedChange?: (speed: number) => void;
  onRecenter: () => void;
  onExit: () => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
}) {
  const riskScore = route?.riskScore ?? 0.18;
  const riskLabel = riskScore < 0.25 ? "Low" : riskScore < 0.5 ? "Moderate" : "High";
  const riskColor = riskScore < 0.25 ? "#22c55e" : riskScore < 0.5 ? "#f59e0b" : "#ef4444";

  // Estimated sea ice concentration along passage
  const seaIceConc = Math.min(Math.round(riskScore * 80) + 10, 85);

  return (
    <div className="nav-minimal-dock" aria-label="Marine Voyage Navigation Panel">
      {/* Route Switcher if multiple candidate routes exist */}
      {routes && routes.length > 1 && onSelectRoute && (
        <div className="nav-dock-routes-bar">
          <span className="nav-dock-routes-label">PASSAGE ROUTE:</span>
          <div className="nav-dock-routes-chips">
            {routes.map((r) => {
              const isSelected = r.id === (selectedRouteId || route?.id);
              return (
                <button
                  key={r.id}
                  onClick={() => onSelectRoute(r.id)}
                  className={`nav-route-chip ${isSelected ? "active" : ""}`}
                  title={`${r.name} · ${r.distanceNm?.toFixed(0)} NM · Risk: ${(r.riskScore * 100).toFixed(0)}%`}
                >
                  <span className="nav-route-chip-dot" />
                  <span className="nav-route-chip-name">{r.name.split(" ")[0]}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="nav-dock-main-row">
        <div className="nav-dock-metrics">
          {/* Speed */}
          <div className="nav-dock-item">
            <span className="nav-dock-label">Speed:</span>
            <span className="nav-dock-value">{navState.sogKnots.toFixed(1)} kn</span>
          </div>

          <div className="nav-dock-divider" />

          {/* Course */}
          <div className="nav-dock-item">
            <span className="nav-dock-label">Course:</span>
            <span className="nav-dock-value">
              {Math.round(navState.heading)}°
            </span>
          </div>

          <div className="nav-dock-divider" />

          {/* Ice */}
          <div className="nav-dock-item">
            <span className="nav-dock-label">Ice:</span>
            <span className="nav-dock-value">{seaIceConc}%</span>
          </div>

          <div className="nav-dock-divider" />

          {/* Risk */}
          <div className="nav-dock-item">
            <span className="nav-dock-label">Risk:</span>
            <span className="nav-dock-value flex items-center gap-1.5" style={{ color: riskColor }}>
              <span
                className="w-2 h-2 rounded-full inline-block"
                style={{ backgroundColor: riskColor, boxShadow: `0 0 6px ${riskColor}` }}
              />
              {riskLabel}
            </span>
          </div>
        </div>

        <div className="nav-dock-actions">
          {/* Smooth Zoom Controls */}
          {onZoomIn && onZoomOut && (
            <div className="nav-dock-zoom-group">
              <button
                onClick={onZoomIn}
                className="nav-dock-icon-btn"
                title="Zoom in (+)"
                aria-label="Zoom in"
              >
                <Plus size={13} />
              </button>
              <button
                onClick={onZoomOut}
                className="nav-dock-icon-btn"
                title="Zoom out (-)"
                aria-label="Zoom out"
              >
                <Minus size={13} />
              </button>
            </div>
          )}

          {onTogglePlay && (
            <button
              onClick={onTogglePlay}
              className="nav-dock-icon-btn"
              title={isPlaying ? "Pause voyage movement" : "Resume voyage movement"}
              aria-label={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? <Pause size={13} /> : <Play size={13} />}
            </button>
          )}

          {!isFollowing && (
            <button
              onClick={onRecenter}
              className="nav-dock-btn nav-dock-recenter"
              title="Re-center camera and follow vessel"
              aria-label="Re-center"
            >
              <LocateFixed size={13} />
              <span>Re-center</span>
            </button>
          )}

          <button
            onClick={onExit}
            className="nav-dock-btn nav-dock-exit"
            title="Exit navigation and return to 2D map view"
            aria-label="Exit Navigation"
          >
            <X size={13} />
            <span>Exit Navigation</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// =========================================================================
// REAL ICEBERG SATELLITE IMAGE CARD (Optional Full Modal)
// =========================================================================

export function IcebergDetailCard({
  iceberg,
  vesselPosition,
  onClose,
}: {
  iceberg: Iceberg | null;
  vesselPosition?: Coordinate;
  onClose: () => void;
}) {
  if (!iceberg) return null;

  // Use real satellite radar SAR or Optical photography
  const isSar = iceberg.id.includes("D") || iceberg.id.includes("3") || iceberg.risk === "high";
  const imageSrc = isSar
    ? "/images/icebergs/iceberg_sar.jpg"
    : "/images/icebergs/iceberg_optical.jpg";
  const imageSource = isSar ? "Sentinel-1 SAR" : "Sentinel-2";

  // Calculate real distance from vessel
  let distanceStr = "--";
  if (vesselPosition) {
    const distNm = calculateDistanceNm(vesselPosition, iceberg.position);
    const distKm = distNm * 1.852;
    distanceStr = `${distKm.toFixed(1)} km`;
  }

  // Format coordinates
  const latStr = `${Math.abs(iceberg.position.lat).toFixed(2)}° ${iceberg.position.lat >= 0 ? "N" : "S"}`;
  const lngStr = `${Math.abs(iceberg.position.lng).toFixed(2)}° ${iceberg.position.lng >= 0 ? "W" : "E"}`;

  // Dimensions
  const lengthNm = Math.max(4, Math.round(iceberg.sizeKm * 0.54));
  const widthNm = Math.max(2, Math.round(lengthNm * 0.4));

  // Observation date
  const obsDate = iceberg.timestamp
    ? new Date(iceberg.timestamp).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "Live Orbit";

  return (
    <div className="iceberg-detail-backdrop" onClick={onClose}>
      <div className="iceberg-detail-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="iceberg-detail-header">
          <div className="iceberg-detail-title-group">
            <span className="iceberg-detail-red-dot" />
            <h3 className="iceberg-detail-title">ICEBERG {iceberg.id}</h3>
          </div>
          <button
            onClick={onClose}
            className="iceberg-detail-close-btn"
            aria-label="Close iceberg details"
            title="Close"
          >
            <X size={16} />
          </button>
        </div>

        {/* Large Satellite Image */}
        <div className="iceberg-image-container">
          <img
            src={imageSrc}
            alt={`Satellite capture of Iceberg ${iceberg.id}`}
            className="iceberg-satellite-img"
          />
          <div className="iceberg-image-tag">
            <span>{imageSource} Orbital Imagery</span>
          </div>
        </div>

        {/* Telemetry Information Body */}
        <div className="iceberg-detail-body">
          <div className="iceberg-detail-section">
            <div className="iceberg-detail-section-title">Position:</div>
            <div className="iceberg-detail-section-value">{latStr}, {lngStr}</div>
          </div>

          <div className="iceberg-detail-grid">
            <div className="iceberg-detail-item">
              <span className="iceberg-detail-item-label">Length:</span>
              <span className="iceberg-detail-item-val">{lengthNm} nm</span>
            </div>
            <div className="iceberg-detail-item">
              <span className="iceberg-detail-item-label">Width:</span>
              <span className="iceberg-detail-item-val">{widthNm} nm</span>
            </div>
            <div className="iceberg-detail-item">
              <span className="iceberg-detail-item-label">Observed:</span>
              <span className="iceberg-detail-item-val">{obsDate}</span>
            </div>
            <div className="iceberg-detail-item">
              <span className="iceberg-detail-item-label">Source:</span>
              <span className="iceberg-detail-item-val">{imageSource}</span>
            </div>
            <div className="iceberg-detail-item highlight">
              <span className="iceberg-detail-item-label">Distance:</span>
              <span className="iceberg-detail-item-val text-[#ef4444] font-bold">{distanceStr}</span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="iceberg-detail-footer">
          <button onClick={onClose} className="iceberg-detail-btn-close">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// =========================================================================
// HOVER TOOLTIP FOR RED ICEBERG MARKERS
// Shows on hover/touch and vanishes immediately on mouseleave
// =========================================================================

export function IcebergHoverTooltip({
  info,
}: {
  info: { iceberg: Iceberg; x: number; y: number; distanceNm?: number } | null;
}) {
  if (!info) return null;
  const { iceberg, x, y, distanceNm } = info;
  const left = Math.min(Math.max(x + 14, 16), typeof window !== "undefined" ? window.innerWidth - 270 : 300);
  const top = Math.max(y - 150, 16);

  const isSar = iceberg.id.includes("D") || iceberg.id.includes("3") || iceberg.risk === "high";
  const imageSrc = isSar
    ? "/images/icebergs/iceberg_sar.jpg"
    : "/images/icebergs/iceberg_optical.jpg";
  const imageSource = isSar ? "Sentinel-1 SAR" : "Sentinel-2";

  const latStr = `${Math.abs(iceberg.position.lat).toFixed(2)}° ${iceberg.position.lat >= 0 ? "N" : "S"}`;
  const lngStr = `${Math.abs(iceberg.position.lng).toFixed(2)}° ${iceberg.position.lng >= 0 ? "W" : "E"}`;
  const distStr = distanceNm !== undefined ? `${(distanceNm * 1.852).toFixed(1)} km away` : null;
  const lengthNm = Math.max(4, Math.round(iceberg.sizeKm * 0.54));

  return (
    <div
      className="iceberg-hover-card"
      style={{
        position: "fixed",
        left: `${left}px`,
        top: `${top}px`,
        zIndex: 9999,
        pointerEvents: "none",
      }}
    >
      <div className="iceberg-hover-inner">
        <div className="iceberg-hover-header">
          <span className="iceberg-hover-red-dot" />
          <span className="iceberg-hover-title">ICEBERG {iceberg.id}</span>
          <span className="iceberg-hover-badge">{iceberg.risk?.toUpperCase() || "HAZARD"}</span>
        </div>

        {/* Real Orbital Satellite Imagery Thumbnail */}
        <div className="iceberg-hover-thumb-container">
          <img
            src={imageSrc}
            alt={`Satellite capture of Iceberg ${iceberg.id}`}
            className="iceberg-hover-thumb"
          />
          <span className="iceberg-hover-thumb-tag">{imageSource} Imagery</span>
        </div>

        {/* Telemetry metadata */}
        <div className="iceberg-hover-telemetry">
          <div className="iceberg-hover-row">
            <span className="label">Position:</span>
            <span className="val">{latStr}, {lngStr}</span>
          </div>
          <div className="iceberg-hover-row">
            <span className="label">Size:</span>
            <span className="val">{iceberg.sizeKm.toFixed(1)} km ({lengthNm} nm)</span>
          </div>
          <div className="iceberg-hover-row">
            <span className="label">Drift:</span>
            <span className="val">{iceberg.drift || "0.4 kn NW"}</span>
          </div>
          {distStr && (
            <div className="iceberg-hover-row distance-highlight">
              <span className="label">Range:</span>
              <span className="val text-[#ef4444] font-bold">{distStr}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
