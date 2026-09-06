from fastapi import APIRouter, Query
from typing import List, Optional
import json
import os
from pydantic import BaseModel

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

@router.get("/", response_model=List[Port])
def get_ports():
    """Returns the full list of all global ports."""
    return PORTS_DATA

@router.get("/search", response_model=List[Port])
def search_ports(q: str = Query(..., min_length=1)):
    """Returns ports matching a name or country substring."""
    q_lower = q.lower()
    results = []
    for p in PORTS_DATA:
        if q_lower in p["name"].lower() or q_lower in p["country"].lower():
            results.append(p)
            if len(results) >= 50: # Limit to 50 results for search
                break
    return results
