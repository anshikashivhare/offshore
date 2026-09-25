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
  { label: "Ushuaia Polar Harbor", coordinate: { lat: -54.81, lng: -68.30 }, country: "Argentina" },
  { label: "Punta Arenas Port", coordinate: { lat: -53.16, lng: -70.91 }, country: "Chile" },
  { label: "Hobart Antarctic Gateway", coordinate: { lat: -42.88, lng: 147.33 }, country: "Australia" },
  { label: "Christchurch Lyttelton", coordinate: { lat: -43.60, lng: 172.72 }, country: "New Zealand" },
  { label: "Port Stanley Harbor", coordinate: { lat: -51.70, lng: -57.85 }, country: "Falkland Islands" },
  { label: "Palmer Station", coordinate: { lat: -64.77, lng: -64.05 }, country: "Antarctica" },
  { label: "Dumont d'Urville Station", coordinate: { lat: -66.66, lng: 140.01 }, country: "Antarctica" },
  { label: "Fremantle Port", coordinate: { lat: -32.05, lng: 115.74 }, country: "Australia" },
];

// Vessels have been migrated to the PostgreSQL backend and are accessible via the API.
// The hardcoded vessels list is intentionally removed to enforce API usage.

export const icebergs: Iceberg[] = [
  {
    id: "D-33D",
    position: { lat: -64.40, lng: -55.70 },
    sizeKm: 27.8, // ~15 nm length
    timestamp: "2026-06-21T10:30:00Z",
    confidence: 0.98,
    drift: "0.8 kn NW",
    risk: "high",
  },
  {
    id: "A-68A",
    position: { lat: -62.15, lng: -58.20 },
    sizeKm: 38.0,
    timestamp: "2026-06-20T14:15:00Z",
    confidence: 0.95,
    drift: "0.5 kn WNW",
    risk: "high",
  },
  {
    id: "B-15A",
    position: { lat: -66.50, lng: -67.80 },
    sizeKm: 18.5,
    timestamp: "2026-06-22T08:00:00Z",
    confidence: 0.92,
    drift: "0.4 kn N",
    risk: "moderate",
  },
  {
    id: "C-19D",
    position: { lat: -65.10, lng: -63.90 },
    sizeKm: 12.0,
    timestamp: "2026-06-23T11:45:00Z",
    confidence: 0.90,
    drift: "0.3 kn NNW",
    risk: "moderate",
  },
  {
    id: "B-22A",
    position: { lat: -68.30, lng: -70.40 },
    sizeKm: 22.0,
    timestamp: "2026-06-24T16:20:00Z",
    confidence: 0.94,
    drift: "0.6 kn NW",
    risk: "high",
  },
];
export const tracks: IcebergTrack[] = [];
export const trajectories: IcebergTrajectory[] = [];
export const uncertainty: UncertaintyRegion[] = [];
export const riskCells: RiskCell[] = [];
export const routes: Route[] = [];
export const alerts: Alert[] = [];

export const forecastMeta: ForecastMeta = { 
  asOf: "Live Data", 
  horizonHours: 0, 
  confidence: "Unknown", 
  status: "Loading" 
};

export const defaultLayers: Record<LayerKey, boolean> = {
  gebco: true,
  seaIce: true,
  seaIceConcentration: true,
  forecast: true,
  icebergs: true,
  ports: true,
  tracks: true,
  trajectories: true,
  uncertainty: true,
  risk: true,
  routes: true,
  vessel: true,
  oceanCurrents: false,
  weather: false,
};

