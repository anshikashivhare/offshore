# ML/ROUTING PROVIDER CONTRACTS
**Project:** SIH 26059

## Objective
The A* pathfinder and the ML/Risk engines must remain completely database-ignorant. They process data delivered strictly via these interfaces.

## 1. IcebergProvider
- **Purpose:** Supplies raw, recent observational data for icebergs within a bounding box.
- **Inputs:** `bounds` (Dict with min_lat, min_lon, max_lat, max_lon).
- **Outputs:** List of dictionaries containing `iceberg_id`, `lat`, `lon`, `timestamp`, `source`.
- **Coordinate Convention:** Lat/Lon tuples.

## 2. VesselProvider
- **Purpose:** Supplies vessel parameters.
- **Inputs:** `vessel_id` (str).
- **Outputs:** Dictionary containing `vessel_id`, `max_speed_knots`, `draft_m`, `source`.
- **Errors:** Must raise an exception if `vessel_id` is invalid.

## 3. PortProvider
- **Purpose:** Supplies port coordinate data.
- **Inputs:** `port_id` (str).
- **Outputs:** Dictionary containing `port_id`, `name`, `lat`, `lon`, `source`.
