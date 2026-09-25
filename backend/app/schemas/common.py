from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Pagination(BaseModel, Generic[T]):
    data: List[T]
    items: Optional[List[T]] = None
    total: int
    skip: int
    limit: int

    @classmethod
    def from_list(cls, items: List[T], skip: int, limit: int) -> "Pagination[T]":
        """Creates a paginated response directly from an in-memory list."""
        sliced = items[skip : skip + limit]
        return cls(
            data=sliced,
            items=sliced,
            total=len(items),
            skip=skip,
            limit=limit,
        )

    @classmethod
    def from_qs(cls, items: List[Any], total: int, skip: int, limit: int, model_cls=None) -> "Pagination[T]":
        """Creates a paginated response from an already sliced query result."""
        data = [model_cls.model_validate(v) for v in items] if model_cls else items
        return cls(
            data=data,
            items=data,
            total=total,
            skip=skip,
            limit=limit,
        )

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
                    "details": ["Latitude must be between -90 and 90"],
                }
            }
        }
    )


class GeoJSONGeometry(BaseModel):
    type: str = Field(
        ..., description="GeoJSON geometry type (e.g., Point, LineString, Polygon)"
    )
    coordinates: Any = Field(
        ...,
        description="Array of coordinates in EPSG:4326 [longitude, latitude] format",
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"type": "Point", "coordinates": [-60.1, -65.2]}}
    )


class GeoJSONFeature(BaseModel, Generic[T]):
    type: str = Field("Feature", description="Literal 'Feature'")
    geometry: GeoJSONGeometry = Field(
        ..., description="The spatial geometry of the feature"
    )
    properties: T = Field(
        ..., description="The properties associated with this feature"
    )


class GeoJSONFeatureCollection(BaseModel, Generic[T]):
    type: str = Field("FeatureCollection", description="Literal 'FeatureCollection'")
    features: List[GeoJSONFeature[T]] = Field(
        ..., description="List of GeoJSON Features"
    )
    total: Optional[int] = Field(
        None, description="Total number of features matching the query (for pagination)"
    )
    skip: Optional[int] = Field(
        None, description="Number of skipped features (for pagination)"
    )
    limit: Optional[int] = Field(
        None, description="Limit applied to the features (for pagination)"
    )

    @classmethod
    def from_list(cls, items: List[Any], skip: int, limit: int) -> "GeoJSONFeatureCollection[T]":
        """Creates a paginated GeoJSON feature collection directly from an in-memory list."""
        return cls(
            features=items[skip : skip + limit],
            total=len(items),
            skip=skip,
            limit=limit,
        )

    @classmethod
    def from_qs(cls, features: List[Any], total: int, skip: int, limit: int) -> "GeoJSONFeatureCollection[T]":
        """Creates a paginated GeoJSON feature collection from an already sliced query result."""
        return cls(
            features=features,
            total=total,
            skip=skip,
            limit=limit,
        )
