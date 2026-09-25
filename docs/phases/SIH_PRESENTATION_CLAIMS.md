# SIH PRESENTATION CLAIMS REGISTER
**Project:** SIH 26059

| Slide | Claim | Evidence | Evidence Type | Safe Wording | Limitation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Slide 6 (Iceberg ML)** | LSTM v002 accurately predicts trajectories | Held-out 4-iceberg test set (0.27km MHE) | Model Test | "Our LSTM model achieved a Mean Haversine Error of 0.27 km on a strictly held-out test set." | Limited to T+3h horizon. |
| **Slide 7 (Risk)** | Iceberg predictions penalize routes | End-to-End Orchestrator testing (`verify_end_to_end.py`) | Integration Test | "Predicted trajectories are converted into encounter-risk indices which dynamically penalize A* edge costs." | Synthetic data used. |
| **Slide 8 (Routing)** | The system prevents dangerous routing | API Safest-fallback returns 400 Bad Request | End-to-End Test | "The architecture fails closed, actively blocking routes when critical safety data is unavailable." | Not a guarantee of absolute safety when data *is* available. |
| **Slide 11 (Limitations)** | The system requires operational data | Data Provenance Audit (Phase 28) | Code Audit | "The system currently operates on synthetic training models." | Real-world telemetry required for production deployment. |
