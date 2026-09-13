import uuid
from datetime import datetime
from typing import Optional

from app.models.base import Base
from app.models.enums import JobStatus, JobType
from sqlalchemy import JSON, DateTime, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    progress: Mapped[Optional[float]] = mapped_column(Float, default=0.0)

    metadata_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
