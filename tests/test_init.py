"""Tests for __init__.py (integration setup/unload)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.pollen_no.const import DOMAIN
from custom_components.pollen_no import async_setup_entry, async_unload_entry

from tests.conftest import (
    MOCK_HOSTNAME,
    MOCK_REGION,
    MOCK_COMBINED_DATA,
    MOCK_CONFIG_ENTRY_DATA,
)


def _make_entry(options=None):
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.domain = DOMAIN
    entry.data = MOCK_CONFIG_ENTRY_DATA.copy()
    entry.options = options or {}
    entry.async_on_unload = MagicMock()
    entry.add_update_listener = MagicMock(return_value=lambda: None)
    return entry


def _patch_coordinator(connected=True, data=None):
    coord = MagicMock()
    coord.async_test_connection = AsyncMock(return_value=connected)
    coord.async_config_entry_first_refresh = AsyncMock()
    coord.data = data or MOCK_COMBINED_DATA.copy()
    coord.last_update_success = True
    return patch(
        "custom_components.pollen_no.PollenDataUpdateCoordinator",
        return_value=coord,
    ), coord


class TestAsyncSetupEntry:
    async def test_stores_coordinator_in_hass_data(self, hass: HomeAssistant):
        patch_coord, coord = _patch_coordinator()
        entry = _make_entry()
        with patch_coord:
            with patch.object(
                hass.config_entries, "async_forward_entry_setups", AsyncMock()
            ):
                await async_setup_entry(hass, entry)
        assert hass.data[DOMAIN][entry.entry_id] is coord

    async def test_raises_not_ready_when_cannot_connect(self, hass: HomeAssistant):
        patch_coord, _ = _patch_coordinator(connected=False)
        entry = _make_entry()
        with patch_coord:
            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, entry)

    async def test_raises_not_ready_on_refresh_exception(self, hass: HomeAssistant):
        patch_coord, coord = _patch_coordinator()
        coord.async_config_entry_first_refresh = AsyncMock(
            side_effect=Exception("API down")
        )
        entry = _make_entry()
        with patch_coord:
            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, entry)

    async def test_forwards_sensor_platform(self, hass: HomeAssistant):
        patch_coord, _ = _patch_coordinator()
        entry = _make_entry()
        forward_mock = AsyncMock()
        with patch_coord:
            with patch.object(hass.config_entries, "async_forward_entry_setups", forward_mock):
                await async_setup_entry(hass, entry)
        forward_mock.assert_awaited_once()
        _, platforms = forward_mock.call_args[0]
        assert "sensor" in [p.value if hasattr(p, "value") else p for p in platforms]

    async def test_registers_update_listener(self, hass: HomeAssistant):
        patch_coord, _ = _patch_coordinator()
        entry = _make_entry()
        with patch_coord:
            with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()):
                await async_setup_entry(hass, entry)
        entry.add_update_listener.assert_called_once()


class TestAsyncUnloadEntry:
    async def _setup(self, hass: HomeAssistant):
        patch_coord, coord = _patch_coordinator()
        entry = _make_entry()
        with patch_coord:
            with patch.object(hass.config_entries, "async_forward_entry_setups", AsyncMock()):
                await async_setup_entry(hass, entry)
        return entry, coord

    async def test_removes_coordinator_from_hass_data(self, hass: HomeAssistant):
        entry, _ = await self._setup(hass)
        with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)):
            result = await async_unload_entry(hass, entry)
        assert result is True
        assert entry.entry_id not in hass.data.get(DOMAIN, {})

    async def test_keeps_data_when_unload_fails(self, hass: HomeAssistant):
        entry, _ = await self._setup(hass)
        with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=False)):
            result = await async_unload_entry(hass, entry)
        assert result is False
        assert entry.entry_id in hass.data[DOMAIN]
