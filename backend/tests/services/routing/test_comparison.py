import pytest
import uuid
import math
from datetime import datetime, timezone
from app.models.enums import ObjectiveType
from app.schemas.route import RouteProperties, OptimizationWeights, RouteRequest
from app.models.vessel import Vessel
from app.services.routing.comparison import RouteComparisonService

class MockRoutePlanner:
    async def plan_route(self, request: RouteRequest, vessel: Vessel, risk_grid: dict):
        if request.objective_type == ObjectiveType.SHORTEST:
            return type('MockRouteCreate', (), {
                'vessel_id': request.vessel_id,
                'origin': request.origin,
                'destination': request.destination,
                'departure_time': request.departure_time,
                'distance': 100.0,
                'eta': request.departure_time,
                'estimated_fuel': 500.0,
                'risk_score': 0.8,
                'objective_type': request.objective_type,
                'algorithm_version': 'mock',
                'geometry': 'LINESTRING(0 0, 1 1)'
            })()
        else: # e.g. SAFEST
            return type('MockRouteCreate', (), {
                'vessel_id': request.vessel_id,
                'origin': request.origin,
                'destination': request.destination,
                'departure_time': request.departure_time,
                'distance': 150.0, # longer distance
                'eta': request.departure_time,
                'estimated_fuel': 700.0, # more fuel
                'risk_score': 0.1, # much lower risk
                'objective_type': request.objective_type,
                'algorithm_version': 'mock',
                'geometry': 'LINESTRING(0 0, 1 1)'
            })()

@pytest.fixture
def comparison_service():
    return RouteComparisonService(MockRoutePlanner())

def test_generate_explanation_lower_risk(comparison_service):
    shortest = RouteProperties(
        route_id=uuid.uuid4(), vessel_id=uuid.uuid4(), origin="0,0", destination="1,1",
        departure_time=datetime.now(timezone.utc), distance=100.0, travel_time=10.0, eta=datetime.now(timezone.utc),
        estimated_fuel=500.0, risk_score=0.8, risk_exposure=8.0, objective_type=ObjectiveType.SHORTEST
    )
    
    safest = RouteProperties(
        route_id=uuid.uuid4(), vessel_id=uuid.uuid4(), origin="0,0", destination="1,1",
        departure_time=datetime.now(timezone.utc), distance=150.0, travel_time=15.0, eta=datetime.now(timezone.utc),
        estimated_fuel=700.0, risk_score=0.1, risk_exposure=1.0, objective_type=ObjectiveType.SAFEST
    )
    
    explanation = comparison_service._generate_explanation(safest, shortest, ObjectiveType.SAFEST)
    
    assert "SAFEST" in explanation
    assert "significantly reduces risk exposure" in explanation
    assert "by 7.00" in explanation
    assert "requires 200.0 additional units of fuel" in explanation

@pytest.mark.asyncio
async def test_compare_routes(comparison_service):
    vessel = Vessel(vessel_id=uuid.uuid4(), vessel_name="Test", cruising_speed=10.0, fuel_consumption=10.0)
    req = RouteRequest(
        origin="0,0",
        destination="1,1",
        vessel_id=vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.SAFEST,
        weights=OptimizationWeights()
    )
    
    response = await comparison_service.compare_routes(req, vessel, {})
    
    assert response.recommended_route.properties.objective_type == ObjectiveType.SAFEST
    assert len(response.alternatives) > 0
    
    # Assert shortest is in alternatives
    shortest_alt = next((alt for alt in response.alternatives if alt.route.properties.objective_type == ObjectiveType.SHORTEST), None)
    assert shortest_alt is not None
    assert math.isclose(shortest_alt.comparison_metrics.risk_diff, 0.7, rel_tol=1e-5) # shortest risk 0.8 - safest risk 0.1
