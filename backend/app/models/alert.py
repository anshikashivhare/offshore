from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum
import uuid
from typing import Optional
from datetime import datetime
from geoalchemy2 import Geometry

from app.models.base import Base
from app.models.enums import AlertSeverity

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    alert_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity))
    location: Mapped[str] = mapped_column(Geometry('GEOMETRY', srid=4326), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    route_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("routes.route_id"), nullable=True, index=True)
    hazard_source: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="active")
    triggering_metric: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
