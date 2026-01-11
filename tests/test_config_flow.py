"""Test Pixoo config flow."""

from unittest.mock import AsyncMock, patch
from typing import Any, cast

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.pixoo.const import CONF_DEVICE_IP, CONF_DEVICE_NAME, DOMAIN


async def test_user_flow_success(hass: HomeAssistant, mock_pixoo) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = cast(dict[str, Any], result)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    # Step 1: choose mode
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"mode": "manual"},
    )
    result = cast(dict[str, Any], result)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"

    validate_info = {
        "title": "Pixoo64",
        "unique_id": "AA:BB:CC:DD:EE:FF",
        "ip_address": "192.168.1.100",
        "model": "Pixoo64",
        "size": 64,
        "firmware_version": "Unknown",
        "device_id": "0",
    }

    with patch(
        "custom_components.pixoo.config_flow.validate_connection",
        new=AsyncMock(return_value=validate_info),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_IP: "192.168.1.100",
                CONF_DEVICE_NAME: "Test Pixoo",
            },
        )
    result = cast(dict[str, Any], result)
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Pixoo"
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        "name": "Test Pixoo",
        "device_size": 64,
    }


async def test_user_flow_cannot_connect(hass: HomeAssistant, mock_pixoo) -> None:
    """Test user flow when connection fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = cast(dict[str, Any], result)

    # Step 1: choose mode
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"mode": "manual"},
    )
    result = cast(dict[str, Any], result)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"

    with patch(
        "custom_components.pixoo.config_flow.validate_connection",
        new=AsyncMock(side_effect=ConnectionError("Connection error")),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_IP: "192.168.1.100",
            },
        )
    result = cast(dict[str, Any], result)
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_already_configured(hass: HomeAssistant, mock_pixoo, mock_config_entry) -> None:
    """Test user flow when device is already configured."""
    mock_config_entry.add_to_hass(hass)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = cast(dict[str, Any], result)
    
    # Step 1: choose mode
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"mode": "manual"},
    )
    result = cast(dict[str, Any], result)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "manual"

    validate_info = {
        "title": "Pixoo64",
        "unique_id": mock_config_entry.unique_id,
        "ip_address": "192.168.1.100",
        "model": "Pixoo64",
        "size": 64,
        "firmware_version": "Unknown",
        "device_id": "0",
    }

    with patch(
        "custom_components.pixoo.config_flow.validate_connection",
        new=AsyncMock(return_value=validate_info),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_IP: "192.168.1.100",
            },
        )
    result = cast(dict[str, Any], result)
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_ssdp_flow_success(hass: HomeAssistant, mock_pixoo) -> None:
    """Test SSDP discovery flow is not supported."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data={
            "ssdp_location": "http://192.168.1.100:80/",
            "manufacturer": "Divoom",
        },
    )
    result = cast(dict[str, Any], result)

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "ssdp_not_supported"


async def test_reauth_flow(hass: HomeAssistant, mock_pixoo, mock_config_entry) -> None:
    """Test reauth flow when IP address changes."""
    mock_config_entry.add_to_hass(hass)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )
    result = cast(dict[str, Any], result)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    
    validate_info = {
        "title": "Pixoo64",
        "unique_id": mock_config_entry.unique_id,
        "ip_address": "192.168.1.200",
        "model": "Pixoo64",
        "size": 64,
        "firmware_version": "Unknown",
        "device_id": "0",
    }

    with patch(
        "custom_components.pixoo.config_flow.validate_connection",
        new=AsyncMock(return_value=validate_info),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_IP: "192.168.1.200",
            },
        )
    result = cast(dict[str, Any], result)
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    # Verify entry was updated
    updated_entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert updated_entry is not None
    assert updated_entry.data[CONF_HOST] == "192.168.1.200"
