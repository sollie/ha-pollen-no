"""Config flow for Pollen Data integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PollenDataAPI, PollenDataAPIError
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
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is invalid host."""


async def validate_input(hass: core.HomeAssistant, data: dict) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = PollenDataAPI(hostname=data[CONF_HOSTNAME], session=session)
    
    # Test connection
    if not await api.test_connection():
        raise CannotConnect
    
    # Get available regions
    try:
        regions = await api.get_regions()
    except PollenDataAPIError as err:
        _LOGGER.error("Error getting regions: %s", err)
        raise CannotConnect from err
    
    if not regions:
        raise InvalidHost
    
    return {"regions": regions}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pollen Data."""

    VERSION = 1

    def __init__(self):
        """Initialize config flow."""
        self.regions = []
        self.hostname = ""

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
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
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_region(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the region step."""
        errors = {}
        
        if user_input is not None:
            region = user_input[CONF_REGION]
            
            # Create entry with basic configuration
            title = f"Pollen Data ({region})"
            data = {
                CONF_HOSTNAME: self.hostname,
                CONF_REGION: region,
            }
            
            return self.async_create_entry(title=title, data=data)

        # Create region selection schema
        region_schema = vol.Schema(
            {
                vol.Required(CONF_REGION): vol.In(self.regions),
            }
        )

        return self.async_show_form(
            step_id="region",
            data_schema=region_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OptionsFlowHandler":
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Pollen Data."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options
        current_pollen_types = self.config_entry.options.get(CONF_POLLEN_TYPES, [])
        
        # Create options schema
        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_POLLEN_TYPES,
                    default=current_pollen_types,
                ): vol.All(
                    vol.Coerce(list),
                    [vol.In(COMMON_POLLEN_TYPES)],
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )