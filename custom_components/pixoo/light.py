"""Light platform for Pixoo integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PixooSystemCoordinator
from .entity import PixooEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixoo light from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinators = data["coordinators"]
    coordinator = coordinators["system"]
    pixoo = data["pixoo"]
    device_name = entry.data.get(CONF_NAME, "Pixoo")
    
    async_add_entities([PixooLight(coordinator, pixoo, entry.entry_id, device_name)])


class PixooLight(PixooEntity, LightEntity):
    """Representation of a Pixoo display as a light entity."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_translation_key = "pixoo"

    def __init__(
        self,
        coordinator: PixooSystemCoordinator,
        pixoo,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator, entry_id, device_name)
        self._pixoo = pixoo
        self._attr_name = "Display"

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        if not self.coordinator.data or "system" not in self.coordinator.data:
            return False
        system_config = self.coordinator.data["system"]
        # Use screen_power if available, fallback to brightness > 0
        if isinstance(system_config, dict):
            return system_config.get("screen_power", system_config.get("brightness", 0) > 0)
        # SystemConfig Pydantic model
        return system_config.screen_power

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        # Device brightness is 0-100, HA expects 0-255
        if not self.coordinator.data or "system" not in self.coordinator.data:
            return 128  # Default to 50% brightness
        system_config = self.coordinator.data["system"]
        if isinstance(system_config, dict):
            device_brightness = system_config.get("brightness", 50)
        else:
            device_brightness = system_config.brightness
        return round(device_brightness * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            # Convert from 0-255 to 0-100
            brightness_pct = int(brightness * 100 / 255)
            await self._pixoo.set_brightness(brightness_pct)
        
        # Turn screen on (separate from brightness)
        await self._pixoo.set_screen(on=True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        # Turn screen off (keeps brightness setting)
        await self._pixoo.set_screen(on=False)
        await self.coordinator.async_request_refresh()
