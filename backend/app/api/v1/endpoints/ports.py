import json
import os
from typing import List, Optional

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from app.api import deps
from app.schemas.common import Pagination

router = APIRouter()


class Port(BaseModel):
    name: str
    country: str
    lat: float
    lon: float


# Load ports into memory on startup
PORTS_DATA = []
try:
    ports_file = os.path.join(os.path.dirname(__file__), "../../../../data/ports.json")
    with open(ports_file, "r") as f:
        PORTS_DATA = json.load(f)
except Exception as e:
    print(f"Error loading ports: {e}")


@router.get("/", response_model=Pagination[Port])
def get_ports(pagination: deps.PaginationParams = Depends()):
    """Returns the paginated list of all global ports."""
    return Pagination.from_list(PORTS_DATA, pagination.skip, pagination.limit)


@router.get("/search", response_model=Pagination[Port])
def search_ports(
    q: str = Query(..., min_length=1),
    pagination: deps.PaginationParams = Depends(),
):
    """Returns ports matching a name or country substring with pagination."""
    q_lower = q.lower()
    results = [
        p for p in PORTS_DATA 
        if q_lower in p["name"].lower() or q_lower in p["country"].lower()
    ]
    return Pagination.from_list(results, pagination.skip, pagination.limit)
