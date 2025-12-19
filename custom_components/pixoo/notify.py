"""Support for Pixoo notifications."""

from __future__ import annotations

from typing import Any

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    BaseNotificationService,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN

# Notification data attributes
ATTR_COLOR = "color"
ATTR_FONT = "font"
ATTR_SPEED = "speed"
ATTR_X = "x"
ATTR_Y = "y"
ATTR_SCROLL_DIRECTION = "scroll_direction"
ATTR_TEXT_ID = "text_id"
ATTR_IMAGE = "image"
ATTR_BUZZER = "buzzer"
ATTR_BUZZER_ACTIVE_TIME = "buzzer_active_time"
ATTR_BUZZER_OFF_TIME = "buzzer_off_time"
ATTR_BUZZER_TOTAL_TIME = "buzzer_total_time"


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> PixooNotificationService | None:
    """Get the Pixoo notification service."""
    if discovery_info is None:
        return None

    return PixooNotificationService(hass, discovery_info["entry_id"])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixoo notify from a config entry - not used but required."""
    # Notify platform uses async_get_service instead of entities
    pass


class PixooNotificationService(BaseNotificationService):
    """Implement the notification service for Pixoo."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the service."""
        self.hass = hass
        self._entry_id = entry_id

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a notification message to Pixoo device."""
        if not message:
            return

        data = kwargs.get(ATTR_DATA) or {}
        title = kwargs.get(ATTR_TITLE)

        # Get the light entity for this entry
        entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)
        light_entity = None
        
        for entity in entity_registry.entities.values():
            if entity.config_entry_id == self._entry_id and entity.domain == "light":
                light_entity = entity.entity_id
                break
        
        if not light_entity:
            raise HomeAssistantError(
                "Could not find Pixoo light entity for notification"
            )

        # Display image if provided
        if ATTR_IMAGE in data:
            try:
                await self.hass.services.async_call(
                    DOMAIN,
                    "display_image",
                    {
                        "entity_id": light_entity,
                        "url": data[ATTR_IMAGE],
                    },
                    blocking=True,
                )
            except Exception as err:
                raise HomeAssistantError(f"Failed to display image: {err}") from err

        # Build text message (combine title and message)
        text = f"{title}: {message}" if title else message

        # Prepare text display data
        text_data: dict[str, Any] = {
            "entity_id": light_entity,
            "text": text,
            "color": data.get(ATTR_COLOR, "#FFFFFF"),
            "x": data.get(ATTR_X, 0),
            "y": data.get(ATTR_Y, 32),
            "font": data.get(ATTR_FONT, 2),
            "speed": data.get(ATTR_SPEED, 50),
            "text_id": data.get(ATTR_TEXT_ID, 1),
            "scroll_direction": data.get(ATTR_SCROLL_DIRECTION, "left"),
        }

        # Display text
        try:
            await self.hass.services.async_call(
                DOMAIN,
                "display_text",
                text_data,
                blocking=True,
            )
        except Exception as err:
            raise HomeAssistantError(f"Failed to display text: {err}") from err

        # Play buzzer if requested
        if data.get(ATTR_BUZZER, False):
            buzzer_data: dict[str, Any] = {
                "entity_id": light_entity,
                "active_time": data.get(ATTR_BUZZER_ACTIVE_TIME, 500),
                "off_time": data.get(ATTR_BUZZER_OFF_TIME, 500),
                "total_time": data.get(ATTR_BUZZER_TOTAL_TIME, 2000),
            }
            try:
                await self.hass.services.async_call(
                    DOMAIN,
                    "play_buzzer",
                    buzzer_data,
                    blocking=True,
                )
            except Exception:
                # Don't fail notification if buzzer fails
                pass
