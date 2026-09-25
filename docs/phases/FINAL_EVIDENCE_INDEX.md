# FINAL EVIDENCE INDEX
**Project:** SIH 26059

| Capability | Evidence file | Command / procedure | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **PPTX Generation** | `SIH_26059_Final_Presentation.pptx` | `python3 generate_ppt.py` | VERIFIED | Slide text fully respects scientific limitations. |
| **Browser Execution** | N/A | `npm list` (playwright not found) | NOT VERIFIED | Headless browser execution unavailable. |
| **PostgreSQL / PostGIS** | N/A | `which psql` (failed) | NOT VERIFIED | PostgreSQL/Docker missing from environment. |
| **DB-Backed Routing** | N/A | `DEMO_MODE=False` fails | NOT VERIFIED | DB offline forces DEMO_MODE fallback. |
| **DEMO_MODE** | `verify_end_to_end.py` | API Trace | VERIFIED | Deterministic synthetic grid array returned. |
| **ML Inference (LSTM)** | `preflight_demo.py` | Model Artifact Check | VERIFIED | `iceberg_lstm_v002.pt` is required for startup. |
| **A* + RouteValidator** | `verify_end_to_end.py` | 201 Created Response | VERIFIED | `land_avoidance_validated: True` returned. |
