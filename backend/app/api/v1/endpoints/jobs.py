import uuid
from typing import Any

from app.api import deps
from app.models.enums import JobStatus
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse
from app.worker.tasks import process_generic_job
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: JobCreate, db: AsyncSession = Depends(deps.get_db), sync: bool = False
) -> Any:
    """
    Submit a background job. If sync=True, run the job synchronously (for prototyping).
    """
    job = Job(job_type=request.job_type, metadata_info=request.metadata_info)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if sync:
        job.status = JobStatus.RUNNING
        await db.commit()
        try:
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            await db.commit()
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            await db.commit()
        await db.refresh(job)
    else:
        task = process_generic_job.delay(
            str(job.job_id), request.job_type.value, request.payload
        )
        merged_metadata = dict(job.metadata_info or {})
        merged_metadata["celery_task_id"] = task.id
        job.metadata_info = merged_metadata
        await db.commit()
        await db.refresh(job)

    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(deps.get_db)) -> Any:
    """
    Get job status.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.refresh(job)
    return JobResponse.model_validate(job)
