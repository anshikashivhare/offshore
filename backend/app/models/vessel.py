import uuid
from typing import Any, Dict, Optional

from app.models.base import Base
from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column


class Vessel(Base):
    __tablename__ = "vessels"

    vessel_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vessel_name: Mapped[str] = mapped_column(String(255), index=True)
    imo_number: Mapped[Optional[str]] = mapped_column(String(20), index=True, nullable=True)
    mmsi: Mapped[Optional[str]] = mapped_column(String(20), index=True, nullable=True)
    flag_country: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    vessel_type: Mapped[str] = mapped_column(String(100))
    max_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cruising_speed: Mapped[float] = mapped_column(Float, comment="in knots")
    ice_capability: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="ice class")
    icebreaking_capability: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    polar_operating_capability: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    length_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    beam_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    draft_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fuel_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fuel_consumption: Mapped[float] = mapped_column(Float, comment="rate of consumption")
    passenger_capacity: Mapped[Optional[int]] = mapped_column(nullable=True)
    cargo_capacity: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_updated_timestamp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verification_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    operational_limits: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
