"""Button platform for Pixoo integration."""

from __future__ import annotations

import logging
from typing import Any

from .pixooasync import PixooAsync
from .pixooasync.enums import Channel

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import PixooEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixoo button entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    pixoo: PixooAsync = data["pixoo"]

    device_name = entry.data.get("name", "Pixoo")
    entry_id = entry.entry_id

    entities = [
        PixooDismissNotificationButton(entry_id, device_name, pixoo),
        PixooBuzzerButton(entry_id, device_name, pixoo),
        PixooResetStopwatchButton(entry_id, device_name, pixoo),
        PixooResetBufferButton(entry_id, device_name, pixoo),
        PixooPushBufferButton(entry_id, device_name, pixoo),
        # Channel switching buttons
        PixooChannelCloudButton(entry_id, device_name, pixoo),
        PixooChannelFacesButton(entry_id, device_name, pixoo),
        PixooChannelVisualizerButton(entry_id, device_name, pixoo),
        PixooChannelCustomButton(entry_id, device_name, pixoo),
    ]

    async_add_entities(entities)


class PixooDismissNotificationButton(ButtonEntity):
    """Button to dismiss current notification and restore previous state."""

    _attr_icon = "mdi:bell-off"
    _attr_device_class = ButtonDeviceClass.UPDATE
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the dismiss notification button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_dismiss_notification"
        self._attr_name = "Dismiss Notification"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Dismiss notification and restore previous state."""
        # TODO: Implement state restoration logic
        # For now, just clear the display
        try:
            await self._pixoo.clear_text()
            _LOGGER.info("Notification dismissed on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to dismiss notification: %s", err)
            raise


class PixooBuzzerButton(ButtonEntity):
    """Button to trigger the buzzer."""

    _attr_icon = "mdi:bell-ring"
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the buzzer button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_buzzer"
        self._attr_name = "Play Buzzer"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Trigger the buzzer with default settings."""
        try:
            # Default: 500ms on, 500ms off, 1000ms total (2 beeps)
            await self._pixoo.play_buzzer(active_time=500, off_time=500, total_time=1000)
            _LOGGER.debug("Buzzer triggered on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to trigger buzzer: %s", err)
            raise


class PixooResetStopwatchButton(ButtonEntity):
    """Button to reset the stopwatch to zero."""

    _attr_icon = "mdi:timer-refresh"
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the reset stopwatch button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_reset_stopwatch"
        self._attr_name = "Reset Stopwatch"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Reset the stopwatch to zero."""
        try:
            # Resetting stopwatch is done by disabling it
            await self._pixoo.set_stopwatch(enabled=False)
            _LOGGER.debug("Stopwatch reset on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to reset stopwatch: %s", err)
            raise


class PixooResetBufferButton(ButtonEntity):
    """Button to reset the drawing buffer."""

    _attr_icon = "mdi:eraser"
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the reset buffer button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_reset_buffer"
        self._attr_name = "Reset Buffer"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Reset the drawing buffer."""
        try:
            # Clear buffer by filling with black
            self._pixoo.clear()
            _LOGGER.debug("Drawing buffer reset on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to reset buffer: %s", err)
            raise


class PixooPushBufferButton(ButtonEntity):
    """Button to push the drawing buffer to the display."""

    _attr_icon = "mdi:upload"
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the push buffer button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_push_buffer"
        self._attr_name = "Push Buffer"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Push the drawing buffer to the display."""
        try:
            await self._pixoo.push()
            _LOGGER.debug("Drawing buffer pushed on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to push buffer: %s", err)
            raise


class PixooChannelCloudButton(ButtonEntity):
    """Button to switch to Cloud Gallery channel."""

    _attr_icon = "mdi:cloud"
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the cloud channel button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_channel_cloud"
        self._attr_name = "Switch to Cloud Channel"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Switch to Cloud Gallery channel."""
        try:
            await self._pixoo.set_channel(Channel.CLOUD)
            _LOGGER.debug("Switched to cloud channel on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to switch to cloud channel: %s", err)
            raise


class PixooChannelFacesButton(ButtonEntity):
    """Button to switch to Clock Faces channel."""

    _attr_icon = "mdi:clock-outline"
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the faces channel button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_channel_faces"
        self._attr_name = "Switch to Clock Channel"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Switch to Clock Faces channel."""
        try:
            await self._pixoo.set_channel(Channel.FACES)
            _LOGGER.debug("Switched to faces channel on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to switch to faces channel: %s", err)
            raise


class PixooChannelVisualizerButton(ButtonEntity):
    """Button to switch to Visualizer channel."""

    _attr_icon = "mdi:waveform"
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the visualizer channel button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_channel_visualizer"
        self._attr_name = "Switch to Visualizer Channel"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Switch to Visualizer channel."""
        try:
            await self._pixoo.set_channel(Channel.VISUALIZER)
            _LOGGER.debug("Switched to visualizer channel on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to switch to visualizer channel: %s", err)
            raise


class PixooChannelCustomButton(ButtonEntity):
    """Button to switch to Custom channel."""

    _attr_icon = "mdi:palette"
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        pixoo: PixooAsync,
    ) -> None:
        """Initialize the custom channel button."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_channel_custom"
        self._attr_name = "Switch to Custom Channel"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._device_name,
        }

    async def async_press(self) -> None:
        """Switch to Custom channel."""
        try:
            await self._pixoo.set_channel(Channel.CUSTOM)
            _LOGGER.debug("Switched to custom channel on %s", self._pixoo.config.address)
        except Exception as err:
            _LOGGER.error("Failed to switch to custom channel: %s", err)
            raise
