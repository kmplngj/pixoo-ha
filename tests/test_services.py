"""Test Pixoo services."""

import base64
from unittest.mock import patch, AsyncMock

import pytest

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError, HomeAssistantError

from custom_components.pixoo.const import (
    DOMAIN,
    SERVICE_DISPLAY_IMAGE,
    SERVICE_DISPLAY_GIF,
    SERVICE_DISPLAY_TEXT,
    SERVICE_CLEAR_DISPLAY,
)


async def test_display_image_service(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test display_image service."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Mock download_image with a valid 1x1 PNG
    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X+R5cAAAAASUVORK5CYII="
    )
    with patch("custom_components.pixoo.download_image", return_value=png_1x1):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DISPLAY_IMAGE,
            {"url": "http://example.com/image.jpg"},
            blocking=True,
        )

    assert mock_pixoo.draw_image.call_count == 1
    mock_pixoo.push.assert_awaited_once()


async def test_display_image_service_invalid_url(
    hass: HomeAssistant, config_entry, mock_pixoo
) -> None:
    """Test display_image service with invalid URL."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Mock download_image to raise a validation error
    with patch(
        "custom_components.pixoo.download_image",
        side_effect=ServiceValidationError("Invalid URL"),
    ):
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_DISPLAY_IMAGE,
                {"url": "invalid://url"},
                blocking=True,
            )


async def test_display_gif_service(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test display_gif service."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Mock download_image with a valid 1x1 GIF
    gif_1x1 = base64.b64decode(
        "R0lGODdhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
    )
    with patch("custom_components.pixoo.download_image", return_value=gif_1x1):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DISPLAY_GIF,
            {"url": "http://example.com/animation.gif"},
            blocking=True,
        )

    assert mock_pixoo.draw_image.call_count == 1
    mock_pixoo.push.assert_awaited_once()


async def test_display_text_service(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test display_text service with default parameters."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISPLAY_TEXT,
        {"text": "Hello, World!"},
        blocking=True,
    )
    
    # Check that send_text was called with correct parameters
    from custom_components.pixoo.pixooasync.enums import TextScrollDirection

    mock_pixoo.send_text.assert_called_once_with(
        text="Hello, World!",
        xy=(0, 0),
        color=(255, 255, 255),  # Default white color
        identifier=1,
        font=2,
        width=64,
        movement_speed=0,
        direction=TextScrollDirection.LEFT,
    )


async def test_display_text_service_with_color(
    hass: HomeAssistant, config_entry, mock_pixoo
) -> None:
    """Test display_text service with custom color."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISPLAY_TEXT,
        {
            "text": "Red Text",
            "color": "#FF0000",
            "scroll_direction": "right",
        },
        blocking=True,
    )
    
    from custom_components.pixoo.pixooasync.enums import TextScrollDirection

    mock_pixoo.send_text.assert_called_once_with(
        text="Red Text",
        xy=(0, 0),
        color=(255, 0, 0),  # Red color
        identifier=1,
        font=2,
        width=64,
        movement_speed=0,
        direction=TextScrollDirection.RIGHT,
    )


async def test_display_text_service_invalid_color(
    hass: HomeAssistant, config_entry, mock_pixoo
) -> None:
    """Test display_text service with invalid color."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DISPLAY_TEXT,
            {"text": "Test", "color": "invalid"},
            blocking=True,
        )


async def test_clear_display_service(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test clear_display service."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLEAR_DISPLAY,
        {},
        blocking=True,
    )

    mock_pixoo.clear.assert_called_once()
    mock_pixoo.push.assert_awaited_once()


async def test_service_device_error(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test service handling when device communication fails."""
    config_entry.add_to_hass(hass)
    
    # Make the mock raise an exception
    mock_pixoo.push = AsyncMock(side_effect=Exception("Device offline"))
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CLEAR_DISPLAY,
            {},
            blocking=True,
        )


async def test_play_buzzer_service(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test play_buzzer service with default parameters."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    from custom_components.pixoo.const import SERVICE_PLAY_BUZZER
    
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PLAY_BUZZER,
        {},
        blocking=True,
    )
    
    # Should use default values
    mock_pixoo.play_buzzer.assert_called_once_with(active_time=500, off_time=500, total_time=1000)


async def test_play_buzzer_service_custom_params(
    hass: HomeAssistant, config_entry, mock_pixoo
) -> None:
    """Test play_buzzer service with custom parameters."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    from custom_components.pixoo.const import SERVICE_PLAY_BUZZER
    
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PLAY_BUZZER,
        {
            "active_ms": 1000,
            "off_ms": 200,
            "count": 3,
        },
        blocking=True,
    )
    
    mock_pixoo.play_buzzer.assert_called_once_with(active_time=1000, off_time=200, total_time=3600)
