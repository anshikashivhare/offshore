import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_alerts_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data

@pytest.mark.asyncio
async def test_get_alerts_filtering():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/alerts/?severity=critical&alert_type=iceberg")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    # Will be empty without DB fixture seeding, but confirms no 500 error
    assert isinstance(data["features"], list)
