"""Base entity class for Pixoo integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_DEVICE_SIZE
from .coordinator import PixooDataUpdateCoordinator


class PixooEntity(CoordinatorEntity[PixooDataUpdateCoordinator]):
    """Base entity for Pixoo devices."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PixooDataUpdateCoordinator,
        entry_id_or_entry: str | ConfigEntry,
        device_name: str | None = None,
    ) -> None:
        """Initialize the entity.
        
        Args:
            coordinator: Data update coordinator
            entry_id_or_entry: Config entry ID (legacy) or ConfigEntry object (new)
            device_name: Device name (legacy, ignored if entry is provided)
        """
        super().__init__(coordinator)
        
        # Support both old (entry_id, device_name) and new (entry) signatures
        if isinstance(entry_id_or_entry, ConfigEntry):
            self._entry = entry_id_or_entry
            self._entry_id = entry_id_or_entry.entry_id
            self._device_name = entry_id_or_entry.data.get(CONF_NAME, "Pixoo")
        else:
            # Legacy support - store entry_id and device_name
            self._entry = None
            self._entry_id = entry_id_or_entry
            self._device_name = device_name or "Pixoo"
        
        self._attr_unique_id = f"{self._entry_id}_{self.__class__.__name__}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Pixoo device."""
        # Use config entry if available (new approach)
        if self._entry:
            device_size = self._entry.data.get(CONF_DEVICE_SIZE, 64)
            ip_address = self._entry.data.get(CONF_HOST)
            model = f"Pixoo-{device_size}"
        else:
            # Legacy fallback - use generic model
            ip_address = None
            model = "Pixoo"

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
            manufacturer="Divoom",
            model=model,
            configuration_url=f"http://{ip_address}" if ip_address else None,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
