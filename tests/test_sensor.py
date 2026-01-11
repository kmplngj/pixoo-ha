"""Tests for Pixoo sensor entities."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from homeassistant.core import HomeAssistant

from custom_components.pixoo.coordinator import PixooSystemCoordinator
from custom_components.pixoo.sensor import PixooChannelSensor, PixooTimeSensor, PixooWeatherSensor


@pytest.fixture
def mock_system_coordinator() -> MagicMock:
    """Mock system coordinator with data."""
    coordinator = MagicMock(spec=PixooSystemCoordinator)
    coordinator.data = {
        "system": {
            "brightness": 75,
            "screen_power": True,
            "rotation": 0,
            "mirror_mode": False,
        },
        "channel_index": 3,
        "weather": {
            "condition": "clear",
            "temperature": 22,
            "humidity": 65,
            "min_temp": 18,
            "max_temp": 26,
            "pressure": 1013,
        },
        "time": {
            "utc_time": 1_700_000_000,
            "local_time": 1_700_000_360,
        },
    }
    coordinator.last_update_success = True
    return coordinator


def test_channel_sensor_maps_index(
    hass: HomeAssistant,
    mock_system_coordinator: MagicMock,
) -> None:
    """Test active channel sensor mapping (index -> name)."""
    sensor = PixooChannelSensor(mock_system_coordinator, "test_entry", "Pixoo Test")

    assert sensor.native_value == "Custom"  # channel_index=3
    attrs = sensor.extra_state_attributes
    assert attrs["channel_index"] == 3
    assert attrs["brightness"] == 75


def test_weather_sensor(
    hass: HomeAssistant,
    mock_system_coordinator: MagicMock,
) -> None:
    """Test weather sensor."""
    sensor = PixooWeatherSensor(mock_system_coordinator, "test_entry", "Pixoo Test")

    assert sensor.native_value == "clear"
    attrs = sensor.extra_state_attributes
    assert attrs["temperature"] == 22
    assert attrs["humidity"] == 65
    assert attrs["min_temp"] == 18
    assert attrs["max_temp"] == 26


def test_time_sensor(
    hass: HomeAssistant,
    mock_system_coordinator: MagicMock,
) -> None:
    """Test time sensor."""
    sensor = PixooTimeSensor(mock_system_coordinator, "test_entry", "Pixoo Test")

    assert sensor.native_value == datetime.fromtimestamp(1_700_000_000, tz=timezone.utc)
    attrs = sensor.extra_state_attributes
    assert attrs["utc_timestamp"] == 1_700_000_000
    assert attrs["local_time"] == 1_700_000_360


def test_sensor_unavailable_when_no_data(
    hass: HomeAssistant,
) -> None:
    """Test sensors return None when coordinator has no data."""
    coordinator = MagicMock(spec=PixooSystemCoordinator)
    coordinator.data = {}
    coordinator.last_update_success = True

    assert PixooChannelSensor(coordinator, "test_entry", "Pixoo Test").native_value is None
    assert PixooTimeSensor(coordinator, "test_entry", "Pixoo Test").native_value is None
