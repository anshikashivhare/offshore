import uuid
from typing import Any, Dict, Optional

from app.models.base import Base
from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column


class Vessel(Base):
    __tablename__ = "vessels"

    vessel_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vessel_name: Mapped[str] = mapped_column(String(255), index=True)
    vessel_type: Mapped[str] = mapped_column(String(100))
    cruising_speed: Mapped[float] = mapped_column(Float, comment="in knots")
    ice_capability: Mapped[str] = mapped_column(String(50), comment="ice class")
    fuel_consumption: Mapped[float] = mapped_column(Float, comment="rate of consumption")
    operational_limits: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
