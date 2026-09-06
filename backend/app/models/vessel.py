from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, JSON
import uuid
from typing import Optional, Dict, Any

from app.models.base import Base

class Vessel(Base):
    __tablename__ = "vessels"

    vessel_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vessel_name: Mapped[str] = mapped_column(String(255), index=True)
    vessel_type: Mapped[str] = mapped_column(String(100))
    cruising_speed: Mapped[float] = mapped_column(Float, comment="in knots")
    fuel_consumption: Mapped[float] = mapped_column(Float, comment="rate of consumption")
    ice_capability: Mapped[str] = mapped_column(String(50), comment="ice class")
    operational_limits: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
