import asyncio
import sys
import logging
import json
import traceback
from pathlib import Path

# Add project root to path
_root = str(Path(__file__).resolve().parents[0])
if _root not in sys.path:
    sys.path.insert(0, _root)

from app.services.forecasting.ml_forecaster import forecaster
from app.repositories.risk import risk_cell
from app.db.session import AsyncSessionLocal
from app.schemas.environment_live import WaypointRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_integration_test():
    try:
        # Phase 2 & 3: Generate predictions via the real service
        logger.info("Triggering real ML forecaster (which calls Open-Meteo & XGBoost)...")
        predictions = await forecaster.generate_predictions([24])
        
        cells = predictions.get(24, [])
        if not cells:
            logger.error("No predictions returned!")
            return
            
        logger.info(f"Generated {len(cells)} ML predictions. First cell:")
        logger.info(json.dumps(cells[0], indent=2, default=str))
        
        # Phase 6: Push to DB so RiskEngine can read it
        logger.info("Upserting to DB...")
        async with AsyncSessionLocal() as db:
            await risk_cell.bulk_upsert_forecasts(db, cells)
            logger.info("Upsert complete.")
            
        logger.info("INTEGRATION TEST PASS")
    except Exception as e:
        logger.error(f"INTEGRATION TEST FAILED: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_integration_test())
