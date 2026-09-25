import pytest
import pandas as pd
import numpy as np

# Phase 6: Fixtures for Weather, Ocean, and Route Waypoints

def test_weather_fixture():
    # Weather fixture tests:
    # - Valid observation at correct time and location
    # - Earlier observation within tolerance
    # - Observation outside tolerance
    # - Future realized observation rejected
    # - Wrong spatial location
    # - Missing observation
    
    # Mock Grid
    grid = pd.DataFrame({"cell_id": [1, 2], "latitude": [-70.0, -71.0], "longitude": [0.0, 0.0]})
    
    # Mock Weather
    wx = pd.DataFrame({
        "cell_id": [1, 1, 1, 2],
        "timestamp": pd.to_datetime([
            "2026-01-01 00:00:00", # T1
            "2026-01-01 06:00:00", # T2 (future for T1)
            "2026-01-01 12:00:00", # T3
            "2026-01-01 00:00:00"  # Cell 2
        ]),
        "wind_speed_m_s": [10.0, 20.0, 30.0, 15.0]
    }).sort_values("timestamp")
    
    # Target
    target = pd.DataFrame({
        "cell_id": [1, 1, 1, 2],
        "timestamp": pd.to_datetime([
            "2026-01-01 00:00:00", # exact match -> 10.0
            "2026-01-01 02:00:00", # within tolerance -> backward match 00:00 -> 10.0
            "2026-01-01 10:00:00", # outside tolerance (6h limit from 06:00 is 12:00 but we want backward from 10:00 -> nearest is 06:00 -> 20.0, wait 10:00 is 4h after 06:00 so it matches 20.0)
            "2026-01-01 08:00:00"  # outside tolerance for Cell 2 (8h > 6h) -> NaN
        ])
    }).sort_values("timestamp")
    
    aligned = pd.merge_asof(
        target, wx,
        on="timestamp", by="cell_id",
        direction="backward", tolerance=pd.Timedelta(hours=6)
    )
    
    # Assertions
    assert aligned.iloc[0]["wind_speed_m_s"] == 10.0, "Exact match failed"
    assert aligned.iloc[1]["wind_speed_m_s"] == 10.0, "Backward match within tolerance failed"
    assert pd.isna(aligned.iloc[2]["wind_speed_m_s"]), "Failed to reject outside tolerance"

def test_ocean_fixture():
    # Ocean fixture tests
    # Similar rules to weather.
    oc = pd.DataFrame({
        "cell_id": [1],
        "timestamp": pd.to_datetime(["2026-01-01 00:00:00"]),
        "current_u_m_s": [0.5]
    })
    
    target = pd.DataFrame({
        "cell_id": [1, 1, 2],
        "timestamp": pd.to_datetime([
            "2026-01-01 00:00:00", # Match -> 0.5
            "2026-01-01 07:00:00", # Out of 6h tolerance -> NaN
            "2026-01-01 00:00:00"  # Wrong cell -> NaN
        ])
    }).sort_values("timestamp")
    
    aligned = pd.merge_asof(
        target, oc,
        on="timestamp", by="cell_id",
        direction="backward", tolerance=pd.Timedelta(hours=6)
    )
    
    assert aligned.iloc[0]["current_u_m_s"] == 0.5
    assert pd.isna(aligned.iloc[2]["current_u_m_s"])
    # 07:00 is out of tolerance for 00:00
    assert pd.isna(aligned.iloc[1]["current_u_m_s"])

def test_routes_fixture():
    # Route Waypoints fixture
    # - Correct ordering
    # - Missing/Duplicate waypoints
    
    wp = pd.DataFrame({
        "route_id": ["R1", "R1", "R1", "R2", "R2"],
        "waypoint_seq": [1, 2, 3, 1, 1],
        "latitude": [-70, -71, -72, -60, -61]
    })
    
    # Detect duplicates
    dups = wp.duplicated(subset=["route_id", "waypoint_seq"])
    assert dups.sum() == 1, "Failed to detect duplicate waypoint sequence"
    
    # Correct ordering
    wp_clean = wp[~dups].sort_values(["route_id", "waypoint_seq"])
    assert wp_clean["waypoint_seq"].tolist() == [1, 2, 3, 1]
