from app.api.middleware import request_timeout_seconds


def test_route_api_path_receives_the_extended_deadline():
    assert request_timeout_seconds("/api/v1/routes/plan") == 60.0


def test_regular_api_path_keeps_the_standard_deadline():
    assert request_timeout_seconds("/api/v1/ports/") == 15.0
