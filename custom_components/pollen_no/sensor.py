"""Sensor platform for Pollen Data."""
import logging
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_REGION,
    COMMON_POLLEN_TYPES,
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
    """Set up sensor platform."""
    coordinator: PollenDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    region = entry.data[CONF_REGION]

    sensors: list[SensorEntity] = [
        PollenSensor(coordinator=coordinator, pollen_type=pt, region=region)
        for pt in COMMON_POLLEN_TYPES
    ]
    sensors.append(PollenForecastSensor(coordinator=coordinator, region=region))

    async_add_entities(sensors)


class PollenSensor(CoordinatorEntity[PollenDataUpdateCoordinator], SensorEntity):
    """Sensor for one pollen type. State = 0 when not active."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PollenDataUpdateCoordinator,
        pollen_type: str,
        region: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.pollen_type = pollen_type
        self.region = region

        display_name = POLLEN_NAME_MAPPING.get(pollen_type, pollen_type)
        self._attr_name = display_name.title()
        self._attr_unique_id = f"{DOMAIN}_{region}_{pollen_type}"
        self._attr_icon = POLLEN_ICONS.get(pollen_type, POLLEN_ICONS["default"])
        self._attr_native_unit_of_measurement = "level"

    @property
    def native_value(self) -> int:
        """Return pollen level (0 when no data or not active)."""
        if not self.coordinator.data:
            return 0
        return self.coordinator.data.get("pollen", {}).get(self.pollen_type, 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes."""
        level = self.native_value
        forecast = [
            {"date": entry["date"], "level": entry["levels"].get(self.pollen_type, 0)}
            for entry in self.coordinator.pollen_forecast
        ]
        return {
            "level_name": POLLEN_LEVELS.get(level, "Unknown"),
            "level_threshold": POLLEN_THRESHOLDS.get(level, "Unknown"),
            "color": POLLEN_COLORS.get(level, "#000000"),
            "pollen_type": self.pollen_type,
            "region": self.region,
            "forecast": forecast,
            "last_updated": self.coordinator.last_updated_time,
        }

    @property
    def available(self) -> bool:
        """Available when coordinator last update succeeded."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.hostname, self.region)},
            "name": f"Pollen Data {self.region}",
            "manufacturer": "Pollen Data",
            "model": "Pollen Monitor",
        }


class PollenForecastSensor(CoordinatorEntity[PollenDataUpdateCoordinator], SensorEntity):
    """Sensor for pollen forecast text."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(
        self,
        coordinator: PollenDataUpdateCoordinator,
        region: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.region = region
        self._attr_name = "Forecast"
        self._attr_unique_id = f"{DOMAIN}_{region}_forecast"

    @property
    def native_value(self) -> Optional[str]:
        """Return forecast text."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("forecast") or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes."""
        return {
            "region": self.region,
            "last_updated": self.coordinator.last_updated_time,
            "active_pollen_types": list(self.coordinator.available_pollen_types),
        }

    @property
    def available(self) -> bool:
        """Available when coordinator last update succeeded."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.hostname, self.region)},
            "name": f"Pollen Data {self.region}",
            "manufacturer": "Pollen Data",
            "model": "Pollen Monitor",
        }
