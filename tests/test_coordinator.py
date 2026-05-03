"""Tests for coordinator.py."""
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.pollen_no.api import PollenDataAPIError
from custom_components.pollen_no.coordinator import PollenDataUpdateCoordinator

from tests.conftest import (
    MOCK_HOSTNAME,
    MOCK_REGION,
    MOCK_COMBINED_DATA,
)

TODAY = "2026-05-03"
TOMORROW = "2026-05-04"
DAY_AFTER = "2026-05-05"


def _make_coordinator(mock_api, pollen_types=None):
    entry = MagicMock()
    entry.entry_id = "test"
    hass = MagicMock()
    with patch(
        "custom_components.pollen_no.coordinator.async_get_clientsession",
        return_value=MagicMock(),
    ):
        coord = PollenDataUpdateCoordinator(
            hass=hass,
            hostname=MOCK_HOSTNAME,
            region=MOCK_REGION,
            config_entry=entry,
            pollen_types=pollen_types or [],
        )
    coord.api = mock_api
    return coord


class TestCoordinatorUpdate:
    async def test_returns_today_pollen_data(self, mock_api):
        coord = _make_coordinator(mock_api)
        with patch("custom_components.pollen_no.coordinator.date") as mock_date:
            mock_date.today.return_value = date.fromisoformat(TODAY)
            data = await coord._async_update_data()
        assert data["pollen"] == MOCK_COMBINED_DATA["pollen"][TODAY]
        assert data["region"] == MOCK_REGION

    async def test_forecast_text_extracted_from_region_dict(self, mock_api):
        coord = _make_coordinator(mock_api)
        with patch("custom_components.pollen_no.coordinator.date") as mock_date:
            mock_date.today.return_value = date.fromisoformat(TODAY)
            data = await coord._async_update_data()
        assert data["forecast"] == MOCK_COMBINED_DATA["forecast"][MOCK_REGION]

    async def test_pollen_forecast_excludes_today(self, mock_api):
        coord = _make_coordinator(mock_api)
        with patch("custom_components.pollen_no.coordinator.date") as mock_date:
            mock_date.today.return_value = date.fromisoformat(TODAY)
            data = await coord._async_update_data()
        dates = [e["date"] for e in data["pollen_forecast"]]
        assert TODAY not in dates
        assert TOMORROW in dates
        assert DAY_AFTER in dates

    async def test_api_error_raises_update_failed(self, mock_api):
        mock_api.get_combined_data = AsyncMock(side_effect=PollenDataAPIError("API down"))
        coord = _make_coordinator(mock_api)
        with pytest.raises(UpdateFailed, match="API down"):
            await coord._async_update_data()

    async def test_empty_response_raises_update_failed(self, mock_api):
        mock_api.get_combined_data = AsyncMock(return_value={})
        coord = _make_coordinator(mock_api)
        with pytest.raises(UpdateFailed, match="No data"):
            await coord._async_update_data()

    async def test_pollen_type_filter_applied(self, mock_api):
        coord = _make_coordinator(mock_api, pollen_types=["bjork"])
        with patch("custom_components.pollen_no.coordinator.date") as mock_date:
            mock_date.today.return_value = date.fromisoformat(TODAY)
            data = await coord._async_update_data()
        assert list(data["pollen"].keys()) == ["bjork"]

    async def test_filter_excludes_absent_types(self, mock_api):
        coord = _make_coordinator(mock_api, pollen_types=["nonexistent"])
        with patch("custom_components.pollen_no.coordinator.date") as mock_date:
            mock_date.today.return_value = date.fromisoformat(TODAY)
            data = await coord._async_update_data()
        assert data["pollen"] == {}

    async def test_level_zero_preserved_in_data(self, mock_api):
        mock_api.get_combined_data = AsyncMock(return_value={
            "pollen": {TODAY: {"gress": 0, "bjork": 3}},
            "forecast": {},
            "last_updated": "",
        })
        coord = _make_coordinator(mock_api)
        with patch("custom_components.pollen_no.coordinator.date") as mock_date:
            mock_date.today.return_value = date.fromisoformat(TODAY)
            data = await coord._async_update_data()
        assert data["pollen"]["gress"] == 0
        assert data["pollen"]["bjork"] == 3


class TestCoordinatorProperties:
    def test_available_pollen_types_excludes_zeros(self, mock_api):
        coord = _make_coordinator(mock_api)
        coord.data = {
            "pollen": {"bjork": 3, "gress": 0, "or": 1},
            "pollen_forecast": [],
            "forecast": "",
            "last_updated": "",
        }
        active = coord.available_pollen_types
        assert "bjork" in active
        assert "or" in active
        assert "gress" not in active

    def test_available_pollen_types_empty_when_no_data(self, mock_api):
        coord = _make_coordinator(mock_api)
        coord.data = None
        assert coord.available_pollen_types == []

    def test_pollen_data_returns_full_dict(self, mock_api):
        coord = _make_coordinator(mock_api)
        pollen = {"bjork": 3, "gress": 0}
        coord.data = {"pollen": pollen, "pollen_forecast": [], "forecast": "", "last_updated": ""}
        assert coord.pollen_data == pollen

    def test_pollen_forecast_property(self, mock_api):
        coord = _make_coordinator(mock_api)
        forecast = [{"date": TOMORROW, "levels": {"bjork": 2}}]
        coord.data = {"pollen": {}, "pollen_forecast": forecast, "forecast": "", "last_updated": ""}
        assert coord.pollen_forecast == forecast

    def test_pollen_forecast_empty_when_no_data(self, mock_api):
        coord = _make_coordinator(mock_api)
        coord.data = None
        assert coord.pollen_forecast == []

    def test_forecast_text_returns_string(self, mock_api):
        coord = _make_coordinator(mock_api)
        coord.data = {"pollen": {}, "pollen_forecast": [], "forecast": "High pollen", "last_updated": ""}
        assert coord.forecast_text == "High pollen"

    def test_last_updated_returns_string(self, mock_api):
        coord = _make_coordinator(mock_api)
        coord.data = {"pollen": {}, "pollen_forecast": [], "forecast": "", "last_updated": "2025-04-15T10:00:00Z"}
        assert coord.last_updated_time == "2025-04-15T10:00:00Z"

    def test_hostname_normalized_to_base_url(self, mock_api):
        coord = _make_coordinator(mock_api)
        assert coord.hostname == "http://localhost:8080"


class TestCoordinatorHelpers:
    async def test_test_connection_delegates_to_api(self, mock_api):
        coord = _make_coordinator(mock_api)
        result = await coord.async_test_connection()
        assert result is True
        mock_api.test_connection.assert_awaited_once()

    async def test_get_regions_returns_list(self, mock_api):
        coord = _make_coordinator(mock_api)
        regions = await coord.async_get_regions()
        assert regions == ["oslo", "bergen", "trondheim"]

    async def test_get_regions_returns_empty_on_error(self, mock_api):
        mock_api.get_regions = AsyncMock(side_effect=PollenDataAPIError("fail"))
        coord = _make_coordinator(mock_api)
        regions = await coord.async_get_regions()
        assert regions == []
