import pytest
import uuid
from datetime import datetime, timezone
from app.models.route import Route
from app.models.enums import ObjectiveType, AlertSeverity
from app.services.alerts.engine import AlertEngine

@pytest.fixture
def alert_engine():
    # ``proximity_buffer_deg`` keeps the original degree-based threshold the
    # tests were written against (0.5° ≈ 30 NM).
    return AlertEngine(proximity_buffer_deg=0.5)

@pytest.fixture
def mock_route():
    return Route(
        route_id=uuid.uuid4(),
        vessel_id=uuid.uuid4(),
        origin="0.0,0.0",
        destination="2.0,0.0",
        departure_time=datetime.now(timezone.utc),
        distance=100.0,
        eta=datetime.now(timezone.utc),
        estimated_fuel=100.0,
        risk_score=0.5,
        objective_type=ObjectiveType.FASTEST,
        geometry="LINESTRING(0.0 0.0, 1.0 0.0, 2.0 0.0)"
    )

def test_alert_engine_missing_data(alert_engine, mock_route):
    alerts = alert_engine.evaluate_route(mock_route, {})
    assert len(alerts) == 1
    assert alerts[0].alert_type == "missing_data"
    assert "Missing prediction data" in alerts[0].message

def test_alert_engine_intersection(alert_engine, mock_route):
    # Hazard exactly on the route origin
    risk_grid = {
        (0.0, 0.0): {"iceberg": 0.8}
    }
    
    alerts = alert_engine.evaluate_route(mock_route, risk_grid)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_type == "iceberg"
    assert alert.severity == AlertSeverity.CRITICAL
    assert "intersects" in alert.message

def test_alert_engine_proximity(alert_engine, mock_route):
    # Hazard just off the route, within buffer (0.5)
    risk_grid = {
        (0.4, 0.0): {"weather": 0.9}
    }
    
    alerts = alert_engine.evaluate_route(mock_route, risk_grid)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_type == "weather"
    assert alert.severity == AlertSeverity.CRITICAL
    assert "approaches within proximity buffer" in alert.message

def test_alert_engine_threshold(alert_engine, mock_route):
    # Hazard below threshold
    risk_grid = {
        (0.0, 1.0): {"sea_ice": 0.5} # threshold is 0.7
    }
    alerts = alert_engine.evaluate_route(mock_route, risk_grid)
    assert len(alerts) == 0

def test_alert_engine_severity_classification(alert_engine, mock_route):
    # Test varying severities
    # Sea ice threshold is 0.7
    risk_grid = {
        (0.0, 1.0): {"sea_ice": 0.7}, # HIGH
        (0.0, 1.5): {"sea_ice": 0.95} # CRITICAL
    }
    alerts = alert_engine.evaluate_route(mock_route, risk_grid)
    assert len(alerts) == 2
    severities = {a.severity for a in alerts}
    assert AlertSeverity.HIGH in severities
    assert AlertSeverity.CRITICAL in severities
