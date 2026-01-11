"""Tests for Pixoo coordinators."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.pixoo.coordinator import (
    PixooGalleryCoordinator,
    PixooSystemCoordinator,
    PixooWeatherCoordinator,
)


@pytest.fixture
def mock_pixoo():
    """Create a mock PixooAsync client."""
    pixoo = MagicMock()
    pixoo.get_system_config = AsyncMock()
    pixoo.get_current_channel = AsyncMock()
    pixoo.get_time_info = AsyncMock()
    pixoo.get_weather_info = AsyncMock()
    pixoo.get_animation_list = AsyncMock()
    return pixoo


def _system_config_mock(*, brightness: int = 75, screen_power: bool = True) -> MagicMock:
    cfg = MagicMock()
    cfg.brightness = brightness
    cfg.rotation = 0
    cfg.mirror_mode = False
    cfg.temperature_mode = 0
    cfg.hour_mode = 24
    cfg.screen_power = screen_power
    return cfg


def _time_info_mock() -> MagicMock:
    ti = MagicMock()
    ti.utc_time = 1_700_000_000
    ti.local_time = 1_700_000_360
    return ti


def _weather_info_mock() -> MagicMock:
    wi = MagicMock()
    wi.CurTemp = 22
    wi.Weather = "clear"
    wi.MinTemp = 18
    wi.MaxTemp = 26
    wi.Humidity = 65
    wi.Pressure = 1013
    return wi


async def test_system_coordinator_fetch(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
    config_entry,
) -> None:
    """Test system coordinator fetches system data + channel index."""
    mock_pixoo.get_system_config.return_value = _system_config_mock()
    mock_pixoo.get_current_channel.return_value = 0
    mock_pixoo.get_time_info.return_value = _time_info_mock()

    coordinator = PixooSystemCoordinator(hass, mock_pixoo, config_entry)
    data = await coordinator._async_update_data()

    assert data is not None
    assert data["system"]["brightness"] == 75
    assert data["system"]["screen_power"] is True
    assert data["channel_index"] == 0
    assert data["time"]["utc_time"] == 1_700_000_000


async def test_weather_coordinator_fetch(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
    config_entry,
) -> None:
    """Test weather coordinator fetches weather + time (best-effort per field)."""
    mock_pixoo.get_weather_info.return_value = _weather_info_mock()
    mock_pixoo.get_time_info.return_value = _time_info_mock()

    coordinator = PixooWeatherCoordinator(hass, mock_pixoo, config_entry)
    data = await coordinator._async_update_data()

    assert data is not None
    assert data["weather"]["condition"] == "clear"
    assert data["weather"]["temperature"] == 22
    assert data["time"]["utc_time"] == 1_700_000_000


async def test_gallery_coordinator_tuple_handling(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
    config_entry,
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

    coordinator = PixooGalleryCoordinator(hass, mock_pixoo, config_entry)
    data = await coordinator._async_update_data()

    assert data is not None
    assert len(data["animations"]) == 3
    assert data["animations"][0] == {"id": 1, "name": "Animation 1"}
    assert data["animations"][1] == {"id": 2, "name": "Animation 2"}
    assert data["animations"][2] == {"id": 42, "name": "Test Animation"}


async def test_coordinator_error_handling(
    hass: HomeAssistant,
    mock_pixoo: MagicMock,
    config_entry,
) -> None:
    """Test coordinator surfaces UpdateFailed on hard failures."""
    mock_pixoo.get_system_config.side_effect = Exception("Device unreachable")

    coordinator = PixooSystemCoordinator(hass, mock_pixoo, config_entry)

    with pytest.raises(UpdateFailed, match="Error fetching system data"):
        await coordinator._async_update_data()
