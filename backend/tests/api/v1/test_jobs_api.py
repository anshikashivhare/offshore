import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch
from app.main import app
from app.models.enums import JobType

@pytest.mark.asyncio
async def test_create_job_async():
    # Mock the celery .delay call so we don't actually need redis running
    with patch("app.worker.tasks.process_generic_job.delay") as mock_delay:
        mock_delay.return_value.id = "mock-task-id-123"
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/jobs/", json={
                "job_type": JobType.DATASET_INGESTION.value,
                "payload": {"source": "S3"},
                "metadata_info": {"version": "v1"}
            })
            
        assert response.status_code == 201
        data = response.json()
        assert data["job_type"] == JobType.DATASET_INGESTION.value
        assert data["status"] == "pending"
        assert data["metadata_info"]["celery_task_id"] == "mock-task-id-123"
        
        # Test getting the job
        job_id = data["job_id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            get_resp = await ac.get(f"/api/v1/jobs/{job_id}")
            
        assert get_resp.status_code == 200
        assert get_resp.json()["job_id"] == job_id

@pytest.mark.asyncio
async def test_create_job_sync():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/jobs/?sync=true", json={
            "job_type": JobType.RISK_GENERATION.value,
            "payload": {}
        })
        
    assert response.status_code == 201
    data = response.json()
    assert data["job_type"] == JobType.RISK_GENERATION.value
    # Sync fallback mocks completion
    assert data["status"] == "completed"
    assert data["progress"] == 100.0
