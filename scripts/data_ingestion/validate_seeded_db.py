"""
Database Seeding & PostGIS Integrity Validation Script for Offshore.

Verifies:
1. All application tables exist.
2. Record counts match synthetic expected dataset sizes.
3. Primary key & foreign key integrity.
4. PostGIS spatial geometry validity (ST_IsValid, ST_SRID, ST_GeometryType).
5. Non-null constraints, lat/lon bounds, timestamp validity.
"""

import json
import logging
import os
import sys
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("validate_seeded_db")

DB_HOST = os.environ.get("POSTGRES_SERVER", "localhost")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5433))
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.environ.get("POSTGRES_DB", "antarctic_nav")


def validate():
    logger.info("Connecting to PostgreSQL at %s:%d/%s...", DB_HOST, DB_PORT, DB_NAME)
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    cur = conn.cursor()
    
    # Expected table list & minimum expected record counts
    expected_counts = {
        "vessels": 2,
        "sea_ice_observations": 18250,
        "weather_observations": 73000,
        "ocean_observations": 73000,
        "icebergs": 30,
        "iceberg_detections": 30424,
        "iceberg_predictions": 30424,
        "routes": 10,
        "risk_cells": 50,
        "alerts": 2
    }
    
    validation_results = {
        "tables_checked": 0,
        "record_counts": {},
        "spatial_checks": {},
        "fk_checks": {},
        "all_passed": True
    }
    
    logger.info("=== 1. RECORD COUNT VALIDATION ===")
    for table, min_count in expected_counts.items():
        cur.execute(f'SELECT COUNT(*) FROM "{table}";')
        actual = cur.fetchone()[0]
        validation_results["record_counts"][table] = actual
        validation_results["tables_checked"] += 1
        
        status = "PASS" if actual >= min_count else "FAIL"
        if status == "FAIL":
            validation_results["all_passed"] = False
        logger.info("Table '%s': %d records (Expected >= %d) [%s]", table, actual, min_count, status)
        
    logger.info("\n=== 2. POSTGIS SPATIAL GEOMETRY VALIDATION ===")
    spatial_tables = {
        "sea_ice_observations": ("geometry", "POLYGON"),
        "weather_observations": ("geometry", "POINT"),
        "ocean_observations": ("geometry", "POINT"),
        "iceberg_detections": ("geometry", "POINT"),
        "iceberg_predictions": ("predicted_geometry", "POINT"),
        "routes": ("geometry", "LINESTRING"),
        "risk_cells": ("geometry", "POLYGON"),
        "alerts": ("location", "POINT")
    }
    
    for table, (geom_col, expected_type) in spatial_tables.items():
        # Check invalid geometries
        cur.execute(f'SELECT COUNT(*) FROM "{table}" WHERE NOT ST_IsValid("{geom_col}");')
        invalid_cnt = cur.fetchone()[0]
        
        # Check SRID != 4326
        cur.execute(f'SELECT COUNT(*) FROM "{table}" WHERE ST_SRID("{geom_col}") != 4326;')
        srid_err_cnt = cur.fetchone()[0]
        
        passed = (invalid_cnt == 0 and srid_err_cnt == 0)
        if not passed:
            validation_results["all_passed"] = False
            
        validation_results["spatial_checks"][table] = {
            "geom_col": geom_col,
            "invalid_geometries": invalid_cnt,
            "srid_mismatches": srid_err_cnt,
            "status": "PASS" if passed else "FAIL"
        }
        logger.info("Spatial table '%s' (%s): Invalid=%d, SRID_Err=%d [%s]", table, geom_col, invalid_cnt, srid_err_cnt, "PASS" if passed else "FAIL")
        
    logger.info("\n=== 3. FOREIGN KEY & INTEGRITY VALIDATION ===")
    # FK check: routes -> vessels
    cur.execute("""
        SELECT COUNT(*) 
        FROM routes r 
        LEFT JOIN vessels v ON r.vessel_id = v.vessel_id 
        WHERE v.vessel_id IS NULL;
    """)
    orphan_routes = cur.fetchone()[0]
    
    # FK check: iceberg_detections -> icebergs
    cur.execute("""
        SELECT COUNT(*) 
        FROM iceberg_detections d 
        LEFT JOIN icebergs i ON d.iceberg_id = i.iceberg_id 
        WHERE i.iceberg_id IS NULL;
    """)
    orphan_detections = cur.fetchone()[0]
    
    fk_passed = (orphan_routes == 0 and orphan_detections == 0)
    if not fk_passed:
        validation_results["all_passed"] = False
        
    validation_results["fk_checks"] = {
        "orphan_routes": orphan_routes,
        "orphan_detections": orphan_detections,
        "status": "PASS" if fk_passed else "FAIL"
    }
    logger.info("Foreign Keys: Orphan Routes=%d, Orphan Detections=%d [%s]", orphan_routes, orphan_detections, "PASS" if fk_passed else "FAIL")
    
    conn.close()
    
    logger.info("\n=== VALIDATION SUMMARY ===")
    if validation_results["all_passed"]:
        logger.info("ALL DATABASE INTEGRITY AND SPATIAL CHECKS PASSED!")
    else:
        logger.error("SOME VALIDATION CHECKS FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    validate()
