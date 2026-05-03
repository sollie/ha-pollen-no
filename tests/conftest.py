"""Test fixtures shared across all test modules."""
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.pollen_no.const import (
    DOMAIN,
    CONF_HOSTNAME,
    CONF_REGION,
    CONF_POLLEN_TYPES,
)

MOCK_HOSTNAME = "http://localhost:8080"
MOCK_REGION = "oslo"
MOCK_REGIONS = ["oslo", "bergen", "trondheim"]

MOCK_POLLEN_DATA = {
    "2026-05-03": {
        "or": 2,
        "hassel": 1,
        "salix": 0,
        "bjork": 3,
        "gress": 0,
        "burot": 0,
    },
    "2026-05-04": {
        "or": 1,
        "hassel": 0,
        "salix": 0,
        "bjork": 2,
        "gress": 0,
        "burot": 0,
    },
    "2026-05-05": {
        "or": 1,
        "hassel": 0,
        "salix": 0,
        "bjork": 2,
        "gress": 0,
        "burot": 0,
    },
}

MOCK_COMBINED_DATA = {
    "pollen": MOCK_POLLEN_DATA,
    "forecast": {"oslo": "Moderate birch pollen expected this week."},
    "last_updated": "2025-04-15T10:00:00Z",
}

MOCK_FORECAST_TEXT = "Moderate birch pollen expected this week."

MOCK_CONFIG_ENTRY_DATA = {
    CONF_HOSTNAME: MOCK_HOSTNAME,
    CONF_REGION: MOCK_REGION,
}

MOCK_CONFIG_ENTRY_OPTIONS: dict = {}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_api():
    """Return a mock PollenDataAPI instance."""
    api = AsyncMock()
    api.test_connection = AsyncMock(return_value=True)
    api.get_regions = AsyncMock(return_value=MOCK_REGIONS)
    api.get_combined_data = AsyncMock(return_value=MOCK_COMBINED_DATA)
    api.get_pollen_data = AsyncMock(return_value=MOCK_POLLEN_DATA)
    api.get_forecast = AsyncMock(return_value=MOCK_FORECAST_TEXT)
    return api
