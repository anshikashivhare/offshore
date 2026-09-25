# SIH 26059: ARCHITECTURE & DATA FLOW
**Antarctic Navigation Decision Support System**

## 1. High-Level Data Flow Diagram (DFD)

```mermaid
flowchart TD
    User([User / Navigator]) -->|Selects Origin, Dest, Vessel| ReactUI(Frontend - React)
    
    subgraph Frontend
        ReactUI
        DeckGL(Mapbox / Deck.gl)
    end
    
    ReactUI -->|POST /api/v1/routes/plan| API(FastAPI Orchestrator)
    
    subgraph Backend
        API --> DB[(PostgreSQL / PostGIS)]
        API --> Orchestrator(RouteOrchestrator)
        
        Orchestrator -->|Fetch Vessel| Repo(VesselRepository)
        Orchestrator -->|Request Context| SeaIce[Sea-Ice XGBoost v002]
        Orchestrator -->|Request Context| Iceberg[Iceberg LSTM v002]
        Orchestrator -->|Request Context| Weather(Open-Meteo API)
        
        SeaIce --> Risk[Composite Risk Engine]
        Iceberg --> Risk
        Weather --> Risk
        
        Risk -->|Heuristic Penalty| AStar[4D A* Pathfinding]
        Repo -->|Vessel Draft/Speed| AStar
        
        AStar -->|Candidate Route| Validator(RouteValidator)
    end
    
    Validator -->|GeoJSON Feature| ReactUI
    ReactUI -->|Render LineString| DeckGL
```

## 2. Risk Aggregation Architecture

```mermaid
flowchart LR
    A[Iceberg LSTM Prediction] -->|Mean Haversine Error| B[CPA Geodesic Calc]
    B --> C[Iceberg Encounter Risk Index]
    
    D[Sea-Ice XGBoost Prediction] --> E[Sea-Ice Concentration Risk]
    
    C --> F{Max() Aggregation}
    E --> F
    
    F -->|Effective Spatial Risk| G[A* Edge Cost Function]
```

## 3. Fallback / Failure Sequence (UML)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as React Frontend
    participant API as FastAPI Orchestrator
    participant DB as PostGIS / DB
    
    U->>UI: Click "Calculate Route (Safest)"
    UI->>API: POST JSON Request
    API->>DB: Query Risk Data
    alt DB is Offline
        DB-->>API: Connection Refused
        API->>API: trigger DEMO_MODE fallback
        API->>API: Detect 'Safest' Objective
        API-->>UI: 400 Bad Request (INSUFFICIENT_RISK_DATA)
        UI-->>U: Render Warning Panel (No Silent 0-Risk Route)
    else DB is Online
        DB-->>API: Yield Valid Context
        API->>API: Execute A*
        API-->>UI: 201 Created (GeoJSON)
        UI-->>U: Render Validated Route
    end
```
