# SIH DEMO RUNBOOK
**Project:** SIH 26059 - Antarctic Navigation

## 1. Prerequisites
- Python 3.9+ with initialized backend `.venv`
- Node.js 18+ with frontend `node_modules` installed

## 2. Startup Command
```bash
./scripts/start_demo.sh
```
- **Backend URL:** http://localhost:8000
- **Frontend URL:** http://localhost:5173
- **DEMO_MODE:** Active by default (PostGIS disconnected)

## 3. Canonical Demo Scenario
1. **Origin:** `-60.0, 50.0`
2. **Destination:** `-60.0, 52.0`
3. **Vessel:** `123e4567-e89b-12d3-a456-426614174001` (Research Icebreaker PC1)
4. **Objective:** `Fastest`
5. **Expected Outcome:** The backend will successfully route the vessel using synthetic environmental grids. It will attach warnings noting that the DB is offline.
6. **Risk Fallback:** If Objective is changed to `Safest`, the backend explicitly blocks the route with a 400 Error `INSUFFICIENT_RISK_DATA`, proving the No-Silent-Zero-Risk architecture.

## 4. Reset & Recovery
- **Stale State:** Refresh the browser. `Home.tsx` drops stale coordinates on refresh.
- **Service Crash:** Press `Ctrl+C` in the terminal to terminate the `start_demo.sh` orchestrator. Rerun the script.
- **Troubleshooting:** 
  - If map doesn't load: Check Mapbox/Deck.gl API tokens.
  - If backend 500s: Check `preflight_demo.py` output for missing LSTM/XGBoost models.
