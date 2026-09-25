import uuid
from typing import Any, List

from app.api import deps
from app.repositories.vessel import vessel as vessel_repo
from app.schemas.common import Pagination
from app.schemas.vessel import VesselCreate, VesselResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

from typing import Any, List, Optional
from app.config.config import settings

@router.get("/", response_model=Pagination[VesselResponse])
async def read_vessels(
    country: Optional[str] = None,
    name: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
) -> Any:
    """List vessels with pagination and filtering."""
    
    if getattr(settings, "DEMO_MODE", False):
        import json
        from pathlib import Path
        try:
            vessels_path = Path(__file__).resolve().parents[4] / "data" / "vessels.json"
            with vessels_path.open("r", encoding="utf-8") as f:
                all_vessels = json.load(f)
            
            # Apply simple filters
            if name:
                all_vessels = [v for v in all_vessels if name.lower() in v["vessel_name"].lower()]
            if country:
                all_vessels = [v for v in all_vessels if country.lower() in v["flag_country"].lower()]
                
            total = len(all_vessels)
            items = [VesselResponse.model_validate(v) for v in all_vessels[pagination.skip : pagination.skip + pagination.limit]]
            
            return Pagination[VesselResponse].from_qs(
                items=items,
                total=total,
                skip=pagination.skip,
                limit=pagination.limit,
                model_cls=VesselResponse,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Demo mode vessels loading failed: {e}"
            )

    try:
        db_items = await vessel_repo.get_filtered(
            db, skip=pagination.skip, limit=pagination.limit, name=name, country=country
        )
        items = [VesselResponse.model_validate(v) for v in db_items]
        total = await vessel_repo.count_filtered(db, name=name, country=country)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        ) from exc

    return Pagination[VesselResponse].from_qs(
        items=items,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        model_cls=VesselResponse,
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
    if getattr(settings, "DEMO_MODE", False):
        import json
        from pathlib import Path
        try:
            vessels_path = Path(__file__).resolve().parents[4] / "data" / "vessels.json"
            with vessels_path.open("r", encoding="utf-8") as f:
                all_vessels = json.load(f)
            
            v_id_str = str(vessel_id)
            for v in all_vessels:
                if str(v.get("vessel_id")) == v_id_str:
                    return VesselResponse.model_validate(v)
            
            # If not found by exact ID, return the first vessel as fallback in demo mode
            if all_vessels:
                return VesselResponse.model_validate(all_vessels[0])
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Demo mode vessel lookup failed: {e}"
            )

    try:
        obj = await vessel_repo.get(db, vessel_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vessel not found"
            )
        return VesselResponse.model_validate(obj)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        ) from exc


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
