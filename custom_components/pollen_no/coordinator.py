"""Data update coordinator for Pollen Data."""
from datetime import timedelta
import logging
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PollenDataAPI, PollenDataAPIError, build_base_url
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class PollenDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manage fetching pollen data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        hostname: str,
        region: str,
        config_entry: ConfigEntry,
        pollen_types: Optional[list[str]] = None,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize."""
        self.hostname = build_base_url(hostname)
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
            config_entry=config_entry,
            update_interval=timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and filter pollen data."""
        try:
            combined = await self.api.get_combined_data(self.region)
        except PollenDataAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        if not combined:
            raise UpdateFailed("No data received from API")

        pollen: dict[str, int] = combined.get("pollen", {})

        if self.pollen_types:
            pollen = {k: v for k, v in pollen.items() if k in self.pollen_types}

        return {
            "pollen": pollen,
            "forecast": combined.get("forecast", ""),
            "last_updated": combined.get("last_updated", ""),
            "region": self.region,
        }

    async def async_get_regions(self) -> list[str]:
        """Get available regions."""
        try:
            return await self.api.get_regions()
        except PollenDataAPIError as err:
            _LOGGER.error("Error getting regions: %s", err)
            return []

    async def async_test_connection(self) -> bool:
        """Test API connectivity."""
        return await self.api.test_connection()

    @property
    def available_pollen_types(self) -> list[str]:
        """Active pollen types (level > 0) from current data."""
        if not self.data:
            return []
        return [k for k, v in self.data.get("pollen", {}).items() if v > 0]

    @property
    def pollen_data(self) -> dict[str, int]:
        """Full pollen dict (includes level 0 entries)."""
        if not self.data:
            return {}
        return self.data["pollen"]

    @property
    def forecast_text(self) -> str:
        """Forecast string."""
        if not self.data:
            return ""
        return self.data.get("forecast", "")

    @property
    def last_updated_time(self) -> str:
        """Last updated timestamp string from API."""
        if not self.data:
            return ""
        return self.data.get("last_updated", "")
