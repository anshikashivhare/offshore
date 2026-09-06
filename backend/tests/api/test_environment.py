import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_get_sea_ice_observations_requires_bbox(client: AsyncClient):
    # bbox is required; without it the API returns 422.
    response = await client.get("/api/v1/environment/sea-ice")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_weather_observations_requires_bbox(client: AsyncClient):
    response = await client.get("/api/v1/environment/weather")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_ocean_observations_requires_bbox(client: AsyncClient):
    response = await client.get("/api/v1/environment/ocean")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_sea_ice_observations_empty_grid(client: AsyncClient):
    response = await client.get(
        "/api/v1/environment/sea-ice",
        params={
            "min_lat": -65.0, "min_lon": -60.0,
            "max_lat": -64.0, "max_lon": -59.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert body["features"] == []
    assert body["total"] == 0