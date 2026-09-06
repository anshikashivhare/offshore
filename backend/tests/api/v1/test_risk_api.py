import pytest
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timezone
from app.main import app

@pytest.mark.asyncio
async def test_generate_risk_map_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/risk/map", json={
            "bbox": "-10,-10,10,10",
            "weights": {
                "ice": 0.4,
                "iceberg": 0.3,
                "weather": 0.2,
                "current": 0.1
            }
        })
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Risk map generated"
    assert "cell_ids" in data
    assert data["n_cells"] > 0

@pytest.mark.asyncio
async def test_get_risk_cells_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/risk/cells")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
