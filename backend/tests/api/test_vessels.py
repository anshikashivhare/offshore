import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_create_and_read_vessel(client: AsyncClient):
    payload = {
        "vessel_name": "RRS Sir David Attenborough",
        "vessel_type": "Research Icebreaker",
        "cruising_speed": 13.0,
        "fuel_consumption": 25.5,
        "ice_capability": "Polar Class 4",
        "operational_limits": {"max_ice_thickness_m": 1.5},
    }
    response = await client.post("/api/v1/vessels/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert "vessel_id" in body
    assert body["vessel_name"] == payload["vessel_name"]

    vessel_id = body["vessel_id"]

    get_resp = await client.get(f"/api/v1/vessels/{vessel_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["vessel_id"] == vessel_id

    list_resp = await client.get("/api/v1/vessels/")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert listed["total"] >= 1
    assert any(v["vessel_id"] == vessel_id for v in listed["data"])


@pytest.mark.asyncio
async def test_create_duplicate_vessel_returns_409(client: AsyncClient):
    payload = {
        "vessel_name": "Aurora",
        "vessel_type": "Cargo",
        "cruising_speed": 10.0,
        "fuel_consumption": 1.0,
        "ice_capability": "None",
    }
    r1 = await client.post("/api/v1/vessels/", json=payload)
    assert r1.status_code == status.HTTP_201_CREATED
    r2 = await client.post("/api/v1/vessels/", json=payload)
    assert r2.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_get_unknown_vessel_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/vessels/00000000-0000-0000-0000-000000000000")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_and_delete_vessel(client: AsyncClient):
    create = await client.post(
        "/api/v1/vessels/",
        json={
            "vessel_name": "Polaris",
            "vessel_type": "Icebreaker",
            "cruising_speed": 11.0,
            "fuel_consumption": 1.5,
            "ice_capability": "PC5",
        },
    )
    assert create.status_code == status.HTTP_201_CREATED
    vessel_id = create.json()["vessel_id"]

    update = await client.put(
        f"/api/v1/vessels/{vessel_id}",
        json={
            "vessel_name": "Polaris",
            "vessel_type": "Icebreaker",
            "cruising_speed": 14.0,
            "fuel_consumption": 1.5,
            "ice_capability": "PC5",
        },
    )
    assert update.status_code == 200
    assert update.json()["cruising_speed"] == 14.0

    delete = await client.delete(f"/api/v1/vessels/{vessel_id}")
    assert delete.status_code == status.HTTP_204_NO_CONTENT

    missing = await client.get(f"/api/v1/vessels/{vessel_id}")
    assert missing.status_code == status.HTTP_404_NOT_FOUND