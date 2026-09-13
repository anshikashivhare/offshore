from abc import ABC, abstractmethod
from typing import Any, Dict


class SeaIceForecaster(ABC):
    """
    Abstract Base Class for Sea Ice Forecasting Models.
    Allows for swapping in different architectures (e.g., Persistence, CNN, Transformer).
    """

    @abstractmethod
    async def predict(self, inputs: Any, horizon: int, region: Dict[str, float]) -> Any:
        """
        Generate a forecast given historical inputs for a specific horizon and region.

        Args:
            inputs: Environmental features (historical sea ice, weather, etc.)
            horizon: Forecast horizon (e.g., number of days)
            region: Dictionary containing spatial bounds (min_lon, min_lat, max_lon, max_lat)

        Returns:
            ForecastResult (or dict matching the schema)
        """
        pass

    @abstractmethod
    def validate_input(self, inputs: Any) -> bool:
        """
        Validates that the provided inputs match the model's expectations
        (e.g., dimensions, feature channels).
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns model metadata, such as version, architecture, and expected inputs.
        """
        pass
