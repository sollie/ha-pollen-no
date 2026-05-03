"""Tests for config_flow.py."""
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Prevent HA from actually setting up the integration after entry creation."""
    with patch(
        "custom_components.pollen_no.async_setup_entry",
        return_value=True,
    ):
        yield

from custom_components.pollen_no.const import (
    DOMAIN,
    CONF_HOSTNAME,
    CONF_REGION,
    CONF_POLLEN_TYPES,
)
from tests.conftest import MOCK_HOSTNAME, MOCK_REGION, MOCK_REGIONS


@contextmanager
def _patch_api(connected=True, regions=None):
    """Patch PollenDataAPI and async_get_clientsession inside config_flow."""
    if regions is None:
        regions = MOCK_REGIONS
    api = AsyncMock()
    api.test_connection = AsyncMock(return_value=connected)
    api.get_regions = AsyncMock(return_value=regions)
    with patch(
        "custom_components.pollen_no.config_flow.PollenDataAPI",
        return_value=api,
    ), patch(
        "custom_components.pollen_no.config_flow.async_get_clientsession",
        return_value=MagicMock(),
    ):
        yield api


class TestUserStep:
    async def test_shows_form_on_no_input(self, hass: HomeAssistant):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_proceeds_to_region_step_on_valid_host(self, hass: HomeAssistant):
        with _patch_api():
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_HOSTNAME: MOCK_HOSTNAME}
            )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "region"

    async def test_cannot_connect_error(self, hass: HomeAssistant):
        with _patch_api(connected=False):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_HOSTNAME: MOCK_HOSTNAME}
            )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"

    async def test_invalid_host_error_on_bad_url(self, hass: HomeAssistant):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        with patch(
            "custom_components.pollen_no.config_flow.build_base_url",
            side_effect=ValueError("bad"),
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_HOSTNAME: "ftp://bad"}
            )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_host"

    async def test_invalid_host_on_empty_regions(self, hass: HomeAssistant):
        with _patch_api(regions=[]):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_HOSTNAME: MOCK_HOSTNAME}
            )
        assert result["errors"]["base"] == "invalid_host"


class TestRegionStep:
    async def _init_to_region(self, hass: HomeAssistant):
        with _patch_api():
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_HOSTNAME: MOCK_HOSTNAME}
            )
        return result

    async def test_creates_entry_on_valid_region(self, hass: HomeAssistant):
        region_result = await self._init_to_region(hass)
        result = await hass.config_entries.flow.async_configure(
            region_result["flow_id"], {CONF_REGION: MOCK_REGION}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_HOSTNAME] == MOCK_HOSTNAME
        assert result["data"][CONF_REGION] == MOCK_REGION

    async def test_entry_title_contains_region(self, hass: HomeAssistant):
        region_result = await self._init_to_region(hass)
        result = await hass.config_entries.flow.async_configure(
            region_result["flow_id"], {CONF_REGION: MOCK_REGION}
        )
        assert MOCK_REGION in result["title"]

    async def test_duplicate_entry_aborted(self, hass: HomeAssistant):
        region_result = await self._init_to_region(hass)
        await hass.config_entries.flow.async_configure(
            region_result["flow_id"], {CONF_REGION: MOCK_REGION}
        )

        with _patch_api():
            result2 = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result2 = await hass.config_entries.flow.async_configure(
                result2["flow_id"], {CONF_HOSTNAME: MOCK_HOSTNAME}
            )
            result2 = await hass.config_entries.flow.async_configure(
                result2["flow_id"], {CONF_REGION: MOCK_REGION}
            )
        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "already_configured"


class TestOptionsFlow:
    async def _create_entry(self, hass: HomeAssistant):
        with _patch_api():
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_HOSTNAME: MOCK_HOSTNAME}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_REGION: MOCK_REGION}
            )
        return hass.config_entries.async_entries(DOMAIN)[0]

    async def test_options_flow_shows_form(self, hass: HomeAssistant):
        entry = await self._create_entry(hass)
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_flow_saves_pollen_types(self, hass: HomeAssistant):
        entry = await self._create_entry(hass)
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_POLLEN_TYPES: ["bjork", "gress"]},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_POLLEN_TYPES] == ["bjork", "gress"]

    async def test_options_flow_accepts_empty_filter(self, hass: HomeAssistant):
        entry = await self._create_entry(hass)
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
