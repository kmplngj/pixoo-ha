# Pixoo 16 Support Implementation Summary

## Overview
This implementation adds native support for the Divoom Pixoo 16 (16x16 pixel display) to the Home Assistant integration. The changes enable automatic detection of device models and proper handling of different screen sizes.

## Changes Made

### 1. Device Size Detection (`utils.py`)
**New Function:** `detect_device_size(model_name: str) -> int`

Parses device model names to determine screen size:
- `"Pixoo-16"` → 16 pixels
- `"Pixoo-64"` → 64 pixels  
- `"Pixoo Max"` → 32 pixels
- Unknown models → 64 pixels (default)

**Examples:**
```python
detect_device_size("Pixoo-16")  # Returns 16
detect_device_size("Pixoo-64")  # Returns 64
detect_device_size("Unknown")   # Returns 64 (backward compatible)
```

### 2. Configuration Flow (`config_flow.py`)
**Enhanced:** `validate_connection()` function

- Detects device model from Divoom cloud API during setup
- Extracts size using `detect_device_size()` function
- Stores size in config entry data with `CONF_DEVICE_SIZE` key

**Data Stored:**
```python
{
    CONF_HOST: "192.168.1.100",
    CONF_NAME: "Pixoo-16",
    CONF_DEVICE_SIZE: 16,  # NEW
}
```

### 3. Integration Initialization (`__init__.py`)
**Updated:** `async_setup_entry()`

- Reads device size from config entry: `entry.data.get(CONF_DEVICE_SIZE, 64)`
- Passes size to PixooAsync client: `PixooAsync(host, size=device_size)`
- Defaults to 64 for backward compatibility with existing installations

**Updated Services:**
- `handle_display_image()`: Uses device-specific target size for image resizing
- `handle_display_text()`: Uses device-specific width parameter

### 4. Entity Base Class (`entity.py`)
**Enhanced:** `PixooEntity.__init__()` and `device_info` property

- Accepts both legacy (entry_id, device_name) and new (ConfigEntry) signatures
- Shows correct model in device info: "Pixoo-16", "Pixoo-64", etc.
- Backward compatible with existing entity platforms

**Device Info:**
```python
{
    "model": "Pixoo-16",  # Previously always "Pixoo"
    "manufacturer": "Divoom",
    # ... other fields
}
```

### 5. Light Entity (`light.py`)
**Improvements:**

- Updated to use new ConfigEntry-based initialization
- Changed from `async_request_refresh()` to `async_refresh()` for immediate state updates
- Added debug logging for on/off operations

**Debug Output:**
```
DEBUG: Turning on Pixoo display
DEBUG: Screen turned on, refreshing coordinator
DEBUG: System config updated: brightness=80, screen_power=True
```

### 6. Media Player (`media_player.py`)
**Updated:** `_display_image()` method

- Retrieves device size from config entry
- Passes correct target size to `download_image()` function

### 7. Image Handling (`utils.py`)
**Enhanced:** `download_image()` function

- Accepts `target_size` parameter (default: `(64, 64)`)
- Automatically resizes images to match device resolution
- Uses high-quality LANCZOS resampling

### 8. Coordinator (`coordinator.py`)
**Enhanced:** System coordinator

- Added debug logging showing brightness and screen_power values
- Helps troubleshoot on/off state synchronization issues

### 9. Testing (`tests/`)
**New:** `test_utils.py`

Comprehensive tests for device size detection:
```python
def test_detect_device_size_pixoo_16():
    assert detect_device_size("Pixoo-16") == 16
    
def test_detect_device_size_pixoo_64():
    assert detect_device_size("Pixoo-64") == 64
    
def test_detect_device_size_unknown():
    assert detect_device_size("Unknown") == 64  # Default
```

**Updated:** `conftest.py`
- Added `CONF_DEVICE_SIZE` to test fixtures

### 10. Documentation (`README.md`)
**Added Sections:**

- Supported Devices list with Pixoo 16
- Automatic size detection explanation
- Pixoo 16-specific troubleshooting guide
- On/off state synchronization debugging steps

## Backward Compatibility

All changes are **fully backward compatible**:

1. **Existing Installations:** Config entries without `CONF_DEVICE_SIZE` default to 64
2. **Entity Platforms:** Support both old and new initialization signatures
3. **API Calls:** All existing functionality preserved

## Testing Checklist

- [x] Device size detection for various model names
- [x] Config flow stores device size correctly
- [x] PixooAsync client receives correct size parameter
- [x] Images automatically resize to device resolution
- [x] Device info shows correct model name
- [x] Backward compatibility with existing installations
- [ ] Physical testing on actual Pixoo 16 device
- [ ] Verify on/off state synchronization on Pixoo 16
- [ ] Test image display quality on 16x16 screen
- [ ] Verify all entities work on Pixoo 16

## Known Issues & Limitations

1. **Physical Device Testing:** Implementation based on API documentation and user reports. Needs validation on actual Pixoo 16 hardware.

2. **On/Off State Sync:** The integration now uses `async_refresh()` for immediate updates, but physical button presses may still take up to 30 seconds to reflect (coordinator polling interval).

3. **Image Quality:** Very detailed images may lose clarity when scaled to 16x16. Users should prefer pixel art style images for best results.

## Debugging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: info
  logs:
    custom_components.pixoo: debug
```

Look for these log messages:
- `"System config updated: brightness=X, screen_power=Y"`
- `"Turning on/off Pixoo display"`
- `"Screen turned on/off, refreshing coordinator"`

## Next Steps

1. Test on physical Pixoo 16 device
2. Gather user feedback on state synchronization
3. Consider adding device size to diagnostics data
4. Monitor for any edge cases in production use
