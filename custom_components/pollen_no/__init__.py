"""The Pollen Data integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_HOSTNAME, CONF_REGION, CONF_POLLEN_TYPES, DEFAULT_SCAN_INTERVAL
from .coordinator import PollenDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pollen Data from a config entry."""
    coordinator = PollenDataUpdateCoordinator(
        hass=hass,
        hostname=entry.data[CONF_HOSTNAME],
        region=entry.data[CONF_REGION],
        pollen_types=entry.options.get(CONF_POLLEN_TYPES, []),
        scan_interval=DEFAULT_SCAN_INTERVAL,
        config_entry=entry,
    )

    try:
        if not await coordinator.async_test_connection():
            raise ConfigEntryNotReady(f"Cannot connect to {entry.data[CONF_HOSTNAME]}")
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Error connecting to API: {err}") from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
