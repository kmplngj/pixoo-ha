"""Switch platform for Pixoo integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from .pixooasync import PixooAsync

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import PixooSystemCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PixooSwitchEntityDescription(SwitchEntityDescription):
    """Class describing Pixoo switch entities."""
    
    is_on_fn: Callable[[dict], bool] | None = None
    turn_on_fn: Callable[[PixooAsync], Awaitable[Any]]
    turn_off_fn: Callable[[PixooAsync], Awaitable[Any]]
    restore_state: bool = False  # Whether this is a write-only entity needing state restoration


# Write-only switch entities (need RestoreEntity)
WRITE_ONLY_SWITCHES = [
    PixooSwitchEntityDescription(
        key="timer",
        translation_key="timer",
        icon="mdi:timer",
        turn_on_fn=lambda api: api.set_timer(minutes=0, seconds=0, enabled=True),
        turn_off_fn=lambda api: api.set_timer(minutes=0, seconds=0, enabled=False),
        restore_state=True,
    ),
    PixooSwitchEntityDescription(
        key="alarm",
        translation_key="alarm",
        icon="mdi:alarm",
        turn_on_fn=lambda api: api.set_alarm(hour=0, minute=0, enabled=True),
        turn_off_fn=lambda api: api.set_alarm(hour=0, minute=0, enabled=False),
        restore_state=True,
    ),
    PixooSwitchEntityDescription(
        key="stopwatch",
        translation_key="stopwatch",
        icon="mdi:timer-play",
        turn_on_fn=lambda api: api.set_stopwatch(enabled=True),
        turn_off_fn=lambda api: api.set_stopwatch(enabled=False),
        restore_state=True,
    ),
    PixooSwitchEntityDescription(
        key="scoreboard",
        translation_key="scoreboard",
        icon="mdi:scoreboard",
        turn_on_fn=lambda api: api.set_scoreboard(red_score=0, blue_score=0),
        turn_off_fn=lambda api: api.set_scoreboard(red_score=0, blue_score=0),
        restore_state=True,
    ),
    PixooSwitchEntityDescription(
        key="noise_meter",
        translation_key="noise_meter",
        icon="mdi:microphone",
        turn_on_fn=lambda api: api.set_noise_meter(enabled=True),
        turn_off_fn=lambda api: api.set_noise_meter(enabled=False),
        restore_state=True,
    ),
]

# Readable switch entities (use coordinator)
READABLE_SWITCHES = [
    PixooSwitchEntityDescription(
        key="mirror_mode",
        translation_key="mirror_mode",
        icon="mdi:flip-horizontal",
        is_on_fn=lambda data: data.get("system", {}).get("mirror_mode", False),
        turn_on_fn=lambda api: api.set_mirror_mode(True),
        turn_off_fn=lambda api: api.set_mirror_mode(False),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixoo switch entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinators = data["coordinators"]
    system_coordinator = coordinators["system"]
    pixoo = data["pixoo"]
    device_name = entry.data.get(CONF_NAME, "Pixoo")

    # Add readable entities (coordinator-based)
    entities = [
        PixooReadableSwitchEntity(system_coordinator, description, pixoo, entry.entry_id, device_name)
        for description in READABLE_SWITCHES
    ]

    # Add write-only entities (RestoreEntity-based)
    entities.extend([
        PixooWriteOnlySwitchEntity(description, pixoo, entry.entry_id, device_name)
        for description in WRITE_ONLY_SWITCHES
    ])

    async_add_entities(entities)


class PixooReadableSwitchEntity(SwitchEntity):
    """Readable switch entity (coordinator-based)."""

    _attr_has_entity_name = True
    entity_description: PixooSwitchEntityDescription

    def __init__(
        self,
        coordinator: PixooSystemCoordinator,
        description: PixooSwitchEntityDescription,
        pixoo: PixooAsync,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the switch entity."""
        self._coordinator = coordinator
        self._pixoo = pixoo
        self._entry_id = entry_id
        self._device_name = device_name
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.last_update_success

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        if self.entity_description.is_on_fn:
            return self.entity_description.is_on_fn(self._coordinator.data)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self.entity_description.turn_on_fn(self._pixoo)
            await self._coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on %s: %s", self.entity_description.key, err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self.entity_description.turn_off_fn(self._pixoo)
            await self._coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off %s: %s", self.entity_description.key, err)
            raise


class PixooWriteOnlySwitchEntity(SwitchEntity, RestoreEntity):
    """Write-only switch entity (uses RestoreEntity for state persistence)."""

    _attr_assumed_state = True
    _attr_has_entity_name = True
    entity_description: PixooSwitchEntityDescription

    def __init__(
        self,
        description: PixooSwitchEntityDescription,
        pixoo: PixooAsync,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the switch entity."""
        self._pixoo = pixoo
        self._entry_id = entry_id
        self._device_name = device_name
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._is_on = False

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
    def is_on(self) -> bool:
        """Return true if switch is on from local state."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self.entity_description.turn_on_fn(self._pixoo)
            self._is_on = True
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn on %s: %s", self.entity_description.key, err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self.entity_description.turn_off_fn(self._pixoo)
            self._is_on = False
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to turn off %s: %s", self.entity_description.key, err)
            raise

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state not in ("unknown", "unavailable"):
            self._is_on = last_state.state == "on"
