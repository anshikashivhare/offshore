import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.session import AsyncSessionLocal
from app.repositories.iceberg import iceberg as iceberg_repo
from app.schemas.forecast import ForecastRequest
from app.schemas.route import RouteRequest
from app.services.forecasting.baseline import BaselinePersistenceForecaster
from app.services.icebergs.tracking import IcebergTracker
from app.services.icebergs.trajectory import PhysicsBasedTrajectoryPredictor
from app.ws.connection_manager import manager

# Reusing HTTP endpoint logic for route risk grid and planning
from app.api.v1.endpoints.routes import _build_risk_grid, astar_planner, shortest_planner
from app.repositories.vessel import vessel as vessel_repo

logger = logging.getLogger(__name__)

router = APIRouter()

# Note: In a production environment, these periodic polling background loops should be 
# replaced by a pub/sub event bus (e.g., Redis PubSub) where "new data loaded" events 
# trigger pushes to connected clients instead of polling the DB.


# ----------------- ICEBERG -----------------

async def iceberg_update_loop(websocket: WebSocket, iceberg_id: uuid.UUID):
    """
    Periodically checks the iceberg trajectory and sends updates if changed.
    """
    last_trajectory = None
    while True:
        try:
            await asyncio.sleep(10)
            
            async with AsyncSessionLocal() as db:
                iceberg = await iceberg_repo.get(db, iceberg_id)
                if not iceberg:
                    continue
                
                tracker = IcebergTracker(db)
                historical_track = await tracker.build_track(iceberg_id)
                
                predictor = PhysicsBasedTrajectoryPredictor(db)
                predictions = await predictor.predict_trajectory(
                    iceberg_id=iceberg_id,
                    historical_track=historical_track,
                    environmental_conditions={},
                    horizon_hours=24,
                    start_time=datetime.now(timezone.utc),
                )
                
                # Compare to last trajectory to avoid spamming
                current_trajectory = [p.model_dump() for p in predictions]
                if current_trajectory != last_trajectory:
                    last_trajectory = current_trajectory
                    
                    message = {
                        "type": "trajectory_update",
                        "payload": {
                            "type": "FeatureCollection",
                            "features": current_trajectory,
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await manager.send_personal_message(message, websocket)
                    
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error in iceberg update loop for %s: %s", iceberg_id, e)


@router.websocket("/iceberg/{iceberg_id}")
async def ws_iceberg(websocket: WebSocket, iceberg_id: uuid.UUID):
    channel = f"iceberg_{iceberg_id}"
    await manager.connect(websocket, channel)
    
    update_task = None
    try:
        # Initial push
        async with AsyncSessionLocal() as db:
            iceberg = await iceberg_repo.get(db, iceberg_id)
            if not iceberg:
                await manager.send_personal_message({
                    "type": "error",
                    "payload": {"message": "Iceberg not found"},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, websocket)
            else:
                tracker = IcebergTracker(db)
                historical_track = await tracker.build_track(iceberg_id)
                
                predictor = PhysicsBasedTrajectoryPredictor(db)
                predictions = await predictor.predict_trajectory(
                    iceberg_id=iceberg_id,
                    historical_track=historical_track,
                    environmental_conditions={},
                    horizon_hours=24,
                    start_time=datetime.now(timezone.utc),
                )
                message = {
                    "type": "trajectory_update",
                    "payload": {
                        "type": "FeatureCollection",
                        "features": [p.model_dump() for p in predictions],
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_personal_message(message, websocket)
        
        # Start background loop
        update_task = asyncio.create_task(iceberg_update_loop(websocket, iceberg_id))
        
        # Keep connection open and wait for disconnect
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    finally:
        if update_task:
            update_task.cancel()


# ----------------- SEA-ICE -----------------

async def seaice_update_loop(websocket: WebSocket, lat: float, lon: float):
    """
    Periodically checks the seaice forecast and sends updates if changed.
    """
    last_forecast = None
    # Standard region around the requested coordinate
    request = ForecastRequest(
        region={"type": "Polygon", "coordinates": [[[lon-1, lat-1], [lon+1, lat-1], [lon+1, lat+1], [lon-1, lat+1], [lon-1, lat-1]]]},
        horizon_days=3
    )
    
    while True:
        try:
            await asyncio.sleep(10)
            
            async with AsyncSessionLocal() as db:
                forecaster = BaselinePersistenceForecaster(db=db)
                forecaster.validate_input(request)
                result = await forecaster.predict(
                    inputs=request,
                    horizon=request.horizon_days,
                    region=request.region,
                )
                
                current_forecast = result.model_dump()
                if current_forecast != last_forecast:
                    last_forecast = current_forecast
                    
                    message = {
                        "type": "forecast_update",
                        "payload": current_forecast,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await manager.send_personal_message(message, websocket)
                    
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error in seaice update loop: %s", e)


@router.websocket("/seaice/{lat}/{lon}")
async def ws_seaice(websocket: WebSocket, lat: float, lon: float):
    channel = f"seaice_{lat}_{lon}"
    await manager.connect(websocket, channel)
    
    update_task = None
    try:
        # Initial push
        request = ForecastRequest(
            region={"type": "Polygon", "coordinates": [[[lon-1, lat-1], [lon+1, lat-1], [lon+1, lat+1], [lon-1, lat+1], [lon-1, lat-1]]]},
            horizon_days=3
        )
        async with AsyncSessionLocal() as db:
            forecaster = BaselinePersistenceForecaster(db=db)
            forecaster.validate_input(request)
            result = await forecaster.predict(
                inputs=request,
                horizon=request.horizon_days,
                region=request.region,
            )
            message = {
                "type": "forecast_update",
                "payload": result.model_dump(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await manager.send_personal_message(message, websocket)
        
        # Start background loop
        update_task = asyncio.create_task(seaice_update_loop(websocket, lat, lon))
        
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    finally:
        if update_task:
            update_task.cancel()


# ----------------- ROUTE -----------------

async def route_update_loop(websocket: WebSocket, request: RouteRequest):
    """
    Periodically checks the risk grid and re-plans the route if changed.
    """
    last_route = None
    
    while True:
        try:
            await asyncio.sleep(10)
            
            async with AsyncSessionLocal() as db:
                vessel = await vessel_repo.get(db, request.vessel_id)
                if not vessel:
                    continue
                
                risk_grid = await _build_risk_grid(db, request)
                
                try:
                    if request.objective_type.value == "shortest":
                        route_create = await shortest_planner.plan_route(request, vessel, risk_grid)
                    else:
                        route_create = await astar_planner.plan_route(request, vessel, risk_grid)
                        
                    current_route = route_create.model_dump()
                    if current_route != last_route:
                        last_route = current_route
                        
                        message = {
                            "type": "route_update",
                            "payload": current_route,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await manager.send_personal_message(message, websocket)
                except Exception as eval_exc:
                    logger.error("Error evaluating route in background task: %s", eval_exc)
                    
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error in route update loop: %s", e)


@router.websocket("/route")
async def ws_route(websocket: WebSocket):
    channel = "route"
    await manager.connect(websocket, channel)
    
    update_task = None
    try:
        while True:
            data = await websocket.receive_json()
            
            # The client sends a JSON message representing a RouteRequest
            try:
                request = RouteRequest(**data)
                
                async with AsyncSessionLocal() as db:
                    vessel = await vessel_repo.get(db, request.vessel_id)
                    if not vessel:
                        await manager.send_personal_message({
                            "type": "error",
                            "payload": {"message": "Vessel not found"},
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }, websocket)
                        continue
                    
                    risk_grid = await _build_risk_grid(db, request)
                    
                    if request.objective_type.value == "shortest":
                        route_create = await shortest_planner.plan_route(request, vessel, risk_grid)
                    else:
                        route_create = await astar_planner.plan_route(request, vessel, risk_grid)
                        
                    message = {
                        "type": "route_update",
                        "payload": route_create.model_dump(),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await manager.send_personal_message(message, websocket)
                    
                    # Cancel any existing loop for this connection
                    if update_task:
                        update_task.cancel()
                    update_task = asyncio.create_task(route_update_loop(websocket, request))

            except Exception as exc:
                await manager.send_personal_message({
                    "type": "error",
                    "payload": {"message": str(exc)},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    finally:
        if update_task:
            update_task.cancel()
