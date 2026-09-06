import pytest
from datetime import datetime, timezone
from app.schemas.vessel import VesselCreate
from app.schemas.alert import AlertCreate
from app.models.enums import AlertSeverity

def test_vessel_schema():
    vessel_data = {
        "vessel_name": "Polarstern",
        "vessel_type": "Research Icebreaker",
        "cruising_speed": 12.5,
        "fuel_consumption": 100.0,
        "ice_capability": "PC3",
        "operational_limits": {"max_ice_thickness": 1.5}
    }
    vessel = VesselCreate(**vessel_data)
    assert vessel.vessel_name == "Polarstern"
    assert vessel.cruising_speed == 12.5

def test_alert_schema():
    alert_data = {
        "alert_type": "ICEBERG_PROXIMITY",
        "severity": AlertSeverity.CRITICAL,
        "location": "POINT(10 20)",
        "timestamp": datetime.now(timezone.utc),
        "hazard_source": "Satellite Detection",
        "message": "Large iceberg within 5nm."
    }
    alert = AlertCreate(**alert_data)
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.status == "active"
