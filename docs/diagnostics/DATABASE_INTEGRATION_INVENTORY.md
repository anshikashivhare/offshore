# Database Integration Inventory

## 1. PostgreSQL/PostGIS Database

The main database supplied is available in `database/offshore_db.dump`.
It was restored into the `offshore_qa_db` container running PostgreSQL 15.8 with PostGIS 3.4.

### 1.1 Tables and Schemas

#### **Table:** `vessels`
- **Columns:** `vessel_id` (uuid, PK), `vessel_name` (varchar), `vessel_type` (varchar), `cruising_speed` (float, knots), `fuel_consumption` (float), `ice_capability` (varchar), `operational_limits` (json).
- **Indexes:** BTree on `vessel_id`, BTree on `vessel_name`.
- **Purpose:** Stores vessel definitions.

#### **Table:** `routes`
- **Columns:** `route_id` (uuid, PK), `origin` (varchar), `destination` (varchar), `vessel_id` (uuid, FK to `vessels`), `departure_time` (timestamptz), `geometry` (LineString, 4326), `distance` (float), `eta` (timestamptz), `estimated_fuel` (float), `risk_score` (float), `objective_type` (enum), `algorithm_version` (varchar).
- **Indexes:** GiST on `geometry`, BTree on `vessel_id`.
- **Purpose:** Stores generated and validated routes.

#### **Table:** `risk_cells`
- **Columns:** `id` (uuid, PK), `geometry` (Polygon, 4326), `timestamp` (timestamptz), `ice_risk` (float), `iceberg_risk` (float), `weather_risk` (float), `current_risk` (float), `composite_risk` (float), `risk_category` (varchar), `confidence_score` (float), `missing_data_flags` (json), `metadata_info` (json).
- **Indexes:** GiST on `geometry`, BTree on `timestamp`.
- **Purpose:** Represents gridded risk data constructed from ML predictions and environmental conditions.

#### **Table:** `icebergs`
- **Columns:** `iceberg_id` (uuid, PK).
- **Purpose:** Root entity for iceberg tracking.

#### **Table:** `iceberg_detections`
- **Columns:** `id` (uuid, PK), `iceberg_id` (uuid, FK to `icebergs`), `timestamp` (timestamptz), `geometry` (Point, 4326), `estimated_size` (float), `extent` (Polygon, 4326), `confidence` (float), `source_imagery` (varchar), `detection_metadata` (json).
- **Indexes:** GiST on `geometry`, GiST on `extent`, BTree on `timestamp`, BTree on `iceberg_id`.
- **Purpose:** Stores spatial and temporal observations of icebergs over time. It distinguishes *observations* (not predictions).

#### **Table:** `ocean_observations`
- **Columns:** `id` (uuid, PK), `timestamp` (timestamptz), `geometry` (Point, 4326), `current_speed` (float), `current_direction` (float), `sea_surface_temperature` (float), `wave_information` (varchar), `source` (varchar).
- **Indexes:** GiST on `geometry`, BTree on `timestamp`.
- **Purpose:** Environment context.

### 1.2 General Characteristics
- **SRID:** 4326 for all spatial columns.
- **Coordinates:** PostGIS standard `lon, lat` pairs inside WKT/geometry types.
- **Timestamps:** Timezone-aware (`timestamp with time zone`).

## 2. Text / JSON Data Stores

### **Ports Data**
- **Location:** `backend/data/ports.json` and `backend/data/world_ports_index.csv`.
- **Purpose:** The real world port coordinate data does not reside in the SQL dump, and will be mapped and parsed from the file storage JSON.
