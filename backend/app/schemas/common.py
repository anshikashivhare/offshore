from typing import Any, Generic, List, Optional, TypeVar, Dict
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")

class Pagination(BaseModel, Generic[T]):
    data: List[T]
    total: int
    skip: int
    limit: int

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[List[Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid coordinates provided",
                    "details": ["Latitude must be between -90 and 90"]
                }
            }
        }
    )

class GeoJSONGeometry(BaseModel):
    type: str = Field(..., description="GeoJSON geometry type (e.g., Point, LineString, Polygon)")
    coordinates: Any = Field(..., description="Array of coordinates in EPSG:4326 [longitude, latitude] format")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Point",
                "coordinates": [-60.1, -65.2]
            }
        }
    )

class GeoJSONFeature(BaseModel, Generic[T]):
    type: str = Field("Feature", description="Literal 'Feature'")
    geometry: GeoJSONGeometry = Field(..., description="The spatial geometry of the feature")
    properties: T = Field(..., description="The properties associated with this feature")

class GeoJSONFeatureCollection(BaseModel, Generic[T]):
    type: str = Field("FeatureCollection", description="Literal 'FeatureCollection'")
    features: List[GeoJSONFeature[T]] = Field(..., description="List of GeoJSON Features")
    total: Optional[int] = Field(None, description="Total number of features matching the query (for pagination)")
    skip: Optional[int] = Field(None, description="Number of skipped features (for pagination)")
    limit: Optional[int] = Field(None, description="Limit applied to the features (for pagination)")
