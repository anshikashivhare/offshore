export interface VesselTelemetry {
  id: string;
  name: string;
  callsign: string;
  iceClass: string;
  lat: number;
  lon: number;
  heading: number;
  speedKnots: number;
  destination: string;
  eta: string;
  hullIceLoadPct: number;
  corridorRisk: "Low" | "Moderate" | "High" | "Critical";
  fuelConsumptionBurnRate: string;
  waterTempC: number;
  airTempC: number;
  windSpeedKnots: number;
  windDirection: string;
}

export interface Iceberg {
  id: string;
  name: string;
  classification: "Tabular" | "Pinnacle" | "Growler" | "Very Large Tabular" | "Growler Cluster";
  lat: number;
  lon: number;
  lengthKm: number;
  widthKm: number;
  freeboardM: number;
  estimatedMassMt: number;
  driftSpeedKnots: number;
  driftHeading: number;
  driftDirLabel: string;
  cpaDistanceNm: number;
  cpaTimeHours: number;
  riskLevel: "Low" | "Moderate" | "High" | "Critical";
  firstDetected: string;
  historicalPositions: { lat: number; lon: number; timestamp: string }[];
  predictedPositions: { lat: number; lon: number; hoursAhead: number }[];
}

export interface RiskZone {
  id: string;
  name: string;
  category: "Ice Concentration" | "Multi-Hazard" | "Compression Ridge" | "Gale Swell";
  level: "Low" | "Moderate" | "High" | "Critical";
  score: number; // 0 - 100
  polygon: [number, number][]; // [x, y] in viewBox coords
  latRange: string;
  lonRange: string;
  recommendation: string;
  dominantHazards: string[];
}

export interface RouteOption {
  id: "safest" | "fastest" | "fuel";
  title: string;
  tagline: string;
  distanceNm: number;
  etaHours: number;
  fuelBurnTons: number;
  avgIceConcentration: number;
  maxRiskScore: number;
  riskLabel: "Low" | "Moderate" | "High";
  waypointsCount: number;
  summary: string;
  color: string;
  points: [number, number][]; // [x, y] coordinates
}

export const ACTIVE_VESSEL: VesselTelemetry = {
  id: "polar-explorer",
  name: "MV Polar Explorer",
  callsign: "WDE-8921",
  iceClass: "Polar Class 6 (PC6)",
  lat: -64.82,
  lon: -63.5,
  heading: 218,
  speedKnots: 11.4,
  destination: "Rothera Research Station",
  eta: "08 OCT 14:30 UTC",
  hullIceLoadPct: 42,
  corridorRisk: "Moderate",
  fuelConsumptionBurnRate: "1.42 MT/hr",
  waterTempC: -1.2,
  airTempC: -8.4,
  windSpeedKnots: 28,
  windDirection: "SSW (205°)",
};

export const TRACKED_ICEBERGS: Iceberg[] = [
  {
    id: "B-102",
    name: "Iceberg B-102",
    classification: "Very Large Tabular",
    lat: -65.12,
    lon: -64.15,
    lengthKm: 34.2,
    widthKm: 18.5,
    freeboardM: 42,
    estimatedMassMt: 840,
    driftSpeedKnots: 1.8,
    driftHeading: 284,
    driftDirLabel: "WNW",
    cpaDistanceNm: 14.2,
    cpaTimeHours: 9.4,
    riskLevel: "High",
    firstDetected: "2024-03-12 (Sentinel-1 SAR)",
    historicalPositions: [
      { lat: -65.3, lon: -63.8, timestamp: "-48h" },
      { lat: -65.22, lon: -63.95, timestamp: "-24h" },
      { lat: -65.12, lon: -64.15, timestamp: "Now" },
    ],
    predictedPositions: [
      { lat: -65.12, lon: -64.15, hoursAhead: 0 },
      { lat: -65.04, lon: -64.38, hoursAhead: 12 },
      { lat: -64.95, lon: -64.62, hoursAhead: 24 },
      { lat: -64.82, lon: -64.9, hoursAhead: 36 },
      { lat: -64.7, lon: -65.18, hoursAhead: 48 },
    ],
  },
  {
    id: "A-68A",
    name: "Iceberg A-68A Fragment",
    classification: "Tabular",
    lat: -64.4,
    lon: -61.8,
    lengthKm: 14.6,
    widthKm: 8.2,
    freeboardM: 35,
    estimatedMassMt: 320,
    driftSpeedKnots: 2.3,
    driftHeading: 310,
    driftDirLabel: "NW",
    cpaDistanceNm: 38.0,
    cpaTimeHours: 19.1,
    riskLevel: "Moderate",
    firstDetected: "2024-05-02 (MODIS Aqua)",
    historicalPositions: [
      { lat: -64.8, lon: -61.2, timestamp: "-48h" },
      { lat: -64.6, lon: -61.5, timestamp: "-24h" },
      { lat: -64.4, lon: -61.8, timestamp: "Now" },
    ],
    predictedPositions: [
      { lat: -64.4, lon: -61.8, hoursAhead: 0 },
      { lat: -64.25, lon: -62.15, hoursAhead: 12 },
      { lat: -64.1, lon: -62.5, hoursAhead: 24 },
      { lat: -63.95, lon: -62.88, hoursAhead: 36 },
      { lat: -63.8, lon: -63.25, hoursAhead: 48 },
    ],
  },
  {
    id: "C-19B",
    name: "Iceberg C-19B",
    classification: "Growler Cluster",
    lat: -63.9,
    lon: -65.4,
    lengthKm: 6.8,
    widthKm: 3.4,
    freeboardM: 18,
    estimatedMassMt: 85,
    driftSpeedKnots: 3.1,
    driftHeading: 230,
    driftDirLabel: "SW",
    cpaDistanceNm: 52.4,
    cpaTimeHours: 24.5,
    riskLevel: "Low",
    firstDetected: "2024-06-18 (Radarsat-2)",
    historicalPositions: [
      { lat: -63.6, lon: -65.0, timestamp: "-48h" },
      { lat: -63.75, lon: -65.2, timestamp: "-24h" },
      { lat: -63.9, lon: -65.4, timestamp: "Now" },
    ],
    predictedPositions: [
      { lat: -63.9, lon: -65.4, hoursAhead: 0 },
      { lat: -64.05, lon: -65.75, hoursAhead: 12 },
      { lat: -64.22, lon: -66.1, hoursAhead: 24 },
      { lat: -64.38, lon: -66.5, hoursAhead: 36 },
      { lat: -64.55, lon: -66.9, hoursAhead: 48 },
    ],
  },
  {
    id: "D-28",
    name: "Iceberg D-28 (Mertz)",
    classification: "Tabular",
    lat: -66.05,
    lon: -66.2,
    lengthKm: 28.0,
    widthKm: 12.0,
    freeboardM: 38,
    estimatedMassMt: 510,
    driftSpeedKnots: 1.2,
    driftHeading: 195,
    driftDirLabel: "SSW",
    cpaDistanceNm: 64.1,
    cpaTimeHours: 32.0,
    riskLevel: "Low",
    firstDetected: "2023-11-10 (Sentinel-1 SAR)",
    historicalPositions: [
      { lat: -65.8, lon: -66.1, timestamp: "-48h" },
      { lat: -65.92, lon: -66.15, timestamp: "-24h" },
      { lat: -66.05, lon: -66.2, timestamp: "Now" },
    ],
    predictedPositions: [
      { lat: -66.05, lon: -66.2, hoursAhead: 0 },
      { lat: -66.18, lon: -66.28, hoursAhead: 12 },
      { lat: -66.3, lon: -66.35, hoursAhead: 24 },
      { lat: -66.45, lon: -66.42, hoursAhead: 36 },
      { lat: -66.6, lon: -66.5, hoursAhead: 48 },
    ],
  },
];

export const RISK_ZONES: RiskZone[] = [
  {
    id: "zone-1",
    name: "Weddell Alpha Sector",
    category: "Compression Ridge",
    level: "Moderate",
    score: 48,
    polygon: [
      [360, 240],
      [490, 260],
      [470, 370],
      [340, 350],
    ],
    latRange: "64°20'S - 65°10'S",
    lonRange: "58°40'W - 61°15'W",
    recommendation: "Maintain minimum 10 kn headway. Continuous sonar depth tracking.",
    dominantHazards: ["Dynamic pressure ridge (1.8m)", "B-102 debris field", "SW 32kn winds"],
  },
  {
    id: "zone-2",
    name: "Gerlache Strait Passage",
    category: "Multi-Hazard",
    level: "Critical",
    score: 82,
    polygon: [
      [560, 380],
      [680, 400],
      [660, 520],
      [530, 490],
    ],
    latRange: "64°45'S - 65°30'S",
    lonRange: "63°00'W - 64°40'W",
    recommendation: "Navigation restricted to PC4+ hull classes. Recommended detour via Corridor Bravo.",
    dominantHazards: ["Consolidated pack ice (88%)", "Narrow choke points", "High iceberg drift velocity"],
  },
  {
    id: "zone-3",
    name: "Bransfield Basin",
    category: "Ice Concentration",
    level: "High",
    score: 64,
    polygon: [
      [220, 140],
      [350, 150],
      [330, 250],
      [200, 230],
    ],
    latRange: "62°30'S - 63°40'S",
    lonRange: "56°00'W - 59°00'W",
    recommendation: "Reduce speed to 8 knots. Deploy infrared ice radar surveillance.",
    dominantHazards: ["Multi-year ice inclusions", "Low visibility fog bank (<500m)"],
  },
  {
    id: "zone-4",
    name: "Drake Southern Margin",
    category: "Gale Swell",
    level: "Low",
    score: 22,
    polygon: [
      [620, 110],
      [760, 130],
      [740, 220],
      [600, 200],
    ],
    latRange: "60°10'S - 61°50'S",
    lonRange: "62°00'W - 67°00'W",
    recommendation: "Clear navigation channel. Standard watch conditions in force.",
    dominantHazards: ["Moderate open swell (3.2m)", "Scattered growlers"],
  },
];

export const ROUTE_OPTIONS: RouteOption[] = [
  {
    id: "safest",
    title: "Polar Safe Corridor (Recommended)",
    tagline: "Prioritizes minimum hull stress & avoids convergent drift chokepoints",
    distanceNm: 384,
    etaHours: 34.2,
    fuelBurnTons: 48.6,
    avgIceConcentration: 24,
    maxRiskScore: 32,
    riskLabel: "Low",
    waypointsCount: 14,
    summary: "Circles outer Gerlache perimeter into wide open leads. Maximum iceberg separation is 28 nm.",
    color: "#34d399",
    points: [
      [240, 180],
      [290, 240],
      [360, 310],
      [420, 360],
      [510, 410],
      [620, 480],
      [740, 560],
      [820, 640],
    ],
  },
  {
    id: "fastest",
    title: "Direct Polar Transit",
    tagline: "Shortest geodetic path through Gerlache Strait with escort advisory",
    distanceNm: 312,
    etaHours: 27.5,
    fuelBurnTons: 41.2,
    avgIceConcentration: 58,
    maxRiskScore: 78,
    riskLabel: "High",
    waypointsCount: 9,
    summary: "Direct passage saves 6.7 hours but encounters 142 kPa ice pressure ridges and iceberg B-102 CPA.",
    color: "#f87171",
    points: [
      [240, 180],
      [330, 260],
      [440, 340],
      [560, 420],
      [680, 510],
      [820, 640],
    ],
  },
  {
    id: "fuel",
    title: "Hydrodynamic Eco-Glide",
    tagline: "Optimized along Antarctic Coastal Current drift vectors",
    distanceNm: 348,
    etaHours: 31.0,
    fuelBurnTons: 37.8,
    avgIceConcentration: 38,
    maxRiskScore: 46,
    riskLabel: "Moderate",
    waypointsCount: 11,
    summary: "Exploits 1.4 knot westward current assist. Fuel consumption reduced by 22% compared to standard transit.",
    color: "#22d3ee",
    points: [
      [240, 180],
      [310, 220],
      [380, 280],
      [470, 350],
      [580, 430],
      [710, 520],
      [820, 640],
    ],
  },
];

export const SEA_ICE_FORECAST_DATA = [
  { time: "00:00", current: 68, predicted: 68, threshold: 75 },
  { time: "06:00", current: 67, predicted: 69, threshold: 75 },
  { time: "12:00", current: 69, predicted: 71, threshold: 75 },
  { time: "18:00", current: 71, predicted: 74, threshold: 75 },
  { time: "24:00", current: null, predicted: 76, threshold: 75 },
  { time: "30:00", current: null, predicted: 78, threshold: 75 },
  { time: "36:00", current: null, predicted: 75, threshold: 75 },
  { time: "42:00", current: null, predicted: 72, threshold: 75 },
  { time: "48:00", current: null, predicted: 69, threshold: 75 },
];

export const RISK_TREND_DATA = [
  { hour: "00h", score: 28, upper: 38, lower: 20 },
  { hour: "04h", score: 32, upper: 44, lower: 24 },
  { hour: "08h", score: 45, upper: 56, lower: 34 },
  { hour: "12h", score: 62, upper: 74, lower: 50 },
  { hour: "16h", score: 71, upper: 82, lower: 60 },
  { hour: "20h", score: 64, upper: 76, lower: 52 },
  { hour: "24h", score: 49, upper: 60, lower: 39 },
];

export const ANALYTICS_TRENDS = {
  seaIce: [
    { month: "Jan", baseline: 42, year2024: 38, year2025: 35 },
    { month: "Feb", baseline: 28, year2024: 24, year2025: 22 },
    { month: "Mar", baseline: 36, year2024: 31, year2025: 29 },
    { month: "Apr", baseline: 54, year2024: 49, year2025: 48 },
    { month: "May", baseline: 68, year2024: 63, year2025: 61 },
    { month: "Jun", baseline: 79, year2024: 76, year2025: 74 },
    { month: "Jul", baseline: 86, year2024: 83, year2025: 81 },
    { month: "Aug", baseline: 91, year2024: 88, year2025: 86 },
    { month: "Sep", baseline: 94, year2024: 91, year2025: 89 },
    { month: "Oct", baseline: 88, year2024: 84, year2025: 82 },
    { month: "Nov", baseline: 72, year2024: 68, year2025: 65 },
    { month: "Dec", baseline: 55, year2024: 50, year2025: 47 },
  ],
  icebergs: [
    { week: "W1", detected: 42, highRisk: 3 },
    { week: "W2", detected: 51, highRisk: 4 },
    { week: "W3", detected: 48, highRisk: 6 },
    { week: "W4", detected: 62, highRisk: 9 },
    { week: "W5", detected: 58, highRisk: 7 },
    { week: "W6", detected: 69, highRisk: 11 },
  ],
  performance: [
    { voyage: "V-01", safeScore: 92, fuelEfficiency: 88 },
    { voyage: "V-02", safeScore: 89, fuelEfficiency: 94 },
    { voyage: "V-03", safeScore: 95, fuelEfficiency: 91 },
    { voyage: "V-04", safeScore: 86, fuelEfficiency: 87 },
    { voyage: "V-05", safeScore: 94, fuelEfficiency: 96 },
  ],
};
