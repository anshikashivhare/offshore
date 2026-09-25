export type Coordinate = {
  lat: number;
  lng: number;
};

export type LayerKey =
  | "gebco"
  | "seaIce"
  | "seaIceConcentration"
  | "forecast"
  | "icebergs"
  | "ports"
  | "tracks"
  | "trajectories"
  | "uncertainty"
  | "risk"
  | "routes"
  | "vessel"
  | "oceanCurrents"
  | "weather";

export interface PortRecord {
  id: string;
  name: string;
  country: string;
  lat: number;
  lon: number;
  port_type?: string;
  code?: string;
}

export type Priority = "Safety First" | "Balanced" | "Fuel Efficient" | "Time Efficient";

export type Iceberg = {
  id: string;
  position: Coordinate;
  sizeKm: number;
  timestamp: string;
  confidence: number;
  drift: string;
  risk: "low" | "moderate" | "high";
};

export type IcebergTrack = {
  icebergId: string;
  history: Coordinate[];
};

export type IcebergTrajectory = {
  icebergId: string;
  prediction: Coordinate[];
  horizonHours: number;
  confidence: number;
};

export type UncertaintyRegion = {
  icebergId: string;
  center: Coordinate;
  radiusKm: number;
};

export type Route = {
  id: string;
  name: string;
  objective: "Recommended" | "Safest" | "Fastest" | "Fuel Efficient";
  geometry: Coordinate[];
  distanceKm: number;
  etaHours: number;
  fuelLitres: number;
  riskScore: number;
  exposure: string;
  status: string;
  accent: string;
  risk_data_status?: string;
  ml_prediction_status?: string;
  warnings?: string[];
};

export type Vessel = {
  vessel_id: string;
  vessel_name: string;
  imo_number?: string;
  mmsi?: string;
  flag_country?: string;
  vessel_type: string;
  max_speed?: number;
  cruising_speed: number;
  ice_capability?: string;
  icebreaking_capability?: string;
  polar_operating_capability?: string;
  length_m?: number;
  beam_m?: number;
  draft_m?: number;
  fuel_type?: string;
  fuel_consumption: number;
  passenger_capacity?: number;
  cargo_capacity?: string;
  data_source?: string;
  last_updated_timestamp?: string;
  verification_status?: string;
  operational_limits?: any;
};

export type Alert = {
  id: string;
  severity: "high" | "moderate" | "info";
  hazardType: string;
  title: string;
  detail: string;
  time: string;
  location: Coordinate;
};

export type ViewMode = "map" | "globe" | "navigation";

export type ForecastMeta = {
  asOf: string;
  horizonHours: number;
  confidence: "High" | "Moderate" | "Limited" | "Unknown";
  status: "Available" | "Delayed" | "Unavailable" | "Loading";
};

export type RiskCell = {
  center: Coordinate;
  radius: number;
  level: "low" | "moderate" | "high" | "avoid";
  score: number;
};

export type AppLocation = {
  label: string;
  coordinate: Coordinate;
  country?: string;
};
