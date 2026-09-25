# FINAL CLAIMS REGISTER
**Project:** SIH 26059 - Antarctic Navigation

| Claim | Evidence | Evidence Type | Status | Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **Iceberg LSTM v002 predicts unseen trajectories better than baselines** | `verify_lstm_test_set.py` metrics (MAE 0.27km) | MODEL TEST VERIFIED | VERIFIED | Evaluated only up to T+3h horizon. |
| **LSTM prediction alters A* route costs dynamically** | `verify_end_to_end.py` executing `planRoute` | INTEGRATION TEST VERIFIED | VERIFIED | N/A |
| **The system is scientifically validated for operational navigation** | None | N/A | NOT VERIFIED | Models utilize synthetic training data. |
| **Composite risk aggregation prevents silent failure** | Missing DB yields 400 Error on `Safest` | INTEGRATION TEST VERIFIED | VERIFIED | Max() is deterministic, not statistical probability. |
| **Frontend displays actual A* route** | `api.ts` maps GeoJSON exactly | CODE VERIFIED | PARTIALLY VERIFIED | Browser automation offline. |
| **Production PostGIS infrastructure persists models** | `astar.py` uses SQLAlchemy queries | CODE VERIFIED | NOT VERIFIED | Local PostGIS database offline. |
