"""Sensor platform for Pollen Data."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_REGION,
    POLLEN_LEVELS,
    POLLEN_THRESHOLDS,
    POLLEN_ICONS,
    POLLEN_COLORS,
    POLLEN_NAME_MAPPING,
)
from .coordinator import PollenDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: PollenDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Wait for first data update
    await coordinator.async_config_entry_first_refresh()
    
    # Create sensors for each active pollen type
    sensors = []
    
    # Add individual pollen sensors
    for pollen_type in coordinator.available_pollen_types:
        sensors.append(
            PollenSensor(
                coordinator=coordinator,
                pollen_type=pollen_type,
                region=entry.data[CONF_REGION],
            )
        )
    
    # Add forecast sensor if available
    if coordinator.forecast_text:
        sensors.append(
            PollenForecastSensor(
                coordinator=coordinator,
                region=entry.data[CONF_REGION],
            )
        )
    
    async_add_entities(sensors, update_before_add=True)


class PollenSensor(CoordinatorEntity, SensorEntity):
    """Sensor for individual pollen types."""

    def __init__(
        self,
        coordinator: PollenDataUpdateCoordinator,
        pollen_type: str,
        region: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.pollen_type = pollen_type
        self.region = region
        
        # Get English display name for the pollen type
        display_name = POLLEN_NAME_MAPPING.get(pollen_type, pollen_type)
        
        # Entity configuration
        self._attr_name = f"Pollen {display_name.title()}"
        self._attr_unique_id = f"{DOMAIN}_{region}_{pollen_type}"
        self._attr_icon = POLLEN_ICONS.get(pollen_type, POLLEN_ICONS["default"])
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "level"

    @property
    def native_value(self) -> Optional[int]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        pollen_data = self.coordinator.data.get("pollen", {})
        return pollen_data.get(self.pollen_type, 0)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        level = self.native_value
        if level is None:
            return {}
        
        return {
            "level_name": POLLEN_LEVELS.get(level, "Unknown"),
            "level_threshold": POLLEN_THRESHOLDS.get(level, "Unknown"),
            "color": POLLEN_COLORS.get(level, "#000000"),
            "pollen_type": self.pollen_type,
            "region": self.region,
            "last_updated": self.coordinator.last_updated_time,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.pollen_type in self.coordinator.data.get("pollen", {})
        )

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.hostname, self.region)},
            "name": f"Pollen Data {self.region}",
            "manufacturer": "Pollen Data",
            "model": "Pollen Monitor",
            "sw_version": "1.0.0",
        }


class PollenForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor for pollen forecast text."""

    def __init__(
        self,
        coordinator: PollenDataUpdateCoordinator,
        region: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.region = region
        
        # Entity configuration
        self._attr_name = f"Pollen Forecast"
        self._attr_unique_id = f"{DOMAIN}_{region}_forecast"
        self._attr_icon = "mdi:weather-partly-cloudy"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("forecast", "")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        return {
            "region": self.region,
            "last_updated": self.coordinator.last_updated_time,
            "active_pollen_types": list(self.coordinator.available_pollen_types),
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.get("forecast")
        )

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.hostname, self.region)},
            "name": f"Pollen Data {self.region}",
            "manufacturer": "Pollen Data",
            "model": "Pollen Monitor",
            "sw_version": "1.0.0",
        }