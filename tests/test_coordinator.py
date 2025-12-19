"""Tests for Pixoo coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun.api import FrozenDateTimeFactory

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.pixoo.coordinator import (
    PixooDeviceCoordinator,
    PixooSystemCoordinator,
    PixooToolCoordinator,
    PixooGalleryCoordinator,
)
from custom_components.pixoo.pixooasync.models import (
    DeviceInfo,
    NetworkStatus,
    SystemConfig,
    TimerConfig,
    AlarmConfig,
    StopwatchConfig,
)
from custom_components.pixoo.pixooasync.enums import Channel


@pytest.fixture
def mock_pixoo():
    """Create a mock PixooAsync client."""
    pixoo = MagicMock()
    pixoo.get_device_info = AsyncMock()
    pixoo.get_system_config = AsyncMock()
    pixoo.get_network_status = AsyncMock()
    pixoo.get_current_channel = AsyncMock()
    pixoo.get_timer_config = AsyncMock()
    pixoo.get_alarm_config = AsyncMock()
    pixoo.get_stopwatch_config = AsyncMock()
    pixoo.get_animation_list = AsyncMock()
    return pixoo


@pytest.fixture
def device_info_mock():
    """Mock device info response."""
    return DeviceInfo(
        device_name="Pixoo64",
        device_id="12345",
        device_mac="AA:BB:CC:DD:EE:FF",
        hardware_version="1.0",
        software_version="2.0.1",
        device_model="Pixoo64",
        brightness=50,
    )


@pytest.fixture
def system_config_mock():
    """Mock system config response."""
    return SystemConfig(
        brightness=75,
        rotation=0,
        mirror_mode=False,
        temperature_mode=0,
        hour_mode=24,
        screen_power=True,
    )


@pytest.fixture
def network_status_mock():
    """Mock network status response."""
    return NetworkStatus(
        ssid="TestWiFi",
        rssi=-45,
        ip_address="192.168.1.100",
        mac_address="AA:BB:CC:DD:EE:FF",
        connected=True,
    )


async def test_device_coordinator_fetch(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
    device_info_mock: DeviceInfo,
) -> None:
    """Test device coordinator fetches device info once."""
    mock_pixoo.get_device_info.return_value = device_info_mock

    coordinator = PixooDeviceCoordinator(hass, mock_pixoo)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert coordinator.data["device_info"]["device_model"] == "Pixoo64"
    assert coordinator.data["device_info"]["software_version"] == "2.0.1"
    assert coordinator.data["device_info"]["brightness"] == 50
    mock_pixoo.get_device_info.assert_called_once()


async def test_system_coordinator_fetch(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
    system_config_mock: SystemConfig,
    network_status_mock: NetworkStatus,
) -> None:
    """Test system coordinator fetches system and network data."""
    mock_pixoo.get_system_config.return_value = system_config_mock
    mock_pixoo.get_network_status.return_value = network_status_mock
    mock_pixoo.get_current_channel.return_value = Channel.FACES

    coordinator = PixooSystemCoordinator(hass, mock_pixoo)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert coordinator.data["system"]["brightness"] == 75
    assert coordinator.data["system"]["screen_power"] is True
    assert coordinator.data["system"]["channel"] == "faces"
    
    # Network data fetched on first refresh (counter=0 initially)
    assert "network" in coordinator.data
    assert coordinator.data["network"]["ip_address"] == "192.168.1.100"
    assert coordinator.data["network"]["rssi"] == -45


async def test_system_coordinator_network_polling(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
    system_config_mock: SystemConfig,
    network_status_mock: NetworkStatus,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test system coordinator polls network every 60s (every 2nd update at 30s intervals)."""
    mock_pixoo.get_system_config.return_value = system_config_mock
    mock_pixoo.get_network_status.return_value = network_status_mock
    mock_pixoo.get_current_channel.return_value = Channel.CLOUD

    coordinator = PixooSystemCoordinator(hass, mock_pixoo)
    await coordinator.async_config_entry_first_refresh()

    initial_network_calls = mock_pixoo.get_network_status.call_count
    
    # First refresh at 0s includes network (counter starts at 0)
    # After first update, counter becomes 1, second update at 30s will reset counter and fetch network
    freezer.tick(timedelta(seconds=30))
    await coordinator.async_refresh()

    # Network should be fetched again on second update (counter was 1, now resets to 0)
    assert mock_pixoo.get_network_status.call_count == initial_network_calls + 1


async def test_tool_coordinator_dynamic_polling(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
) -> None:
    """Test tool coordinator adjusts polling interval dynamically."""
    # Start with inactive tools
    mock_pixoo.get_timer_config.return_value = TimerConfig(running=False, minutes=0, seconds=0)
    mock_pixoo.get_alarm_config.return_value = AlarmConfig(enabled=False, hour=0, minute=0)
    mock_pixoo.get_stopwatch_config.return_value = StopwatchConfig(running=False, elapsed_seconds=0)

    coordinator = PixooToolCoordinator(hass, mock_pixoo)
    await coordinator.async_config_entry_first_refresh()

    # Should start with fast polling (1s)
    assert coordinator.update_interval == timedelta(seconds=1)
    assert coordinator._any_tool_active is False

    # Activate timer
    mock_pixoo.get_timer_config.return_value = TimerConfig(running=True, minutes=5, seconds=30, remaining_seconds=330)
    await coordinator.async_refresh()

    # Should remain at 1s but mark active
    assert coordinator.update_interval == timedelta(seconds=1)
    assert coordinator._any_tool_active is True

    # Deactivate all tools
    mock_pixoo.get_timer_config.return_value = TimerConfig(running=False, minutes=0, seconds=0)
    await coordinator.async_refresh()

    # Should slow down to 30s
    assert coordinator.update_interval == timedelta(seconds=30)
    assert coordinator._any_tool_active is False


async def test_gallery_coordinator_tuple_handling(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
) -> None:
    """Test gallery coordinator handles both tuple and object animations."""
    # Return mix of tuples and objects
    class AnimObj:
        animation_id = 42
        name = "Test Animation"

    mock_pixoo.get_animation_list.return_value = [
        (1, "Animation 1"),
        (2, "Animation 2"),
        AnimObj(),
    ]

    coordinator = PixooGalleryCoordinator(hass, mock_pixoo)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert len(coordinator.data["animations"]) == 3
    assert coordinator.data["animations"][0] == {"id": 1, "name": "Animation 1"}
    assert coordinator.data["animations"][1] == {"id": 2, "name": "Animation 2"}
    assert coordinator.data["animations"][2] == {"id": 42, "name": "Test Animation"}


async def test_coordinator_error_handling(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
) -> None:
    """Test coordinator handles errors gracefully."""
    mock_pixoo.get_device_info.side_effect = Exception("Device unreachable")

    coordinator = PixooDeviceCoordinator(hass, mock_pixoo)
    
    with pytest.raises(UpdateFailed, match="Error fetching device info"):
        await coordinator.async_config_entry_first_refresh()
