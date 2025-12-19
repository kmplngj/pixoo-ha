"""Number platform for Pixoo integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from .pixooasync import PixooAsync

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

@dataclass(frozen=True, kw_only=True)
class PixooNumberEntityDescription(NumberEntityDescription):
    """Class describing Pixoo number entities."""
    
    value_fn: Callable[[dict], float] | None = None
    set_fn: Callable[[PixooAsync, float], Awaitable[Any]]
    restore_state: bool = False  # Whether this is a write-only entity needing state restoration


# Write-only number entities (need RestoreEntity)
WRITE_ONLY_NUMBERS = [
    PixooNumberEntityDescription(
        key="timer_minutes",
        translation_key="timer_minutes",
        icon="mdi:timer",
        native_min_value=0,
        native_max_value=59,
        native_step=1,
        native_unit_of_measurement="min",
        set_fn=lambda api, value: api.set_timer(minutes=int(value), seconds=0),
        restore_state=True,
    ),
    PixooNumberEntityDescription(
        key="timer_seconds",
        translation_key="timer_seconds",
        icon="mdi:timer",
        native_min_value=0,
        native_max_value=59,
        native_step=1,
        native_unit_of_measurement="s",
        set_fn=lambda api, value: api.set_timer(minutes=0, seconds=int(value)),
        restore_state=True,
    ),
    PixooNumberEntityDescription(
        key="alarm_hour",
        translation_key="alarm_hour",
        icon="mdi:alarm",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        native_unit_of_measurement="h",
        set_fn=lambda api, value: api.set_alarm(hour=int(value), minute=0),
        restore_state=True,
    ),
    PixooNumberEntityDescription(
        key="alarm_minute",
        translation_key="alarm_minute",
        icon="mdi:alarm",
        native_min_value=0,
        native_max_value=59,
        native_step=1,
        native_unit_of_measurement="min",
        set_fn=lambda api, value: api.set_alarm(hour=0, minute=int(value)),
        restore_state=True,
    ),
    # Note: Scoreboard entities handled specially in PixooScoreboardNumber class
    # to preserve both scores when updating either one
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixoo number entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    pixoo = data["pixoo"]
    device_name = entry.data.get(CONF_NAME, "Pixoo")

    # Add write-only entities (RestoreEntity-based)
    entities = [
        PixooWriteOnlyNumberEntity(description, pixoo, entry.entry_id, device_name)
        for description in WRITE_ONLY_NUMBERS
    ]

    # Add scoreboard entities (special handling to preserve both scores)
    scoreboard_red = PixooScoreboardNumber("red", pixoo, entry.entry_id, device_name)
    scoreboard_blue = PixooScoreboardNumber("blue", pixoo, entry.entry_id, device_name)
    # Link them together so they can share state
    scoreboard_red._sibling = scoreboard_blue
    scoreboard_blue._sibling = scoreboard_red
    entities.extend([scoreboard_red, scoreboard_blue])

    async_add_entities(entities)


class PixooWriteOnlyNumberEntity(NumberEntity, RestoreEntity):
    """Write-only number entity (uses RestoreEntity for state persistence)."""

    _attr_assumed_state = True
    _attr_has_entity_name = True
    entity_description: PixooNumberEntityDescription

    def __init__(
        self,
        description: PixooNumberEntityDescription,
        pixoo: PixooAsync,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the number entity."""
        self._pixoo = pixoo
        self._entry_id = entry_id
        self._device_name = device_name
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._native_value = description.native_min_value or 0

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
        )

    @property
    def available(self) -> bool:
        """Write-only entities are always available."""
        return True

    @property
    def native_value(self) -> float:
        """Return current value from local state."""
        return self._native_value

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value."""
        try:
            await self.entity_description.set_fn(self._pixoo, value)
            self._native_value = value
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set %s: %s", self.entity_description.key, err)
            raise

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state not in ("unknown", "unavailable"):
            try:
                self._native_value = float(last_state.state)
            except (TypeError, ValueError):
                pass


class PixooScoreboardNumber(NumberEntity, RestoreEntity):
    """Scoreboard number entity that preserves the other team's score."""

    _attr_assumed_state = True
    _attr_has_entity_name = True
    _attr_icon = "mdi:scoreboard"
    _attr_native_min_value = 0
    _attr_native_max_value = 999
    _attr_native_step = 1

    def __init__(
        self,
        team: str,  # "red" or "blue"
        pixoo: PixooAsync,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the scoreboard number entity."""
        self._team = team
        self._pixoo = pixoo
        self._entry_id = entry_id
        self._device_name = device_name
        self._attr_unique_id = f"{entry_id}_scoreboard_{team}"
        self._attr_name = f"Scoreboard {team.capitalize()} Score"
        self._attr_translation_key = f"scoreboard_{team}"
        self._native_value = 0
        self._sibling: PixooScoreboardNumber | None = None  # Will be set after initialization

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
        )

    @property
    def available(self) -> bool:
        """Scoreboard entities are always available."""
        return True

    @property
    def native_value(self) -> float:
        """Return current value from local state."""
        return self._native_value

    async def async_set_native_value(self, value: float) -> None:
        """Set the score, preserving the other team's score."""
        try:
            # Get sibling's score (or 0 if not available)
            other_score = int(self._sibling._native_value) if self._sibling else 0
            my_score = int(value)

            # Call set_scoreboard with both scores
            if self._team == "red":
                await self._pixoo.set_scoreboard(red_score=my_score, blue_score=other_score)
            else:
                await self._pixoo.set_scoreboard(red_score=other_score, blue_score=my_score)

            # Update local state
            self._native_value = value
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set scoreboard %s score: %s", self._team, err)
            raise

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state not in ("unknown", "unavailable"):
            try:
                self._native_value = float(last_state.state)
            except (TypeError, ValueError):
                pass
