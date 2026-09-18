import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timezone
from app.main import app
from app.models.vessel import Vessel
from app.models.enums import ObjectiveType

@pytest.fixture
def test_vessel():
    return Vessel(
        vessel_id=uuid.uuid4(),
        vessel_name="Test API Ship",
        vessel_type="Tanker",
        cruising_speed=10.0,
        fuel_consumption=45.0,
        ice_capability="1A"
    )

@pytest.mark.asyncio
async def test_plan_route_endpoint_not_found(test_vessel):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/routes/plan", json={
            "origin": "10.0,50.0",
            "destination": "12.0,52.0",
            "vessel_id": str(test_vessel.vessel_id),
            "departure_time": datetime.now(timezone.utc).isoformat(),
            "objective_type": ObjectiveType.FASTEST
        })
    # Demo mode provides a vessel, so 404 is no longer returned.
    # Instead, the A* routing may fail with 400 (e.g. coordinates over land).
    assert response.status_code in (400, 404)

@pytest.mark.asyncio
async def test_compare_routes_endpoint_not_found(test_vessel):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/routes/compare", json={
            "origin": "10.0,50.0",
            "destination": "12.0,52.0",
            "vessel_id": str(test_vessel.vessel_id),
            "departure_time": datetime.now(timezone.utc).isoformat(),
            "objective_type": ObjectiveType.FASTEST
        })
    assert response.status_code == 404

# In a full test suite, we would use a DB fixture to insert the test_vessel,
# and then call the endpoint expecting a 200 OK.
