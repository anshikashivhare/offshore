# OFFSHORE Antarctic Navigation Prototype - System Architecture Audit

**Audit Date:** 2026-09-24  
**Auditor:** Senior Engineering Review  
**Scope:** Complete prototype codebase review to identify root causes of hardcoded routes, fake metrics, and disconnected ML models

---

## Executive Summary

This audit reveals a **functional but incomplete** prototype where:
- ✅ **Route planning DOES work** with real A* pathfinding over a global land/water mask
- ✅ **ML models exist and ARE loaded** (sea-ice XGBoost, iceberg trajectory XGBoost)
- ⚠️ **ML predictions are NOT fed into route planning** - models exist but aren't integrated into the risk pipeline
- ⚠️ **Risk data exists but is often missing** - synthetic database seeding exists but isn't connected to live routing
- ⚠️ **Metrics are computed correctly** but may appear "fake" when risk_grid is empty (DEMO_MODE fallback)

**Overall Assessment:** This is NOT a hardcoded demo. It's a working pathfinder with real A* search, genuine land avoidance, and 4D time-aware routing that currently lacks integration between its ML prediction layer and route cost calculation.

---

## 1. Route Planning Architecture

### 1.1 Route Generation Flow (VERIFIED WORKING)

**Entry Point:** `backend/app/api/v1/endpoints/routes.py:92`
```
POST /api/v1/routes/plan
  ↓
  RouteRequest parsed (origin, destination, vessel_id, objective_type)
  ↓
  Vessel loaded from DB or fallback JSON (routes.py:106-127)
  ↓
  _build_risk_grid() fetches RiskCell records from DB (routes.py:31-89)
  ↓
  AStarRoutePlanner.plan_route() with risk_grid (routes.py:159)
  ↓
  A* search with land avoidance, 4D forecast, risk scoring (astar.py:104-245)
  ↓
  RouteCreate returned with WKT LineString geometry
```

**Severity:** ✅ **LOW** - Core routing logic is legitimate

**Evidence:**
- `backend/app/services/routing/astar.py:104-245` - Full A* implementation with open/closed sets, g_score, f_score
- `backend/app/services/routing/grid.py:33-93` - Land mask checking on EVERY edge via `globe.is_land()` with 0.05° sampling
- `backend/app/services/routing/grid.py:95-143` - BFS snap-to-water for port locations
- Routes are computed per-request, not retrieved from a dataset

### 1.2 Land/Water Mask Verification

**CRITICAL:** A* planner DOES use a land mask.

**File:** `backend/app/services/routing/grid.py:60-90`

```python
# Line 68: samples = max(5, int(math.ceil(dist_deg / 0.05)))
# Line 75-87: Every 0.05° increment along each edge is checked:
for i in range(1, samples + 1):
    test_lat = current.lat + t * dlat
    test_lon = current.lon + t * dlon_shortest
    if globe.is_land(test_lat, test_lon):
        is_safe = False
        break
```

**Verification:**
- Uses `global-land-mask` library (Python package)
- Samples edges at ~5km intervals to prevent clipping through narrow coastlines
- Any edge touching land is rejected from neighbor generation

**Severity:** ✅ **NONE** - Land avoidance is production-grade

### 1.3 Adaptive Grid Resolution (WORKING)

**File:** `backend/app/services/routing/astar.py:39-56`

Routes dynamically adjust grid resolution:
- **< 2000 NM:** 0.5° resolution (Antarctic coastal navigation)
- **2000-4000 NM:** 1.0° resolution
- **> 4000 NM:** 2.0° resolution (trans-oceanic)

This prevents node explosion on long voyages while maintaining precision near ice zones.

**Severity:** ✅ **NONE** - Intelligent optimization

---

## 2. ML Model Integration - **ROOT CAUSE IDENTIFIED**

### 2.1 ML Models: Loaded But Not Connected

**Severity:** 🔴 **CRITICAL** - Models exist and load successfully but predictions DO NOT influence routing

#### Sea-Ice Concentration Model
**File:** `ml/inference/seaice_predict.py:27-39`

```python
def _load_model():
    global _model, _schema
    if _model is None:
        import xgboost as xgb
        _model = xgb.XGBRegressor()
        _model.load_model(str(_MODEL_PATH))  # Loads seaice_xgb_latest.json
```

**Model Files Found:**
- `ml/models/weights/seaice_xgb_latest.json` (XGBoost model in JSON format)
- `ml/models/weights/seaice_feature_schema.json` (17 features including lag, wind, SST, currents)
- 13+ versioned model snapshots in `ml/models/weights/`

**Model Output:** `predict_sea_ice_concentration()` returns:
- `predicted_sea_ice_concentration_clipped` (0.0-1.0)
- `model_run_id`
- `data_source_type: "SYNTHETIC_PROTOTYPE"`
- **Warning flag** that data is synthetic

#### Iceberg Trajectory Model
**File:** `ml/inference/trajectory_predict.py:28-41`

```python
def _load_models():
    _model_lat = xgb.XGBRegressor()
    _model_lat.load_model(str(_LAT_MODEL_PATH))  # iceberg_xgb_lat_latest.json
    _model_lon = xgb.XGBRegressor()
    _model_lon.load_model(str(_LON_MODEL_PATH))  # iceberg_xgb_lon_latest.json
```

**Model Files Found:**
- `ml/models/weights/iceberg_xgb_lat_latest.json`
- `ml/models/weights/iceberg_xgb_lon_latest.json`
- Predicts `delta_lat`, `delta_lon` from current position + 2 lag positions + environmental features

### 2.2 WHERE THE DISCONNECT HAPPENS

**Risk Calculation Flow:**

```
RiskEngine.calculate_cell_risk() [backend/app/services/risk/engine.py:108-146]
  ↓
  Calls 4 calculators in parallel:
    - IceRiskCalculator [backend/app/services/risk/calculators.py:79-139]
    - IcebergRiskCalculator [calculators.py:142-198]
    - WeatherRiskCalculator [calculators.py:201-260]
    - CurrentRiskCalculator [calculators.py:263-320]
  ↓
  Each calculator queries DB observation tables (sea_ice_observations, iceberg_detections, etc.)
  ↓
  **ML MODELS ARE NEVER CALLED**
  ↓
  Composite risk = weighted sum of observation-based risks
```

**ROOT CAUSE:**

1. **Risk calculators read ONLY from observation tables** (`calculators.py:96`, `calculators.py:157`, etc.)
2. **ML inference functions exist but are never imported** by `RiskEngine` or calculators
3. **No code path from route planner → ML predict functions**
4. Routes use `risk_grid` but risk_grid is populated from `RiskCell` DB table, not live ML predictions

**File Evidence:**
- `backend/app/services/risk/calculators.py` - Imports: NO ML inference modules
- `backend/app/services/routing/astar.py` - Imports: NO ML inference modules
- `ml/inference/seaice_predict.py` - Function exists but grep shows it's only called in `__main__` block (demo/test)

### 2.3 What WOULD Be Required to Connect Them

```python
# In IceRiskCalculator.calculate() - MISSING INTEGRATION:

from ml.inference.seaice_predict import predict_sea_ice_concentration

async def calculate(self, lat, lon, timestamp):
    # Current: Query sea_ice_observations table
    # NEEDED: If no recent observation, call ML model:
    
    if not rows or best_d > self.search_radius_km:
        # Fetch environmental features (wind, SST, currents)
        env_features = await self._fetch_env_features(lat, lon, timestamp)
        
        # Call ML model for forecast
        ml_result = predict_sea_ice_concentration(
            latitude=lat,
            longitude=lon,
            sea_ice_concentration=env_features['current_conc'],
            air_temperature_c=env_features['air_temp'],
            # ... 14 more features
        )
        
        # Use ml_result['predicted_sea_ice_concentration_clipped'] as risk
        return RiskComponentResult(
            risk_value=ml_result['predicted_sea_ice_concentration_clipped'],
            confidence=0.7,  # Lower confidence for ML prediction
            is_missing=False,
            metadata={'source': 'ml_forecast', 'model_run_id': ml_result['model_run_id']}
        )
```

**Similar integration needed for:**
- `IcebergRiskCalculator` → `ml.inference.trajectory_predict.predict_iceberg_trajectory()`
- Forecast horizon propagation through A* search waypoints

**Severity:** 🔴 **CRITICAL** - This is the primary gap between "prototype" and "working system"

---

## 3. Risk Data Pipeline

### 3.1 Risk Grid Construction (FUNCTIONAL)

**File:** `backend/app/api/v1/endpoints/routes.py:31-89`

```python
async def _build_risk_grid(db: AsyncSession, request: RouteRequest) -> Dict[Any, float]:
    # 1. Compute bbox from origin/destination + 2° margin
    envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    
    # 2. Query RiskCell table with spatial intersection
    stmt = select(RiskCell).where(RiskCell.geometry.ST_Intersects(envelope))
    
    # 3. Return dict keyed by (lat, lon) rounded to 0.1°
    grid[(round(clat, 1), round(clon, 1))] = float(cell.composite_risk)
```

**Database Table:** `risk_cells`
- Contains: `ice_risk`, `iceberg_risk`, `weather_risk`, `current_risk`, `composite_risk`
- Populated by: `scripts/data_ingestion/seed_synthetic_data.py:142-198` (synthetic seeder)
- **NOT populated by ML models in real-time**

**Severity:** 🟡 **HIGH** - Risk grid works but uses static synthetic data, not dynamic ML predictions

### 3.2 Risk Integration into A* Cost Function (VERIFIED WORKING)

**File:** `backend/app/services/routing/cost.py:99-135`

```python
def calculate_edge_cost_4d(self, current, neighbor, vessel, risk_score, env_conditions):
    distance = current.distance_to(neighbor)
    sog = self.get_effective_speed(current, neighbor, vessel, env_conditions)
    time_hours = distance / sog
    fuel = time_hours * vessel.fuel_consumption
    
    cost = (
        self.weights.alpha * fuel                    # Fuel component
        + self.weights.beta * time_hours             # Time component
        + self.weights.gamma * (risk_score * distance)  # Risk component
    )
    return cost
```

**Evidence of Real Use:**
- A* planner calls `cost_calculator.get_risk_at(neighbor, risk_grid)` at line `astar.py:207`
- Risk is multiplied by distance to accumulate exposure
- Different objectives change weights: SAFEST = `gamma=0.8`, FASTEST = `gamma=0.1`

**Severity:** ✅ **NONE** - Cost calculation is legitimate when risk_grid has data

### 3.3 DEMO_MODE Fallback Behavior

**File:** `backend/app/config/config.py:15`
```python
DEMO_MODE: bool = True  # Default is DEMO mode
```

**Observed Behavior When DEMO_MODE=True:**

1. **Risk grid empty check** (`routes.py:40-41`): Returns `{}` immediately if DEMO_MODE
2. **Missing risk fallback** (`astar.py:209-218`):
   ```python
   if risk is None:
       if demo_mode:
           effective_risk = 0.5  # Arbitrary penalty, not 0.0
       else:
           if objective == SAFEST:
               raise ValueError("Safety First requires verified risk data")
           effective_risk = 0.0
   ```
3. **Heuristic weight boost** (`astar.py:173`): `heuristic_weight = 8.0` in demo mode (vs 1.05 in production) to reduce search space
4. **Database bypass** (`routes.py:166-168`): Routes are NOT persisted to DB in demo mode

**Why This Matters:**
- In DEMO_MODE without database, risk_grid is empty
- A* still runs but with `effective_risk=0.5` (unverified penalty)
- Routes ARE computed, not hardcoded
- Metrics (distance, ETA, fuel) are real calculations, not fake

**Severity:** 🟡 **MEDIUM** - Demo mode gives functional but unverified routes (by design)

---

## 4. Metric Calculation Verification

### 4.1 Distance Calculation (REAL)

**File:** `backend/app/services/routing/grid.py:17-26`

```python
def distance_to(self, other: "Node") -> float:
    """Haversine distance in nautical miles"""
    R = 3440.065  # Earth radius in NM
    dlat = math.radians(other.lat - self.lat)
    dlon = math.radians(other.lon - self.lon)
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c
```

**Verification:**
- Standard Haversine formula
- Earth radius: 3440.065 NM (correct for WGS84)
- Called for EVERY edge in path reconstruction (`astar.py:299-307`)

**Total Distance:** Sum of all edge distances in final path

**Severity:** ✅ **NONE** - Distance is geometrically accurate

### 4.2 ETA Calculation (4D TIME-AWARE)

**File:** `backend/app/services/routing/astar.py:202-243`

```python
# ETA propagates through A* search state
env = global_forecast_grid.get_conditions(neighbor.lat, neighbor.lon, rough_eta)
sog = scorer.get_effective_speed(current, neighbor, vessel, env)
exact_eta = current_time + timedelta(hours=(rough_dist / sog))
arrival_times[neighbor] = exact_eta

heapq.heappush(open_set, (f_score[neighbor], id(neighbor), neighbor, exact_eta))
```

**4D Forecast Grid:**
- `backend/app/services/environment/forecast_grid.py:1-118`
- Fetches wind/wave/current forecasts from Open-Meteo API
- 3-hour temporal resolution, 0.1° spatial resolution
- 14-day forecast horizon
- **This IS real environmental data, not synthetic**

**Speed Over Ground Calculation:**
- `backend/app/services/routing/cost.py:56-97`
- `SOG = STW + current_parallel - wave_penalty - headwind_penalty`
- Vector math with current direction, wind direction, wave height

**ETA Accuracy:**
- Each waypoint has individual ETA based on accumulated travel time
- Final ETA = `arrival_times[goal_node]` from A* state

**Severity:** ✅ **NONE** - ETA is dynamically computed with real weather forecasts

### 4.3 Fuel Calculation (SIMPLIFIED BUT CONSISTENT)

**File:** `backend/app/services/routing/cost.py:9-17`

```python
def estimate_fuel(self, vessel: Vessel, distance_nm: float) -> float:
    hours = distance_nm / vessel.cruising_speed
    return hours * vessel.fuel_consumption
```

**Vessel Data:**
- `backend/data/vessels.json` contains real vessels:
  - RRS Sir David Attenborough: 25.5 units/hr
  - RV Polarstern: 30.0 units/hr
  - USCGC Healy: 35.0 units/hr

**Fuel Accumulation:**
- A* computes time per edge with variable SOG
- Fuel = `time_hours * vessel.fuel_consumption` per edge
- Total fuel = sum across all waypoints (`astar.py:310`)

**Limitation:**
- Fuel rate is constant (no throttle model)
- No ice resistance penalty
- **BUT**: It's consistently calculated, not randomly generated

**Severity:** 🟡 **MEDIUM** - Simplified model but mathematically consistent

### 4.4 Risk Score Calculation (REAL WHEN DATA EXISTS)

**File:** `backend/app/services/routing/astar.py:299-307`

```python
for i in range(len(path) - 1):
    dist = path[i].distance_to(path[i + 1])
    total_distance += dist
    cell_risk = self.cost_calculator.get_risk_at(path[i + 1], risk_grid)
    if cell_risk is None and demo_mode:
        total_risk += 0.5 * dist  # Unverified penalty
    else:
        total_risk += (cell_risk if cell_risk is not None else 0.0) * dist
```

**Risk Score = Σ(risk × distance)** for each waypoint

- Units: risk·nautical_miles
- Higher score = more cumulative risk exposure
- Used for route comparison in multi-objective optimization

**Severity:** ✅ **NONE** when risk_grid populated, 🟡 **MEDIUM** in DEMO_MODE (uses placeholder)

---

## 5. Synthetic Data Seeding Pipeline

### 5.1 Synthetic Data Source

**File:** `scripts/data_ingestion/seed_synthetic_data.py:1-572`

**Dataset Location:** `C:\Users\ASUS\Desktop\Synthetic data for offshore` (ZIP archive)

**Contents:**
- `data/raw/grid_cells_2026.csv` → 50 risk cells
- `data/raw/sea_ice_synthetic_2026.csv` → 18,250 observations
- `data/raw/weather_synthetic_2026.csv` → 73,000 observations
- `data/raw/ocean_currents_synthetic_2026.csv` → 73,000 observations
- `data/raw/iceberg_trajectory_synthetic_2026.csv` → 30,424 detections + predictions
- `data/raw/routes_synthetic_2026.csv` → 10 pre-computed routes
- `data/raw/route_waypoints_synthetic_2026.csv` → Waypoint geometries

### 5.2 Database Tables Populated

**Seeding Flow:**
```
seed_synthetic_data.py (Python script using psycopg2)
  ↓
  PostgreSQL + PostGIS database: antarctic_nav
  ↓
  Tables populated:
    - vessels (2 records)
    - risk_cells (50 records) - USED BY ROUTE PLANNER
    - sea_ice_observations (18,250)
    - weather_observations (73,000)
    - ocean_observations (73,000)
    - icebergs (30 unique)
    - iceberg_detections (30,424)
    - iceberg_predictions (30,424) - NOT USED BY ROUTE PLANNER
    - routes (10 pre-seeded) - NOT RETURNED BY /plan ENDPOINT
    - alerts (2 initial)
```

**Key Finding:**
- Pre-seeded routes in DB are NOT the routes returned by `/api/v1/routes/plan`
- `/plan` endpoint computes NEW routes per request
- Pre-seeded routes are for demo/testing of the `/routes/{route_id}` GET endpoint

**Severity:** ✅ **NONE** - Seeded routes are samples, not what the planner returns

### 5.3 Validation Script

**File:** `scripts/data_ingestion/validate_seeded_db.py:1-151`

**Checks Performed:**
1. Record counts match expected minimums
2. PostGIS geometry validity (`ST_IsValid`)
3. SRID=4326 enforcement
4. Foreign key integrity (routes→vessels, detections→icebergs)
5. Spatial type checks (POINT, LINESTRING, POLYGON)

**Severity:** ✅ **NONE** - Proper data quality validation exists

---

## 6. Frontend → Backend → ML Data Flow

### 6.1 Frontend Route Request

**File:** `frontend/src/lib/api.ts:75-90`

```typescript
export async function planRoute(request: any) {
  const response = await fetch(`${API_BASE_URL}/api/v1/routes/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
  return response.json();
}
```

**Request Payload:**
```json
{
  "origin": "-77.85,166.67",  // lon,lat string
  "destination": "-67.57,-68.13",
  "vessel_id": "uuid",
  "departure_time": "2026-09-24T12:00:00Z",
  "objective_type": "SAFEST",  // or FASTEST, FUEL_EFFICIENT, SHORTEST
  "weights": {
    "alpha": 0.1,  // Fuel weight
    "beta": 0.1,   // Time weight
    "gamma": 0.8   // Risk weight
  }
}
```

### 6.2 Response Data Structure

**File:** `backend/app/schemas/route.py` (Pydantic models)

```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [166.67, -77.85],  // [lon, lat] waypoints
      [165.2, -76.8],
      ...
      [-68.13, -67.57]
    ]
  },
  "properties": {
    "route_id": "uuid",
    "vessel_id": "uuid",
    "origin": "-77.85,166.67",
    "destination": "-67.57,-68.13",
    "departure_time": "2026-09-24T12:00:00Z",
    "distance": 2847.3,  // nautical miles
    "eta": "2026-09-28T15:20:00Z",
    "estimated_fuel": 62543.8,
    "risk_score": 1245.6,
    "objective_type": "SAFEST",
    "algorithm_version": "AStar-4D-TimeAware-v1.0",
    "risk_data_status": "demo_unverified",  // in DEMO_MODE
    "ml_prediction_status": "unavailable",
    "warnings": [
      "DEMO ROUTE — Risk data unavailable. This route has NOT been verified..."
    ],
    "waypoints": [
      {
        "lat": -77.85, "lon": 166.67,
        "eta": "2026-09-24T12:00:00Z",
        "data_provenance": "observation",
        "env_conditions": {
          "wind_speed_10m": 12.4,
          "wave_height": 2.1,
          "ocean_current_velocity": 0.3
        }
      },
      // ... more waypoints
    ]
  }
}
```

**Data Provenance Field:**
- `backend/app/services/routing/modes.py` (referenced in `astar.py:326`)
- Marks waypoints as "observation" (0-72hrs) or "forecast" (>72hrs)
- 14-day horizon limit

**Severity:** ✅ **NONE** - Response structure is complete and transparent about data quality

---

## 7. Critical Gaps Summary

### 7.1 Confirmed Working Components

| Component | Status | Evidence |
|-----------|--------|----------|
| A* Pathfinding | ✅ WORKING | `astar.py:104-245` - Full heap-based search |
| Land Avoidance | ✅ WORKING | `grid.py:60-90` - `globe.is_land()` on every edge |
| Distance Calculation | ✅ WORKING | `grid.py:17-26` - Haversine formula |
| ETA with 4D Forecasts | ✅ WORKING | `astar.py:202-243`, `forecast_grid.py:1-118` |
| Fuel Calculation | ✅ WORKING | Simplified but consistent linear model |
| Risk Grid Construction | ✅ WORKING | `routes.py:31-89` - Spatial query from DB |
| Multi-Objective Comparison | ✅ WORKING | `comparison.py:137-223` - 4 objectives compared |
| Adaptive Grid Resolution | ✅ WORKING | `astar.py:39-56` - Dynamic 0.5°-2.0° |
| Port Snap-to-Water | ✅ WORKING | `grid.py:95-143` - BFS to nearest water |
| Coastal Approach Refinement | ✅ WORKING | `astar.py:58-102` - Fine-grid final leg |

### 7.2 Confirmed Gaps (ROOT CAUSES)

| Issue | Severity | Root Cause | File Reference |
|-------|----------|------------|----------------|
| **ML predictions not used in routing** | 🔴 CRITICAL | Risk calculators query DB observations only, never call ML inference functions | `calculators.py:79-320` - No ML imports |
| **Risk grid often empty in demo** | 🟡 HIGH | DEMO_MODE bypasses DB query; synthetic seeder not run automatically | `routes.py:40-41`, `config.py:15` |
| **Iceberg predictions stored but ignored** | 🔴 CRITICAL | `iceberg_predictions` table populated but `IcebergRiskCalculator` only reads `iceberg_detections` | `calculators.py:157` |
| **Sea-ice forecasts not generated live** | 🔴 CRITICAL | XGBoost model exists but `IceRiskCalculator` uses historical observations only | `calculators.py:96` |
| **Static risk cells** | 🟡 HIGH | `risk_cells` table seeded once, not updated with new ML predictions | `seed_synthetic_data.py:142-198` |
| **No ML prediction API endpoint** | 🟡 MEDIUM | No `/api/v1/forecasts/predict` endpoint to test ML models directly | N/A - Missing feature |

### 7.3 NOT Issues (Misconceptions Clarified)

| Claim | Reality | Evidence |
|-------|---------|----------|
| "Routes are hardcoded" | ❌ FALSE | Routes computed per request via A* search | `astar.py:104-369` |
| "Metrics are fake" | ❌ FALSE | Distance/ETA/fuel calculated from path geometry and vessel specs | `cost.py:9-135`, `grid.py:17-26` |
| "Planner treats all coords as valid" | ❌ FALSE | Land mask checked on every edge with 5km sampling | `grid.py:60-90` |
| "ML models don't exist" | ❌ FALSE | XGBoost models present and loadable | `ml/models/weights/*.json` (105 files) |
| "Routes from static dataset" | ❌ FALSE | Pre-seeded routes in DB are samples, not planner output | `seed_synthetic_data.py:411-485` |

---

## 8. Recommended Fixes (Priority Order)

### 8.1 CRITICAL - Integrate ML Predictions into Risk Calculators

**File:** `backend/app/services/risk/calculators.py`

**Changes Required:**
1. Import ML inference functions:
   ```python
   from ml.inference.seaice_predict import predict_sea_ice_concentration
   from ml.inference.trajectory_predict import predict_iceberg_trajectory
   ```

2. Modify `IceRiskCalculator.calculate()` to:
   - Query observation as baseline
   - If observation missing/stale, call ML model with environmental features
   - Return ML prediction with `confidence=0.7` and `metadata={'source': 'ml_forecast'}`

3. Modify `IcebergRiskCalculator.calculate()` to:
   - Read iceberg detections (current behavior)
   - Call `predict_iceberg_trajectory()` for each detected iceberg
   - Project trajectory forward to check intersection with route corridor
   - Return risk based on predicted proximity, not just current position

**Estimated Effort:** 3-5 days

### 8.2 HIGH - Create Real-Time Risk Cell Update Pipeline

**New Component:** `backend/app/services/risk/forecast_pipeline.py`

**Purpose:**
- Background job that runs every 3 hours
- Queries current environmental observations
- Calls ML models for grid cells in operational area
- Updates `risk_cells` table with fresh forecasts
- Marks cells with `forecast_timestamp` and `ml_model_version`

**Integration:** Celery task or FastAPI BackgroundTasks

**Estimated Effort:** 2-3 days

### 8.3 MEDIUM - Add ML Prediction API Endpoints

**New Endpoints:**
```
POST /api/v1/forecasts/sea-ice/predict
POST /api/v1/forecasts/iceberg/trajectory
```

**Purpose:**
- Allow frontend to visualize ML predictions independently
- Enable testing of ML models without full route planning
- Return confidence intervals and feature importance

**Estimated Effort:** 1-2 days

### 8.4 LOW - Enhanced DEMO_MODE Warning UI

**Frontend Change:** Show prominent banner when `risk_data_status === "demo_unverified"`

**Purpose:** Users currently may not notice the warning buried in response properties

**Estimated Effort:** 0.5 days

---

## 9. Database Dependency Analysis

**Current Setup:**
- PostgreSQL + PostGIS required for production
- Synthetic seeding script: `scripts/data_ingestion/seed_synthetic_data.py`
- Manual seeding: `python seed_synthetic_data.py <zip_path>`
- Docker Compose: `docker-compose.yml` defines postgres service on port 5433

**DEMO_MODE Behavior:**
- Backend starts without DB connection
- Vessel data loaded from JSON fallback: `backend/data/vessels.json`
- Port data: Empty file `backend/data/ports.json` (0 bytes) - ports fetched from API in production
- Routes computed but not persisted
- Risk grid empty → `effective_risk=0.5` fallback

**Production Requirements:**
1. PostgreSQL 15+ with PostGIS 3.3+
2. Seeded observation tables (sea_ice, weather, ocean, icebergs)
3. Seeded risk_cells table OR real-time ML pipeline
4. `DEMO_MODE=False` in environment

**Severity:** 🟡 **MEDIUM** - Docker setup exists but seeding is manual

---

## 10. Conclusion

This prototype is **significantly more functional than a mockup**:

### Strengths:
- ✅ Real A* pathfinding with admissible heuristics
- ✅ Robust land avoidance with coastline sampling
- ✅ 4D time-aware routing with live weather forecasts (Open-Meteo API)
- ✅ Multi-objective optimization (SHORTEST, FASTEST, SAFEST, FUEL_EFFICIENT)
- ✅ Adaptive grid resolution for global voyages
- ✅ ML models trained and ready (XGBoost for sea-ice and icebergs)
- ✅ Complete database schema with PostGIS spatial types
- ✅ Transparent data quality warnings in API responses

### Critical Gaps:
- 🔴 **ML models exist but are not called** by the risk pipeline
- 🔴 **Risk calculators use observations only**, missing forecasting capability
- 🟡 **Static risk data** requires manual seeding or background job integration

### Assessment:
This is **NOT a fake demo**. It's a working pathfinder with a **disconnected ML layer**. The route geometries, distances, ETAs, and fuel estimates are all **legitimately computed**. The missing piece is the **integration bridge** between trained ML models and the risk scoring system that feeds the route planner.

**Recommended Path Forward:**
1. Implement changes in Section 8.1 (ML integration) - **Highest Priority**
2. Run synthetic seeding pipeline - **Immediate Quick Win**
3. Add real-time forecast pipeline - **Production Readiness**
4. Create ML test endpoints - **Development QOL**

---

**Audit Complete**  
**Next Steps:** Review findings with development team and prioritize integration tasks.
