import uuid
from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import JobStatus, JobType

class JobCreate(BaseModel):
    job_type: JobType
    payload: Dict[str, Any]
    metadata_info: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_type": "dataset_ingestion",
                "payload": {
                    "source_url": "s3://antarctic-data/modis_2026.tif"
                },
                "metadata_info": {
                    "priority": "high"
                }
            }
        }
    )

class JobResponse(BaseModel):
    job_id: uuid.UUID
    job_type: JobType
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    progress: float
    metadata_info: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "job_type": "dataset_ingestion",
                "status": "running",
                "created_at": "2026-09-03T12:00:00Z",
                "started_at": "2026-09-03T12:00:01Z",
                "progress": 45.5,
                "metadata_info": {
                    "celery_task_id": "987e6543-e21b-12d3-a456-426614174001"
                }
            }
        }
    )
