from enum import Enum

class PlanningMode(Enum):
    FORECAST_CONSTRAINED = "forecast_constrained"
    HYBRID = "hybrid"
    RESEARCH_SIMULATION = "research_simulation"
    
def get_data_provenance(eta_hours_from_start: float, forecast_horizon_days: int = 14) -> str:
    """Returns the provenance of the data based on ETA (in hours from departure)"""
    eta_days = eta_hours_from_start / 24.0
    if eta_days <= forecast_horizon_days:
        return "live_forecast"
    # For day 15+, Open-Meteo does not provide data.
    return "forecast_unavailable"
