# DB TEAM INTEGRATION CHECKLIST
**Project:** SIH 26059 (RC2 Development)

## Required Concrete Implementations
The ML/Routing team has decoupled the A* and ML layers from the database. We now strictly consume abstract providers. You must implement the following three classes inheriting from our ABCs located in `backend/app/services/providers/interfaces.py`.

### 1. PostGISIcebergProvider
- **Interface Method:** `get_candidate_icebergs(bounds: Dict[str, float]) -> List[Dict[str, Any]]`
- **Expected DB Action:** Run an `ST_Intersects` (or similar bounding box spatial query) against the iceberg observation table.
- **Rules:** Do NOT invoke ML or Monte Carlo. Just return the raw observational state, lat, lon, and timestamp. Return empty list if none found.

### 2. PostGISVesselProvider
- **Interface Method:** `get_vessel(vessel_id: str) -> Dict[str, Any]`
- **Expected DB Action:** Query vessel parameters by ID.
- **Rules:** MUST raise an explicit exception (e.g., ValueError) if the vessel does not exist in the database. Do not fallback to a default vessel.

### 3. PostGISPortProvider
- **Interface Method:** `get_port(port_id: str) -> Dict[str, Any]`
- **Expected DB Action:** Query port coordinates by ID.

## Handoff Rules
- Please place your concrete providers in `backend/app/services/providers/postgis.py` (or similar).
- Update the `RouteOrchestrator` dependency injection boundary to load your classes when `DEMO_MODE=False`.
