# OFFSHORE Architecture

## High-Level Flow

```text
Satellite / Sea-Ice Data     Weather Data     Ocean Data     Vessel Data
            \                    |               |              /
             \                   |               |             /
                        Data Processing
                               |
        +----------------------+----------------------+
        |                      |                      |
 Sea-Ice Forecasting    Iceberg Detection      Trajectory Prediction
        |                      |                      |
        +----------------------+----------------------+
                               |
                           Risk Engine
                               |
                         Dynamic Risk Map
                               |
                          A* Route Planner
                               |
                 +-------------+-------------+
                 |             |             |
             Safest        Fastest     Fuel-Efficient
                               |
                         React Dashboard
```

## Responsibility Boundaries

- **Data layer:** collects and normalizes environmental and vessel data.
- **ML layer:** produces forecasts and predictions.
- **Risk engine:** converts environmental information into navigation costs.
- **Routing layer:** finds optimized paths through the risk map.
- **Backend:** exposes all functionality through APIs.
- **Frontend:** presents maps, predictions, routes and decision metrics.
