# Implementation Plan: AI-Enabled Antarctic Sea-Ice, Iceberg Trajectory, and Navigation Decision Support System (MVP)

**Problem Statement ID:** 26059
**Organization:** Ministry of Earth Sciences (MoES) / NCPOR

This document outlines the step-by-step implementation plan for the Minimum Viable Product (MVP) of the Antarctic Navigation Decision Support System. This plan is shared with the 6-member team to coordinate the development effort.

## 1. Project Setup & Architecture
**Stack:**
- **Frontend:** React / Next.js with geospatial mapping (CesiumJS or Mapbox/Leaflet)
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL + PostGIS for spatial data
- **ML / Data Processing:** Python (PyTorch, scikit-learn, GeoPandas, Rasterio)

**Directory Structure overview:**
- `/frontend`: React dashboard
- `/backend`: FastAPI service
- `/database`: DB initialization scripts and schemas
- `/ml`: Model training, data preprocessing, and inference scripts
- `/risk_engine`: Logic for constructing spatial risk heatmaps
- `/routing`: A* pathfinding and optimization algorithms

## 2. Phase 1: Data Ingestion & Database Setup (Backend & DB Team)
1. **Database Initialization:** Set up PostgreSQL with the PostGIS extension.
2. **Schema Creation:** Implement tables based on SRS Section 21:
   - `vessels` (specs, speed, fuel, ice capability)
   - `sea_ice` (timestamp, lat/lon, concentration)
   - `icebergs` and `iceberg_trajectories`
   - `weather` and `routes`
3. **Data Pipelines:** Write Python scripts to download/mock sample historical data (e.g., NSIDC sea-ice data, Copernicus Sentinel imagery) and ingest it into the database.

## 3. Phase 2: Machine Learning Models (ML & CV Team)
*For the MVP, we will focus on a narrow spatial and temporal corridor to demonstrate feasibility.*

1. **Sea-Ice Forecasting:**
   - Implement a baseline model (e.g., historical average or simple CNN) to forecast sea-ice concentration over a short horizon.
2. **Iceberg Detection (CV):**
   - Process sample satellite imagery (SAR/Optical) using an object detection/segmentation model (e.g., YOLO or UNet) to detect icebergs and extract coordinates.
3. **Trajectory Prediction:**
   - Create a model predicting future iceberg locations based on historical tracks, ocean currents, and wind. Introduce a basic uncertainty radius for the MVP.

## 4. Phase 3: Risk Engine & Route Optimization (Optimization Team)
1. **Dynamic Risk Map:**
   - Implement the `Risk Engine` to fuse Sea-Ice concentration, Iceberg proximity, Weather, and Current data into a gridded composite risk score: `R = w₁R_ice + w₂R_berg + w₃R_weather + w₄R_current`
2. **Route Optimizer (A*):**
   - Build an A* algorithm over the gridded map.
   - The cost function should balance risk, distance (time), and fuel consumption based on the vessel profile.
   - Generate multi-objective outputs: Fastest, Safest, Fuel-Efficient.

## 5. Phase 4: Backend API Integration (Backend Team)
1. **API Endpoints:**
   - `GET /api/forecast/sea-ice` - Returns sea-ice layers.
   - `GET /api/icebergs` - Returns detected icebergs and predicted trajectories.
   - `GET /api/risk-map` - Returns the dynamic risk heatmap data.
   - `POST /api/routes/plan` - Accepts origin, destination, vessel profile, and priority, returning optimal paths.

## 6. Phase 5: Interactive Dashboard (Frontend Team)
1. **Geospatial Map UI:** Integrate a map component centered on Antarctica.
2. **Layer Toggles:** Allow users to overlay Sea-Ice forecasts, Risk Heatmaps, and Iceberg tracking data.
3. **Route Planning Panel:**
   - Form to select Origin, Destination, Vessel Profile, and Routing Priority.
   - Display a comparison of route options (Shortest vs. Safest vs. Most Efficient).
4. **Metrics & Alerts:** Show estimated ETA, Fuel consumption, Risk score, and human-readable explanation alerts (e.g., "Route avoided High Risk Iceberg zone").

## 7. Progress Log (Completed Work)

**Backend & Database:**
- [x] Initialized FastAPI backend with CORS middleware in `app/main.py`.
- [x] Set up PostgreSQL with PostGIS in `docker-compose.yml`.
- [x] Configured SQLAlchemy + GeoAlchemy2 ORM (`app/db/database.py` and `app/db/models.py`).
- [x] Fixed `PYTHONPATH` module import bugs and `shapely` dependencies for standalone scripts (`load_sample_seaice.py`, `init_db.py`).

**Machine Learning & Algorithms:**
- [x] Implemented A* Route Optimizer (`ml/route_optimizer/optimizer.py`) with grid graph construction and cost calculation based on sea-ice concentration.
- [x] Developed Sea-Ice Forecasting XGBoost baseline (`ml/seaice_model`), trained on synthetic NSIDC-style data.
- [x] Developed Iceberg Trajectory Prediction model (`ml/trajectory_model`) using `MultiOutputRegressor` to project delta-lat/delta-lon based on ocean currents and wind.
- [x] Verified both ML models outperforming naive (persistence/zero-movement) baselines.

**API Integrations:**
- [x] `POST /routes/optimize`: Connected to the A* route optimizer.
- [x] `GET /seaice/forecast`: Integrated with the sea-ice XGBoost baseline model.
- [x] `GET /iceberg/trajectory`: Integrated with the multi-step trajectory projection model.

## Next Steps
- **Execution:** Begin Phase 5 (Interactive Dashboard / Frontend setup) to visualize the route optimizer, sea-ice forecasts, and trajectory projections on a geospatial map.
