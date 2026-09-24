"""Integration test to verify API-level validation works correctly."""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_api_returns_validation_metadata():
    """Verify that API responses include land avoidance validation metadata."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/routes/plan",
            json={
                "origin": "-60,-62",
                "destination": "-55,-65",
                "vessel_id": "00000000-0000-0000-0000-000000000000",
                "departure_time": "2026-09-24T12:00:00Z",
                "objective_type": "shortest"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify GeoJSON structure
        assert data["type"] == "Feature"
        assert "geometry" in data
        assert "properties" in data

        props = data["properties"]

        # Verify validation metadata exists
        assert "land_avoidance_validated" in props
        assert props["land_avoidance_validated"] is True, "Route should be validated"

        # Verify snapping metadata exists
        assert "endpoint_snapping_applied" in props

        # If snapping was applied, verify snapped coordinates are present
        if props.get("endpoint_snapping_applied"):
            assert "snapped_origin" in props
            assert "snapped_destination" in props
            assert props["snapped_origin"] is not None
            assert props["snapped_destination"] is not None

        # Verify route geometry is present
        assert data["geometry"]["type"] == "LineString"
        assert len(data["geometry"]["coordinates"]) > 0


@pytest.mark.asyncio
async def test_api_rejects_impossible_land_route():
    """Verify that API returns error for ports with no water nearby."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # South Pole - no water within 2.0° radius
        response = await client.post(
            "/api/v1/routes/plan",
            json={
                "origin": "0,-89",  # Near South Pole
                "destination": "-60,-62",
                "vessel_id": "00000000-0000-0000-0000-000000000000",
                "departure_time": "2026-09-24T12:00:00Z",
                "objective_type": "shortest"
            }
        )

        # Should return 400 with appropriate error message
        assert response.status_code == 400
        assert "no navigable water found" in response.json()["detail"].lower()
