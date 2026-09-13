from typing import Any

from app.models.vessel import Vessel
from app.services.routing.grid import Node


class VesselConstraintChecker:
    def is_navigable(self, node: Node, vessel: Vessel, risk_grid: Any) -> bool:
        """
        Check if a given node is navigable by the vessel based on its constraints.
        For example, a high risk cell may be blocked for vessels without sufficient ice_capability.
        """
        if isinstance(risk_grid, dict):
            key = (round(node.lat, 1), round(node.lon, 1))
            risk_entry = risk_grid.get(key, 0.0)
            if isinstance(risk_entry, dict):
                risk_val = max(risk_entry.values()) if risk_entry else 0.0
            else:
                risk_val = float(risk_entry)

            # Simple thresholding logic:
            # If composite risk is > 0.75, it's considered AVOID for all unless highly capable.
            # Here we just treat risk >= 0.9 as an absolute block.
            if risk_val >= 0.9:
                return False

            # If vessel has no ice capability, it shouldn't enter risk >= 0.5
            if not vessel.ice_capability and risk_val >= 0.5:
                return False

        return True
