import pytest
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError

from app.utils.coordinates import parse_wgs84_lon_lat
from app.models.enums import ObjectiveType
from app.schemas.route import RouteRequest


def test_parses_wgs84_coordinates_in_geojson_order():
    assert parse_wgs84_lon_lat("110.53,-66.28") == (110.53, -66.28)


@pytest.mark.parametrize(
    "value",
    ["110.53", "200,-66", "110,-91", "invalid,-66", "3031000,-2500000"],
)
def test_rejects_non_wgs84_coordinate_input(value):
    with pytest.raises(ValueError):
        parse_wgs84_lon_lat(value)


def test_route_request_enforces_the_wgs84_coordinate_contract():
    request = RouteRequest(
        origin="110.53,-66.28",
        destination="18.42,-33.92",
        vessel_id=uuid4(),
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.SAFEST,
    )
    assert request.origin == "110.53,-66.28"

    with pytest.raises(ValidationError):
        RouteRequest(
            origin="3031000,-2500000",
            destination="18.42,-33.92",
            vessel_id=uuid4(),
            departure_time=datetime.now(timezone.utc),
            objective_type=ObjectiveType.SAFEST,
        )
