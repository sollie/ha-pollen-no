"""Data update coordinator for Pollen Data."""
from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PollenDataAPI, PollenDataAPIError
from .const import (
    DOMAIN,
    CONF_HOSTNAME,
    CONF_REGION,
    CONF_POLLEN_TYPES,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class PollenDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        hostname: str,
        region: str,
        pollen_types: Optional[List[str]] = None,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize."""
        self.hostname = hostname
        self.region = region
        self.pollen_types = pollen_types or []
        self.api = PollenDataAPI(
            hostname=hostname,
            session=async_get_clientsession(hass),
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            # Get combined data (pollen data + forecast)
            combined_data = await self.api.get_combined_data(self.region)
            
            if not combined_data:
                raise UpdateFailed("No data received from API")
            
            pollen_data = combined_data.get("pollen", {})
            
            # Filter by specific pollen types if configured
            if self.pollen_types:
                filtered_pollen = {}
                for pollen_type in self.pollen_types:
                    if pollen_type in pollen_data:
                        filtered_pollen[pollen_type] = pollen_data[pollen_type]
                pollen_data = filtered_pollen
            
            # Only include active pollen types (level > 0)
            active_pollen = {
                pollen_type: level
                for pollen_type, level in pollen_data.items()
                if level > 0
            }
            
            result = {
                "pollen": active_pollen,
                "forecast": combined_data.get("forecast", ""),
                "last_updated": combined_data.get("last_updated", ""),
                "region": self.region,
            }
            
            _LOGGER.debug("Updated pollen data: %s", result)
            return result
            
        except PollenDataAPIError as err:
            _LOGGER.error("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error updating data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_get_regions(self) -> List[str]:
        """Get available regions from API."""
        try:
            return await self.api.get_regions()
        except PollenDataAPIError as err:
            _LOGGER.error("Error getting regions: %s", err)
            return []

    async def async_test_connection(self) -> bool:
        """Test connection to the API."""
        return await self.api.test_connection()

    @property
    def available_pollen_types(self) -> List[str]:
        """Get list of available pollen types from current data."""
        if not self.data or "pollen" not in self.data:
            return []
        return list(self.data["pollen"].keys())

    @property
    def pollen_data(self) -> Dict[str, int]:
        """Get current pollen data."""
        if not self.data or "pollen" not in self.data:
            return {}
        return self.data["pollen"]

    @property
    def forecast_text(self) -> str:
        """Get forecast text."""
        if not self.data or "forecast" not in self.data:
            return ""
        return self.data["forecast"]

    @property
    def last_updated_time(self) -> str:
        """Get last updated time."""
        if not self.data or "last_updated" not in self.data:
            return ""
        return self.data["last_updated"]