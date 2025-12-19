"""Tests for Pixoo sensor entities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers import entity_registry as er

from custom_components.pixoo.coordinator import (
    PixooDeviceCoordinator,
    PixooSystemCoordinator,
    PixooToolCoordinator,
)
from custom_components.pixoo.sensor import (
    PixooDeviceInfoSensor,
    PixooNetworkStatusSensor,
    PixooSystemConfigSensor,
    PixooWeatherSensor,
    PixooTimeSensor,
    PixooToolStateSensor,
)


@pytest.fixture
def mock_device_coordinator():
    """Mock device coordinator with data."""
    coordinator = MagicMock(spec=PixooDeviceCoordinator)
    coordinator.data = {
        "device_info": {
            "device_model": "Pixoo64",
            "software_version": "2.0.1",
            "device_mac": "AA:BB:CC:DD:EE:FF",
        }
    }
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_system_coordinator():
    """Mock system coordinator with data."""
    coordinator = MagicMock(spec=PixooSystemCoordinator)
    coordinator.data = {
        "system": {
            "brightness": 75,
            "channel": "faces",
            "screen_power": True,
            "rotation": 0,
            "mirror_mode": False,
        },
        "network": {
            "ip_address": "192.168.1.100",
            "rssi": -45,
            "ssid": "TestWiFi",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "connected": True,
        },
        "weather": {
            "condition": "clear",
            "temperature": 22,
            "humidity": 65,
            "min_temp": 18,
            "max_temp": 26,
            "pressure": 1013,
        },
        "time": {
            "local_timestamp": "2025-11-13T20:00:00+00:00",
            "utc_timestamp": "2025-11-13T20:00:00Z",
            "timezone": "UTC",
            "timezone_offset": 0,
        },
    }
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_tool_coordinator():
    """Mock tool coordinator with data."""
    coordinator = MagicMock(spec=PixooToolCoordinator)
    coordinator.data = {
        "timer_state": {
            "status": "running",
            "remaining_seconds": 120,
            "total_seconds": 300,
        },
        "alarm_state": {
            "status": "enabled",
            "alarm_time": "07:00",
            "enabled": True,
        },
        "stopwatch_state": {
            "status": "stopped",
            "elapsed_seconds": 0,
            "running": False,
        },
    }
    coordinator.last_update_success = True
    return coordinator


def test_device_info_sensor_model(
    hass: HomeAssistant,
    mock_device_coordinator: MagicMock,
) -> None:
    """Test device model sensor."""
    sensor = PixooDeviceInfoSensor(
        mock_device_coordinator, "test_entry", "Pixoo Test", "model"
    )

    assert sensor.native_value == "Pixoo64"
    assert sensor.name == "Pixoo Test Model"
    assert sensor.icon == "mdi:monitor"


def test_device_info_sensor_firmware(
    hass: HomeAssistant,
    mock_device_coordinator: MagicMock,
) -> None:
    """Test device firmware sensor."""
    sensor = PixooDeviceInfoSensor(
        mock_device_coordinator, "test_entry", "Pixoo Test", "firmware"
    )

    assert sensor.native_value == "2.0.1"
    assert sensor.name == "Pixoo Test Firmware Version"


def test_network_status_sensor_ip(
    hass: HomeAssistant,
    mock_system_coordinator: MagicMock,
) -> None:
    """Test network IP sensor."""
    sensor = PixooNetworkStatusSensor(
        mock_system_coordinator, "test_entry", "Pixoo Test", "ip"
    )

    assert sensor.native_value == "192.168.1.100"
    assert sensor.name == "Pixoo Test IP Address"
    assert sensor.extra_state_attributes["mac_address"] == "AA:BB:CC:DD:EE:FF"
    assert sensor.extra_state_attributes["connected"] is True


def test_network_status_sensor_rssi(
    hass: HomeAssistant,
    mock_system_coordinator: MagicMock,
) -> None:
    """Test network RSSI sensor."""
    sensor = PixooNetworkStatusSensor(
        mock_system_coordinator, "test_entry", "Pixoo Test", "rssi"
    )

    assert sensor.native_value == -45
    assert sensor.device_class == SensorDeviceClass.SIGNAL_STRENGTH
    assert sensor.state_class is not None


def test_system_config_sensor_brightness(
    hass: HomeAssistant,
    mock_system_coordinator: MagicMock,
) -> None:
    """Test brightness sensor."""
    sensor = PixooSystemConfigSensor(
        mock_system_coordinator, "test_entry", "Pixoo Test", "brightness"
    )

    assert sensor.native_value == 75
    assert sensor.native_unit_of_measurement == PERCENTAGE
    assert sensor.extra_state_attributes["screen_power"] is True


def test_system_config_sensor_channel(
    hass: HomeAssistant,
    mock_system_coordinator: MagicMock,
) -> None:
    """Test channel sensor."""
    sensor = PixooSystemConfigSensor(
        mock_system_coordinator, "test_entry", "Pixoo Test", "channel"
    )

    assert sensor.native_value == "faces"
    assert sensor.extra_state_attributes["rotation"] == 0
    assert sensor.extra_state_attributes["mirror_mode"] is False


def test_weather_sensor(
    hass: HomeAssistant,
    mock_system_coordinator: MagicMock,
) -> None:
    """Test weather sensor."""
    sensor = PixooWeatherSensor(mock_system_coordinator, "test_entry", "Pixoo Test")

    assert sensor.native_value == "clear"
    assert sensor.device_class == SensorDeviceClass.ENUM
    assert "clear" in sensor.options
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

    assert sensor.native_value == "2025-11-13T20:00:00+00:00"
    assert sensor.device_class == SensorDeviceClass.TIMESTAMP
    attrs = sensor.extra_state_attributes
    assert attrs["timezone"] == "UTC"
    assert attrs["timezone_offset"] == 0


def test_tool_state_sensor_timer(
    hass: HomeAssistant,
    mock_tool_coordinator: MagicMock,
) -> None:
    """Test timer state sensor."""
    sensor = PixooToolStateSensor(
        mock_tool_coordinator, "test_entry", "Pixoo Test", "timer"
    )

    assert sensor.native_value == "running"
    attrs = sensor.extra_state_attributes
    assert attrs["remaining_seconds"] == 120
    assert attrs["total_seconds"] == 300


def test_tool_state_sensor_alarm(
    hass: HomeAssistant,
    mock_tool_coordinator: MagicMock,
) -> None:
    """Test alarm state sensor."""
    sensor = PixooToolStateSensor(
        mock_tool_coordinator, "test_entry", "Pixoo Test", "alarm"
    )

    assert sensor.native_value == "enabled"
    attrs = sensor.extra_state_attributes
    assert attrs["next_alarm_time"] == "07:00"
    assert attrs["enabled"] is True


def test_sensor_unavailable_when_no_data(
    hass: HomeAssistant,
) -> None:
    """Test sensors return None when coordinator has no data."""
    coordinator = MagicMock(spec=PixooDeviceCoordinator)
    coordinator.data = {}
    coordinator.last_update_success = True

    sensor = PixooDeviceInfoSensor(coordinator, "test_entry", "Pixoo Test", "model")
    assert sensor.native_value is None
