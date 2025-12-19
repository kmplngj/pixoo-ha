"""Data update coordinators for Pixoo integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from .pixooasync import PixooAsync
from .pixooasync.models import DeviceInfo, NetworkStatus, SystemConfig, WeatherInfo, TimeInfo, TimerConfig, AlarmConfig, StopwatchConfig
from .pixooasync.enums import Channel

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    UPDATE_INTERVAL_DEVICE,
    UPDATE_INTERVAL_SYSTEM,
    UPDATE_INTERVAL_NETWORK,
    UPDATE_INTERVAL_WEATHER,
    UPDATE_INTERVAL_TOOL,
    UPDATE_INTERVAL_GALLERY,
)

_LOGGER = logging.getLogger(__name__)


class PixooDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Base coordinator for Pixoo device data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        pixoo: PixooAsync,
        name: str,
        update_interval: timedelta | None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self.pixoo = pixoo


# PixooDeviceCoordinator removed - Device/GetDeviceInfo API doesn't work
# Use cloud discovery (find_device_on_lan) in config flow instead


class PixooSystemCoordinator(PixooDataUpdateCoordinator):
    """Coordinator for system and network status (30s system, 60s network)."""

    def __init__(self, hass: HomeAssistant, pixoo: PixooAsync) -> None:
        """Initialize system coordinator."""
        super().__init__(
            hass,
            pixoo,
            name=f"{DOMAIN}_system",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SYSTEM),
        )
        # Optimistic state fields (write-only API aspects)
        self._optimistic_channel: str | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch system and network data from the device."""
        try:
            data: dict[str, Any] = {}

            # Always fetch system config (30s interval) - now uses Channel/GetAllConf which works!
            system_config: SystemConfig = await self.pixoo.get_system_config()
            data["system"] = {
                "brightness": system_config.brightness,
                "rotation": system_config.rotation,
                "mirror_mode": system_config.mirror_mode,
                "temperature_mode": system_config.temperature_mode,
                "hour_mode": system_config.hour_mode,
                "screen_power": system_config.screen_power,
            }

            # Fetch current channel (Channel/GetIndex API works!)
            channel_index: int = await self.pixoo.get_current_channel()
            data["channel_index"] = channel_index

            # Always provide optimistic channel value (None if not set yet)
            data["system"]["optimistic_channel"] = self._optimistic_channel

            # Fetch time info (30s interval)
            try:
                time_info: TimeInfo | None = await self.pixoo.get_time_info()
                if time_info is not None:
                    data["time"] = {
                        "utc_time": time_info.utc_time,
                        "local_time": time_info.local_time,
                    }
                else:
                    data["time"] = None
            except Exception as time_err:
                _LOGGER.debug("Time info not available: %s", time_err)
                data["time"] = None

            # Network status removed - Device/GetNetworkStatus API doesn't work
            # IP address is already available from config entry

            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching system data: {err}") from err


class PixooWeatherCoordinator(PixooDataUpdateCoordinator):
    """Coordinator for weather and time information (5 minute interval)."""

    def __init__(self, hass: HomeAssistant, pixoo: PixooAsync) -> None:
        """Initialize weather coordinator."""
        super().__init__(
            hass,
            pixoo,
            name=f"{DOMAIN}_weather",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_WEATHER),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch weather and time data from the device."""
        try:
            data: dict[str, Any] = {}

            try:
                weather_info: WeatherInfo | None = await self.pixoo.get_weather_info()
                if weather_info is not None:
                    data["weather"] = {
                        "temperature": weather_info.CurTemp,
                        "condition": weather_info.Weather,
                        "min_temp": weather_info.MinTemp,
                        "max_temp": weather_info.MaxTemp,
                        "humidity": weather_info.Humidity,
                        "pressure": weather_info.Pressure,
                    }
                else:
                    data["weather"] = None
            except Exception as weather_err:
                _LOGGER.debug("Weather info not available: %s", weather_err)
                data["weather"] = None

            try:
                time_info: TimeInfo | None = await self.pixoo.get_time_info()
                if time_info is not None:
                    data["time"] = {
                        "utc_time": time_info.utc_time,
                        "local_time": time_info.local_time,
                    }
                else:
                    data["time"] = None
            except Exception as time_err:
                _LOGGER.debug("Time info not available: %s", time_err)
                data["time"] = None

            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching weather/time data: {err}") from err


class PixooGalleryCoordinator(PixooDataUpdateCoordinator):
    """Coordinator for gallery/animation list (on-demand updates)."""

    def __init__(self, hass: HomeAssistant, pixoo: PixooAsync) -> None:
        """Initialize gallery coordinator."""
        super().__init__(
            hass,
            pixoo,
            name=f"{DOMAIN}_gallery",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_GALLERY),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch animation list from the device."""
        try:
            # Get list of available animations
            animations = await self.pixoo.get_animation_list()
            parsed = []
            for anim in animations:
                # Support pixooasync returning either a model or a tuple (id, name)
                if isinstance(anim, tuple) and len(anim) >= 2:
                    parsed.append({"id": anim[0], "name": anim[1]})
                else:
                    parsed.append({"id": getattr(anim, "animation_id", None), "name": getattr(anim, "name", None)})

            return {"animations": parsed}
        except Exception as err:
            raise UpdateFailed(f"Error fetching gallery data: {err}") from err
