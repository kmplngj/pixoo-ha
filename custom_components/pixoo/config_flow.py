"""Config flow for Divoom Pixoo integration."""

from __future__ import annotations

import logging
from typing import Any

from .pixooasync import PixooAsync
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_DEVICE_IP, CONF_DEVICE_NAME, CONF_DEVICE_SIZE, DEFAULT_NAME, DOMAIN
from .utils import detect_device_size

_LOGGER = logging.getLogger(__name__)

# Initial mode selection: manual or scan
STEP_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("mode", default="manual"): vol.In(["manual", "scan"]),
    }
)

# Manual entry schema
STEP_MANUAL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_IP): cv.string,
        vol.Optional(CONF_DEVICE_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def validate_connection(
    hass: HomeAssistant, device_ip: str
) -> dict[str, Any]:
    """Validate the connection to the device and return device info."""
    pixoo = PixooAsync(device_ip)

    try:
        # Initialize the client (creates httpx.AsyncClient)
        await pixoo.initialize()
        
        # Test connection by fetching real config (Channel/GetAllConf works!)
        await pixoo.get_all_channel_config()
        
        # Try to get device info from cloud discovery
        device_info = await PixooAsync.find_device_on_lan()
        
        if device_info and device_info.get("DevicePrivateIP") == device_ip:
            # Found matching device via cloud discovery
            model_name = device_info.get("DeviceName", "Pixoo")
            device_size = detect_device_size(model_name)
            
            return {
                "title": model_name,
                "unique_id": device_info.get("DeviceMac", device_ip.replace(".", "")),
                "ip_address": device_ip,
                "model": model_name,
                "size": device_size,
                "device_id": device_info.get("DeviceId", "0"),
            }
        else:
            # Fallback if cloud discovery fails or no match
            return {
                "title": DEFAULT_NAME,
                "unique_id": device_ip.replace(".", ""),  # Use IP as unique_id fallback
                "ip_address": device_ip,
                "model": "Pixoo",
                "size": 64,  # Default to 64 for unknown devices
                "device_id": "0",
            }
    finally:
        await pixoo.close()


class PixooConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg,misc]
    """Handle a config flow for Pixoo."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        pass

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """First step: choose discovery mode."""
        if user_input is not None:
            mode = user_input["mode"]
            if mode == "scan":
                return await self.async_step_scan()
            return await self.async_step_manual()

        return self.async_show_form(step_id="user", data_schema=STEP_MODE_SCHEMA)

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manual IP entry step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            ip = user_input[CONF_DEVICE_IP]
            try:
                info = await validate_connection(self.hass, ip)
            except ConnectionError:
                _LOGGER.error("Cannot connect to Pixoo device at %s", ip)
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error validating Pixoo device: %s", err)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured(updates={CONF_HOST: ip})
                return self.async_create_entry(
                    title=user_input.get(CONF_DEVICE_NAME, info["title"]),
                    data={
                        CONF_HOST: ip,
                        CONF_NAME: user_input.get(CONF_DEVICE_NAME, info["title"]),
                        CONF_DEVICE_SIZE: info["size"],
                    },
                )
        return self.async_show_form(step_id="manual", data_schema=STEP_MANUAL_SCHEMA, errors=errors)

    # Note: Pixoo devices do not support SSDP discovery.
    # Discovery is handled via the Divoom cloud API.

    async def async_step_scan(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Discover Pixoo devices via Divoom cloud API."""
        errors: dict[str, str] = {}
        
        # If user selected a device, configure it
        if user_input and "choose_ip" in user_input:
            chosen_ip = user_input.get("choose_ip")
            if chosen_ip:
                try:
                    info = await validate_connection(self.hass, chosen_ip)
                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.exception("Error validating selected device: %s", err)
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(info["unique_id"])
                    self._abort_if_unique_id_configured(updates={CONF_HOST: chosen_ip})
                    return self.async_create_entry(
                        title=info["title"],
                        data={
                            CONF_HOST: chosen_ip,
                            CONF_NAME: info["title"],
                            CONF_DEVICE_SIZE: info["size"],
                        },
                    )
        
        # Discover devices via Divoom cloud API
        _LOGGER.debug("Starting Pixoo discovery via Divoom cloud API")
        found: list[dict[str, Any]] = []

        try:
            session = async_get_clientsession(self.hass)
            # Use POST request to Divoom cloud API (not GET!)
            resp = await session.post(
                "https://app.divoom-gz.com/Device/ReturnSameLANDevice",
                timeout=10,
            )
            _LOGGER.debug("Cloud API response status: %d", resp.status)
            result = await resp.json(content_type=None)
            _LOGGER.debug("Cloud API response: %s", result)

            # API returns "ReturnCode" not "error_code"
            if result.get("ReturnCode") == 0 and "DeviceList" in result:
                device_list = result["DeviceList"]
                _LOGGER.debug("Found %d devices from Divoom API", len(device_list))

                # Validate each discovered device
                for device in device_list:
                    ip = device.get("DevicePrivateIP")
                    if ip:
                        try:
                            info = await validate_connection(self.hass, ip)
                            found.append(info)
                        except Exception:  # pylint: disable=broad-except
                            _LOGGER.debug("Device at %s not reachable, skipping", ip)
                            continue
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Error during Pixoo discovery: %s", err)
            errors["base"] = "cannot_connect"
        
        if not found and not errors:
            return self.async_show_form(
                step_id="scan",
                description_placeholders={"result": "No Pixoo devices found on your network"},
                errors={"base": "not_found"},
                data_schema=vol.Schema(
                    {
                        vol.Optional("retry", default=False): cv.boolean,
                    }
                ),
            )
        
        if errors:
            return self.async_show_form(
                step_id="scan",
                description_placeholders={"result": "Discovery failed"},
                errors=errors,
                data_schema=vol.Schema(
                    {
                        vol.Optional("retry", default=False): cv.boolean,
                    }
                ),
            )
        
        options = {d["ip_address"]: f"{d['title']} ({d['ip_address']})" for d in found}
        
        return self.async_show_form(
            step_id="scan",
            data_schema=vol.Schema(
                {
                    vol.Required("choose_ip"): vol.In(options),
                }
            ),
            description_placeholders={"result": f"Found {len(found)} Pixoo device(s)"},
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle reauth when device IP changes."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm reauth with new IP address."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_connection(
                    self.hass, user_input[CONF_DEVICE_IP]
                )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Error validating Pixoo device during reauth")
                errors["base"] = "cannot_connect"
            else:
                # Update the existing entry with new IP
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={
                            CONF_HOST: user_input[CONF_DEVICE_IP],
                            CONF_NAME: entry.data.get(CONF_NAME, info["title"]),
                        },
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_IP): cv.string,
                }
            ),
            errors=errors,
        )
