"""Sensor platform for Pixoo integration."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import (
    PixooSystemCoordinator,
)
from .entity import PixooEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixoo sensor entities."""
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]

    system_coordinator: PixooSystemCoordinator = coordinators["system"]

    entry_id = entry.entry_id
    device_name = entry.title

    entities: list[SensorEntity] = [
        # Device info sensors removed - Device/GetDeviceInfo API doesn't work
        # Network sensors removed - Device/GetNetworkStatus API doesn't work
        # Use cloud discovery in config flow for MAC address instead

        # System configuration sensors
        PixooChannelSensor(system_coordinator, entry_id, device_name),  # Uses Channel/GetIndex

        # Weather sensor (if weather configured)
        PixooWeatherSensor(system_coordinator, entry_id, device_name),

        # Time sensor
        PixooTimeSensor(system_coordinator, entry_id, device_name),

        # Tool state sensors removed - write-only APIs with no readable state
    ]

    async_add_entities(entities)


# PixooDeviceInfoSensor removed - Device/GetDeviceInfo API doesn't work
# PixooNetworkStatusSensor removed - Device/GetNetworkStatus API doesn't work
# Use cloud discovery (find_device_on_lan) in config flow for device info instead


class PixooChannelSensor(PixooEntity, SensorEntity):
    """Active channel sensor (using Channel/GetIndex API)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:television-classic"

    def __init__(
        self,
        coordinator: PixooSystemCoordinator,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id, device_name)
        self._attr_unique_id = f"{entry_id}_active_channel"
        self._attr_translation_key = "active_channel"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._device_name} Active Channel"

    @property
    def native_value(self) -> str | None:
        """Return the current channel name."""
        channel_index = self.coordinator.data.get("channel_index")
        if channel_index is None:
            return None

        # Map channel index to name
        channel_map = {
            0: "Faces",
            1: "Cloud",
            2: "Visualizer",
            3: "Custom",
        }
        return channel_map.get(channel_index, "Unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional channel attributes."""
        system_config = self.coordinator.data.get("system")
        if not system_config:
            return {}

        return {
            "channel_index": self.coordinator.data.get("channel_index", 0),
            "rotation": system_config.get("rotation"),
            "mirror_mode": system_config.get("mirror_mode"),
            "brightness": system_config.get("brightness"),
        }


class PixooWeatherSensor(PixooEntity, SensorEntity):
    """Weather information sensor."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [
        "clear",
        "cloudy",
        "rain",
        "snow",
        "thunderstorm",
        "fog",
        "unknown",
    ]

    def __init__(
        self,
        coordinator: PixooSystemCoordinator,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id, device_name)
        self._attr_unique_id = f"{entry_id}_weather"
        self._attr_translation_key = "weather"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._device_name} Weather Condition"

    @property
    def native_value(self) -> str | None:
        """Return the weather condition."""
        weather_info = self.coordinator.data.get("weather")
        if not weather_info:
            return "unknown"

        return weather_info.get("condition", "unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional weather attributes."""
        weather_info = self.coordinator.data.get("weather")
        if not weather_info:
            return {}

        return {
            "temperature": weather_info.get("temperature"),
            "humidity": weather_info.get("humidity"),
            "min_temp": weather_info.get("min_temp"),
            "max_temp": weather_info.get("max_temp"),
            "pressure": weather_info.get("pressure"),
        }

    @property
    def icon(self) -> str:
        """Return weather icon."""
        return "mdi:weather-partly-cloudy"


class PixooTimeSensor(PixooEntity, SensorEntity):
    """Time information sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_registry_enabled_default = False  # Disabled by default

    def __init__(
        self,
        coordinator: PixooSystemCoordinator,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id, device_name)
        self._attr_unique_id = f"{entry_id}_time"
        self._attr_translation_key = "time"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._device_name} Device Time"

    @property
    def native_value(self) -> datetime | None:
        """Return the device time as datetime (timestamp device class)."""
        time_info = self.coordinator.data.get("time")
        if not time_info:
            return None

        # TIMESTAMP device class expects datetime object
        utc_time = time_info.get("utc_time")
        if utc_time:
            return datetime.fromtimestamp(utc_time, tz=timezone.utc)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional time attributes."""
        time_info = self.coordinator.data.get("time")
        if not time_info:
            return {}

        return {
            "utc_timestamp": time_info.get("utc_time"),
            "local_time": time_info.get("local_time"),
        }

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:clock-outline"
