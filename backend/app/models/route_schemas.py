from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    start_row: int = Field(..., description="Start cell row index in the ice grid")
    start_col: int = Field(..., description="Start cell col index in the ice grid")
    end_row: int = Field(..., description="End cell row index in the ice grid")
    end_col: int = Field(..., description="End cell col index in the ice grid")
    origin_lat: float = Field(default=-65.0, description="Latitude of grid cell (0,0)")
    origin_lon: float = Field(default=-60.0, description="Longitude of grid cell (0,0)")
    cell_size_deg: float = Field(default=0.1, description="Degrees per grid cell")


class RoutePoint(BaseModel):
    lat: float
    lon: float


class RouteResponse(BaseModel):
    status: str
    total_cost: float | None
    path: list[RoutePoint]
    reason: str | None = None