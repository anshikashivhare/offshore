# Antarctic Navigation API — Reference

Base URL (local dev): `http://127.0.0.1:8000`

Interactive Swagger docs are auto-generated at `/docs` once the server is running.

---

## `GET /health`

Basic liveness check.

**Response**
```json
{"status": "ok"}
```

---

## `POST /routes/optimize`

Finds the safest, most fuel-efficient path between two grid cells, avoiding dense sea ice. Uses A* pathfinding over a cost grid built from stored sea-ice concentration data.

**Request body**
| Field | Type | Required | Description |
|---|---|---|---|
| `start_row` | int | yes | Start cell row index in the ice grid |
| `start_col` | int | yes | Start cell col index in the ice grid |
| `end_row` | int | yes | End cell row index in the ice grid |
| `end_col` | int | yes | End cell col index in the ice grid |
| `origin_lat` | float | no (default -65.0) | Latitude of grid cell (0,0) |
| `origin_lon` | float | no (default -60.0) | Longitude of grid cell (0,0) |
| `cell_size_deg` | float | no (default 0.1) | Degrees per grid cell |

**Example request**
```json
{"start_row": 0, "start_col": 0, "end_row": 19, "end_col": 19}
```

**Example response**
```json
{
  "status": "ok",
  "total_cost": 62.72,
  "path": [
    {"lat": -65.0, "lon": -60.0},
    {"lat": -65.1, "lon": -59.9},
    "...",
    {"lat": -66.9, "lon": -58.1}
  ],
  "reason": null
}
```

**Possible `status` values**
- `"ok"` — path found, `path` and `total_cost` populated
- `"no_path_found"` — no passable route exists, or start/end is impassable; check `reason`

**Errors**
- `400` — a row/col index is out of grid bounds

---

## `GET /seaice/forecast`

Predicts sea-ice concentration for a given cell and date. Automatically pulls the last 3 days of observations from the database to build lag features — no need to pass historical values manually.

**Query params**
| Param | Type | Required | Description |
|---|---|---|---|
| `lat` | float | yes | Target cell latitude |
| `lon` | float | yes | Target cell longitude |
| `date` | string | yes | Forecast target date, `YYYY-MM-DD` |

**Example request**
```
GET /seaice/forecast?lat=-65.0&lon=-60.0&date=2025-05-10
```

**Example response**
```json
{
  "lat": -65.0,
  "lon": -60.0,
  "date": "2025-05-10",
  "predicted_concentration": 0.4914,
  "based_on_lags": [0.41, 0.38, 0.42]
}
```

**Errors**
- `404` — fewer than 3 historical observations found for that cell before the target date. Load more data via `scripts/load_sample_seaice.py` (or the real NSIDC/Copernicus loader) first.

**Notes**
- `lat`/`lon` currently require an exact match to a stored grid cell. For real satellite data with floating-point coordinates, this should be changed to a nearest-cell/tolerance match (see backend notes).

---

## `GET /iceberg/trajectory`

Projects an iceberg's position forward several steps, using its most recent tracked position plus the nearest matching ocean current / wind data.

**Query params**
| Param | Type | Required | Description |
|---|---|---|---|
| `iceberg_id` | string | yes | ID of the iceberg to track |
| `num_steps` | int | no (default 5) | How many steps ahead to project |

**Example request**
```
GET /iceberg/trajectory?iceberg_id=berg-001&num_steps=5
```

**Example response**
```json
{
  "iceberg_id": "berg-001",
  "as_of": "2025-05-10",
  "environmental_source": {"lat": -65.0, "lon": -60.0},
  "projected_path": [
    {"lat": -65.03, "lon": -59.98},
    {"lat": -65.0325, "lon": -59.97269},
    "...",
    {"lat": -65.04248, "lon": -59.94344}
  ]
}
```

**Errors**
- `404` — no tracked position found for the given `iceberg_id`, or no environmental data available for that date.

---

## `GET /dashboard/summary`

Combines route optimization, sea-ice forecast, and one or more iceberg trajectories into a single response — the recommended endpoint for the main dashboard view, so the frontend doesn't need to make three separate calls.

**Query params**
| Param | Type | Required | Description |
|---|---|---|---|
| `start_row`, `start_col`, `end_row`, `end_col` | int | yes | Route start/end grid cells |
| `forecast_lat`, `forecast_lon` | float | yes | Cell to forecast sea-ice for |
| `forecast_date` | string | yes | `YYYY-MM-DD` |
| `iceberg_ids` | string | no | Comma-separated iceberg IDs, e.g. `berg-001,berg-002` |

**Example request**
```
GET /dashboard/summary?start_row=0&start_col=0&end_row=19&end_col=19&forecast_lat=-65.0&forecast_lon=-60.0&forecast_date=2025-05-10&iceberg_ids=berg-001,berg-999
```

**Example response**
```json
{
  "route": {
    "status": "ok",
    "total_cost": 62.72,
    "path": ["..."]
  },
  "seaice_forecast": {
    "predicted_concentration": 0.4914
  },
  "iceberg_trajectories": [
    {
      "iceberg_id": "berg-001",
      "projected_path": ["..."]
    },
    {
      "iceberg_id": "berg-999",
      "error": "not found"
    }
  ]
}
```

**Error handling behavior**
Each section (`route`, `seaice_forecast`, each entry in `iceberg_trajectories`) fails independently — one section erroring (e.g. an unknown iceberg ID) does not prevent the other sections from returning valid data. Check each section for an `"error"` key rather than relying on the overall HTTP status code.

---

## Data status (as of this doc)

| Model | Data source | Status |
|---|---|---|
| Route optimizer | Sea-ice observations table (PostGIS) | Synthetic sample data loaded; real NSIDC/Copernicus loader available (`ml/seaice_model/real_data_loader.py`) but not yet run against live data |
| Sea-ice forecast | XGBoost, trained on lag features | Baseline trained on synthetic data; can retrain on real NetCDF via `python -m ml.seaice_model.train path/to/file.nc` |
| Iceberg trajectory | XGBoost multi-output, trained on synthetic drift data | Baseline only; real ERA5 wind/current integration not yet built |

## Known limitations to flag in the demo
- Exact lat/lon matching (not tolerance-based) in `/seaice/forecast` — fine for the sample grid, will need a tolerance match for real-resolution data.
- Nearest-environmental-cell lookup in `/iceberg/trajectory` does a full table scan — fine at hackathon scale, would need a spatial index (`ST_Distance` + PostGIS index) at full Antarctic resolution.
- `/iceberg/trajectory` holds current/wind constant across all projected steps rather than looking up per-step forecasts — a reasonable simplification for a 5-step projection, worth mentioning if judges ask about accuracy over longer horizons.
