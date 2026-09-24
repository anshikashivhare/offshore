import asyncio
import os
import sys
import numpy as np
from datetime import datetime
from pathlib import Path

_root = str(Path(__file__).resolve().parents[0] / "backend")
if _root not in sys.path:
    sys.path.insert(0, _root)

from ml.inference.seaice_predict import predict_sea_ice_concentration
from app.services.routing.cost import CostCalculator, OptimizationWeights
from app.services.routing.grid import Node
from app.schemas.route import RiskGridData

async def main():
    print("\n--- TEST A & B: CAUSAL PREDICTION AND RISK PROPAGATION ---")
    
    # 1. Fetch real Open-Meteo inputs (mocking slightly to control the input, or using the live fetcher)
    from app.services.environment.live_data import fetch_live_environment_for_waypoints
    from app.schemas.environment_live import WaypointRequest
    
    wp = WaypointRequest(lat=-65.0, lon=-60.0, eta=datetime.utcnow())
    try:
        live_env = await fetch_live_environment_for_waypoints([wp])
        env_data = live_env.waypoints[0]
        base_temp = env_data.temperature_2m if env_data.temperature_2m is not None else -10.0
        base_wind = env_data.wind_speed_10m if env_data.wind_speed_10m is not None else 5.0
        print(f"Live Environment Fetched: Temp={base_temp}C, Wind={base_wind}m/s")
    except Exception as e:
        print(f"Failed live environment fetch: {e}")
        base_temp, base_wind = -10.0, 5.0

    # Test B: Controlled Inputs
    temp_A = base_temp
    temp_B = temp_A - 15.0  # Much colder

    print(f"Input A (Real): Temp={temp_A}C")
    print(f"Input B (Controlled): Temp={temp_B}C")

    # Real Inference
    res_A = predict_sea_ice_concentration(
        latitude=-65.0, longitude=-60.0, sea_ice_concentration=0.5,
        air_temperature_c=temp_A, sea_surface_temperature_c=-1.0,
        sea_level_pressure_hpa=1000.0, wind_speed_m_s=base_wind,
        wind_u_m_s=0.0, wind_v_m_s=0.0, current_speed_m_s=0.1,
        current_u_m_s=0.0, current_v_m_s=0.0, sea_surface_height_anomaly_cm=0.0,
        forecast_horizon_hours=0, timestamp=datetime.utcnow().isoformat()
    )
    ice_A = res_A["predicted_sea_ice_concentration_clipped"]
    print(f"Prediction A (ice concentration): {ice_A:.4f}")

    res_B = predict_sea_ice_concentration(
        latitude=-65.0, longitude=-60.0, sea_ice_concentration=0.5,
        air_temperature_c=temp_B, sea_surface_temperature_c=-1.0,
        sea_level_pressure_hpa=1000.0, wind_speed_m_s=base_wind,
        wind_u_m_s=0.0, wind_v_m_s=0.0, current_speed_m_s=0.1,
        current_u_m_s=0.0, current_v_m_s=0.0, sea_surface_height_anomaly_cm=0.0,
        forecast_horizon_hours=0, timestamp=datetime.utcnow().isoformat()
    )
    ice_B = res_B["predicted_sea_ice_concentration_clipped"]
    print(f"Prediction B (ice concentration): {ice_B:.4f}")

    # Risk Calculation (Composite: Ice*0.5 + Iceberg*0.3 + Weather*0.2)
    risk_A = ice_A * 0.5
    risk_B = ice_B * 0.5
    print(f"Risk A: {risk_A:.4f}")
    print(f"Risk B: {risk_B:.4f}")

    # A* Edge Cost 
    cost_calc = CostCalculator()
    node = Node(lat=-65.0, lon=-60.0)
    
    grid_A = RiskGridData(cells={(-65.0, -60.0): risk_A}, status="KNOWN", ml_status="AVAILABLE")
    grid_B = RiskGridData(cells={(-65.0, -60.0): risk_B}, status="KNOWN", ml_status="AVAILABLE")
    
    # Cost uses risk directly inside heuristic/penalty
    risk_at_node_A = cost_calc.get_risk_at(node, grid_A.cells)
    risk_at_node_B = cost_calc.get_risk_at(node, grid_B.cells)
    
    print(f"A* Node Risk Retrieval A: {risk_at_node_A}")
    print(f"A* Node Risk Retrieval B: {risk_at_node_B}")
    
    if risk_at_node_A != risk_at_node_B:
        print("PASS: Causal Prediction changes A* Node Risk properly.\n")
    else:
        print("FAIL: Risk did not change.\n")
        
if __name__ == "__main__":
    asyncio.run(main())
