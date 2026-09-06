import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_get_iceberg_detections(client: AsyncClient):
    response = await client.get("/api/v1/icebergs/detections")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0


@pytest.mark.asyncio
async def test_get_unknown_iceberg_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/icebergs/123e4567-e89b-12d3-a456-426614174000")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_iceberg_track_unknown_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/icebergs/123e4567-e89b-12d3-a456-426614174000/track")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_iceberg_trajectory_unknown_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/icebergs/123e4567-e89b-12d3-a456-426614174000/trajectory")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_iceberg_trajectory_validates_horizon(client: AsyncClient):
    # Generate a detection first so an iceberg exists.
    await client.get("/api/v1/icebergs/detections")
    # Pull a known iceberg id from the detections collection.
    det = await client.get("/api/v1/icebergs/detections")
    iceberg_id = det.json()["features"][0]["properties"]["iceberg_id"]
    bad = await client.get(f"/api/v1/icebergs/{iceberg_id}/trajectory?horizon_hours=0")
    assert bad.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY