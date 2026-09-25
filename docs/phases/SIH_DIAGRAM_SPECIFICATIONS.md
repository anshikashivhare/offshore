# SIH DIAGRAM SPECIFICATIONS
**Project:** SIH 26059

*These specifications are designed for importing into Mermaid.js or standard charting software.*

## 1. High-Level Architecture
```mermaid
flowchart TD
    UI[React Interface] -->|POST GeoJSON Request| API[FastAPI Orchestrator]
    API -->|Live Data Request| Environment[Sea-Ice XGBoost & Iceberg LSTM]
    Environment -->|Predicted Hazards| Risk[Risk Engine max()]
    Risk -->|Penalized Grid| Routing[4D Time-Aware A*]
    Routing -->|GeoJSON LineString| Validator[RouteValidator]
    Validator -->|Validated Route + Warnings| UI
```

## 2. Iceberg Prediction to CPA
```mermaid
flowchart LR
    Data[Iceberg Kinematics] --> Model[LSTM v002]
    Model -->|Wrapped Delta Lon/Lat| Future[T+3h Prediction]
    Future --> CPA[Geodesic Distance]
    CPA -->|Encounter Index| AStar[A* Cost Penalty]
```

## 3. Safest Fallback Sequence
```mermaid
sequenceDiagram
    participant User
    participant API
    participant RiskData
    
    User->>API: Route Request (Safest)
    API->>RiskData: Query DB
    RiskData-->>API: Unavailable (Offline)
    API-->>User: 400 Bad Request (Fail Closed)
```
