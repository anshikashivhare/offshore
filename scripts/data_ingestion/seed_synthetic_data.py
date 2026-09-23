"""
Synthetic Data Ingestion & Database Seeding Script for Offshore.

Reads synthetic datasets from 'C:/Users/ASUS/Desktop/Synthetic data for offshore' (ZIP archive)
and seeds the antarctic_nav PostgreSQL + PostGIS database.
"""

import csv
import io
import json
import logging
import os
import sys
import uuid
import zipfile
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("seed_synthetic_data")

# Deterministic UUID Namespace
NS_OFFSHORE = uuid.UUID("a9b8c7d6-e5f4-3210-9876-543210fedcba")

# Default Synthetic Data Path
DEFAULT_SYNTHETIC_PATH = r"C:\Users\ASUS\Desktop\Synthetic data for offshore"

# DB Connection Config
DB_HOST = os.environ.get("POSTGRES_SERVER", "localhost")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5433))
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.environ.get("POSTGRES_DB", "antarctic_nav")


def get_uuid(key_str: str) -> str:
    """Generate a deterministic UUID v5 from a string key."""
    return str(uuid.uuid5(NS_OFFSHORE, key_str))


def parse_iso_dt(dt_str: str) -> datetime:
    """Parse ISO 8601 timestamp string into UTC timezone-aware datetime."""
    if not dt_str:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def create_bbox_polygon(lat: float, lon: float, dlat: float = 0.5, dlon: float = 1.0) -> str:
    """Create a WKT POLYGON centered at lat, lon with given delta bounds."""
    min_lat, max_lat = max(-90.0, lat - dlat), min(90.0, lat + dlat)
    min_lon, max_lon = max(-180.0, lon - dlon), min(180.0, lon + dlon)
    return f"SRID=4326;POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"


def create_point(lat: float, lon: float) -> str:
    """Create a WKT POINT string from lat and lon."""
    return f"SRID=4326;POINT({lon} {lat})"


def open_synthetic_archive(archive_path: str):
    """Return a zipfile object or raises error."""
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"Synthetic data file not found at: {archive_path}")
    return zipfile.ZipFile(archive_path, "r")


def read_csv_from_zip(zf: zipfile.ZipFile, csv_name: str):
    """Read CSV file content from zip and yield DictReader rows."""
    content = zf.read(csv_name).decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


def clean_existing_data(conn):
    """Truncate tables in correct dependency order before seeding."""
    logger.info("Cleaning up existing dummy records in dependency order...")
    tables_to_truncate = [
        "alerts",
        "routes",
        "iceberg_predictions",
        "iceberg_detections",
        "icebergs",
        "vessels",
        "risk_cells",
        "ocean_observations",
        "weather_observations",
        "sea_ice_observations",
        "forecasts",
        "jobs"
    ]
    with conn.cursor() as cur:
        for t in tables_to_truncate:
            cur.execute(f'TRUNCATE TABLE "{t}" CASCADE;')
    conn.commit()
    logger.info("All application tables successfully cleared.")


def seed_vessels(conn, zf):
    """Seed vessels table with VSL_00 and VSL_01."""
    logger.info("Seeding vessels...")
    vessels_data = [
        {
            "vessel_id": get_uuid("VSL_00"),
            "vessel_name": "RV Aurora Australis",
            "vessel_type": "Research icebreaker",
            "cruising_speed": 12.0,
            "fuel_consumption": 860.0,
            "ice_capability": "PC4 / 1.2 m first-year ice",
            "operational_limits": json.dumps({"wind_knots_max": 45, "visibility_nm_min": 1.0, "source_id": "VSL_00"})
        },
        {
            "vessel_id": get_uuid("VSL_01"),
            "vessel_name": "RV Endurance",
            "vessel_type": "Polar research vessel",
            "cruising_speed": 14.0,
            "fuel_consumption": 940.0,
            "ice_capability": "PC3 / 1.5 m first-year ice",
            "operational_limits": json.dumps({"wind_knots_max": 50, "visibility_nm_min": 0.8, "source_id": "VSL_01"})
        }
    ]
    sql = """
        INSERT INTO vessels (vessel_id, vessel_name, vessel_type, cruising_speed, fuel_consumption, ice_capability, operational_limits)
        VALUES %s;
    """
    values = [
        (v["vessel_id"], v["vessel_name"], v["vessel_type"], v["cruising_speed"], v["fuel_consumption"], v["ice_capability"], v["operational_limits"])
        for v in vessels_data
    ]
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    conn.commit()
    logger.info("Seeded %d vessels.", len(vessels_data))


def seed_grid_cells_and_risk_cells(conn, zf):
    """Seed risk_cells table using grid_cells_2026.csv."""
    logger.info("Seeding risk_cells from grid_cells_2026.csv...")
    cells = read_csv_from_zip(zf, "data/raw/grid_cells_2026.csv")
    
    cfg_raw = zf.read("data/metadata/generation_config_2026.json").decode("utf-8")
    cfg = json.loads(cfg_raw)
    
    risk_cell_records = []
    base_time = parse_iso_dt("2026-09-18T06:00:00+00:00")
    
    for row in cells:
        cell_id = int(row["cell_id"])
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        poly_wkt = create_bbox_polygon(lat, lon, dlat=1.2, dlon=3.6)
        
        lat_factor = min(1.0, max(0.0, (abs(lat) - 55.0) / 25.0))
        ice_risk = round(0.1 + 0.8 * lat_factor, 3)
        iceberg_risk = round(0.05 + 0.7 * lat_factor, 3)
        weather_risk = round(0.2 + 0.5 * (1.0 - abs(lon)/180.0), 3)
        current_risk = round(0.1 + 0.3 * lat_factor, 3)
        
        composite = round(0.35 * ice_risk + 0.35 * iceberg_risk + 0.15 * weather_risk + 0.15 * current_risk, 3)
        if composite > 0.75:
            cat = "avoid"
        elif composite > 0.55:
            cat = "high"
        elif composite > 0.35:
            cat = "moderate"
        else:
            cat = "low"
            
        r_id = get_uuid(f"RISK_CELL_{cell_id}")
        risk_cell_records.append((
            r_id,
            poly_wkt,
            base_time,
            ice_risk,
            iceberg_risk,
            weather_risk,
            current_risk,
            composite,
            cat,
            1.0,
            json.dumps({"has_gap": False}),
            json.dumps({"cell_id": cell_id, "lat_band": row["lat_band"], "lon_band": row["lon_band"]})
        ))

    sql = """
        INSERT INTO risk_cells (id, geometry, timestamp, ice_risk, iceberg_risk, weather_risk, current_risk, composite_risk, risk_category, confidence_score, missing_data_flags, metadata_info)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, risk_cell_records, page_size=500)
    conn.commit()
    logger.info("Seeded %d risk_cells.", len(risk_cell_records))


def seed_sea_ice(conn, zf):
    """Seed sea_ice_observations table from sea_ice_synthetic_2026.csv."""
    logger.info("Seeding sea_ice_observations...")
    rows = read_csv_from_zip(zf, "data/raw/sea_ice_synthetic_2026.csv")
    records = []
    for r in rows:
        sample_id = r["sample_id"]
        obs_id = get_uuid(sample_id)
        dt = parse_iso_dt(r["timestamp"])
        lat, lon = float(r["latitude"]), float(r["longitude"])
        poly_wkt = create_bbox_polygon(lat, lon, dlat=0.6, dlon=1.8)
        conc = float(r["sea_ice_concentration"])
        thickness = round(max(0.0, conc * 1.8), 2) if conc > 0.1 else 0.0
        ice_type = "multi_year_ice" if conc > 0.6 else ("first_year_ice" if conc > 0.15 else "open_water")
        src = r.get("data_source_type", "SYNTHETIC_PROTOTYPE")
        
        records.append((
            obs_id,
            dt,
            poly_wkt,
            conc,
            thickness,
            ice_type,
            src,
            1.0
        ))

    sql = """
        INSERT INTO sea_ice_observations (id, timestamp, geometry, concentration, thickness, ice_type, source, data_quality)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, records, page_size=2000)
    conn.commit()
    logger.info("Seeded %d sea_ice_observations.", len(records))


def seed_weather(conn, zf):
    """Seed weather_observations table from weather_synthetic_2026.csv."""
    logger.info("Seeding weather_observations...")
    rows = read_csv_from_zip(zf, "data/raw/weather_synthetic_2026.csv")
    records = []
    for r in rows:
        sample_id = r["sample_id"]
        obs_id = get_uuid(sample_id)
        dt = parse_iso_dt(r["timestamp"])
        lat, lon = float(r["latitude"]), float(r["longitude"])
        pt_wkt = create_point(lat, lon)
        w_speed = float(r["wind_speed_m_s"])
        w_dir = float(r["wind_direction_deg"])
        temp = float(r["air_temperature_c"])
        press = float(r["sea_level_pressure_hpa"])
        wave_h = round(0.015 * (w_speed ** 1.8), 2)
        src = r.get("data_source_type", "SYNTHETIC_PROTOTYPE")
        
        records.append((
            obs_id,
            dt,
            pt_wkt,
            w_speed,
            w_dir,
            temp,
            wave_h,
            press,
            src
        ))

    sql = """
        INSERT INTO weather_observations (id, timestamp, geometry, wind_speed, wind_direction, temperature, wave_height, pressure, source)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, records, page_size=5000)
    conn.commit()
    logger.info("Seeded %d weather_observations.", len(records))


def seed_ocean(conn, zf):
    """Seed ocean_observations table from ocean_currents_synthetic_2026.csv."""
    logger.info("Seeding ocean_observations...")
    rows = read_csv_from_zip(zf, "data/raw/ocean_currents_synthetic_2026.csv")
    records = []
    for r in rows:
        sample_id = r["sample_id"]
        obs_id = get_uuid(sample_id)
        dt = parse_iso_dt(r["timestamp"])
        lat, lon = float(r["latitude"]), float(r["longitude"])
        pt_wkt = create_point(lat, lon)
        c_speed = float(r["current_speed_m_s"])
        c_dir = float(r["current_direction_deg"])
        sst = round(-1.8 + max(0.0, (lat + 75.0) * 0.2), 2)
        ssh_anom = r.get("sea_surface_height_anomaly_cm", "0.0")
        wave_info = f"SSH anomaly {ssh_anom} cm"
        src = r.get("data_source_type", "SYNTHETIC_PROTOTYPE")
        
        records.append((
            obs_id,
            dt,
            pt_wkt,
            c_speed,
            c_dir,
            sst,
            wave_info,
            src
        ))

    sql = """
        INSERT INTO ocean_observations (id, timestamp, geometry, current_speed, current_direction, sea_surface_temperature, wave_information, source)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, records, page_size=5000)
    conn.commit()
    logger.info("Seeded %d ocean_observations.", len(records))


def seed_icebergs(conn, zf):
    """Seed icebergs, iceberg_detections, and iceberg_predictions from iceberg_trajectory_synthetic_2026.csv."""
    logger.info("Seeding icebergs and trajectories...")
    rows = read_csv_from_zip(zf, "data/raw/iceberg_trajectory_synthetic_2026.csv")
    
    unique_berg_ids = sorted(list(set(r["iceberg_id"] for r in rows)))
    iceberg_records = [(get_uuid(b_id),) for b_id in unique_berg_ids]
    
    sql_berg = "INSERT INTO icebergs (iceberg_id) VALUES %s;"
    with conn.cursor() as cur:
        execute_values(cur, sql_berg, iceberg_records)
    conn.commit()
    logger.info("Seeded %d unique icebergs.", len(iceberg_records))

    detection_records = []
    prediction_records = []
    
    size_map = {"IB-102": 2.8, "IB-221": 4.6, "IB-309": 1.2, "IB-412": 3.4, "IB-508": 2.1}
    
    for r in rows:
        sample_id = r["sample_id"]
        b_str_id = r["iceberg_id"]
        b_uuid = get_uuid(b_str_id)
        dt = parse_iso_dt(r["timestamp"])
        
        lat_t = float(r["latitude_t"])
        lon_t = float(r["longitude_t"])
        pt_wkt = create_point(lat_t, lon_t)
        
        est_size = size_map.get(b_str_id, 2.0)
        extent_wkt = create_bbox_polygon(lat_t, lon_t, dlat=0.02, dlon=0.05)
        
        d_id = get_uuid(f"DET_{sample_id}")
        detection_records.append((
            d_id,
            b_uuid,
            dt,
            pt_wkt,
            est_size,
            extent_wkt,
            0.95,
            "Synthetic SAR Sentinel-1",
            json.dumps({
                "sample_id": sample_id,
                "wind_speed": float(r["wind_speed_m_s"]),
                "sea_ice_conc": float(r["sea_ice_concentration"])
            })
        ))
        
        target_lat = float(r["target_latitude"])
        target_lon = float(r["target_longitude"])
        pred_pt_wkt = create_point(target_lat, target_lon)
        path_json = json.dumps([
            [float(r["longitude_t_minus_2"]), float(r["latitude_t_minus_2"])],
            [float(r["longitude_t_minus_1"]), float(r["latitude_t_minus_1"])],
            [lon_t, lat_t],
            [target_lon, target_lat]
        ])
        uncert_wkt = create_bbox_polygon(target_lat, target_lon, dlat=0.1, dlon=0.2)
        horizon = int(float(r["forecast_horizon_hours"]))
        
        p_id = get_uuid(f"PRED_{sample_id}")
        prediction_records.append((
            p_id,
            b_uuid,
            dt,
            horizon,
            "hours",
            pred_pt_wkt,
            path_json,
            uncert_wkt,
            0.88,
            "synthetic-xgb-v1"
        ))

    sql_det = """
        INSERT INTO iceberg_detections (id, iceberg_id, timestamp, geometry, estimated_size, extent, confidence, source_imagery, detection_metadata)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql_det, detection_records, page_size=2000)
    conn.commit()
    logger.info("Seeded %d iceberg_detections.", len(detection_records))

    sql_pred = """
        INSERT INTO iceberg_predictions (id, iceberg_id, prediction_timestamp, forecast_horizon, forecast_horizon_unit, predicted_geometry, predicted_path, uncertainty_representation, model_confidence, model_version)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql_pred, prediction_records, page_size=2000)
    conn.commit()
    logger.info("Seeded %d iceberg_predictions.", len(prediction_records))


def seed_routes(conn, zf):
    """Seed routes table from routes_synthetic_2026.csv and route_waypoints_synthetic_2026.csv."""
    logger.info("Seeding routes...")
    routes_raw = read_csv_from_zip(zf, "data/raw/routes_synthetic_2026.csv")
    waypoints_raw = read_csv_from_zip(zf, "data/raw/route_waypoints_synthetic_2026.csv")
    
    wp_by_route = {}
    for wp in waypoints_raw:
        r_id = wp["route_id"]
        if r_id not in wp_by_route:
            wp_by_route[r_id] = []
        wp_by_route[r_id].append(wp)
        
    for r_id in wp_by_route:
        wp_by_route[r_id].sort(key=lambda x: int(x["waypoint_seq"]))

    route_records = []
    objective_mapping = {
        "recommended": "SAFEST",
        "fastest": "FASTEST",
        "safest": "SAFEST",
        "fuel_efficient": "FUEL_EFFICIENT",
        "shortest": "SHORTEST"
    }

    for r in routes_raw:
        r_str_id = r["route_id"]
        r_uuid = get_uuid(r_str_id)
        vessel_uuid = get_uuid(r["vessel_id"])
        
        orig = r["origin_name"]
        dest = r["destination_name"]
        dep_time = parse_iso_dt(r["departure_time"])
        arr_time = parse_iso_dt(r["arrival_time"])
        
        dist_km = float(r["total_distance_km"])
        dist_nm = round(dist_km / 1.852, 2)
        
        est_fuel = round(dist_nm * 15.0, 2)
        risk_score = float(r["overall_risk_score"])
        
        obj_type = objective_mapping.get(r["route_type"].lower(), "SAFEST")
        
        wps = wp_by_route.get(r_str_id, [])
        if wps:
            pts_str = ", ".join(f"{float(wp['longitude'])} {float(wp['latitude'])}" for wp in wps)
            line_wkt = f"SRID=4326;LINESTRING({pts_str})"
        else:
            orig_lat, orig_lon = float(r["origin_lat"]), float(r["origin_lon"])
            dest_lat, dest_lon = float(r["destination_lat"]), float(r["destination_lon"])
            line_wkt = f"SRID=4326;LINESTRING({orig_lon} {orig_lat}, {dest_lon} {dest_lat})"
            
        route_records.append((
            r_uuid,
            orig,
            dest,
            vessel_uuid,
            dep_time,
            line_wkt,
            dist_nm,
            arr_time,
            est_fuel,
            risk_score,
            obj_type,
            "synthetic-a-star-v1"
        ))

    sql = """
        INSERT INTO routes (route_id, origin, destination, vessel_id, departure_time, geometry, distance, eta, estimated_fuel, risk_score, objective_type, algorithm_version)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, route_records)
    conn.commit()
    logger.info("Seeded %d routes.", len(route_records))


def seed_alerts(conn, zf):
    """Seed alerts table with initial synthetic alerts."""
    logger.info("Seeding alerts...")
    
    route_uuid = get_uuid("RT_0000")
    
    alerts_data = [
        (
            get_uuid("ALERT_001"),
            "Iceberg Proximity Warning",
            "HIGH",
            create_point(-63.8, 11.8),
            parse_iso_dt("2026-09-18T06:00:00+00:00"),
            route_uuid,
            "IB-102 Trajectory",
            "Iceberg IB-102 projected to intersect recommended route corridor near 63.8S 11.8E within 12 hours.",
            "active",
            2.8,
            5.0,
            0.94
        ),
        (
            get_uuid("ALERT_002"),
            "High Sea-Ice Concentration",
            "MEDIUM",
            create_point(-67.57, -68.13),
            parse_iso_dt("2026-09-18T06:00:00+00:00"),
            route_uuid,
            "Sea-Ice Forecast",
            "Sea-ice concentration exceeds 60% in Rothera approach channel.",
            "active",
            0.62,
            0.50,
            0.89
        )
    ]
    
    sql = """
        INSERT INTO alerts (id, alert_type, severity, location, timestamp, route_id, hazard_source, message, status, triggering_metric, threshold, confidence)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, alerts_data)
    conn.commit()
    logger.info("Seeded %d alerts.", len(alerts_data))


def main():
    archive_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SYNTHETIC_PATH
    logger.info("Starting synthetic database seeding from: %s", archive_path)
    
    zf = open_synthetic_archive(archive_path)
    
    logger.info("Connecting to PostgreSQL at %s:%d/%s...", DB_HOST, DB_PORT, DB_NAME)
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    
    try:
        clean_existing_data(conn)
        seed_vessels(conn, zf)
        seed_grid_cells_and_risk_cells(conn, zf)
        seed_sea_ice(conn, zf)
        seed_weather(conn, zf)
        seed_ocean(conn, zf)
        seed_icebergs(conn, zf)
        seed_routes(conn, zf)
        seed_alerts(conn, zf)
        logger.info("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    except Exception as e:
        logger.error("Seeding failed: %s", e, exc_info=True)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()
        zf.close()


if __name__ == "__main__":
    main()
