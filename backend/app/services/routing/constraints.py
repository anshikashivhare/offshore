from typing import Any

from app.models.vessel import Vessel
from app.services.routing.grid import Node


from app.services.environment.bathymetry import BathymetryService

class VesselConstraintChecker:
    def __init__(self):
        self.bathymetry = BathymetryService()
        
    def is_navigable(self, node: Node, vessel: Vessel, risk_grid: Any) -> bool:
        """
        Check if a given node is navigable by the vessel based on its constraints.
        For example, a high risk cell may be blocked for vessels without sufficient ice_capability.
        """
        if isinstance(risk_grid, dict) and risk_grid:
            key = (round(node.lat, 1), round(node.lon, 1))
            if key not in risk_grid:
                return True
            risk_entry = risk_grid.get(key)
            if isinstance(risk_entry, dict):
                risk_val = max(risk_entry.values()) if risk_entry else None
            else:
                risk_val = float(risk_entry) if risk_entry is not None else None

            if risk_val is None:
                return True

            # Simple thresholding logic:
            # If composite risk is > 0.75, it's considered AVOID for all unless highly capable.
            # Here we just treat risk >= 0.9 as an absolute block.
            if risk_val >= 0.9:
                return False

            if not vessel.ice_capability and risk_val >= 0.5:
                return False

        # Bathymetry constraint (Draft vs Depth)
        if getattr(vessel, 'draft_m', None):
            depth = self.bathymetry.get_depth_at(node.lat, node.lon)
            # Require at least 2m under keel clearance
            if depth < (vessel.draft_m + 2.0):
                return False

        return True
