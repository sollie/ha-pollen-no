"""Config flow for Pollen Data integration."""
import logging
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PollenDataAPI, PollenDataAPIError, build_base_url
from .const import (
    DOMAIN,
    CONF_HOSTNAME,
    CONF_REGION,
    CONF_POLLEN_TYPES,
    DEFAULT_HOSTNAME,
    COMMON_POLLEN_TYPES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOSTNAME, default=DEFAULT_HOSTNAME): str,
    }
)


class CannotConnect(exceptions.HomeAssistantError):
    """Cannot connect to API."""


class InvalidHost(exceptions.HomeAssistantError):
    """Invalid hostname or no regions returned."""


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate hostname and return available regions."""
    try:
        build_base_url(data[CONF_HOSTNAME])
    except ValueError as err:
        raise InvalidHost from err

    session = async_get_clientsession(hass)
    api = PollenDataAPI(hostname=data[CONF_HOSTNAME], session=session)

    if not await api.test_connection():
        raise CannotConnect

    try:
        regions = await api.get_regions()
    except PollenDataAPIError as err:
        raise CannotConnect from err

    if not regions:
        raise InvalidHost

    return {"regions": regions}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Pollen Data."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.regions: list[str] = []
        self.hostname: str = ""

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Handle initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.hostname = user_input[CONF_HOSTNAME]
            try:
                info = await validate_input(self.hass, user_input)
                self.regions = info["regions"]
                return await self.async_step_region()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception:
                _LOGGER.exception("Unexpected exception in config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_region(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Handle region selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            region = user_input[CONF_REGION]

            await self.async_set_unique_id(f"{self.hostname}_{region}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Pollen Data ({region})",
                data={
                    CONF_HOSTNAME: self.hostname,
                    CONF_REGION: region,
                },
            )

        return self.async_show_form(
            step_id="region",
            data_schema=vol.Schema({vol.Required(CONF_REGION): vol.In(self.regions)}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OptionsFlowHandler":
        """Create options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for Pollen Data."""

    async def async_step_init(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(CONF_POLLEN_TYPES, [])

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Optional(CONF_POLLEN_TYPES): vol.All(
                            vol.Coerce(list),
                            [vol.In(COMMON_POLLEN_TYPES)],
                        ),
                    }
                ),
                {CONF_POLLEN_TYPES: current},
            ),
        )
