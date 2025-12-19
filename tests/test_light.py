"""Test Pixoo light platform."""

from unittest.mock import patch

from homeassistant.components.light import ATTR_BRIGHTNESS, DOMAIN as LIGHT_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant

from custom_components.pixoo.const import DOMAIN


async def test_light_turn_on(hass: HomeAssistant, mock_pixoo, setup_integration) -> None:
    """Test turning on the light."""
    entity_id = "light.test_pixoo_display"
    
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    
    mock_pixoo.turn_on.assert_called_once()


async def test_light_turn_on_with_brightness(hass: HomeAssistant, mock_pixoo, setup_integration) -> None:
    """Test turning on the light with brightness."""
    entity_id = "light.test_pixoo_display"
    
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 128},
        blocking=True,
    )
    
    # 128/255 * 100 = 50%
    mock_pixoo.set_brightness.assert_called_with(50)


async def test_light_turn_off(hass: HomeAssistant, mock_pixoo, setup_integration) -> None:
    """Test turning off the light."""
    entity_id = "light.test_pixoo_display"
    
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    
    mock_pixoo.set_brightness.assert_called_with(0)


async def test_light_state(hass: HomeAssistant, mock_pixoo, setup_integration) -> None:
    """Test light state reflects device state."""
    entity_id = "light.test_pixoo_display"
    
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 204  # 80% -> 204/255
