import type {
  Alert,
  AppLocation,
  ForecastMeta,
  Iceberg,
  IcebergTrack,
  IcebergTrajectory,
  LayerKey,
  RiskCell,
  Route,
  UncertaintyRegion,
  Vessel,
} from "./offshore-types";

export const locations: AppLocation[] = [
  { label: "Cape Town Research Port", coordinate: { lat: -33.92, lng: 18.42 }, country: "South Africa" },
  { label: "McMurdo Station", coordinate: { lat: -77.84, lng: 166.67 }, country: "Antarctica" },
  { label: "Rothera Research Station", coordinate: { lat: -67.57, lng: -68.13 }, country: "Antarctica" },
  { label: "Casey Station", coordinate: { lat: -66.28, lng: 110.53 }, country: "Antarctica" },
];

// Vessels have been migrated to the PostgreSQL backend and are accessible via the API.
// The hardcoded vessels list is intentionally removed to enforce API usage.

export const icebergs: Iceberg[] = [
  { id: "IB-102", position: { lat: -63.8, lng: 11.8 }, sizeKm: 2.8, timestamp: "13 Sep · 08:40 UTC", confidence: 94, drift: "ESE · 0.7 kn", risk: "moderate" },
  { id: "IB-221", position: { lat: -67.1, lng: 38.4 }, sizeKm: 4.6, timestamp: "13 Sep · 07:15 UTC", confidence: 88, drift: "SE · 0.4 kn", risk: "high" },
  { id: "IB-309", position: { lat: -70.5, lng: -28.2 }, sizeKm: 1.2, timestamp: "13 Sep · 06:02 UTC", confidence: 97, drift: "ENE · 0.3 kn", risk: "low" },
  { id: "IB-412", position: { lat: -65.8, lng: -86.2 }, sizeKm: 3.4, timestamp: "12 Sep · 22:50 UTC", confidence: 81, drift: "NNE · 0.5 kn", risk: "moderate" },
  { id: "IB-508", position: { lat: -74.2, lng: 141.5 }, sizeKm: 2.1, timestamp: "13 Sep · 05:18 UTC", confidence: 91, drift: "E · 0.6 kn", risk: "low" },
];

export const tracks: IcebergTrack[] = [
  { icebergId: "IB-102", history: [{ lat: -65.5, lng: 2.0 }, { lat: -64.8, lng: 5.6 }, { lat: -64.2, lng: 8.7 }, { lat: -63.8, lng: 11.8 }] },
  { icebergId: "IB-221", history: [{ lat: -65.2, lng: 31.0 }, { lat: -65.8, lng: 33.5 }, { lat: -66.5, lng: 36.0 }, { lat: -67.1, lng: 38.4 }] },
  { icebergId: "IB-309", history: [{ lat: -71.6, lng: -33.5 }, { lat: -71.2, lng: -31.5 }, { lat: -70.9, lng: -29.8 }, { lat: -70.5, lng: -28.2 }] },
];

export const trajectories: IcebergTrajectory[] = [
  { icebergId: "IB-102", prediction: [{ lat: -63.4, lng: 14.4 }, { lat: -63.0, lng: 17.1 }, { lat: -62.6, lng: 20.0 }, { lat: -62.4, lng: 23.2 }], horizonHours: 72, confidence: 71 },
  { icebergId: "IB-221", prediction: [{ lat: -67.5, lng: 41.0 }, { lat: -68.1, lng: 43.7 }, { lat: -68.8, lng: 46.5 }, { lat: -69.3, lng: 49.2 }], horizonHours: 72, confidence: 62 },
  { icebergId: "IB-309", prediction: [{ lat: -70.3, lng: -25.4 }, { lat: -70.1, lng: -22.5 }, { lat: -69.8, lng: -19.8 }], horizonHours: 48, confidence: 79 },
];

export const uncertainty: UncertaintyRegion[] = [
  { icebergId: "IB-102", center: { lat: -62.5, lng: 19 }, radiusKm: 48 },
  { icebergId: "IB-221", center: { lat: -68.2, lng: 44 }, radiusKm: 64 },
  { icebergId: "IB-309", center: { lat: -70.0, lng: -22 }, radiusKm: 32 },
];

export const riskCells: RiskCell[] = [
  { center: { lat: -64.7, lng: 22 }, radius: 30, level: "high", score: 0.78 },
  { center: { lat: -67.6, lng: 42 }, radius: 35, level: "avoid", score: 0.91 },
  { center: { lat: -69.6, lng: -11 }, radius: 38, level: "moderate", score: 0.54 },
  { center: { lat: -71.2, lng: -62 }, radius: 28, level: "low", score: 0.24 },
  { center: { lat: -63.5, lng: -78 }, radius: 32, level: "moderate", score: 0.49 },
  { center: { lat: -73.4, lng: 100 }, radius: 42, level: "high", score: 0.73 },
];

const routeGeometry = {
  recommended: [{ lat: -67.57, lng: -68.13 }, { lat: -67.0, lng: -49 }, { lat: -66.0, lng: -22 }, { lat: -64.6, lng: 4 }, { lat: -63.5, lng: 32 }, { lat: -62.4, lng: 54 }, { lat: -66.3, lng: 110.5 }],
  safest: [{ lat: -67.57, lng: -68.13 }, { lat: -68.3, lng: -48 }, { lat: -68.1, lng: -24 }, { lat: -67.1, lng: 2 }, { lat: -65.8, lng: 28 }, { lat: -64.8, lng: 54 }, { lat: -66.3, lng: 110.5 }],
  fastest: [{ lat: -67.57, lng: -68.13 }, { lat: -65.8, lng: -39 }, { lat: -64.3, lng: -10 }, { lat: -63.8, lng: 20 }, { lat: -62.4, lng: 54 }, { lat: -66.3, lng: 110.5 }],
  fuel: [{ lat: -67.57, lng: -68.13 }, { lat: -67.4, lng: -48 }, { lat: -66.7, lng: -18 }, { lat: -65.3, lng: 12 }, { lat: -63.7, lng: 38 }, { lat: -62.4, lng: 54 }, { lat: -66.3, lng: 110.5 }],
};

export const routes: Route[] = [
  { id: "route-a", name: "Route A", objective: "Recommended", geometry: routeGeometry.recommended, distanceKm: 2840, etaHours: 118, fuelLitres: 101480, riskScore: 0.31, exposure: "Low iceberg exposure", status: "Recommended for current priority", accent: "teal" },
  { id: "route-b", name: "Route B", objective: "Safest", geometry: routeGeometry.safest, distanceKm: 2995, etaHours: 126, fuelLitres: 108360, riskScore: 0.22, exposure: "Lowest predicted risk", status: "Lower risk · +8 h transit", accent: "blue" },
  { id: "route-c", name: "Route C", objective: "Fastest", geometry: routeGeometry.fastest, distanceKm: 2668, etaHours: 109, fuelLitres: 103120, riskScore: 0.49, exposure: "Moderate iceberg exposure", status: "Fastest · higher exposure", accent: "amber" },
  { id: "route-d", name: "Route D", objective: "Fuel Efficient", geometry: routeGeometry.fuel, distanceKm: 2784, etaHours: 116, fuelLitres: 97840, riskScore: 0.38, exposure: "Moderate sea-ice exposure", status: "Lowest estimated fuel", accent: "violet" },
];

export const alerts: Alert[] = [
  { id: "alert-1", severity: "high", hazardType: "Iceberg exposure", title: "Predicted iceberg exposure near Route A", detail: "IB-221 trajectory approaches the recommended corridor after 16 Sep.", time: "16 Sep · 06:00 UTC", location: { lat: -67.6, lng: 42 } },
  { id: "alert-2", severity: "moderate", hazardType: "Sea-ice risk", title: "Sea-ice concentration increasing east of 20°E", detail: "Forecast concentration rises to 58–64% across the fastest route window.", time: "15 Sep · 12:00 UTC", location: { lat: -65.5, lng: 21 } },
  { id: "alert-3", severity: "info", hazardType: "Observation gap", title: "Limited observations in eastern sector", detail: "Confidence is reduced where satellite revisit exceeds 9 hours.", time: "Current", location: { lat: -72, lng: 110 } },
];

export const forecastMeta: ForecastMeta = { asOf: "13 Sep 2026 · 09:00 UTC", horizonHours: 72, confidence: "Moderate", status: "Available" };

export const defaultLayers: Record<LayerKey, boolean> = {
  gebco: true,
  seaIce: true,
  seaIceConcentration: true,
  forecast: true,
  icebergs: true,
  tracks: true,
  trajectories: true,
  uncertainty: true,
  risk: true,
  routes: true,
  vessel: true,
  oceanCurrents: false,
  weather: false,
};

