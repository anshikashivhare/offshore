CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS vessels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    vessel_type VARCHAR(100),
    cruising_speed NUMERIC,
    fuel_consumption_rate NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS iceberg_positions (
    id SERIAL PRIMARY KEY,
    iceberg_id VARCHAR(100) NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    position GEOGRAPHY(POINT, 4326) NOT NULL,
    confidence NUMERIC
);

CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER REFERENCES vessels(id),
    route_type VARCHAR(50),
    total_distance NUMERIC,
    estimated_time NUMERIC,
    estimated_fuel NUMERIC,
    risk_score NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
