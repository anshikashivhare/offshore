# OFFSHORE

## AI-Powered Antarctic Maritime Navigation Decision Support System

OFFSHORE is an AI-powered decision support platform designed to help vessels navigate Antarctic waters more safely and efficiently. The system combines sea-ice data, iceberg information, weather and ocean conditions to predict maritime hazards, generate dynamic risk maps, and recommend optimized vessel routes.

### Core Features
- Sea-ice concentration forecasting (XGBoost + ConvLSTM)
- Iceberg detection, tracking and trajectory prediction
- Dynamic maritime risk maps
- A* and Dijkstra route optimization
- Safest, fastest and fuel-efficient route options
- Real-time navigational alerts
- Interactive Antarctic navigation dashboard

### Tech Stack
- **Frontend:** Next.js + TypeScript + TailwindCSS
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL + PostGIS
- **ML:** PyTorch + XGBoost + scikit-learn
- **Task Queue:** Celery + Redis
- **Infrastructure:** Docker + Docker Compose

## Repository Structure

```text
offshore/
│
├── frontend/                       # 1. FRONTEND — Next.js Dashboard
│   └── src/
│       ├── app/                    # Pages & layouts
│       ├── components/map/         # Map layers (iceberg, sea-ice, route, currents)
│       ├── lib/                    # Routing algorithms, data, types
│       └── stores/                 # Zustand state management
│
├── backend/
│   ├── app/                        # 2. API — FastAPI Application
│   │   ├── api/v1/                 # Versioned REST endpoints
│   │   ├── core/                   # Config, logging, security
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/               # Business logic (routing, risk, alerts, forecasting, icebergs)
│   │   ├── utils/                  # GeoJSON, geometry helpers
│   │   └── worker/                 # Celery async tasks
│   │
│   │   ├── db/                     # 3. DATABASE — Connection & session
│   │   ├── models/                 # SQLAlchemy ORM models (PostGIS)
│   │   ├── repositories/           # Data access layer
│   │   └── ingestion/              # Data pipeline adapters
│   │
│   ├── ml/                         # 4. ML BACKEND — Standalone Models
│   │   ├── seaice_model/           # Sea-ice forecasting (XGBoost + ConvLSTM)
│   │   ├── trajectory_model/       # Iceberg trajectory (XGBoost + LSTM)
│   │   └── route_optimizer/        # A* grid route optimizer
│   │

│   └── tests/                      # Test suite
│
├── DOCUMENTATION.md                # Single consolidated project doc
├── docker-compose.yml              # Production Docker config
├── Dockerfile

```

## Quick Start

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend (ML training)
cd backend
python -m ml.seaice_model.train
python -m ml.trajectory_model.train

# Full stack (Docker)
docker-compose up --build
```

> OFFSHORE is a decision-support system. It assists human navigation teams and does not autonomously control vessels.
