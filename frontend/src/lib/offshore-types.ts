export type Coordinate = {
  lat: number;
  lng: number;
};

export type LayerKey =
  | "seaIce"
  | "forecast"
  | "icebergs"
  | "tracks"
  | "trajectories"
  | "uncertainty"
  | "risk"
  | "routes"
  | "vessel";

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
};

export type Vessel = {
  id: string;
  name: string;
  type: string;
  cruisingSpeedKn: number;
  fuelBurnLph: number;
  iceClass: string;
  operationalLimit: string;
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

export type ForecastMeta = {
  asOf: string;
  horizonHours: number;
  confidence: "High" | "Moderate" | "Limited";
  status: "Available" | "Delayed" | "Unavailable";
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
};
