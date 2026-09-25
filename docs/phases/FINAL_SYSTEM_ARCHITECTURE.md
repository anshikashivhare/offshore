# FINAL SYSTEM ARCHITECTURE
**Project:** SIH 26059 - Antarctic Navigation

```text
User Request (React UI)
  ↓ [POST /api/v1/routes/plan via api.ts]
FastAPI Router (routes.py)
  ↓
RouteOrchestrator.execute_route_plan() (route_orchestrator.py)
  ↓
Data Providers (DEMO_MODE JSON or PostGIS)
  ↓
Sea-Ice ML (_prepare_forecast_context) + Iceberg ML (_prepare_iceberg_context)
  ↓
Risk / Navigability (Composite Risk Evaluator)
  ↓
4D A* (astar_planner.plan_route)
  ↓
RouteValidator (validator.validate_wkt_linestring)
  ↓
API Response (GeoJSON + Risk Metadata)
  ↓
Frontend (Home.tsx / OffshoreMap.tsx)
```
