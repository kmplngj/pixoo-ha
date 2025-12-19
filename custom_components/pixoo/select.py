"""Select platform for Pixoo integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any

from .pixooasync import PixooAsync
from .pixooasync.enums import Channel, Rotation, TemperatureMode

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import PixooSystemCoordinator, PixooGalleryCoordinator
from .entity import PixooEntity


@dataclass(frozen=True, kw_only=True)
class PixooSelectEntityDescription(SelectEntityDescription):
    """Class describing Pixoo select entities."""

    current_fn: Callable[[Any], str] | None = None
    select_fn: Callable[[PixooAsync, str], Awaitable[Any]]
    restore_state: bool = False  # Whether this is a write-only entity needing state restoration


# Write-only select entities (need RestoreEntity)
WRITE_ONLY_SELECTS = [
    PixooSelectEntityDescription(
        key="channel",
        translation_key="channel",
        options=["faces", "cloud", "visualizer", "custom"],
        select_fn=lambda api, opt: api.set_channel(
            {"faces": Channel.FACES, "cloud": Channel.CLOUD, 
             "visualizer": Channel.VISUALIZER, "custom": Channel.CUSTOM}[opt]
        ),
        restore_state=True,
    ),
    PixooSelectEntityDescription(
        key="clock_face",
        translation_key="clock_face",
        options=[str(i) for i in range(1, 21)],
        select_fn=lambda api, opt: api.set_clock(int(opt)),
        restore_state=True,
    ),
    PixooSelectEntityDescription(
        key="visualizer",
        translation_key="visualizer",
        options=[str(i) for i in range(1, 6)],
        select_fn=lambda api, opt: api.set_visualizer(int(opt)),
        restore_state=True,
    ),
    PixooSelectEntityDescription(
        key="custom_page",
        translation_key="custom_page",
        options=[str(i) for i in range(1, 4)],
        select_fn=lambda api, opt: api.set_custom_page(int(opt)),
        restore_state=True,
    ),
]

# Readable select entities (use coordinator)
READABLE_SELECTS = [
    PixooSelectEntityDescription(
        key="rotation",
        translation_key="rotation",
        options=["normal", "rotate_90", "rotate_180", "rotate_270"],
        current_fn=lambda data: data.get("system", {}).get("rotation", "normal"),
        select_fn=lambda api, opt: api.set_rotation(
            {"normal": Rotation.NORMAL, "rotate_90": Rotation.ROTATE_90,
             "rotate_180": Rotation.ROTATE_180, "rotate_270": Rotation.ROTATE_270}[opt]
        ),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixoo select entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinators = data["coordinators"]
    system_coordinator = coordinators["system"]
    pixoo = data["pixoo"]
    device_name = entry.data.get(CONF_NAME, "Pixoo")

    # Add readable entities (coordinator-based)
    entities = [
        PixooSelectEntity(
            coordinator=system_coordinator,
            description=description,
            pixoo=pixoo,
            entry_id=entry.entry_id,
            device_name=device_name,
        )
        for description in READABLE_SELECTS
    ]

    # Add write-only entities (RestoreEntity-based)
    entities.extend([
        PixooWriteOnlySelectEntity(
            description=description,
            pixoo=pixoo,
            entry_id=entry.entry_id,
            device_name=device_name,
        )
        for description in WRITE_ONLY_SELECTS
    ])

    async_add_entities(entities)


class PixooSelectEntity(PixooEntity, SelectEntity):
    """Representation of a Pixoo select (coordinator-based, readable)."""

    entity_description: PixooSelectEntityDescription

    def __init__(
        self,
        coordinator: PixooSystemCoordinator,
        description: PixooSelectEntityDescription,
        pixoo: PixooAsync,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, entry_id, device_name)
        self.entity_description = description
        self._pixoo = pixoo
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        if self.entity_description.current_fn:
            return self.entity_description.current_fn(self.coordinator.data)
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_fn(self._pixoo, option)
        await self.coordinator.async_request_refresh()


class PixooWriteOnlySelectEntity(SelectEntity, RestoreEntity):
    """Representation of a Pixoo select (write-only, uses RestoreEntity)."""

    entity_description: PixooSelectEntityDescription
    _attr_assumed_state = True
    _attr_has_entity_name = True

    def __init__(
        self,
        description: PixooSelectEntityDescription,
        pixoo: PixooAsync,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the select entity."""
        self.entity_description = description
        self._pixoo = pixoo
        self._entry_id = entry_id
        self._device_name = device_name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_options = description.options
        self._current_option = description.options[0] if description.options else None

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
    def current_option(self) -> str | None:
        """Return the current option from local state."""
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_fn(self._pixoo, option)
        self._current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state not in ("unknown", "unavailable"):
            if last_state.state in self._attr_options:
                self._current_option = last_state.state


# Old entity classes removed - replaced by PixooSelectEntity and PixooWriteOnlySelectEntity with entity descriptions
