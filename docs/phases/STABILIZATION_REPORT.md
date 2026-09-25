# OFFSHORE Prototype Stabilization Report
**Generated:** 2026-09-24  
**Project:** SIH 2026 PS-26059 Antarctic Navigation Decision Support System  
**Mode:** SYNTHETIC DATA PROTOTYPE

---

## Executive Summary

The OFFSHORE prototype is a multi-component AI-powered Antarctic navigation decision support system. Current analysis shows:

✅ **Strengths:**
- Comprehensive architecture with clear separation: Frontend (Vite+React) → Backend (FastAPI) → ML (PyTorch/XGBoost) → Database (PostgreSQL+PostGIS)
- Existing ML models trained on synthetic data (sea-ice XGBoost, iceberg trajectory XGBoost+LSTM, ConvLSTM)
- Working route planning services (A* and Dijkstra with 4D environmental constraints)
- Docker-compose orchestration with proper service dependencies
- Extensive synthetic data generation and seeding infrastructure

⚠️ **Critical Issues Identified:**

### 1. **Build Configuration Inconsistencies**
- **Docker context misalignment:** Backend Dockerfile expects `context: ./backend` but docker-compose now uses `context: .`
- **Frontend build artifacts:** Dockerfile copies `.next` but the build creates `dist` (Vite, not Next.js)
- **API URL configuration:** Frontend changed from relative `/api/v1` to `VITE_API_URL` but Docker env may not pass this through

### 2. **Data Flow Gaps**
- **Risk surface unavailable in demo mode:** `_build_risk_grid()` returns `{}` when `DEMO_MODE=True`, but routing still tries to compute risk-based costs
- **Forecast grid dependency:** A* planner calls `global_forecast_grid.prefetch_corridor()` which makes external API calls to Open-Meteo (not synthetic)
- **ML model loading:** Models pre-load at startup but fallback behavior unclear when weights missing
- **Database requirement:** Routes endpoint bypasses DB persistence in demo mode (commented out) but still requires DB connection for vessel/port lookups

### 3. **Integration Boundaries**
- **No end-to-end smoke test:** No evidence of a working Docker-compose → API → route planning → frontend flow
- **Mixed data sources:** Code uses synthetic ML models but real-time Open-Meteo API for 4D environmental conditions during routing
- **Hardcoded paths:** Synthetic data seeding script references `C:\Users\ASUS\Desktop\Synthetic data for offshore` (not portable)

---

## Current Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vite+React)                    │
│  - Home.tsx calls planRoute() via api.ts                         │
│  - Expects GeoJSON Feature with LineString geometry              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (/routes/plan)                │
│  1. Fetch vessel from DB or vessels.json fallback               │
│  2. Build risk_grid from RiskCell table (empty in demo mode)    │
│  3. Call AStarRoutePlanner.plan_route()                          │
│  4. Return RouteResponse GeoJSON                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    A* ROUTE PLANNER (astar.py)                   │
│  1. Snap origin/dest to water using land mask                    │
│  2. Prefetch corridor via global_forecast_grid (Open-Meteo API)  │
│  3. A* search with 4D cost (distance, time, risk, environment)   │
│  4. Reconstruct route with metrics (distance, ETA, fuel, risk)   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SUPPORTING SERVICES                           │
│  - GridBuilder: Land/water mask from coastline data             │
│  - CostCalculator: Edge costs from vessel speed, fuel, risk     │
│  - ForecastGrid: External API calls to Open-Meteo (NOT SYNTHETIC)│
│  - ML Models: seaice_xgb, iceberg_xgb, convlstm (SYNTHETIC)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Identified Problems by Subsystem

### **Frontend**
| Issue | Impact | Location |
|-------|--------|----------|
| API base URL changed to `VITE_API_URL` | Works in dev, may fail in Docker if env not passed | `frontend/src/lib/api.ts:1` |
| Dockerfile copies `.next` instead of `dist` | Build will fail, wrong artifact path | `frontend/Dockerfile:24` |
| npm install needs `--legacy-peer-deps` | Already fixed in uncommitted changes | `frontend/Dockerfile:5` |

### **Backend**
| Issue | Impact | Location |
|-------|--------|----------|
| Dockerfile context expects `./backend` but compose uses `.` | COPY paths break (app/, ml/, data/) | `docker-compose.yml:43-44` |
| Risk grid returns empty dict in demo mode | Routes computed without risk awareness | `backend/app/api/v1/endpoints/routes.py:40-42` |
| DB persistence commented out in `/routes/plan` | Routes not saved, can't retrieve by ID | `backend/app/api/v1/endpoints/routes.py:166-168` |
| Vessel fallback reads `vessels.json` with hardcoded path | Fragile, may fail in Docker | `backend/app/api/v1/endpoints/routes.py:112` |

### **ML & Routing**
| Issue | Impact | Location |
|-------|--------|----------|
| `ForecastGrid` calls Open-Meteo API (external, not synthetic) | Routes depend on real-time weather, not demo data | `backend/app/services/environment/forecast_grid.py:85-86` |
| A* heuristic weight 8.0 in demo mode vs 1.05 in prod | Aggressive goal-seeking may skip risk zones | `backend/app/services/routing/astar.py:173` |
| Missing risk assigned 0.5 in demo, 0.0 in prod (safety-first fails) | Inconsistent safety behavior | `backend/app/services/routing/astar.py:213-217` |

### **Data & Database**
| Issue | Impact | Location |
|-------|--------|----------|
| Synthetic data seed script uses Windows absolute path | Not portable to Docker/Linux | `scripts/data_ingestion/seed_synthetic_data.py:30` |
| No pre-seeded database in Docker volumes | Fresh docker-compose has empty DB | N/A |
| `backend/data/` only has ports.json and vessels.json | Missing synthetic RiskCell, Iceberg, Observation data | `backend/data/` |

---

## Stabilization Priorities

### **Phase 1: Fix Docker Build (Immediate)**
1. ✅ Align Dockerfile COPY paths with docker-compose context
2. ✅ Fix frontend Dockerfile to copy `dist` instead of `.next`
3. ✅ Pass `VITE_API_URL` environment variable to frontend container
4. ✅ Test `docker-compose up --build` succeeds for all services

### **Phase 2: Demo Mode Consistency (High Priority)**
1. Create a synthetic ForecastGrid that returns pre-generated conditions (no external API)
2. Pre-generate a synthetic risk_grid as a JSON file in `backend/data/`
3. Update `_build_risk_grid()` to load synthetic data in demo mode instead of returning `{}`
4. Validate that routes are computed with actual (synthetic) risk and environment data

### **Phase 3: End-to-End Smoke Test (High Priority)**
1. Start docker-compose stack
2. Load frontend at `http://localhost:3000`
3. Select origin (e.g., Rothera -68.13, -67.57) and destination (e.g., Casey -66.28, 110.53)
4. Select a vessel and click "Calculate Route"
5. Verify:
   - Route geometry is a valid water-only LineString
   - Distance, ETA, fuel, risk_score are non-zero and plausible
   - No hardcoded straight lines or fallback geometry
   - Map displays the route correctly

### **Phase 4: Data Integrity (Medium Priority)**
1. Package minimal synthetic dataset (vessels, ports, risk_cells, icebergs) as SQL dump or JSON
2. Create database initialization script that runs on first startup
3. Document data provenance: what is synthetic, what sources were used for training
4. Remove external API dependency from routing (Open-Meteo) or clearly document it as non-synthetic

### **Phase 5: Verification & Documentation (Medium Priority)**
1. Add `/api/v1/health/ready` endpoint that checks DB connectivity, ML model loading
2. Document the "golden path" flow: frontend → plan route → A* → response
3. Create troubleshooting guide for common failure modes
4. Add integration test script that validates the entire stack without manual UI interaction

---

## Recommendations

### **Do Not:**
- ❌ Delete or regenerate existing ML model weights (`ml/models/weights/*.pt`, `*.json`)
- ❌ Delete existing synthetic datasets or training artifacts
- ❌ Replace synthetic data with real-world data in this prototype phase
- ❌ Remove database tables or change schemas without migration

### **Do:**
- ✅ Make docker-compose the primary deployment method (document local dev as secondary)
- ✅ Create a `.env.docker` or document required environment variables clearly
- ✅ Add a `make test-integration` or similar command that validates the full stack
- ✅ Keep demo mode and production mode clearly separated with feature flags
- ✅ Log data provenance in API responses (e.g., `"data_source": "SYNTHETIC_PROTOTYPE"`)

---

## Next Steps

**Immediate Actions (Today):**
1. Fix Docker build configuration issues (Phase 1)
2. Test that `docker-compose up` successfully starts all services
3. Commit these fixes with clear commit message

**This Week:**
1. Implement synthetic ForecastGrid (Phase 2)
2. Run end-to-end smoke test (Phase 3)
3. Document any gaps found during testing

**Before Presentation:**
1. Ensure 3+ representative routes can be planned successfully
2. Verify all frontend features display correctly (icebergs, risk cells, alerts)
3. Prepare demo script with fallback plan if live demo fails

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Docker build fails due to path issues | High | High | Fix immediately (Phase 1) |
| Routes generated but are straight lines (no real pathfinding) | Medium | High | Test with Antarctica coastline routing |
| External API (Open-Meteo) fails during demo | Medium | High | Implement synthetic forecast fallback |
| Database empty on fresh start | High | Medium | Add init script or seed on startup |
| Frontend can't reach backend in Docker | Medium | High | Fix CORS and API_URL configuration |

---

## Conclusion

The OFFSHORE prototype has a **solid foundation** but requires **immediate stabilization** to ensure reliable end-to-end operation. The core ML models and routing algorithms exist, but the integration layer has configuration inconsistencies and mixed data sources (synthetic models + real-time weather API).

**Estimated effort to stabilize:** 1-2 days of focused work.

**Recommended approach:** Fix Docker builds first, then methodically test and fix each integration point, maintaining the "synthetic data only" constraint throughout.
