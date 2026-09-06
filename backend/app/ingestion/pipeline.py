"""
Reliability-aware ingestion pipeline.

Wraps the abstract pipeline steps with concrete failure handling for:
  * Missing datasets (raises DatasetUnavailable)
  * Failed ingestion (raises IngestionFailure)
  * Unavailable external data source (raises DatasetUnavailable)
  * Low-confidence / partial results (annotated on the returned payload)
"""

import logging
from datetime import datetime
from typing import Any, Optional

from app.core.config import settings
from app.ingestion.interfaces import (
    DataFetcher,
    DataNormalizer,
    DataSource,
    DataValidator,
    SpatialAligner,
    TemporalAligner,
)
from app.ingestion.utils.reliability import (
    DatasetUnavailable,
    IngestionFailure,
    safe_call,
)

logger = logging.getLogger("ingestion")


class IngestionPipeline:
    """Orchestrates the data ingestion process."""

    def __init__(
        self,
        source: DataSource,
        fetcher: DataFetcher,
        validator: DataValidator,
        normalizer: DataNormalizer,
        spatial_aligner: SpatialAligner,
        temporal_aligner: TemporalAligner,
    ):
        self.source = source
        self.fetcher = fetcher
        self.validator = validator
        self.normalizer = normalizer
        self.spatial_aligner = spatial_aligner
        self.temporal_aligner = temporal_aligner

    async def run(
        self,
        bbox: Optional[tuple] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **fetch_kwargs,
    ) -> Any:
        """
        Executes the ingestion pipeline.

        Returns the processed and aligned dataset ready for persistence.
        The returned value is always a dict; if the source was unavailable,
        the dict contains ``{"status": "unavailable", "source": name}`` so
        downstream consumers can react gracefully.
        """
        logger.info("Starting ingestion pipeline for source: %s", self.source.name)

        try:
            logger.info("Fetching data from %s...", self.source.name)
            raw_data = await safe_call(
                self.fetcher.fetch,
                fallback=None,
                error_code="FETCH_FAILED",
                **fetch_kwargs,
            )
            if raw_data is None:
                logger.warning("Source %s returned no data", self.source.name)
                return {
                    "source": self.source.name,
                    "status": "unavailable",
                    "missing_data": True,
                }

            logger.info("Validating metadata and completeness...")
            try:
                self.validator.validate(raw_data)
            except Exception as exc:
                logger.warning(
                    "Validation failed for %s: %s", self.source.name, exc
                )
                raise IngestionFailure(f"validation failed: {exc}") from exc

            logger.info("Normalizing units and handling missing values...")
            normalized_data = safe_call(
                self.normalizer.normalize,
                raw_data,
                fallback=None,
                error_code="NORMALIZE_FAILED",
            )
            if normalized_data is None:
                raise IngestionFailure("normalization returned None")

            logger.info("Aligning spatial data (CRS conversion, clipping)...")
            spatial_aligned = safe_call(
                self.spatial_aligner.align_spatial,
                normalized_data,
                bbox,
                fallback=normalized_data,
                error_code="SPATIAL_ALIGN_FAILED",
            )

            logger.info("Aligning temporal data (Timezone UTC, filtering)...")
            final_data = safe_call(
                self.temporal_aligner.align_temporal,
                spatial_aligned,
                start_time,
                end_time,
                fallback=spatial_aligned,
                error_code="TEMPORAL_ALIGN_FAILED",
            )

            confidence = (
                final_data.get("confidence")
                if isinstance(final_data, dict)
                else None
            )
            if confidence is not None and confidence < settings.RISK_CONFIDENCE_THRESHOLD:
                logger.warning(
                    "Source %s produced low-confidence output: %.3f < %.3f",
                    self.source.name,
                    confidence,
                    settings.RISK_CONFIDENCE_THRESHOLD,
                )
                if isinstance(final_data, dict):
                    final_data["low_confidence"] = True

            logger.info(
                "Successfully processed dataset from %s (confidence=%s)",
                self.source.name,
                confidence,
            )
            return final_data

        except DatasetUnavailable:
            raise
        except IngestionFailure:
            raise
        except Exception as exc:
            logger.error(
                "Pipeline failure for %s: %s", self.source.name, exc, exc_info=True
            )
            raise IngestionFailure(str(exc)) from exc
