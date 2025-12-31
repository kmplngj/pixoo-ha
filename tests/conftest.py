"""Test fixtures for Pixoo integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from pixooasync.models import DeviceInfo, SystemConfig, NetworkStatus
from pixooasync.enums import Channel, Rotation, TemperatureMode
import pytest

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.pixoo.const import DOMAIN, CONF_DEVICE_SIZE

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_pixoo():
    """Mock PixooAsync client."""
    with patch("custom_components.pixoo.config_flow.PixooAsync") as mock_class, \
         patch("custom_components.pixoo.PixooAsync") as mock_init_class:
        
        mock_pixoo = AsyncMock()
        mock_class.return_value = mock_pixoo
        mock_init_class.return_value = mock_pixoo
        
        # Mock device info
        mock_pixoo.get_device_info.return_value = DeviceInfo(
            ip_address="192.168.1.100",
            mac_address="AA:BB:CC:DD:EE:FF",
            model="Pixoo64",
            firmware_version="2.0",
        )
        
        # Mock system config
        mock_pixoo.get_system_config.return_value = SystemConfig(
            brightness=80,
            rotation=Rotation.NORMAL,
            mirror_mode=False,
            temperature_mode=TemperatureMode.CELSIUS,
            time_format_24h=False,
        )
        
        # Mock network status
        mock_pixoo.get_network_status.return_value = NetworkStatus(
            ssid="TestWiFi",
            signal_strength=-50,
            ip_address="192.168.1.100",
        )
        
        # Mock current channel
        mock_pixoo.get_current_channel.return_value = Channel.FACES
        
        # Mock animation list
        mock_pixoo.get_animation_list.return_value = []
        
        # Mock methods
        mock_pixoo.turn_on = AsyncMock()
        mock_pixoo.set_brightness = AsyncMock()
        mock_pixoo.set_channel = AsyncMock()
        mock_pixoo.set_rotation = AsyncMock()
        mock_pixoo.set_temperature_mode = AsyncMock()
        mock_pixoo.set_time_format_24h = AsyncMock()
        mock_pixoo.close = AsyncMock()
        
        yield mock_pixoo


@pytest.fixture
def mock_config_entry():
    """Mock ConfigEntry."""
    return MagicMock(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_NAME: "Test Pixoo",
            CONF_DEVICE_SIZE: 64,
        },
        entry_id="test_entry_id",
        unique_id="AA:BB:CC:DD:EE:FF",
    )


@pytest.fixture
async def setup_integration(hass: HomeAssistant, mock_pixoo, mock_config_entry):
    """Set up the Pixoo integration for testing."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    
    return mock_config_entry
