"""API client for Pollen Data service."""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout

from .const import (
    API_REGIONS,
    API_POLLEN,
    API_FORECAST,
    API_COMBINED,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class PollenDataAPIError(Exception):
    """Exception to indicate a general API error."""


class PollenDataAPIConnectionError(PollenDataAPIError):
    """Exception to indicate a connection error."""


class PollenDataAPITimeoutError(PollenDataAPIError):
    """Exception to indicate a timeout error."""


class PollenDataAPI:
    """API client for Pollen Data service."""

    def __init__(
        self,
        hostname: str,
        session: aiohttp.ClientSession,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the API client."""
        self.hostname = hostname.rstrip("/")
        self.session = session
        self.timeout = timeout
        self.base_url = f"http://{self.hostname}"

    async def _request(self, endpoint: str) -> Dict[str, Any]:
        """Make a request to the API."""
        url = f"{self.base_url}{endpoint}"
        _LOGGER.debug("Making request to %s", url)

        try:
            async with async_timeout.timeout(self.timeout):
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug("Response data: %s", data)
                        return data
                    else:
                        _LOGGER.error(
                            "API request failed with status %s: %s",
                            response.status,
                            await response.text(),
                        )
                        raise PollenDataAPIError(
                            f"API request failed with status {response.status}"
                        )
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout error for %s: %s", url, err)
            raise PollenDataAPITimeoutError(f"Timeout error for {url}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error for %s: %s", url, err)
            raise PollenDataAPIConnectionError(f"Connection error for {url}") from err

    async def get_regions(self) -> List[str]:
        """Get available regions."""
        try:
            data = await self._request(API_REGIONS)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "regions" in data:
                return data["regions"]
            else:
                _LOGGER.error("Unexpected regions response format: %s", data)
                return []
        except PollenDataAPIError as err:
            _LOGGER.error("Error getting regions: %s", err)
            raise

    async def get_pollen_data(self, region: str) -> Dict[str, Any]:
        """Get pollen data for a region."""
        try:
            endpoint = API_POLLEN.format(region=region)
            data = await self._request(endpoint)
            
            # Ensure we have a consistent data structure
            if not isinstance(data, dict):
                _LOGGER.error("Unexpected pollen data response format: %s", data)
                return {}
            
            # Filter out inactive pollen types (level 0)
            active_pollen = {}
            for pollen_type, level in data.items():
                if isinstance(level, (int, float)) and level > 0:
                    active_pollen[pollen_type] = int(level)
                elif isinstance(level, dict) and level.get("level", 0) > 0:
                    active_pollen[pollen_type] = int(level["level"])
            
            return active_pollen
        except PollenDataAPIError as err:
            _LOGGER.error("Error getting pollen data for %s: %s", region, err)
            raise

    async def get_forecast(self, region: str) -> Optional[str]:
        """Get forecast text for a region."""
        try:
            endpoint = API_FORECAST.format(region=region)
            data = await self._request(endpoint)
            
            if isinstance(data, str):
                return data
            elif isinstance(data, dict) and "forecast" in data:
                return data["forecast"]
            else:
                _LOGGER.debug("No forecast data available for %s", region)
                return None
        except PollenDataAPIError as err:
            _LOGGER.error("Error getting forecast for %s: %s", region, err)
            return None

    async def get_combined_data(self, region: str) -> Dict[str, Any]:
        """Get combined pollen data and forecast for a region."""
        try:
            endpoint = API_COMBINED.format(region=region)
            data = await self._request(endpoint)
            
            if not isinstance(data, dict):
                _LOGGER.error("Unexpected combined data response format: %s", data)
                return {}
            
            # Extract pollen data and filter active types
            pollen_data = data.get("pollen", {})
            active_pollen = {}
            
            for pollen_type, level in pollen_data.items():
                if isinstance(level, (int, float)) and level > 0:
                    active_pollen[pollen_type] = int(level)
                elif isinstance(level, dict) and level.get("level", 0) > 0:
                    active_pollen[pollen_type] = int(level["level"])
            
            return {
                "pollen": active_pollen,
                "forecast": data.get("forecast", ""),
                "last_updated": data.get("last_updated", ""),
            }
        except PollenDataAPIError as err:
            _LOGGER.error("Error getting combined data for %s: %s", region, err)
            raise

    async def test_connection(self) -> bool:
        """Test connection to the API."""
        try:
            await self.get_regions()
            return True
        except PollenDataAPIError:
            return False