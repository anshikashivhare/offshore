import logging
import time
from typing import Any, Dict

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# To properly update DB records, tasks would need an async or sync session maker.
# For simplicity in this architecture skeleton, we simulate the workload.


@celery_app.task(bind=True, max_retries=3, name="process_generic_job")
def process_generic_job(self, job_id: str, job_type: str, payload: Dict[str, Any]):
    """
    A generic task processor that delegates to specific logic based on job_type.
    """
    logger.info(f"Starting async job {job_id} of type {job_type}")

    try:
        # Simulate updating DB to RUNNING
        self.update_state(state="RUNNING", meta={"progress": 0.0})

        # Dispatch to specific processors
        if job_type == "dataset_ingestion":
            _process_dataset_ingestion(self, payload)
        elif job_type == "route_generation":
            _process_route_generation(self, payload)
        elif job_type == "risk_generation":
            _process_risk_generation(self, payload)
        else:
            # Fallback mock for other types
            for i in range(5):
                time.sleep(1)  # simulate work
                self.update_state(state="RUNNING", meta={"progress": (i + 1) * 20.0})

        logger.info(f"Completed job {job_id}")
        return {"status": "completed", "job_id": job_id}

    except Exception as exc:
        logger.error(f"Job {job_id} failed: {str(exc)}")
        # In a real app, update DB record to FAILED here.
        # We raise retry if it's a transient issue.
        raise self.retry(exc=exc, countdown=10)


def _process_dataset_ingestion(task, payload):
    task.update_state(state="RUNNING", meta={"progress": 10.0})
    time.sleep(2)
    task.update_state(state="RUNNING", meta={"progress": 50.0})
    time.sleep(2)
    task.update_state(state="RUNNING", meta={"progress": 100.0})


def _process_route_generation(task, payload):
    # E.g. trigger the NavigationOrchestrator for a huge batch
    time.sleep(3)
    task.update_state(state="RUNNING", meta={"progress": 100.0})


def _process_risk_generation(task, payload):
    time.sleep(1)
    task.update_state(state="RUNNING", meta={"progress": 100.0})


@celery_app.task(bind=True, max_retries=3, name="update_ml_risk_forecast")
def update_ml_risk_forecast(self):
    """
    Periodically updates risk_cells with ML forecasts for various horizons.
    """
    logger.info("Starting ML risk forecast update...")
    try:
        from app.services.forecasting.ml_forecaster import forecaster
        from app.repositories.risk import risk_cell
        from app.db.session import AsyncSessionLocal
        import asyncio

        # Run async function using asyncio
        async def run_forecast():
            horizons = [24, 48, 72, 168]
            predictions = await forecaster.generate_predictions(horizons)
            
            total_upserted = 0
            async with AsyncSessionLocal() as db:
                for horizon, cells in predictions.items():
                    logger.info(f"Upserting {len(cells)} forecast cells for horizon {horizon}h")
                    await risk_cell.bulk_upsert_forecasts(db, cells)
                    total_upserted += len(cells)
            return total_upserted

        loop = asyncio.get_event_loop()
        total_upserted = loop.run_until_complete(run_forecast())
                
        logger.info(f"Completed ML risk forecast update. Upserted {total_upserted} cells.")
        return {"status": "completed", "upserted": total_upserted}
            
    except Exception as exc:
        logger.error(f"Failed to update ML risk forecast: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
