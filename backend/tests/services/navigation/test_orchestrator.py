import pytest
import uuid
from datetime import datetime, timezone
from app.models.enums import ObjectiveType
from app.models.vessel import Vessel
from app.schemas.navigation import NavigationScenarioRequest
from app.services.navigation.orchestrator import NavigationOrchestrator

@pytest.fixture
def orchestrator():
    return NavigationOrchestrator()

@pytest.fixture
def test_vessel():
    return Vessel(
        vessel_id=uuid.uuid4(),
        vessel_name="Orchestrator Test Ship",
        vessel_type="Tanker",
        cruising_speed=12.0,
        fuel_consumption=50.0,
        ice_capability="1A"
    )

@pytest.mark.asyncio
async def test_orchestrator_run_scenario(orchestrator, test_vessel):
    req = NavigationScenarioRequest(
        origin="0.0,0.0",
        destination="0.0,2.0",
        vessel_id=test_vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        forecast_horizon=48,
        navigation_priority=ObjectiveType.SAFEST
    )
    
    response = await orchestrator.run_scenario(req, test_vessel)
    
    # Assert unified response structure
    assert response.scenario_metadata["vessel_name"] == test_vessel.vessel_name
    assert response.scenario_metadata["objective"] == ObjectiveType.SAFEST.value
    assert response.recommended_route is not None
    assert "properties" in response.recommended_route
    assert len(response.alternatives) > 0
    assert "alerts" in response.model_dump()
    assert isinstance(response.explanation, str)
    assert response.processing_metadata["status"] == "success"
    
@pytest.mark.asyncio
async def test_orchestrator_missing_vessel(orchestrator):
    req = NavigationScenarioRequest(
        origin="0.0,0.0",
        destination="0.0,2.0",
        vessel_id=uuid.uuid4(),
        departure_time=datetime.now(timezone.utc),
        forecast_horizon=48,
        navigation_priority=ObjectiveType.SAFEST
    )
    # The vessel must be provided to the orchestrator. If not, it expects one.
    # The API layer catches missing vessels, but orchestrator expects it.
    with pytest.raises(AttributeError):
        await orchestrator.run_scenario(req, None)
