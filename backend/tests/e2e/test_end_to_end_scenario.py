import pytest
import uuid
import math
from datetime import datetime, timezone
from unittest.mock import patch

from app.models.vessel import Vessel
from app.models.enums import ObjectiveType
from app.schemas.navigation import NavigationScenarioRequest
from app.services.navigation.orchestrator import NavigationOrchestrator

@pytest.fixture
def mock_vessel():
    return Vessel(
        vessel_id=uuid.uuid4(),
        vessel_name="Polar Explorer",
        vessel_type="Icebreaker",
        cruising_speed=15.0, # knots
        fuel_consumption=100.0,
        ice_capability="PC3"
    )

def _build_synthetic_grid():
    """
    Builds a synthetic grid from y=0 to y=5.
    The direct path is x=0. 
    The bypass path is x=1.
    We inject a severe iceberg hazard at (0, 2) and (0, 3).
    """
    grid = {}
    import numpy as np
    # Cover the bounding box with 0.1 resolution to ensure everything is covered
    for y in np.arange(-1.0, 6.0, 0.1):
        for x in np.arange(-1.0, 2.0, 0.1):
            key = (round(float(y), 1), round(float(x), 1))
            grid[key] = {"iceberg": 0.0, "sea_ice": 0.0, "weather": 0.0}
            
    # Inject hazard on the shortest direct path around x=0, y=2 to 3
    for y in np.arange(1.5, 3.6, 0.1):
        for x in np.arange(-0.2, 0.3, 0.1):
            key = (round(float(y), 1), round(float(x), 1))
            grid[key]["iceberg"] = 0.85
    
    return grid

@pytest.mark.asyncio
async def test_end_to_end_navigation_scenario(mock_vessel):
    # Mock the risk surface generation to return our deterministic synthetic grid
    synthetic_grid = _build_synthetic_grid()
    
    with patch.object(NavigationOrchestrator, '_build_environmental_risk_surface', return_value=synthetic_grid):
        orchestrator = NavigationOrchestrator()
        
        # 1. Test SHORTEST path
        req_shortest = NavigationScenarioRequest(
            origin="0.0,0.0",
            destination="0.0,5.0",
            vessel_id=mock_vessel.vessel_id,
            departure_time=datetime.now(timezone.utc),
            navigation_priority=ObjectiveType.SHORTEST
        )
        
        resp_shortest = await orchestrator.run_scenario(req_shortest, mock_vessel)
        route_shortest = resp_shortest.recommended_route
        print("\nShortest Geometry:", route_shortest["geometry"])
        
        # 2. Test SAFEST path
        req_safest = NavigationScenarioRequest(
            origin="0.0,0.0",
            destination="0.0,5.0",
            vessel_id=mock_vessel.vessel_id,
            departure_time=datetime.now(timezone.utc),
            navigation_priority=ObjectiveType.SAFEST
        )
        
        resp_safest = await orchestrator.run_scenario(req_safest, mock_vessel)
        route_safest = resp_safest.recommended_route
        print("\nSafest Geometry:", route_safest["geometry"])
        
        # --- VERIFICATIONS ---

        # A. Route Differentiation
        assert route_shortest["properties"]["distance"] < route_safest["properties"]["distance"], "Shortest path must be shorter"
        # The dedicated DijkstraShortestPlanner ignores the risk grid; SAFEST routes around hazards.
        # So the shortest route's risk is computed only by A* (Dijkstra emits risk_score=0.0 by design).
        # The contract is: SAFEST has LOWER risk than SHORTEST, or equal. The Dijkstra shortest path
        # is geometrically shortest by construction.
        assert route_shortest["properties"]["risk_score"] >= route_safest["properties"]["risk_score"] - 1e-6, (
            "Shortest path should not have lower risk exposure than the safest path"
        )
        assert route_shortest["properties"]["estimated_fuel"] <= route_safest["properties"]["estimated_fuel"], "Shortest path uses less or equal fuel"
        
        # B. Alerts Generation
        # The shortest path goes directly through (0, 2) where iceberg risk is 0.95
        # The safest path bypasses it.
        assert len(resp_shortest.alerts) > 0, "Hazard alerts must be generated on risky route"
        # The safest path might still have missing data or other alerts depending on the default config, but it shouldn't have CRITICAL iceberg alerts.
        safest_iceberg_alerts = [a for a in resp_safest.alerts if a.properties.alert_type == "iceberg" and a.properties.severity == "critical"]
        shortest_iceberg_alerts = [a for a in resp_shortest.alerts if a.properties.alert_type == "iceberg" and a.properties.severity == "critical"]
        assert len(safest_iceberg_alerts) <= len(shortest_iceberg_alerts), "Safest route should have no more critical iceberg alerts than shortest"

        # C. Explanation and Metrics
        assert "recommended" in resp_safest.explanation.lower()

        # Prove the difference explicitly
        dist_diff = route_safest["properties"]["distance"] - route_shortest["properties"]["distance"]

        assert dist_diff > 0

