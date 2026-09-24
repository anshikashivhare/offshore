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

export const icebergs: Iceberg[] = [];
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
  tracks: true,
  trajectories: true,
  uncertainty: true,
  risk: true,
  routes: true,
  vessel: true,
  oceanCurrents: false,
  weather: false,
};

