def calculate_risk(sea_ice, iceberg, weather, ocean):
    """Return a normalized prototype risk score between 0 and 100."""
    weights = {
        "sea_ice": 0.35,
        "iceberg": 0.35,
        "weather": 0.15,
        "ocean": 0.15,
    }

    score = (
        sea_ice * weights["sea_ice"]
        + iceberg * weights["iceberg"]
        + weather * weights["weather"]
        + ocean * weights["ocean"]
    )
    return max(0, min(100, round(score, 2)))


def risk_level(score):
    if score < 25:
        return "low"
    if score < 50:
        return "moderate"
    if score < 75:
        return "high"
    return "critical"
