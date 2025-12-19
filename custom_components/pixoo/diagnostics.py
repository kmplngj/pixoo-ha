"""Diagnostics support for Pixoo integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    CONF_IP_ADDRESS,
    "device_mac",
    "mac_address",
    "ip_address",
    "ssid",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinators = data["coordinators"]

    diagnostics_data = {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
        },
        "coordinators": {},
    }

    # Device coordinator data (fetched once at startup)
    if "device" in coordinators:
        device_coord = coordinators["device"]
        diagnostics_data["coordinators"]["device"] = {
            "last_update_success": device_coord.last_update_success,
            "data": async_redact_data(device_coord.data, TO_REDACT) if device_coord.data else None,
        }

    # System coordinator data (30s polling)
    if "system" in coordinators:
        system_coord = coordinators["system"]
        diagnostics_data["coordinators"]["system"] = {
            "last_update_success": system_coord.last_update_success,
            "update_interval": str(system_coord.update_interval),
            "data": async_redact_data(system_coord.data, TO_REDACT) if system_coord.data else None,
        }

    # Weather coordinator data (5min polling)
    if "weather" in coordinators:
        weather_coord = coordinators["weather"]
        diagnostics_data["coordinators"]["weather"] = {
            "last_update_success": weather_coord.last_update_success,
            "update_interval": str(weather_coord.update_interval),
            "data": weather_coord.data if weather_coord.data else None,
        }

    # Gallery coordinator data (10s polling)
    if "gallery" in coordinators:
        gallery_coord = coordinators["gallery"]
        diagnostics_data["coordinators"]["gallery"] = {
            "last_update_success": gallery_coord.last_update_success,
            "update_interval": str(gallery_coord.update_interval),
            "data": gallery_coord.data if gallery_coord.data else None,
        }

    return diagnostics_data
