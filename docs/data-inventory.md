# OFFSHORE Synthetic Data Inventory & Usage Analysis

**Generated:** 2026-09-24  
**Purpose:** Complete catalog of all synthetic datasets, ML model files, and their integration points in the codebase

---

## 1. Synthetic Observation Datasets

### 1.1 Sea-Ice Concentration Data

**Source File:** `data/raw/sea_ice_synthetic_2026.csv` (in ZIP archive)

**Location (ZIP):** `C:\Users\ASUS\Desktop\Synthetic data for offshore`

**Records:** 18,250 observations

**Schema:**
```csv
sample_id, timestamp, latitude, longitude, sea_ice_concentration,
air_temperature_c, sea_surface_temperature_c, sea_level_pressure_hpa,
wind_speed_m_s, wind_u_m_s, wind_v_m_s, current_speed_m_s,
current_u_m_s, current_v_m_s, sea_surface_height_anomaly_cm,
data_source_type, model_version
```

**Value Ranges:**
- `latitude`: -90.0 to -50.0 (Antarctic region)
- `longitude`: -180.0 to 180.0 (full Antarctic circumference)
- `sea_ice_concentration`: 0.0 to 1.0 (fractional coverage)
- `timestamp`: 2026-09-01 to 2026-09-30 (1-month window)

**Database Destination:** `sea_ice_observations` table

**Seeding Script:** `scripts/data_ingestion/seed_synthetic_data.py:201-235`
```python
def seed_sea_ice(conn, zf):
    # Creates POLYGON geometries via create_bbox_polygon(lat, lon, dlat=0.6, dlon=1.8)
    # Estimates thickness from concentration: thickness = conc * 1.8 meters
    # Ice type classification: multi_year (>60%), first_year (>15%), open_water
```

**How It's Used:**
- ✅ **READ by:** `IceRiskCalculator.calculate()` in `backend/app/services/risk/calculators.py:93-139`
  - Queries observations within 3° envelope via `ST_Intersects`
  - Finds nearest observation via Haversine distance
  - Returns risk = `concentration × distance_decay_factor`
- ❌ **NOT USED by:** ML model inference (models exist but aren't integrated)

**Data Quality Markers:**
- `data_source_type`: "SYNTHETIC_PROTOTYPE"
- `data_quality`: 1.0 (perfect synthetic data, unrealistic for production)

---

### 1.2 Weather Observations

**Source File:** `data/raw/weather_synthetic_2026.csv`

**Records:** 73,000 observations

**Schema:**
```csv
sample_id, timestamp, latitude, longitude, wind_speed_m_s, wind_direction_deg,
air_temperature_c, sea_level_pressure_hpa, data_source_type
```

**Value Ranges:**
- `wind_speed_m_s`: 0.0 to 35.0 m/s (hurricane-force winds included)
- `wind_direction_deg`: 0.0 to 360.0
- `air_temperature_c`: -40.0 to +5.0 (Antarctic range)
- `sea_level_pressure_hpa`: 950.0 to 1030.0

**Database Destination:** `weather_observations` table

**Seeding Script:** `scripts/data_ingestion/seed_synthetic_data.py:237-275`
```python
def seed_weather(conn, zf):
    # Creates POINT geometries
    # Derives wave_height from wind: wave_h = 0.015 × (wind_speed^1.8)
```

**How It's Used:**
- ✅ **READ by:** `WeatherRiskCalculator.calculate()` in `calculators.py:213-260`
  - Queries within 150 km search radius
  - Risk formula: `risk = 0.6 × wind_norm + 0.4 × wave_norm`
  - `wind_norm = wind_speed / 25.0` (normalized to gale force)
  - `wave_norm = wave_height / 6.0` (normalized to dangerous seas)
- ✅ **READ by:** Route planner cost function for wave height hard constraint check

**Synthetic Wave Model:**
- Wave height NOT in CSV, synthesized during seeding
- Formula: `wave_h = 0.015 × wind_speed^1.8` (simplified empirical relationship)
- **Limitation:** No fetch/duration modeling, no swell propagation

---

### 1.3 Ocean Current Observations

**Source File:** `data/raw/ocean_currents_synthetic_2026.csv`

**Records:** 73,000 observations

**Schema:**
```csv
sample_id, timestamp, latitude, longitude, current_speed_m_s, current_direction_deg,
sea_surface_height_anomaly_cm, data_source_type
```

**Value Ranges:**
- `current_speed_m_s`: 0.0 to 2.5 m/s (includes Antarctic Circumpolar Current)
- `current_direction_deg`: 0.0 to 360.0
- `sea_surface_height_anomaly_cm`: -50.0 to +50.0

**Database Destination:** `ocean_observations` table

**Seeding Script:** `scripts/data_ingestion/seed_synthetic_data.py:277-314`
```python
def seed_ocean(conn, zf):
    # Creates POINT geometries
    # Estimates SST from latitude: sst = -1.8 + max(0, (lat + 75) * 0.2)
```

**How It's Used:**
- ✅ **READ by:** `CurrentRiskCalculator.calculate()` in `calculators.py:275-320`
  - Risk formula: `risk = 0.8 × current_norm + 0.2 × sst_anomaly_norm`
  - `current_norm = current_speed / 2.0 m/s`
  - `sst_norm = abs(sst) / 5.0°C`
- ✅ **READ by:** Route planner SOG calculation in `cost.py:56-97`
  - Decomposes current into parallel/perpendicular components
  - Adds parallel component to vessel STW for SOG

**Synthetic SST Model:**
- SST NOT in CSV, estimated during seeding
- Formula: `sst = -1.8 + max(0, (lat + 75) × 0.2)`
- Assumes linear gradient from ice shelf (-1.8°C at 75°S) to Southern Ocean (-0.8°C at 55°S)

---

### 1.4 Iceberg Detection & Trajectory Data

**Source File:** `data/raw/iceberg_trajectory_synthetic_2026.csv`

**Records:** 30,424 timestamped positions for 30 unique icebergs

**Schema:**
```csv
sample_id, iceberg_id, timestamp, latitude_t, longitude_t,
latitude_t_minus_1, longitude_t_minus_1, latitude_t_minus_2, longitude_t_minus_2,
target_latitude, target_longitude, wind_speed_m_s, wind_u_m_s, wind_v_m_s,
current_speed_m_s, current_u_m_s, current_v_m_s, sea_surface_temperature_c,
air_temperature_c, sea_level_pressure_hpa, sea_surface_height_anomaly_cm,
sea_ice_concentration, forecast_horizon_hours, data_source_type, model_version
```

**Iceberg IDs:** IB-102, IB-221, IB-309, IB-412, IB-508 (repeating pattern for synthetic diversity)

**Temporal Coverage:** Lag-2, lag-1, current (t), and predicted future position (target)

**Database Destinations:**
1. `icebergs` table (30 unique IDs)
2. `iceberg_detections` table (30,424 current position records)
3. `iceberg_predictions` table (30,424 future trajectory predictions)

**Seeding Script:** `scripts/data_ingestion/seed_synthetic_data.py:317-408`
```python
def seed_icebergs(conn, zf):
    # Detection: Creates POINT at (longitude_t, latitude_t)
    # Extent: POLYGON bbox ±0.02° lat, ±0.05° lon
    # Prediction: Creates POINT at (target_longitude, target_latitude)
    # Path JSON: 4-point trajectory [t-2, t-1, t, target]
    # Uncertainty: POLYGON bbox ±0.1° lat, ±0.2° lon
```

**How It's Used:**
- ✅ **DETECTIONS READ by:** `IcebergRiskCalculator.calculate()` in `calculators.py:154-198`
  - Queries within 3° envelope
  - Risk decays with distance: `risk = max(decay × confidence)` within 75 km
- ❌ **PREDICTIONS NOT READ** by route planner
  - Predictions stored in `iceberg_predictions` table
  - **ROOT CAUSE:** `IcebergRiskCalculator` only queries `iceberg_detections`
  - Should project trajectories forward and check route corridor intersection

**Synthetic Sizes:**
```python
size_map = {
    "IB-102": 2.8 km,
    "IB-221": 4.6 km,
    "IB-309": 1.2 km,
    "IB-412": 3.4 km,
    "IB-508": 2.1 km
}
```

---

### 1.5 Grid Cell Risk Surface

**Source File:** `data/raw/grid_cells_2026.csv`

**Records:** 50 grid cells covering Antarctic operational area

**Schema:**
```csv
cell_id, latitude, longitude, lat_band, lon_band
```

**Grid Structure:**
- Latitude bands: -55° to -75° (Antarctic coastal zone)
- Longitude bands: Full 360° circumference
- Cell resolution: ~3.6° longitude × 1.2° latitude

**Database Destination:** `risk_cells` table

**Seeding Script:** `scripts/data_ingestion/seed_synthetic_data.py:142-198`
```python
def seed_grid_cells_and_risk_cells(conn, zf):
    # Risk calculation (SYNTHETIC FORMULA):
    lat_factor = (abs(lat) - 55.0) / 25.0  # Higher risk closer to pole
    ice_risk = 0.1 + 0.8 × lat_factor
    iceberg_risk = 0.05 + 0.7 × lat_factor
    weather_risk = 0.2 + 0.5 × (1 - abs(lon)/180)
    current_risk = 0.1 + 0.3 × lat_factor
    
    composite_risk = 0.35×ice + 0.35×iceberg + 0.15×weather + 0.15×current
    
    # Risk categories: low (<0.35), moderate (0.35-0.55), high (0.55-0.75), avoid (>0.75)
```

**How It's Used:**
- ✅ **READ by:** `_build_risk_grid()` in `routes.py:31-89`
  - Queries `risk_cells` within route bounding box + 2° margin
  - Uses `ST_Intersects` for spatial filtering
  - Returns dict keyed by `(round(lat, 1), round(lon, 1))`
- ✅ **READ by:** A* planner for edge cost calculation
  - `cost_calculator.get_risk_at(neighbor, risk_grid)` at `astar.py:207`
  - Risk multiplied by distance: `gamma × risk_score × distance`

**Data Timestamp:** Fixed at `2026-09-18T06:00:00+00:00` (seeding script line 151)

**Critical Issue:**
- Risk cells are **static** (seeded once)
- NOT updated by ML model predictions
- In production, should be refreshed every 3-6 hours with new forecasts

---

### 1.6 Pre-Seeded Routes

**Source Files:**
- `data/raw/routes_synthetic_2026.csv` (10 routes)
- `data/raw/route_waypoints_synthetic_2026.csv` (waypoint details)

**Routes:**
```
RT_0000: Punta Arenas → Rothera (recommended)
RT_0001: Punta Arenas → Rothera (fastest)
RT_0002: Punta Arenas → Rothera (safest)
RT_0003: Punta Arenas → Rothera (fuel_efficient)
RT_0004: Punta Arenas → Rothera (shortest)
RT_0005: Rothera → McMurdo (fastest)
RT_0006: Hobart → McMurdo (safest)
RT_0007: Cape Town → Neumayer (fuel_efficient)
RT_0008: Christchurch → McMurdo (fastest)
RT_0009: Ushuaia → Palmer Station (shortest)
```

**Schema (routes):**
```csv
route_id, vessel_id, route_type, origin_name, origin_lat, origin_lon,
destination_name, destination_lat, destination_lon, departure_time,
arrival_time, total_distance_km, overall_risk_score
```

**Schema (waypoints):**
```csv
waypoint_id, route_id, waypoint_seq, latitude, longitude, eta, distance_from_prev_km
```

**Database Destination:** `routes` table

**Seeding Script:** `scripts/data_ingestion/seed_synthetic_data.py:411-485`

**How It's Used:**
- ❌ **NOT USED by `/api/v1/routes/plan` endpoint**
  - This endpoint computes NEW routes via A* search
  - Does NOT retrieve pre-seeded routes from database
- ✅ **Used by `/api/v1/routes/{route_id}` GET endpoint**
  - Fetches stored route by UUID for historical retrieval
  - Demo/testing purposes

**Objective Type Mapping:**
```python
objective_mapping = {
    "recommended": "SAFEST",
    "fastest": "FASTEST",
    "safest": "SAFEST",
    "fuel_efficient": "FUEL_EFFICIENT",
    "shortest": "SHORTEST"
}
```

**Fuel Estimation (Synthetic):**
```python
# Seeding script line 449
est_fuel = round(dist_nm * 15.0, 2)  # 15 units per NM (simplified)
```

---

### 1.7 Synthetic Alerts

**Source:** Hardcoded in seeding script (not from CSV)

**Records:** 2 initial alerts

**Seeding Script:** `scripts/data_ingestion/seed_synthetic_data.py:488-532`

**Alert Examples:**
```python
Alert 1: Iceberg Proximity Warning
  - Severity: HIGH
  - Location: -63.8°S, 11.8°E
  - Message: "Iceberg IB-102 projected to intersect recommended route..."
  - Triggering metric: 2.8 km (distance)
  - Threshold: 5.0 km
  - Confidence: 0.94

Alert 2: High Sea-Ice Concentration
  - Severity: MEDIUM
  - Location: -67.57°S, -68.13°E (Rothera approach)
  - Message: "Sea-ice concentration exceeds 60%..."
  - Triggering metric: 0.62 (concentration)
  - Threshold: 0.50
  - Confidence: 0.89
```

**Database Destination:** `alerts` table

**How It's Used:**
- ✅ **CREATED by:** `AlertEngine.evaluate_route()` in `backend/app/services/alerts/engine.py`
  - Called by `NavigationOrchestrator.run_scenario()`
  - Generates new alerts based on route geometry vs risk_grid
- ✅ **READ by:** Frontend alerts panel (not audited in detail)

---

## 2. Machine Learning Model Files

### 2.1 Sea-Ice Concentration XGBoost Models

**Directory:** `ml/models/weights/`

**Files (14 versions):**
```
seaice_xgb_latest.json                    (production symlink)
seaice_xgb_02f388c9.json                  (versioned snapshot)
seaice_xgb_09b46f91.json
seaice_xgb_12503052-90d7-4e5f-a20b-196093387fc8.json
seaice_xgb_3bcbcd7b-2ebb-485f-a7e8-fd34a50946a5.json
seaice_xgb_42d2fa6c.json
seaice_xgb_4aadb0c4-3ece-4326-a698-002ddf2d182d.json
seaice_xgb_70d9c39b.json
seaice_xgb_a9e63d3a-4cf5-411c-92ca-ac726ee79028.json
seaice_xgb_c088c140.json
seaice_xgb_da679bc3-bbbb-4734-aef5-e6ac102f3eb2.json
seaice_xgb_e4c87127-205f-4529-bf61-a604ea48365f.json
seaice_xgb_e6981d10-3728-4c05-b724-1ce0c7af40ba.json
seaice_xgb_ecdab427-b740-40ce-ac8e-7b5916ce07b3.json
production_seaice_xgb.json
```

**Feature Schema:** `ml/models/weights/seaice_feature_schema.json`
```json
{
  "feature_cols": [
    "latitude", "longitude", "sea_ice_concentration",
    "air_temperature_c", "sea_surface_temperature_c", "sea_level_pressure_hpa",
    "wind_speed_m_s", "wind_u_m_s", "wind_v_m_s",
    "current_speed_m_s", "current_u_m_s", "current_v_m_s",
    "sea_surface_height_anomaly_cm", "forecast_horizon_hours",
    "month", "sin_doy", "cos_doy"
  ],
  "run_id": "ecdab427-b740-40ce-ac8e-7b5916ce07b3",
  "training_timestamp": "2026-09-XX",
  "target": "target_sea_ice_concentration"
}
```

**Input Features:** 17 total (13 environmental + 4 temporal)

**Output:** Predicted sea-ice concentration (0.0-1.0) at forecast_horizon_hours ahead

**Model Format:** XGBoost JSON serialization (cross-platform, human-readable)

**Loading Mechanism:** `ml/inference/seaice_predict.py:27-39`
```python
def _load_model():
    global _model, _schema
    if _model is None:
        import xgboost as xgb
        _model = xgb.XGBRegressor()
        _model.load_model(str(_MODEL_PATH))  # Lazy singleton
        with open(_SCHEMA_PATH, "r") as f:
            _schema = json.load(f)
    return _model, _schema
```

**How It's Used:**
- ❌ **NOT CALLED by route planner or risk engine**
- ✅ **Callable via:** `predict_sea_ice_concentration()` function
- ✅ **Used in:** ML training/evaluation scripts in `ml/training/seaice_xgb_train.py`

**Training Data Source:**
- Synthetic CSV: `data/raw/sea_ice_synthetic_2026.csv`
- Features extracted + temporal encoding
- 80/20 train/test split

---

### 2.2 Iceberg Trajectory XGBoost Models

**Directory:** `ml/models/weights/`

**Files (8 versions per component = 16 total):**
```
# Latitude prediction:
iceberg_xgb_lat_latest.json              (production)
iceberg_xgb_lat_2816adce.json
iceberg_xgb_lat_cbb9da29.json
iceberg_xgb_lat_f57dbb9b.json
... (4 more versions)

# Longitude prediction:
iceberg_xgb_lon_latest.json              (production)
iceberg_xgb_lon_2816adce.json
iceberg_xgb_lon_cbb9da29.json
iceberg_xgb_lon_f57dbb9b.json
... (4 more versions)
```

**Feature Schema:** `ml/models/weights/iceberg_feature_schema.json`
```json
{
  "feature_cols": [
    "latitude_t", "longitude_t", "dlat_1", "dlon_1", "dlat_2", "dlon_2",
    "speed_1", "speed_2", "wind_u_m_s", "wind_v_m_s", "wind_speed_m_s",
    "current_u_m_s", "current_v_m_s", "current_speed_m_s",
    "sea_surface_temperature_c", "air_temperature_c", "sea_level_pressure_hpa",
    "sea_surface_height_anomaly_cm", "sea_ice_concentration",
    "forecast_horizon_hours", "month", "sin_doy", "cos_doy"
  ],
  "run_id": "cbb9da29",
  "target_lat": "delta_latitude",
  "target_lon": "delta_longitude"
}
```

**Input Features:** 23 total (8 position/velocity + 11 environmental + 4 temporal)

**Output:** `(delta_lat, delta_lon)` tuple predicting next position

**Model Architecture:** Two separate XGBoost regressors (one for each coordinate)

**Loading Mechanism:** `ml/inference/trajectory_predict.py:28-41`
```python
def _load_models():
    global _model_lat, _model_lon, _schema
    if _model_lat is None:
        _model_lat = xgb.XGBRegressor()
        _model_lat.load_model(str(_LAT_MODEL_PATH))
        _model_lon = xgb.XGBRegressor()
        _model_lon.load_model(str(_LON_MODEL_PATH))
```

**How It's Used:**
- ❌ **NOT CALLED by route planner or risk engine**
- ✅ **Callable via:** `predict_iceberg_trajectory()` function
- ✅ **Used in:** ML training scripts in `ml/training/iceberg_xgb_train.py`

**Training Data Source:**
- Synthetic CSV: `data/raw/iceberg_trajectory_synthetic_2026.csv`
- Lag features (t-2, t-1, t) → predict target position
- Physics-informed features (delta positions, speeds)

---

### 2.3 Legacy Joblib Models (Deprecated)

**Files:**
- `ml/models/weights/seaice_xgb.joblib` (legacy format)
- `ml/models/weights/trajectory_model.joblib` (legacy format)

**Status:** Still present for backward compatibility but NOT used by current inference code

**Note:** JSON format preferred for cross-platform deployment (works on Windows/Linux/Mac without pickle issues)

---

## 3. Configuration & Metadata Files

### 3.1 Model Registry

**File:** `mlops/model_registry.json`

**Purpose:** Tracks deployed model versions with metadata

**Schema:**
```json
{
  "models": {
    "seaice_concentration": {
      "production": {
        "version": "ecdab427-b740-40ce-ac8e-7b5916ce07b3",
        "path": "ml/models/weights/seaice_xgb_latest.json",
        "deployed_at": "2026-09-22T14:30:00Z",
        "performance": {
          "rmse": 0.08,
          "mae": 0.06,
          "r2": 0.89
        }
      },
      "staging": { ... }
    },
    "iceberg_trajectory": { ... }
  }
}
```

**How It's Used:**
- ✅ **READ by:** MLOps deployment scripts (not integrated into runtime)
- ❌ **NOT USED by:** API endpoints or inference functions

---

### 3.2 Spatial Grid Configuration

**File:** `metadata/spatial_grid_config.json`

**Purpose:** Defines grid resolution for risk surface generation

**Schema:**
```json
{
  "antarctic_operational_zone": {
    "min_latitude": -80.0,
    "max_latitude": -50.0,
    "min_longitude": -180.0,
    "max_longitude": 180.0,
    "resolution_degrees": {
      "latitude": 1.2,
      "longitude": 3.6
    }
  }
}
```

**How It's Used:**
- ✅ **Referenced by:** Synthetic data generation scripts
- ❌ **NOT USED by:** Runtime route planner (uses adaptive resolution instead)

---

### 3.3 Temporal Configuration

**File:** `metadata/temporal_config.json`

**Purpose:** Defines forecast horizons and update frequencies

**Schema:**
```json
{
  "forecast_horizons": {
    "sea_ice": {
      "short_range_hours": 24,
      "medium_range_hours": 72,
      "long_range_hours": 168
    },
    "iceberg": {
      "timestep_hours": 6,
      "max_horizon_hours": 48
    }
  },
  "update_frequencies": {
    "observations": "PT3H",
    "risk_surface": "PT6H",
    "route_recalc": "PT12H"
  }
}
```

**How It's Used:**
- ✅ **Referenced by:** ML training scripts to set `forecast_horizon_hours` parameter
- ❌ **NOT USED by:** Runtime API (hardcoded horizon values in inference functions)

---

### 3.4 Benchmark Results

**File:** `ml/benchmarks/reports/benchmark_results.json`

**Purpose:** Stores ML model evaluation metrics across test splits

**Schema:**
```json
{
  "seaice_xgb_ecdab427": {
    "test_rmse": 0.082,
    "test_mae": 0.061,
    "test_r2": 0.887,
    "hard_cases": {
      "ice_edge_rmse": 0.124,
      "polynya_rmse": 0.098
    },
    "timestamp": "2026-09-22T10:15:00Z"
  }
}
```

**How It's Used:**
- ✅ **READ by:** Model comparison dashboard (not part of core app)
- ❌ **NOT EXPOSED via:** API endpoints

---

## 4. Data Flow Diagrams

### 4.1 Current State (Observations Only)

```
┌─────────────────────────────────────────────────────────────────┐
│  SYNTHETIC DATA (ZIP Archive)                                   │
│  C:\Users\ASUS\Desktop\Synthetic data for offshore             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Manual Seeding
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL + PostGIS Database                                  │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ sea_ice_obs      │  │ weather_obs      │                   │
│  │ 18,250 records   │  │ 73,000 records   │                   │
│  └──────────────────┘  └──────────────────┘                   │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ ocean_obs        │  │ iceberg_detect   │                   │
│  │ 73,000 records   │  │ 30,424 records   │                   │
│  └──────────────────┘  └──────────────────┘                   │
│  ┌──────────────────┐                                          │
│  │ risk_cells       │  (STATIC - seeded once)                 │
│  │ 50 cells         │                                          │
│  └──────────────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SQLAlchemy Query
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Risk Calculators (backend/app/services/risk/calculators.py)   │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ IceRiskCalc      │  │ IcebergRiskCalc  │                   │
│  │ queries sea_ice  │  │ queries detects  │                   │
│  └──────────────────┘  └──────────────────┘                   │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ WeatherRiskCalc  │  │ CurrentRiskCalc  │                   │
│  └──────────────────┘  └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ RiskComponentResult
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RiskEngine.calculate_cell_risk()                               │
│  Aggregates 4 components → composite_risk                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ risk_grid dict
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  A* Route Planner (backend/app/services/routing/astar.py)      │
│  Uses risk_grid for edge cost calculation                       │
└─────────────────────────────────────────────────────────────────┘
```

**DISCONNECTED COMPONENTS:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ML Models (ml/models/weights/*.json)                           │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ seaice_xgb       │  │ iceberg_xgb_lat  │                   │
│  │ latest.json      │  │ latest.json      │                   │
│  └──────────────────┘  └──────────────────┘                   │
│           │                       │                             │
│           │ NEVER CALLED          │ NEVER CALLED               │
│           ▼                       ▼                             │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ predict_sea_ice  │  │ predict_iceberg  │                   │
│  │ _concentration() │  │ _trajectory()    │                   │
│  └──────────────────┘  └──────────────────┘                   │
│           │                       │                             │
│           └───────────┬───────────┘                             │
│                       │                                          │
│                    NO INTEGRATION                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Intended State (ML-Integrated)

```
┌─────────────────────────────────────────────────────────────────┐
│  Environmental Data Sources                                     │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ DB Observations  │  │ Live APIs        │                   │
│  │ (historical)     │  │ (Open-Meteo)     │                   │
│  └──────────────────┘  └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Feature Aggregation
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ML Inference Layer (MISSING INTEGRATION)                       │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ predict_sea_ice  │  │ predict_iceberg  │                   │
│  │ _concentration() │  │ _trajectory()    │                   │
│  └──────────────────┘  └──────────────────┘                   │
│           │                       │                             │
│           │ Forecast result       │ Predicted path             │
│           ▼                       ▼                             │
│  ┌──────────────────────────────────────────┐                  │
│  │ Risk Calculators (ENHANCED)              │                  │
│  │ - Use observations as baseline           │                  │
│  │ - Call ML models for forecasts           │                  │
│  │ - Blend results with confidence weights  │                  │
│  └──────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ risk_grid with ML forecasts
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  A* Route Planner                                               │
│  Time-aware routing with ML-enhanced risk surface               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Storage Locations Summary

### 5.1 Synthetic Input Data (Archive)

**Path:** `C:\Users\ASUS\Desktop\Synthetic data for offshore`

**Format:** ZIP archive

**Contents:**
```
Synthetic data for offshore/
├── data/
│   ├── raw/
│   │   ├── grid_cells_2026.csv                    (50 rows)
│   │   ├── sea_ice_synthetic_2026.csv             (18,250 rows)
│   │   ├── weather_synthetic_2026.csv             (73,000 rows)
│   │   ├── ocean_currents_synthetic_2026.csv      (73,000 rows)
│   │   ├── iceberg_trajectory_synthetic_2026.csv  (30,424 rows)
│   │   ├── routes_synthetic_2026.csv              (10 routes)
│   │   └── route_waypoints_synthetic_2026.csv     (waypoint details)
│   └── metadata/
│       └── generation_config_2026.json
└── README.md
```

**Access:** Seeding script reads directly from ZIP without extraction

---

### 5.2 Static Reference Data (Repository)

**Path:** `backend/data/`

**Files:**
- `vessels.json` (5 research icebreakers, 138 lines)
- `ports.json` (EMPTY - 0 bytes, ports fetched from API)

**Vessel Data Used By:**
- Route planner when DB unavailable (DEMO_MODE)
- Fallback in `routes.py:108-127`

---

### 5.3 ML Model Weights (Repository)

**Path:** `ml/models/weights/`

**File Count:** 105 JSON files

**Size:** ~50 MB total

**Naming Convention:**
- `{model}_{algo}_{version}.json` (versioned)
- `{model}_{algo}_latest.json` (production symlink)

---

### 5.4 Database (Runtime)

**Connection:** PostgreSQL on `localhost:5433` (Docker Compose)

**Database Name:** `antarctic_nav`

**Tables (11 total):**
1. `vessels` (2 records)
2. `sea_ice_observations` (18,250 records)
3. `weather_observations` (73,000 records)
4. `ocean_observations` (73,000 records)
5. `icebergs` (30 records)
6. `iceberg_detections` (30,424 records)
7. `iceberg_predictions` (30,424 records)
8. `risk_cells` (50 records)
9. `routes` (10 pre-seeded)
10. `alerts` (2 initial)
11. `jobs` (background task tracking)

**Total Records:** ~225,000

**Disk Space:** ~150 MB (with PostGIS spatial indexes)

---

## 6. Usage Statistics & Integration Status

| Dataset | Records | DB Table | Used by Route Planner | Used by Risk Engine | Used by ML Training | Notes |
|---------|---------|----------|----------------------|--------------------|--------------------|-------|
| Sea-Ice Observations | 18,250 | `sea_ice_observations` | ✅ Indirect (via risk_grid) | ✅ Direct | ✅ Yes | Queried by IceRiskCalculator |
| Weather Observations | 73,000 | `weather_observations` | ✅ Indirect | ✅ Direct | ✅ Yes | Queried by WeatherRiskCalculator |
| Ocean Observations | 73,000 | `ocean_observations` | ✅ Indirect | ✅ Direct | ✅ Yes | Queried by CurrentRiskCalculator |
| Iceberg Detections | 30,424 | `iceberg_detections` | ✅ Indirect | ✅ Direct | ✅ Yes | Queried by IcebergRiskCalculator |
| Iceberg Predictions | 30,424 | `iceberg_predictions` | ❌ NO | ❌ NO | ✅ Yes | **CRITICAL GAP - Not integrated** |
| Risk Cells | 50 | `risk_cells` | ✅ Direct | ✅ Indirect | ❌ No | Static surface, should be ML-updated |
| Pre-Seeded Routes | 10 | `routes` | ❌ NO | ❌ NO | ❌ No | Only for GET /routes/{id} endpoint |
| Vessel Specs | 5 | `vessels` + JSON | ✅ Direct | ❌ No | ❌ No | Used for fuel/speed calculations |
| Ports (Empty) | 0 | N/A | ❌ NO | ❌ NO | ❌ No | Should be populated from external API |

---

| ML Model | File Count | Loaded at Runtime | Called by Risk Engine | Called by Route Planner | Integration Status |
|----------|------------|-------------------|----------------------|------------------------|-------------------|
| Sea-Ice XGBoost | 14 versions | ✅ Loadable | ❌ NO | ❌ NO | 🔴 **Disconnected** |
| Iceberg Lat XGBoost | 4 versions | ✅ Loadable | ❌ NO | ❌ NO | 🔴 **Disconnected** |
| Iceberg Lon XGBoost | 4 versions | ✅ Loadable | ❌ NO | ❌ NO | 🔴 **Disconnected** |
| Legacy Joblib Models | 2 files | ✅ Loadable | ❌ NO | ❌ NO | ⚠️ **Deprecated** |

---

## 7. Data Quality Assessment

### 7.1 Synthetic Data Limitations

**Sea-Ice Observations:**
- ✅ Realistic concentration range (0.0-1.0)
- ⚠️ Perfect data quality (1.0) - unrealistic
- ❌ No data gaps or missing values (real-world has 10-30% gaps)
- ❌ No diurnal or weekly cycles
- ❌ Thickness derived from concentration (simplistic)

**Weather Observations:**
- ✅ Plausible wind speeds for Antarctic conditions
- ⚠️ Wave height derived from wind only (ignores fetch/swell)
- ❌ No storm tracking or frontal systems
- ❌ Pressure field not spatially correlated

**Ocean Observations:**
- ✅ Current speeds match ACC magnitude
- ⚠️ SST estimated from latitude only (ignores upwelling/fronts)
- ❌ No mesoscale eddies or temporal variability

**Iceberg Trajectories:**
- ✅ Includes lag positions (t-2, t-1, t) for physics-informed ML
- ✅ Environmental forcing included (wind, current, sea-ice)
- ⚠️ Only 30 unique icebergs (real database would have 100s-1000s)
- ❌ No calving events, breakup, or size changes

**Risk Cells:**
- ⚠️ Static formula: `risk = f(latitude, longitude)` only
- ❌ No temporal evolution
- ❌ No correlation with actual observation data
- 🔴 **CRITICAL:** Should be generated by ML models, not hardcoded formula

---

### 7.2 ML Model Training Data Quality

**Source:** Same synthetic CSV files above

**Issues:**
1. **Synthetic Circularity:** Models trained on synthetic data, then evaluated on synthetic test split
   - Metrics (RMSE=0.08, R²=0.89) may not transfer to real-world
   - No validation against actual satellite data (NSIDC, Copernicus)

2. **Feature Leakage Risk:** `sea_ice_concentration` is both input feature AND target variable
   - Model is predicting FUTURE concentration from CURRENT concentration
   - This is valid for nowcasting but needs careful temporal splitting

3. **Spatial Autocorrelation:** Grid cells close together have similar values
   - Random train/test split may overestimate performance
   - Should use spatial block cross-validation

**Recommendation:** Label all outputs with `"SYNTHETIC_PROTOTYPE"` and warnings (already done in inference code)

---

## 8. Missing Data

### 8.1 Expected But Not Found

**Port Database:**
- File: `backend/data/ports.json` is **EMPTY** (0 bytes)
- Expected: Antarctic ports and waypoints (McMurdo, Rothera, Palmer, Neumayer, etc.)
- Impact: Frontend may fail port lookups
- Workaround: API endpoint `/api/v1/ports/` should fetch from external source

**Bathymetry Data:**
- No seafloor depth data found
- Impact: Cannot enforce draft restrictions or optimize routes through deep channels
- Status: Not implemented

**Historical Route Data:**
- Only 10 synthetic pre-seeded routes
- No actual vessel AIS tracks or historical passages
- Impact: Cannot validate routes against real-world navigation patterns

---

### 8.2 Data Pipeline Gaps

**Real-Time Data Ingestion:**
- Scripts exist: `scripts/copernicus/`, `scripts/era5/`
- Status: Present but integration not verified
- Missing: Automated schedule (cron/Celery) to refresh observations

**ML Model Retraining:**
- Training scripts exist: `ml/training/*.py`
- Missing: Automated pipeline to retrain on new observations
- Missing: A/B testing framework for model comparison

**Data Validation:**
- Validation script: `scripts/data_ingestion/validate_seeded_db.py`
- Only validates schema and spatial integrity
- Missing: Statistical QC (outlier detection, temporal consistency checks)

---

## 9. Recommendations

### 9.1 Immediate Fixes (< 1 Week)

1. **Run Synthetic Seeding**
   - Execute: `python scripts/data_ingestion/seed_synthetic_data.py <zip_path>`
   - Verify: `python scripts/data_ingestion/validate_seeded_db.py`
   - Result: Populate database so DEMO_MODE can be disabled

2. **Populate Ports File**
   - Source: Antarctic port coordinates from public databases
   - Minimum: 20-30 major stations and anchorages
   - Format: JSON with `[{name, lat, lon, type, country}]`

3. **Add Data Provenance Labels**
   - Ensure all API responses include `data_source_type: "SYNTHETIC_PROTOTYPE"`
   - Add warnings to frontend UI

---

### 9.2 Short-Term Enhancements (1-2 Weeks)

1. **Connect ML Models to Risk Pipeline**
   - Modify `IceRiskCalculator` to call `predict_sea_ice_concentration()`
   - Modify `IcebergRiskCalculator` to call `predict_iceberg_trajectory()`
   - Blend ML forecasts with observations using confidence weighting

2. **Create ML Test Endpoints**
   - `POST /api/v1/forecasts/sea-ice/predict`
   - `POST /api/v1/forecasts/iceberg/trajectory`
   - Allow frontend to visualize ML predictions independently

3. **Document Data Lineage**
   - Add metadata fields: `generated_by`, `model_version`, `confidence`
   - Track which observations → which risk cells → which routes

---

### 9.3 Medium-Term Improvements (1-2 Months)

1. **Real-Time Risk Surface Updates**
   - Celery task every 3 hours
   - Query latest observations
   - Run ML models over grid
   - Update `risk_cells` table with fresh forecasts

2. **Data Quality Monitoring**
   - Track observation recency per cell
   - Alert when data gaps exceed threshold
   - Visualize coverage on map

3. **Replace Synthetic Data**
   - Integrate real NSIDC sea-ice concentration
   - Integrate real ECMWF ERA5 weather reanalysis
   - Validate ML models against real data

---

## 10. Audit Conclusion

**Data Inventory Status:** COMPLETE

**Key Findings:**
- ✅ All synthetic datasets accounted for (18K-73K records each)
- ✅ ML models present and loadable (14 sea-ice, 8 iceberg versions)
- ⚠️ Database seeding manual (not automated)
- 🔴 **ML models NOT integrated into route planning pipeline**
- 🔴 **Iceberg predictions table populated but unused**
- ⚠️ Ports data file is empty

**Data Lineage:** Fully traceable from synthetic CSV → database → risk calculators → route planner

**Missing Links:**
1. ML inference → Risk calculators (CRITICAL)
2. Observation refresh → Risk cell updates (HIGH)
3. Real-world data → Synthetic replacement (MEDIUM)

**Overall Assessment:** Data infrastructure is well-designed but the ML prediction layer is **disconnected** from the operational routing system. All the pieces exist; they just need to be wired together.

---

**Document Version:** 1.0  
**Last Updated:** 2026-09-24
