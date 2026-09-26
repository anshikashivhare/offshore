# FINAL DEMO RUNBOOK
**SIH 26059 - Antarctic Navigation Risk System**

## 1. Startup Instructions

### Start Database
Ensure Docker is running, then execute:
```bash
cd database
docker-compose up -d
```

### Start Backend
In a new terminal window, activate the Python environment and run the server:
```bash
cd backend
source venv_mac/bin/activate
export PYTHONPATH=$(pwd)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start Frontend
In another terminal window, start the React application:
```bash
cd frontend
npm run dev
```

## 2. Accessing the Prototype
Open your web browser and navigate to:
**http://localhost:3000** (or the port specified by Vite/Next.js)

## 3. Demo Scenarios

### Scenario A: Fastest Route (Global)
1. **Origin:** `-75.0, -65.0` (or select from ports)
2. **Destination:** `-70.0, -65.0` (or select from ports)
3. **Vessel:** Select any standard Icebreaker (e.g., `8d56cc55-5f45-58ad-b758-6d68f1c48ec3`)
4. **Objective:** `Fastest`
5. **Action:** Click "Calculate Route"
6. **Expected Outcome:** A globally valid A* route drawn on the map with `0` land intersections, optimized purely for minimum transit time.

### Scenario B: Fuel-Efficient Route (Global)
1. **Origin:** Same as Scenario A
2. **Destination:** Same as Scenario A
3. **Vessel:** Same as Scenario A
4. **Objective:** `Fuel Efficient`
5. **Action:** Click "Calculate Route"
6. **Expected Outcome:** The route generation utilizes the 4D CostCalculator, steering around severe wind/wave weather systems to minimize fuel consumption (metrics will show reduced fuel compared to Fastest).

### Scenario C: Safest Route (Risk-Covered Corridor)
1. **Origin:** `-64.0, -69.0` (Must be within a seeded ML risk cell)
2. **Destination:** `-60.0, -67.5`
3. **Vessel:** Same as Scenario A
4. **Objective:** `Safest`
5. **Action:** Click "Calculate Route"
6. **Expected Outcome:** The system extracts actual Iceberg/Sea-Ice risk metrics from the database polygon bounding box, routing the vessel through the path of lowest possible hazard.

### Scenario D: Fail-Closed Safety (Risk-Uncovered Corridor)
1. **Origin:** `-75.0, -65.0`
2. **Destination:** `-70.0, -65.0`
3. **Objective:** `Safest`
4. **Action:** Click "Calculate Route"
5. **Expected Outcome:** Immediate `HTTP 400` failure due to `INSUFFICIENT_RISK_DATA`. The map does not render a fake/mock geometry line. This validates the strict safety policy.

### Scenario E: Invalid Endpoint (Landmass)
1. **Origin:** `-65.0, -75.0`
2. **Destination:** `0.0, -90.0` (South Pole Land)
3. **Action:** Click "Calculate Route"
4. **Expected Outcome:** `HTTP 400 Bad Request`. The routing engine safely rejects the point during `snap_to_water` validation, rather than hanging or returning HTTP 500.

## 4. Troubleshooting
- **Database Unavailable:** Run `docker-compose ps` to verify Postgres. Ensure `ports.json` was properly seeded into the PostGIS `ports` table using the backend script.
- **Missing Risk Data:** The ML forecast cells seeded in the demo DB are sparse. If `Safest` objective fails, ensure you are routing within `(-65.2 to -58.0 Lon, -69.3 to -66.9 Lat)` or another seeded bounding box.
- **DEMO_MODE:** The application uses real database models and live open-meteo APIs. If an external API is down, DEMO_MODE fallback data will only be utilized if explicitly toggled in configuration.
