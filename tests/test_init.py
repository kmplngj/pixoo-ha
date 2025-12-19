"""Test Pixoo integration initialization."""

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.pixoo.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant, mock_pixoo, mock_config_entry) -> None:
    """Test successful setup of config entry."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    
    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry(hass: HomeAssistant, mock_pixoo, mock_config_entry) -> None:
    """Test successful unload of config entry."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]
    mock_pixoo.close.assert_called_once()


async def test_setup_entry_connection_error(hass: HomeAssistant, mock_pixoo, mock_config_entry) -> None:
    """Test setup fails when connection fails."""
    mock_config_entry.add_to_hass(hass)
    mock_pixoo.get_device_info.side_effect = Exception("Connection error")
    
    with patch("custom_components.pixoo.PixooAsync", return_value=mock_pixoo):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    
    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY
