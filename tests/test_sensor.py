"""Tests for sensor.py."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.pollen_no.const import (
    COMMON_POLLEN_TYPES,
    DOMAIN,
    POLLEN_LEVELS,
    POLLEN_COLORS,
)
from custom_components.pollen_no.sensor import PollenSensor, PollenForecastSensor

from tests.conftest import MOCK_HOSTNAME, MOCK_REGION, MOCK_COMBINED_DATA


def _make_coordinator(data=None, last_update_success=True):
    coord = MagicMock()
    coord.hostname = MOCK_HOSTNAME
    coord.last_update_success = last_update_success
    coord.data = data or MOCK_COMBINED_DATA.copy()
    coord.last_updated_time = data.get("last_updated", "") if data else ""
    coord.available_pollen_types = [
        k for k, v in (data or MOCK_COMBINED_DATA)["pollen"].items() if v > 0
    ]
    return coord


class TestPollenSensorCreation:
    def test_creates_sensor_for_each_common_type(self):
        coord = _make_coordinator()
        sensors = [
            PollenSensor(coordinator=coord, pollen_type=pt, region=MOCK_REGION)
            for pt in COMMON_POLLEN_TYPES
        ]
        assert len(sensors) == len(COMMON_POLLEN_TYPES)

    def test_unique_id_format(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.unique_id == f"{DOMAIN}_{MOCK_REGION}_bjork"

    def test_name_is_english_display_name(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.name == "Birch"

    def test_unknown_pollen_type_uses_raw_name(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="newtype", region=MOCK_REGION)
        assert sensor.name == "Newtype"

    def test_has_entity_name_true(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor._attr_has_entity_name is True


class TestPollenSensorState:
    def test_returns_level_from_coordinator_data(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.native_value == MOCK_COMBINED_DATA["pollen"]["bjork"]

    def test_returns_zero_when_type_absent(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="or", region=MOCK_REGION)
        assert sensor.native_value == MOCK_COMBINED_DATA["pollen"]["or"]

    def test_returns_zero_when_no_data(self):
        coord = _make_coordinator(data={"pollen": {}, "forecast": "", "last_updated": ""})
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.native_value == 0

    def test_returns_zero_when_coordinator_data_none(self):
        coord = _make_coordinator()
        coord.data = None
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.native_value == 0


class TestPollenSensorAttributes:
    def test_level_name_in_attributes(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        attrs = sensor.extra_state_attributes
        expected_level = MOCK_COMBINED_DATA["pollen"]["bjork"]
        assert attrs["level_name"] == POLLEN_LEVELS[expected_level]

    def test_color_matches_level(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        level = sensor.native_value
        assert sensor.extra_state_attributes["color"] == POLLEN_COLORS[level]

    def test_pollen_type_in_attributes(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.extra_state_attributes["pollen_type"] == "bjork"

    def test_region_in_attributes(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.extra_state_attributes["region"] == MOCK_REGION


class TestPollenSensorAvailability:
    def test_available_when_coordinator_success(self):
        coord = _make_coordinator(last_update_success=True)
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.available is True

    def test_unavailable_when_coordinator_failed(self):
        coord = _make_coordinator(last_update_success=False)
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.available is False

    def test_unavailable_when_data_none(self):
        coord = _make_coordinator()
        coord.data = None
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert sensor.available is False


class TestPollenSensorDeviceInfo:
    def test_device_info_identifiers(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        info = sensor.device_info
        assert (DOMAIN, MOCK_HOSTNAME, MOCK_REGION) in info["identifiers"]

    def test_device_info_no_sw_version(self):
        coord = _make_coordinator()
        sensor = PollenSensor(coordinator=coord, pollen_type="bjork", region=MOCK_REGION)
        assert "sw_version" not in sensor.device_info


class TestPollenForecastSensor:
    def test_unique_id_format(self):
        coord = _make_coordinator()
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        assert sensor.unique_id == f"{DOMAIN}_{MOCK_REGION}_forecast"

    def test_name_is_forecast(self):
        coord = _make_coordinator()
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        assert sensor.name == "Forecast"

    def test_returns_forecast_text(self):
        coord = _make_coordinator()
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        assert sensor.native_value == MOCK_COMBINED_DATA["forecast"]

    def test_returns_none_when_no_data(self):
        coord = _make_coordinator()
        coord.data = None
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        assert sensor.native_value is None

    def test_returns_none_when_empty_forecast(self):
        coord = _make_coordinator(data={"pollen": {}, "forecast": "", "last_updated": ""})
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        assert sensor.native_value is None

    def test_active_pollen_types_in_attributes(self):
        coord = _make_coordinator()
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        attrs = sensor.extra_state_attributes
        assert "active_pollen_types" in attrs

    def test_available_when_coordinator_success(self):
        coord = _make_coordinator(last_update_success=True)
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        assert sensor.available is True

    def test_unavailable_when_coordinator_failed(self):
        coord = _make_coordinator(last_update_success=False)
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        assert sensor.available is False

    def test_has_entity_name_true(self):
        coord = _make_coordinator()
        sensor = PollenForecastSensor(coordinator=coord, region=MOCK_REGION)
        assert sensor._attr_has_entity_name is True
