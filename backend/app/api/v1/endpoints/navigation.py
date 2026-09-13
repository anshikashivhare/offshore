from app.api import deps
from app.repositories.vessel import vessel as vessel_repo
from app.schemas.common import ErrorResponse
from app.schemas.navigation import (NavigationScenarioRequest,
                                    NavigationScenarioResponse)
from app.services.navigation.orchestrator import NavigationOrchestrator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post(
    "/plan",
    response_model=NavigationScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Plan End-to-End Navigation Scenario",
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid scenario request parameters.",
        },
        404: {"model": ErrorResponse, "description": "Specified vessel not found."},
        500: {
            "model": ErrorResponse,
            "description": "Internal error during route evaluation.",
        },
    },
)
async def plan_navigation_scenario(
    request: NavigationScenarioRequest,
    db: AsyncSession = Depends(deps.get_db),
):
    """Run the end-to-end navigation decision-support workflow.

    Steps:
    1. Load vessel capabilities.
    2. Build a risk surface from persisted ``RiskCell`` rows intersecting the
       route bbox.
    3. Run multi-objective route comparison (SHORTEST, FASTEST, SAFEST, FUEL_EFFICIENT).
    4. Persist alerts derived from the recommended route against the risk grid.
    5. Return a unified scenario payload with explanation and uncertainty.
    """
    vessel = await vessel_repo.get(db, request.vessel_id)
    if vessel is None:
        raise HTTPException(status_code=404, detail="Vessel not found")

    orchestrator = NavigationOrchestrator(db=db)
    try:
        response = await orchestrator.run_scenario(request, vessel)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal scenario failure: {exc}")
