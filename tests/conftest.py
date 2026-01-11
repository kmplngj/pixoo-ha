"""Test fixtures for Pixoo integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pixoo.pixooasync.enums import Rotation
from custom_components.pixoo.pixooasync.models import DeviceInfo, NetworkStatus, SystemConfig

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.pixoo.const import DOMAIN, CONF_DEVICE_SIZE

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def _auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests.

    Without this, Home Assistant will refuse to load `custom_components/` and
    tests will fail with "Integration not found".
    """
    yield


@pytest.fixture(autouse=True)
def _ensure_builtin_templates_available(hass: HomeAssistant) -> None:
    """Ensure template YAMLs exist in the HA config dir for template page tests.

    The Page Engine template loader (`load_builtin_template`) resolves templates from
    `<config>/pixoo_templates/<name>.yaml`. The test environment uses a temporary
    config dir, so we copy the repository examples into that location.
    """

    templates_dir = Path(hass.config.config_dir) / "pixoo_templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[1]
    examples_dir = repo_root / "examples" / "page_templates"

    for name in ("progress_bar", "now_playing"):
        src = examples_dir / f"{name}.yaml"
        dst = templates_dir / f"{name}.yaml"
        if src.exists() and src.is_file():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")



@pytest.fixture
def mock_pixoo():
    """Mock PixooAsync client."""
    with patch("custom_components.pixoo.config_flow.PixooAsync") as mock_class, \
         patch("custom_components.pixoo.PixooAsync") as mock_init_class:
        
        mock_pixoo = AsyncMock()
        mock_class.return_value = mock_pixoo
        mock_init_class.return_value = mock_pixoo

        # Setup methods that are awaited during setup/teardown
        mock_pixoo.initialize = AsyncMock()
        mock_pixoo.close = AsyncMock()
        mock_pixoo.get_all_channel_config = AsyncMock()
        
        # Mock device info (Device/GetDeviceInfo API is not used by the integration,
        # but some tests may still rely on this model existing.)
        mock_pixoo.get_device_info = AsyncMock(
            return_value=DeviceInfo(
                device_name="Pixoo64",
                device_id="12345",
                device_mac="AA:BB:CC:DD:EE:FF",
                hardware_version="1.0",
                software_version="2.0",
                device_model="Pixoo-64",
                brightness=80,
            )
        )
        
        # Mock system config (Channel/GetAllConf)
        mock_pixoo.get_system_config = AsyncMock(
            return_value=SystemConfig(
                brightness=80,
                rotation=Rotation.NORMAL,
                mirror_mode=False,
                white_balance_r=255,
                white_balance_g=255,
                white_balance_b=255,
                time_zone="UTC",
                hour_mode=24,
                temperature_mode=0,
                screen_power=True,
            )
        )
        
        # Mock network status (Device/GetNetworkStatus - currently not used)
        mock_pixoo.get_network_status = AsyncMock(
            return_value=NetworkStatus(
                ip_address="192.168.1.100",
                mac_address="AA:BB:CC:DD:EE:FF",
                rssi=-50,
                ssid="TestWiFi",
                connected=True,
            )
        )
        
        # Mock current channel index (Channel/GetIndex)
        mock_pixoo.get_current_channel = AsyncMock(return_value=0)

        # Mock time + weather
        mock_pixoo.get_time_info = AsyncMock(return_value=None)
        mock_pixoo.get_weather_info = AsyncMock(return_value=None)
        
        # Mock animation list
        mock_pixoo.get_animation_list = AsyncMock(return_value=[])
        
        # Mock methods used by entities/services
        mock_pixoo.set_screen = AsyncMock()
        mock_pixoo.set_brightness = AsyncMock()
        mock_pixoo.set_channel = AsyncMock()
        mock_pixoo.set_rotation = AsyncMock()
        mock_pixoo.set_temperature_mode = AsyncMock()
        mock_pixoo.set_time_format_24h = AsyncMock()
        mock_pixoo.send_text = AsyncMock()
        # Buffer-based drawing workflow (PixooBase methods are synchronous)
        mock_pixoo.clear = Mock()
        mock_pixoo.fill = Mock()
        mock_pixoo.draw_text = Mock()
        mock_pixoo.draw_line = Mock()
        mock_pixoo.draw_filled_rectangle = Mock()
        mock_pixoo.draw_image = Mock()
        mock_pixoo.push = AsyncMock()
        mock_pixoo.clear_text = AsyncMock()
        mock_pixoo.play_buzzer = AsyncMock()
        
        yield mock_pixoo


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Config entry fixture used by most tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_NAME: "Test Pixoo",
            CONF_DEVICE_SIZE: 64,
        },
        entry_id="test_entry_id",
        unique_id="AA:BB:CC:DD:EE:FF",
        title="Test Pixoo",
    )


@pytest.fixture
def mock_config_entry(config_entry: MockConfigEntry) -> MockConfigEntry:
    """Backward-compatible alias for older tests."""
    return config_entry


@pytest.fixture
async def setup_integration(hass: HomeAssistant, mock_pixoo, config_entry: MockConfigEntry):
    """Set up the Pixoo integration for testing."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    return config_entry
