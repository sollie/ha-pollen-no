"""The Pollen Data integration."""
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    CONF_HOSTNAME,
    CONF_REGION,
    CONF_POLLEN_TYPES,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import PollenDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pollen Data from a config entry."""
    hostname = entry.data[CONF_HOSTNAME]
    region = entry.data[CONF_REGION]
    pollen_types = entry.options.get(CONF_POLLEN_TYPES, [])
    
    coordinator = PollenDataUpdateCoordinator(
        hass=hass,
        hostname=hostname,
        region=region,
        pollen_types=pollen_types,
        scan_interval=DEFAULT_SCAN_INTERVAL,
    )
    
    # Test connection and fetch initial data
    try:
        if not await coordinator.async_test_connection():
            raise ConfigEntryNotReady(f"Cannot connect to {hostname}")
        
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Error connecting to Pollen Data API: %s", err)
        raise ConfigEntryNotReady(f"Error connecting to API: {err}") from err
    
    # Store coordinator in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)