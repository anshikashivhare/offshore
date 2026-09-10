# OFFSHORE — Project Documentation

**Problem Statement ID:** 26059 | **Organization:** Ministry of Earth Sciences (MoES) / NCPOR

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Frontend](#2-frontend)
3. [API Reference](#3-api-reference)
4. [Database](#4-database)
5. [Backend Services](#5-backend-services)
6. [Machine Learning Models](#6-machine-learning-models)
7. [Deployment](#7-deployment)
8. [Frontend Integration Guide](#8-frontend-integration-guide)

---

## 1. Architecture Overview

```text
Satellite / Sea-Ice Data     Weather Data     Ocean Data     Vessel Data
            \                    |               |              /
             \                   |               |             /
                        Data Processing
                               |
        +----------------------+----------------------+
        |                      |                      |
 Sea-Ice Forecasting    Iceberg Detection      Trajectory Prediction
        |                      |                      |
        +----------------------+----------------------+
                               |
                           Risk Engine
                               |
                         Dynamic Risk Map
                               |
                          A* Route Planner
                               |
                 +-------------+-------------+
                 |             |             |
             Safest        Fastest     Fuel-Efficient
                               |
                     React/Next.js Dashboard
```

### Core Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL + PostGIS
- **ORM**: SQLAlchemy 2.0
- **Message Broker & Cache**: Redis
- **Background Workers**: Celery
- **ML**: PyTorch + XGBoost + scikit-learn
- **Geospatial**: GeoPandas, Rasterio, xarray, Shapely
- **Frontend**: Next.js + TypeScript + TailwindCSS

---

## 2. Frontend

### Stack
Next.js + TypeScript + TailwindCSS with MapLibre/Leaflet for geospatial visualization.

### Key Components (`frontend/src/`)
| Directory | Purpose |
|---|---|
| `components/map/mission-map.tsx` | Main map canvas |
| `components/map/iceberg-layer.tsx` | Iceberg markers and trajectories |
| `components/map/sea-ice-layer.tsx` | Sea-ice concentration overlay |
| `components/map/ocean-current-layer.tsx` | Ocean current flow visualization |
| `components/map/route-layer.tsx` | Optimized route polylines |
| `components/map/route-panel.tsx` | Route comparison panel |
| `lib/routing/a-star-router.ts` | Client-side A* for preview routing |
| `stores/` | Zustand state stores (layers, routes, icebergs, currents) |

### Running
```bash
cd frontend && npm install && npm run dev
```

---

## 3. API Reference

Base URL: `http://localhost:8000/api/v1`
Interactive docs: `/api/v1/docs` (Swagger) | `/api/v1/redoc` (ReDoc)

### Navigation & Routing
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/navigation/plan` | End-to-end route planning (origin, destination, vessel, priority) |
| `POST` | `/routes/plan` | A* route optimization over risk grid |
| `POST` | `/routes/compare` | Multi-objective route comparison (safest/fastest/fuel-efficient) |

### Sea-Ice Forecasting
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/forecasts/sea-ice` | Trigger sea-ice concentration forecast |
| `GET` | `/forecasts/sea-ice/{id}` | Retrieve forecast result |

### Iceberg Intelligence
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/icebergs` | List tracked icebergs |
| `POST` | `/icebergs/detect` | Run detection on imagery source |
| `POST` | `/icebergs/trajectory` | Predict iceberg drift trajectory |
| `GET` | `/icebergs/{id}/track` | Get historical iceberg track |

### Risk & Alerts
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/risk/map` | Generate risk surface grid |
| `GET` | `/risk/cells` | Retrieve risk cells |
| `GET` | `/alerts` | Active navigational hazard alerts (filterable by severity) |

### Jobs & Vessels
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/jobs` | Dispatch background computation |
| `GET` | `/jobs/{id}` | Check job status/progress |
| `POST` | `/vessels` | Register vessel profile |
| `GET` | `/vessels` | List vessel profiles |

### API Contracts
- **Geospatial responses**: Standard GeoJSON `Feature` / `FeatureCollection`
- **Coordinates**: `[longitude, latitude]` order (EPSG:4326)
- **Timestamps**: ISO 8601 UTC (`2026-09-03T12:00:00Z`)
- **Pagination**: `skip`/`limit` params; response wraps `data`, `total`, `skip`, `limit`
- **Errors**: `{"error": {"code": "...", "message": "...", "details": [...]}}`

---

## 4. Database

### ORM Models (`backend/app/models/`)
| Table | Key Columns |
|---|---|
| `sea_ice_observations` | date, lat, lon, concentration, geometry (POINT) |
| `iceberg_detections` | iceberg_id, timestamp, lat, lon, confidence, geometry |
| `iceberg_tracks` | iceberg_id, timestamp, lat, lon, geometry |
| `environmental_data` | date, lat, lon, current_u/v, wind_u/v, geometry |
| `vessel_routes` | start/end lat/lon, total_cost, path_json |
| `vessels` | name, ice_class, max_speed, draft |

### Migrations
Managed via **Alembic** (`alembic.ini` + `backend/migrations/`).

---

## 5. Backend Services

### Service Layer (`backend/app/services/`)
| Service | Path | Purpose |
|---|---|---|
| **Alerts** | `services/alerts/engine.py` | Route hazard evaluation, severity classification |
| **Forecasting** | `services/forecasting/` | Sea-ice forecast base + baseline + metrics (MAE/RMSE) |
| **Icebergs** | `services/icebergs/` | Detection, tracking (association), trajectory prediction |
| **Navigation** | `services/navigation/orchestrator.py` | End-to-end orchestration of routing + risk + alerts |
| **Risk** | `services/risk/` | Risk calculators (ice, iceberg, weather, current) + engine |
| **Routing** | `services/routing/` | A*, Dijkstra, cost functions, constraints, comparison |

### Background Processing
Celery workers (`backend/app/worker/`) handle heavy computation: raster ingestion, ML inference, long-horizon forecasting.

---

## 6. Machine Learning Models

All ML code lives in `backend/ml/` as **standalone, decoupled modules** — no DB or API coupling.

### Sea-Ice Concentration Forecasting (`ml/seaice_model/`)
| Model | RMSE | Best For |
|---|---|---|
| **XGBoost** (lag features) | 0.0402 | Fast short-horizon (1-3 day) forecasts |
| **ConvLSTM** (spatiotemporal) | ~0.073 | Multi-day horizons (5-14 days) where persistence degrades |
| Persistence baseline | 0.0225 | Reference (hard to beat at 1-day) |

**Key files**: `data.py`, `train.py`, `train_convlstm.py`, `predict.py`, `convlstm.py`, `grid_sequence.py`, `real_data_loader.py`

### Iceberg Trajectory Prediction (`ml/trajectory_model/`)
| Model | Lat RMSE | Lon RMSE | Best For |
|---|---|---|---|
| **XGBoost** (primary) | 0.0031 | 0.0031 | Production — fastest, most accurate at this scale |
| LSTM (sequence) | 0.0044 | 0.0077 | Evaluated but underperforms XGBoost on small data |
| Naive baseline | 0.0045 | 0.0077 | Reference |

**Key files**: `data.py`, `train.py`, `train_lstm.py`, `predict.py`, `lstm_model.py`, `sequence_data.py`, `real_data_loader.py`

### Route Optimizer (`ml/route_optimizer/`)
A* pathfinding over ice concentration grid with configurable passability threshold.

### Training Commands
```bash
cd backend
python -m ml.seaice_model.train              # Sea-ice XGBoost
python -m ml.seaice_model.train_convlstm     # Sea-ice ConvLSTM
python -m ml.trajectory_model.train           # Trajectory XGBoost
python -m ml.trajectory_model.train_lstm      # Trajectory LSTM
```

### Real Data Sources
- **Sea-ice**: NSIDC / Copernicus Marine Service (NetCDF) → `ml/seaice_model/real_data_loader.py`
- **Iceberg tracks**: NSIDC Antarctic Iceberg Tracking Database (CSV) → `ml/trajectory_model/real_data_loader.py`
- **Environment**: ERA5 via Copernicus CDS (NetCDF: `u10`, `v10`, `uo`, `vo`)

---

## 7. Deployment

### Prerequisites
- Docker Engine (v24.0+), Docker Compose (v2.20+), 4GB+ RAM

### Quick Start
```bash
cp .env.example .env        # Configure environment
docker-compose up -d --build # Start full stack (db, redis, api, worker)
curl http://localhost:8000/api/v1/health  # Verify
```

### Services
| Container | Port | Purpose |
|---|---|---|
| `offshore_db` | 5433 | PostGIS database |
| `offshore_redis` | 6379 | Redis broker + cache |
| `offshore_api` | 8000 | FastAPI application |
| `offshore_worker` | — | Celery background worker |

### Scaling Workers
```bash
docker-compose up -d --scale worker=3
```

---

## 8. Frontend Integration Guide

### Base URL & Auth
- Base: `http://localhost:8000/api/v1`
- CORS: Configured via `BACKEND_CORS_ORIGINS` env var
- Auth: No JWT required for MVP endpoints

### Key Workflows

**1. Navigation Planning** (`POST /navigation/plan`)
- Returns: recommended route (GeoJSON), alternatives, metric deltas, alerts, explanation
- UX: Show loading skeleton (1-3s compute time)

**2. Background Jobs** (`POST /jobs` → poll `GET /jobs/{id}`)
- Poll every 2-5s until `status` is `completed` or `failed`
- Dev shortcut: append `?sync=true` for synchronous execution

**3. GeoJSON Conventions**
- All spatial data returns standard GeoJSON `FeatureCollection`
- Coordinates: `[longitude, latitude]` (EPSG:4326)
- Non-spatial properties embedded in `Feature.properties`
