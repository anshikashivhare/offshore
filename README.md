# OFFSHORE

## AI-Powered Antarctic Maritime Navigation Decision Support System

OFFSHORE is an AI-powered decision support platform designed to help vessels navigate Antarctic waters more safely and efficiently. The system combines sea-ice data, iceberg information, weather and ocean conditions to predict maritime hazards, generate dynamic risk maps, and recommend optimized vessel routes.

### Core Features
- Sea-ice forecasting
- Iceberg detection and tracking
- Iceberg trajectory prediction
- Dynamic maritime risk maps
- A* route optimization
- Safest, fastest and fuel-efficient route options
- ETA, fuel and risk comparison
- Interactive Antarctic navigation dashboard

### Planned Tech Stack
- **Frontend:** React + TypeScript
- **Backend:** Python + FastAPI
- **Machine Learning:** PyTorch + scikit-learn
- **Computer Vision:** OpenCV + YOLO
- **Geospatial Processing:** GeoPandas + Rasterio + xarray
- **Database:** PostgreSQL + PostGIS
- **Routing:** A* pathfinding
- **Visualization:** CesiumJS / MapLibre or Leaflet

## Repository Structure

```text
offshore/
├── frontend/                 # React dashboard
├── backend/                  # FastAPI services
├── ml/                       # AI/ML models
├── routing/                  # A* route planning
├── risk_engine/              # Risk scoring and maps
├── database/                 # Database schema
├── data/                     # Data documentation and samples
├── docs/                     # Architecture and project docs
└── docker/                   # Container configuration
```

## Project Flow

```text
Data Sources
    ↓
Data Processing
    ↓
Sea-Ice Forecasting + Iceberg Detection/Tracking
    ↓
Risk Engine
    ↓
Dynamic Risk Map
    ↓
Route Optimization
    ↓
Interactive Dashboard
```

> OFFSHORE is a decision-support system. It assists human navigation teams and does not autonomously control vessels.
