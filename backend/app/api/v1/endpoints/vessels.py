import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.repositories.vessel import vessel as vessel_repo
from app.schemas.common import Pagination
from app.schemas.vessel import VesselCreate, VesselResponse

router = APIRouter()


@router.get("/", response_model=Pagination[VesselResponse])
async def read_vessels(
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
) -> Any:
    """List vessels with pagination."""
    items = await vessel_repo.get_multi(db, skip=pagination.skip, limit=pagination.limit)
    total = await vessel_repo.count(db)
    return Pagination[VesselResponse](
        data=[VesselResponse.model_validate(v) for v in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.post("/", response_model=VesselResponse, status_code=status.HTTP_201_CREATED)
async def create_vessel(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vessel_in: VesselCreate,
) -> Any:
    """Register a new vessel."""
    existing = await vessel_repo.get_by_name(db, vessel_name=vessel_in.vessel_name)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vessel with name '{vessel_in.vessel_name}' already exists.",
        )
    created = await vessel_repo.create(db, obj_in=vessel_in)
    return VesselResponse.model_validate(created)


@router.get("/{vessel_id}", response_model=VesselResponse)
async def read_vessel(
    vessel_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Fetch a single vessel by id."""
    obj = await vessel_repo.get(db, vessel_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found"
        )
    return VesselResponse.model_validate(obj)


@router.put("/{vessel_id}", response_model=VesselResponse)
async def update_vessel(
    vessel_id: uuid.UUID,
    vessel_in: VesselCreate,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Update a vessel."""
    obj = await vessel_repo.get(db, vessel_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found"
        )
    updated = await vessel_repo.update(db, db_obj=obj, obj_in=vessel_in)
    return VesselResponse.model_validate(updated)


@router.delete("/{vessel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vessel(
    vessel_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> None:
    """Delete a vessel."""
    obj = await vessel_repo.get(db, vessel_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found"
        )
    await vessel_repo.remove(db, id=vessel_id)