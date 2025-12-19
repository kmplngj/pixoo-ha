"""Test Pixoo config flow."""

from unittest.mock import patch

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
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    with patch("custom_components.pixoo.config_flow.PixooAsync", return_value=mock_pixoo):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_IP: "192.168.1.100",
                CONF_DEVICE_NAME: "Test Pixoo",
            },
        )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Pixoo"
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        "name": "Test Pixoo",
    }


async def test_user_flow_cannot_connect(hass: HomeAssistant, mock_pixoo) -> None:
    """Test user flow when connection fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    mock_pixoo.get_device_info.side_effect = Exception("Connection error")
    
    with patch("custom_components.pixoo.config_flow.PixooAsync", return_value=mock_pixoo):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_IP: "192.168.1.100",
            },
        )
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_already_configured(hass: HomeAssistant, mock_pixoo, mock_config_entry) -> None:
    """Test user flow when device is already configured."""
    mock_config_entry.add_to_hass(hass)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    with patch("custom_components.pixoo.config_flow.PixooAsync", return_value=mock_pixoo):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_IP: "192.168.1.100",
            },
        )
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_ssdp_flow_success(hass: HomeAssistant, mock_pixoo) -> None:
    """Test successful SSDP discovery flow."""
    with patch("custom_components.pixoo.config_flow.PixooAsync", return_value=mock_pixoo):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data={
                "ssdp_location": "http://192.168.1.100:80/",
                "manufacturer": "Divoom",
            },
        )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "ssdp_confirm"
    
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        "name": "Pixoo64",
    }


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
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    
    with patch("custom_components.pixoo.config_flow.PixooAsync", return_value=mock_pixoo):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_IP: "192.168.1.200",
            },
        )
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    
    # Verify entry was updated
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.200"
