"""Base entity class for Pixoo integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PixooDataUpdateCoordinator


class PixooEntity(CoordinatorEntity[PixooDataUpdateCoordinator]):
    """Base entity for Pixoo devices."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PixooDataUpdateCoordinator,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{self.__class__.__name__}"
        self._device_name = device_name
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Pixoo device."""
        device_data = None
        if self.coordinator.data:
            device_data = self.coordinator.data.get("device_info")

        # Get IP from config entry or network status
        ip_address = None
        if hasattr(self.coordinator, 'config_entry'):
            ip_address = self.coordinator.config_entry.data.get("ip_address")

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
            manufacturer="Divoom",
            model=device_data.get("device_model", "Pixoo") if device_data else "Pixoo",
            sw_version=device_data.get("software_version") if device_data else None,
            configuration_url=f"http://{ip_address}" if ip_address else None,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
