import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.models.base import Base
from app.models.vessel import Vessel
from app.models.alert import Alert
from app.models.enums import AlertSeverity
from datetime import datetime, timezone

# Use an in-memory SQLite DB for simple tests or a separate test Postgres DB.
# For simplicity in simple unit tests, SQLite can be used, BUT SQLite doesn't support GeoAlchemy2 Geometry type natively unless Spatialite is loaded.
# To avoid Spatialite loading complexities, we'll test simple fields or use mocks, or skip if PostGIS is not available.

@pytest.mark.asyncio
async def test_vessel_model():
    # Instantiate a model object (not testing DB interaction to avoid PostGIS requirement in unit test, 
    # integration tests would use actual PostGIS)
    vessel = Vessel(
        vessel_name="RV Investigator",
        vessel_type="Research",
        cruising_speed=11.0,
        fuel_consumption=80.0,
        ice_capability="PC7"
    )
    
    assert vessel.vessel_name == "RV Investigator"
    assert vessel.ice_capability == "PC7"

@pytest.mark.asyncio
async def test_alert_model():
    alert = Alert(
        alert_type="WEATHER_WARNING",
        severity=AlertSeverity.HIGH,
        location="POINT(10 20)",
        timestamp=datetime.now(timezone.utc),
        hazard_source="Forecast",
        message="Gale warning in sector 4",
        status="active"
    )

    assert alert.severity == AlertSeverity.HIGH
    assert alert.status == "active"
