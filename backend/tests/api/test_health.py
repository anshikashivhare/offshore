import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    # api_status reflects dependency health; ok or degraded are both acceptable
    # in test environments where Redis/Postgres may be absent.
    assert data["api_status"] in {"ok", "degraded"}
    assert "database_connectivity" in data
    assert "redis_connectivity" in data
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"
