"""Test Pixoo button entities."""

from unittest.mock import patch, AsyncMock

import pytest

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from custom_components.pixoo.const import DOMAIN


async def test_button_entities_created(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test button entities are created."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Check that button entities exist
    assert hass.states.get("button.test_pixoo_dismiss_notification") is not None
    assert hass.states.get("button.test_pixoo_play_buzzer") is not None
    assert hass.states.get("button.test_pixoo_reset_buffer") is not None
    assert hass.states.get("button.test_pixoo_push_buffer") is not None


async def test_dismiss_notification_button(
    hass: HomeAssistant, config_entry, mock_pixoo
) -> None:
    """Test dismiss notification button."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Press the button
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.test_pixoo_dismiss_notification"},
        blocking=True,
    )
    
    # For now, it clears scrolling text
    mock_pixoo.clear_text.assert_awaited_once()


async def test_buzzer_button(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test buzzer button."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Press the button
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.test_pixoo_play_buzzer"},
        blocking=True,
    )
    
    # Should call play_buzzer with default settings
    mock_pixoo.play_buzzer.assert_called_once_with(active_time=500, off_time=500, total_time=1000)


async def test_reset_buffer_button(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test reset buffer button."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Press the button
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.test_pixoo_reset_buffer"},
        blocking=True,
    )
    
    mock_pixoo.clear.assert_called_once()


async def test_push_buffer_button(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test push buffer button."""
    config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Press the button
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.test_pixoo_push_buffer"},
        blocking=True,
    )
    
    mock_pixoo.push.assert_awaited_once()


async def test_button_error_handling(hass: HomeAssistant, config_entry, mock_pixoo) -> None:
    """Test button error handling."""
    config_entry.add_to_hass(hass)
    
    # Make the mock raise an exception
    mock_pixoo.play_buzzer = AsyncMock(side_effect=Exception("Device offline"))
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    
    # Press the button - should raise exception
    with pytest.raises(Exception):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.test_pixoo_play_buzzer"},
            blocking=True,
        )
