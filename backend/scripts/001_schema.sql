-- 001_schema.sql
-- Description: Raw PostgreSQL/PostGIS schema definitions matching the existing SQLAlchemy ORM models.
-- Execution: This script must be run against a PostgreSQL database with the PostGIS extension enabled.

-- Enable PostGIS extension (Required for Geometry columns)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enum Type for objective_type is implicitly created by SQLAlchemy as a VARCHAR if native enums aren't used,
-- but typically native enums are preferred. We'll use VARCHAR for broader compatibility, matching the ORM string fallback.
-- Or we can define a native ENUM if `ObjectiveType` is a strict enum in `route.py`.
-- Let's use VARCHAR(20) to keep it simple and aligned with standard SQLAlchemy Enum(native_enum=False).

-------------------------------------------------------------------------------
-- TABLE: vessels
-------------------------------------------------------------------------------
CREATE TABLE vessels (
    vessel_id UUID PRIMARY KEY,
    vessel_name VARCHAR(255) NOT NULL,
    imo_number VARCHAR(20),
    mmsi VARCHAR(20),
    flag_country VARCHAR(100),
    vessel_type VARCHAR(100) NOT NULL,
    max_speed DOUBLE PRECISION,
    cruising_speed DOUBLE PRECISION NOT NULL, -- in knots
    ice_capability VARCHAR(50),               -- ice class
    icebreaking_capability VARCHAR(100),
    polar_operating_capability VARCHAR(100),
    length_m DOUBLE PRECISION,
    beam_m DOUBLE PRECISION,
    draft_m DOUBLE PRECISION,
    fuel_type VARCHAR(100),
    fuel_consumption DOUBLE PRECISION NOT NULL, -- rate of consumption
    passenger_capacity INTEGER,
    cargo_capacity VARCHAR(255),
    data_source VARCHAR(255),
    last_updated_timestamp VARCHAR(50),
    verification_status VARCHAR(50),
    operational_limits JSONB
);

CREATE INDEX ix_vessels_vessel_name ON vessels (vessel_name);
CREATE INDEX ix_vessels_imo_number ON vessels (imo_number);
CREATE INDEX ix_vessels_mmsi ON vessels (mmsi);
CREATE INDEX ix_vessels_flag_country ON vessels (flag_country);

-------------------------------------------------------------------------------
-- TABLE: routes
-------------------------------------------------------------------------------
CREATE TABLE routes (
    route_id UUID PRIMARY KEY,
    origin VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    vessel_id UUID NOT NULL REFERENCES vessels (vessel_id),
    departure_time TIMESTAMP WITH TIME ZONE NOT NULL,
    geometry geometry(LINESTRING, 4326) NOT NULL,
    distance DOUBLE PRECISION NOT NULL, -- distance in nautical miles
    eta TIMESTAMP WITH TIME ZONE NOT NULL,
    estimated_fuel DOUBLE PRECISION NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    algorithm_version VARCHAR(50)
);

CREATE INDEX ix_routes_vessel_id ON routes (vessel_id);
-- Spatial index for routes geometry
CREATE INDEX idx_routes_geometry ON routes USING GIST (geometry);

-------------------------------------------------------------------------------
-- TABLE: risk_cells
-------------------------------------------------------------------------------
CREATE TABLE risk_cells (
    id UUID PRIMARY KEY,
    geometry geometry(POLYGON, 4326) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ice_risk DOUBLE PRECISION NOT NULL,
    iceberg_risk DOUBLE PRECISION NOT NULL,
    weather_risk DOUBLE PRECISION NOT NULL,
    current_risk DOUBLE PRECISION NOT NULL,
    composite_risk DOUBLE PRECISION NOT NULL,
    risk_category VARCHAR(50) NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    missing_data_flags JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata_info JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX ix_risk_cells_timestamp ON risk_cells (timestamp);
-- Spatial index for risk_cells geometry
CREATE INDEX idx_risk_cells_geometry ON risk_cells USING GIST (geometry);
