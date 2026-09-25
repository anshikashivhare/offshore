# DEMO READINESS MATRIX
**Project:** SIH 26059 - Antarctic Navigation

| Feature | Backend | Frontend | Evidence | Status | Known limitation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Startup Scripts** | `start_demo.sh` | React + Uvicorn | Command exits 0 if missing models | VERIFIED | Requires manual `Ctrl+C` to terminate. |
| **API Contract** | Orchestrator built (`POST /api/v1/routes/plan`) | `planRoute()` mapping | `verify_end_to_end.py` execution | VERIFIED | N/A |
| **Actual .pptx presentation** | N/A | N/A | `SIH_26059_Final_Presentation.pptx` exists | VERIFIED | Generated via `python-pptx`. |
| **ML Inference (Sea-Ice/Iceberg)** | XGBoost v002 + LSTM v002 Active | Displayed via metadata | Preflight check verifies weights on disk | VERIFIED | Synthetic training data limitation applies. |
| **Warning Propagation** | Fallback to `fastest` on missing DB | Inline warnings handled | Response yields HTTP 201 with `warnings[]` | VERIFIED | N/A |
| **Missing Risk Fallback** | `objective=safest` fails explicitly | Frontend catches 400 Bad Request | API Script yields HTTP 400 | VERIFIED | No silent zero-risk fallback exists. |
| **Production PostgreSQL/PostGIS** | PostgreSQL/PostGIS schemas exist | N/A | `brew`, `psql`, `docker` not found. | NOT VERIFIED | Local DB unavailable; Demo mode strictly enforced. |
| **Browser-level live verification** | React API calls | Maps render GeoJSON | `npm list playwright` failed | NOT VERIFIED | Automation tooling unsupported in this session. |
