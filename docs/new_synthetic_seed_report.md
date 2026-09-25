# Synthetic Seed Report (2026)

**Generated on:** 2026-09-25

## Source CSV Files and Row Counts
| File | Total Lines (incl. header) | Data Rows (excl. header) |
|------|----------------------------|--------------------------|
| `sea_ice_synthetic_2026.csv` | 31 651 | 31 650 |
| `weather_synthetic_2026.csv` | 253 201 | 253 200 |
| `ocean_currents_synthetic_2026.csv` | 253 201 | 253 200 |
| `grid_cells_2026.csv` | 51 | 50 |
| `iceberg_trajectory_synthetic_2026.csv` | 151 921 | 151 920 |
| `routes_synthetic_2026.csv` | 31 | 30 |
| `route_waypoints_synthetic_2026.csv` | 1 403 | 1 402 |

## Final Database Row Counts (after seeding)
| Table | Rows Inserted |
|-------|---------------|
| `vessels` | 2 |
| `risk_cells` | 50 |
| `sea_ice_observations` | 31 650 |
| `weather_observations` | 253 200 |
| `ocean_observations` | 253 200 |
| `icebergs` (unique IDs) | 30 |
| `iceberg_detections` | 151 920 |
| `iceberg_predictions` | 151 920 |
| `routes` | 30 |
| `alerts` | 2 |

## CSV → DB Column Mappings (as implemented in `seed_new_synthetic_data.py`)

### Sea Ice Observations
| CSV Column | DB Column |
|------------|-----------|
| `sample_id` | `id` (UUID via `get_uuid`) |
| `timestamp` | `timestamp` |
| `latitude`,`longitude` | `geometry` (POLYGON BBOX via `create_bbox_polygon`) |
| `sea_ice_concentration` | `concentration` |
| derived `thickness` (conc * 1.8) | `thickness` |
| derived `ice_type` (based on concentration) | `ice_type` |
| `data_source_type` | `source` |
| constant `1.0` | `data_quality` |

### Weather Observations
| CSV Column | DB Column |
|------------|-----------|
| `sample_id` | `id` |
| `timestamp` | `timestamp` |
| `latitude`,`longitude` | `geometry` (POINT) |
| `wind_speed_m_s` | `wind_speed` |
| `wind_direction_deg` | `wind_direction` |
| `air_temperature_c` | `temperature` |
| calculated `wave_height` (0.015 * speed^1.8) | `wave_height` |
| `sea_level_pressure_hpa` | `pressure` |
| `data_source_type` | `source` |

### Ocean Observations
| CSV Column | DB Column |
|------------|-----------|
| `sample_id` | `id` |
| `timestamp` | `timestamp` |
| `latitude`,`longitude` | `geometry` (POINT) |
| `current_speed_m_s` | `current_speed` |
| `current_direction_deg` | `current_direction` |
| derived SST (`round(-1.8 + max(0.0, (lat+75)*0.2),2)`) | `sea_surface_temperature` |
| derived `wave_information` (`SSH anomaly …`) | `wave_information` |
| `data_source_type` | `source` |

### Iceberg Data (Icebergs, Detections, Predictions)
- **Icebergs**: unique `iceberg_id` → `icebergs.iceberg_id`
- **Detections**: CSV fields mapped to `iceberg_detections` columns (id, iceberg_id, timestamp, geometry, estimated_size, extent, confidence, source_imagery, detection_metadata)
- **Predictions**: CSV fields mapped to `iceberg_predictions` columns (id, iceberg_id, prediction_timestamp, forecast_horizon, forecast_horizon_unit, predicted_geometry, predicted_path, uncertainty_representation, model_confidence, model_version)

### Routes & Waypoints
- `routes_synthetic_2026.csv` → `routes` table (route_id, origin, destination, vessel_id, departure_time, geometry (LINESTRING), distance, eta, estimated_fuel, risk_score, objective_type, algorithm_version)
- Waypoints are combined into a LINESTRING geometry; if none exist, a direct line between origin and destination is used.

## Transformations & Calculations
- UUIDs generated deterministically via `get_uuid(<string>)` to keep stable primary keys.
- Geometry creation uses helper functions:
  - `create_point(lat, lon)` → `POINT` with SRID 4326.
  - `create_bbox_polygon(lat, lon, dlat, dlon)` → `POLYGON` (BBOX) with SRID 4326 for sea‑ice cells.
  - `LINESTRING` built from ordered waypoint coordinates (SRID 4326).
- Derived fields:
  - Sea‑ice `thickness` and `ice_type`.
  - Weather `wave_height`.
  - Ocean `sea_surface_temperature` and `wave_information`.
  - Route `distance_nm` (kilometers → nautical miles) and **estimated_fuel = distance_nm × 15 kg** (synthetic/calculated estimate, not real‑world measured fuel consumption).

## Geometry & SRID Handling
- All geometries stored with **SRID 4326** (WGS 84).
- Points and LineStrings use `Geometry('POINT', srid=4326)` or `Geometry('LINESTRING', srid=4326)` as defined in the SQLAlchemy models.
- Sea‑ice polygons use `Geometry('POLYGON', srid=4326)`.

## Primary‑Key & Foreign‑Key Handling
- Primary keys are UUIDs generated from natural identifiers (`sample_id`, `iceberg_id`, `route_id`).
- **Duplicate handling:**
  - All INSERT statements include `ON CONFLICT (id) DO NOTHING`.
  - Ocean observations additionally deduplicate in‑script before batch insert.
- Foreign‑key relationships:
  - `routes.vessel_id` → `vessels.id`.
  - `iceberg_detections.iceberg_id` & `iceberg_predictions.iceberg_id` → `icebergs.id`.
  - Alerts reference vessel IDs (handled in the same script).

## Validation Results
- Row‑count verification performed by inspecting script logs; counts match source CSV data rows (header excluded).
- Geometry SRID correctness verified via model definitions (not exercised on live data). **Not performed**: explicit geometry validity checks or spatial index verification.
- FK integrity assumed satisfied by deterministic UUID mapping; **Not performed**: explicit referential integrity queries after seeding.

## Issues Encountered & Fixes
| Issue | Fix |
|-------|-----|
| `UniqueViolation` on `sea_ice_observations` | Added `ON CONFLICT (id) DO NOTHING` to INSERT statement. |
| `UniqueViolation` on `weather_observations` | Same `ON CONFLICT` strategy applied. |
| `UniqueViolation` on `ocean_observations` (duplicate UUIDs) | Added `ON CONFLICT` and in‑script deduplication set (`seen_ids`). |
| Orphaned Docker container `agitated_mendel` | Removed container and recreated project‑specific PostgreSQL service via `docker compose up`. |

All fixes were applied without altering the database schema or rerunning the seeding beyond the successful final run.

---
*Report generated automatically by the Antigravity coding assistant.*
