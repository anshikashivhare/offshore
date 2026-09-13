from abc import ABC, abstractmethod
from typing import Any

from app.models.vessel import Vessel
from app.schemas.route import RouteCreate, RouteRequest


class RoutePlanner(ABC):
    """Base class for route optimization planners."""

    @abstractmethod
    async def plan_route(
        self, request: RouteRequest, vessel: Vessel, risk_grid: Any
    ) -> RouteCreate:
        """
        Plan a route from origin to destination based on objective and constraints.

        Args:
            request: The route planning request parameters.
            vessel: The vessel profile constraints.
            risk_grid: Environmental risk data for the relevant area and time.

        Returns:
            RouteCreate schema object containing the computed route geometry and metrics.
        """
        pass
