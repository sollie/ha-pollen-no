"""API client for Pollen Data service."""
import asyncio
import logging
import re
from typing import Any, Optional

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

_HOSTNAME_RE = re.compile(
    r"^(https?://)?"
    r"([a-zA-Z0-9\-\.]+)"
    r"(:\d{1,5})?"
    r"$"
)


class PollenDataAPIError(Exception):
    """General API error."""


class PollenDataAPIConnectionError(PollenDataAPIError):
    """Connection error."""


class PollenDataAPITimeoutError(PollenDataAPIError):
    """Timeout error."""


def build_base_url(hostname: str) -> str:
    """Return validated base URL from user-supplied hostname string.

    Accepts:
      - bare host: localhost:8080
      - with scheme: http://localhost:8080 or https://myserver.com
    Raises ValueError on obviously invalid input.
    """
    stripped = hostname.strip().rstrip("/")
    if not stripped:
        raise ValueError("Hostname must not be empty")
    if len(stripped) > 253:
        raise ValueError("Hostname too long")

    if "://" in stripped:
        scheme, rest = stripped.split("://", 1)
        if scheme not in ("http", "https"):
            raise ValueError(f"Unsupported scheme '{scheme}'. Use http or https.")
        host_part = rest.split("/")[0]
    else:
        scheme = "http"
        host_part = stripped.split("/")[0]

    if not _HOSTNAME_RE.match(host_part if "://" not in host_part else f"{scheme}://{host_part}"):
        raise ValueError(f"Invalid hostname: {host_part!r}")

    return f"{scheme}://{host_part}"


class PollenDataAPI:
    """API client for Pollen Data service."""

    def __init__(
        self,
        hostname: str,
        session: aiohttp.ClientSession,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the API client."""
        self.base_url = build_base_url(hostname)
        self.session = session
        self.timeout = timeout

    async def _request(self, endpoint: str) -> Any:
        """Make a GET request, return parsed JSON."""
        url = f"{self.base_url}{endpoint}"
        _LOGGER.debug("Making request to %s", url)

        try:
            async with async_timeout.timeout(self.timeout):
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug("Response: %s", data)
                        return data
                    _LOGGER.error(
                        "API request failed status=%s body=%s",
                        response.status,
                        await response.text(),
                    )
                    raise PollenDataAPIError(
                        f"API request failed with status {response.status}"
                    )
        except asyncio.TimeoutError as err:
            raise PollenDataAPITimeoutError(f"Timeout for {url}") from err
        except aiohttp.ClientError as err:
            raise PollenDataAPIConnectionError(f"Connection error for {url}") from err

    async def get_regions(self) -> list[str]:
        """Get available regions."""
        data = await self._request(API_REGIONS)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "regions" in data:
            return data["regions"]
        _LOGGER.error("Unexpected regions response: %s", data)
        return []

    async def get_pollen_data(self, region: str) -> dict[str, dict[str, int]]:
        """Get pollen data for a region. Returns date-keyed dict of type->level."""
        data = await self._request(API_POLLEN.format(region=region))
        if not isinstance(data, dict):
            _LOGGER.error("Unexpected pollen data response: %s", data)
            return {}
        result: dict[str, dict[str, int]] = {}
        for date_key, day_data in data.items():
            if not isinstance(day_data, dict):
                continue
            result[date_key] = {
                pollen_type: int(level)
                for pollen_type, level in day_data.items()
                if isinstance(level, (int, float))
            }
        return result

    async def get_forecast(self, region: str) -> Optional[str]:
        """Get forecast text for a region."""
        try:
            data = await self._request(API_FORECAST.format(region=region))
        except PollenDataAPIError:
            return None
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            if region in data:
                return data[region]
            if "forecast" in data:
                return data["forecast"]
        return None

    async def get_combined_data(self, region: str) -> dict[str, Any]:
        """Get combined pollen + forecast for a region.

        Returns date-keyed pollen dict and forecast string.
        """
        data = await self._request(API_COMBINED.format(region=region))
        if not isinstance(data, dict):
            _LOGGER.error("Unexpected combined response: %s", data)
            return {}

        raw_pollen = data.get("pollen", {})
        pollen: dict[str, dict[str, int]] = {}
        for date_key, day_data in raw_pollen.items():
            if not isinstance(day_data, dict):
                continue
            pollen[date_key] = {
                pollen_type: int(level)
                for pollen_type, level in day_data.items()
                if isinstance(level, (int, float))
            }

        raw_forecast = data.get("forecast", "")
        if isinstance(raw_forecast, dict):
            forecast_text = raw_forecast.get(region, "")
        else:
            forecast_text = raw_forecast

        return {
            "pollen": pollen,
            "forecast": forecast_text,
            "last_updated": data.get("last_updated", ""),
        }

    async def test_connection(self) -> bool:
        """Test connection to the API."""
        try:
            await self.get_regions()
            return True
        except PollenDataAPIError:
            return False
