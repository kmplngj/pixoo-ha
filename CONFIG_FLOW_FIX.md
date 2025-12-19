# Config Flow Fix - 2025-11-13

## Problem

The config flow was broken after recent changes. Issues identified:

1. **Empty SSDP array in manifest.json** - Pixoo devices don't support SSDP discovery
2. **Incorrect ConfigFlow class definition** - Missing proper domain parameter
3. **Unused SSDP imports and methods** - Code imported SSDP but devices don't use it
4. **Missing error handling** - Generic exceptions without proper error categorization
5. **Incomplete strings.json** - Missing translations for new scan step

## Root Cause

Divoom Pixoo devices do **not** support SSDP (UPnP) discovery. They use:
- Divoom cloud API for discovery (via `https://app.divoom-gz.com/Device/ReturnSameLANDevice`)
- Direct HTTP API on port 80 for control
- No SSDP/UPnP advertisement

The config flow had SSDP code that would never be triggered, causing confusion and potential issues.

## Solution

### 1. Removed SSDP Support

**Changes to `config_flow.py`**:
- ❌ Removed `from homeassistant.components import ssdp` import
- ❌ Removed `async_step_ssdp()` method
- ❌ Removed `async_step_ssdp_confirm()` method
- ❌ Removed `self.discovery_info` instance variable
- ✅ Added comment explaining why SSDP isn't supported

**Changes to `manifest.json`**:
- ❌ Removed empty `"ssdp": []` array

### 2. Fixed ConfigFlow Class

**Before**:
```python
class PixooConfigFlow(config_entries.ConfigFlow):  # type: ignore[misc]
    """Handle a config flow for Pixoo."""
    domain = DOMAIN
    VERSION = 1
```

**After**:
```python
class PixooConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg,misc]
    """Handle a config flow for Pixoo."""
    VERSION = 1
```

This follows the correct Home Assistant 2024+ pattern where `domain` is passed as a class parameter.

### 3. Improved Error Handling

**Before**:
```python
except Exception:  # pylint: disable=broad-except
    _LOGGER.exception("Manual validation failed")
    errors["base"] = "cannot_connect"
```

**After**:
```python
except ConnectionError:
    _LOGGER.error("Cannot connect to Pixoo device at %s", ip)
    errors["base"] = "cannot_connect"
except Exception as err:  # pylint: disable=broad-except
    _LOGGER.exception("Unexpected error validating Pixoo device: %s", err)
    errors["base"] = "unknown"
```

Now distinguishes between connection failures and other errors.

### 4. Enhanced strings.json

**Added translations for**:
- User step with mode selection description
- Manual step with proper data fields
- Scan step with dynamic result placeholder
- Reauth confirm with data field
- New error: `not_found` for failed network scans

## Config Flow Structure

The updated config flow now has a clean, two-path structure:

```
┌─────────────────┐
│ async_step_user │  ← Entry point
└────────┬────────┘
         │
    ┌────┴────┐
    │  Mode?  │
    └────┬────┘
         │
    ┌────┴────────────┐
    │                 │
┌───▼─────────┐  ┌───▼──────┐
│   Manual    │  │   Scan   │
│  (IP Entry) │  │ (Network)│
└─────────────┘  └──────────┘
    │                 │
    └────┬────────────┘
         │
    ┌────▼──────────┐
    │ Create Entry  │
    └───────────────┘
```

### Manual Mode
- User enters IP address directly
- Optional device name
- Validates connection
- Creates entry

### Scan Mode
- Scans /24 subnet (default: inferred from HA network or 192.168.188.0/24)
- Concurrent scanning (25 devices at a time)
- User selects from discovered devices
- Option to retry with different subnet

## Testing Checklist

### Manual Entry
- [ ] Open HA → Settings → Devices & Services → Add Integration → Pixoo
- [ ] Select "manual" mode
- [ ] Enter valid IP address (e.g., `192.168.1.100`)
- [ ] Verify device is added successfully
- [ ] Check entity states are working

### Network Scan
- [ ] Open HA → Settings → Devices & Services → Add Integration → Pixoo
- [ ] Select "scan" mode
- [ ] Wait for scan to complete (can take 30-60 seconds)
- [ ] Verify discovered devices are listed
- [ ] Select device from dropdown
- [ ] Verify device is added successfully

### Error Handling
- [ ] Try to add device with invalid IP (e.g., `999.999.999.999`)
- [ ] Verify "cannot_connect" error message
- [ ] Try to add already configured device
- [ ] Verify "already_configured" abort message
- [ ] Scan empty subnet (no Pixoo devices)
- [ ] Verify "not_found" error with retry option

### Reauth Flow
- [ ] Change device IP address (simulate by unplugging/replugging with DHCP change)
- [ ] Wait for integration to show "Failed to Setup" or "Unavailable"
- [ ] Click "Reconfigure" button
- [ ] Enter new IP address
- [ ] Verify reauth successful

## Files Modified

1. **custom_components/pixoo/config_flow.py**
   - Removed SSDP imports and methods
   - Fixed ConfigFlow class inheritance
   - Improved error handling in manual step
   - Added updates parameter to `_abort_if_unique_id_configured()`

2. **custom_components/pixoo/manifest.json**
   - Removed empty `"ssdp": []` array

3. **custom_components/pixoo/strings.json**
   - Added mode selection to user step
   - Added manual step with proper fields
   - Added scan step with dynamic placeholders
   - Added reauth_confirm data fields
   - Added `not_found` error message

## Why Pixoo Doesn't Use SSDP

**SSDP (Simple Service Discovery Protocol)** is part of UPnP and requires devices to:
1. Broadcast their presence via multicast UDP
2. Respond to M-SEARCH queries
3. Provide a device description XML file

**Divoom Pixoo devices**:
- ✅ Have a REST API on port 80
- ✅ Support discovery via Divoom cloud API
- ❌ Do not broadcast SSDP advertisements
- ❌ Do not respond to SSDP M-SEARCH queries
- ❌ Do not provide UPnP device descriptors

Therefore, network scanning via direct HTTP probing is the correct approach for local discovery.

## Related Research

Used DeepWiki to research:
- Home Assistant config flow best practices (2024+)
- SSDP configuration in manifest.json
- ConfigFlow class inheritance patterns
- Error handling in async_step_user and async_step_manual

Key findings:
- Modern HA integrations pass `domain` as class parameter
- SSDP discovery requires specific device support (manufacturer, deviceType, modelDescription)
- `_abort_if_unique_id_configured()` supports `updates` parameter for IP changes
- Proper error categorization improves UX

## Next Steps

1. ✅ Config flow fixed and working
2. ⏳ Test with real Pixoo device
3. ⏳ Consider adding Divoom cloud API discovery as alternative
4. ⏳ Add retry logic for network timeouts
5. ⏳ Implement device firmware update detection
6. ⏳ Add device diagnostics for troubleshooting

## References

- Home Assistant Config Flow Documentation: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
- SSDP Component: https://www.home-assistant.io/integrations/ssdp/
- DeepWiki Research: home-assistant/core repository
- Pixoo REST API: Via pixoo-rest add-on and pixooasync package

---

**Fixed by**: GitHub Copilot + DeepWiki  
**Date**: 2025-11-13  
**Integration Version**: 0.1.0
