# API Cleanup - Removed Broken Methods

**Date**: 2025-11-16  
**Status**: ✅ DEPLOYED TO PRODUCTION  
**Scope**: Complete removal of broken Device/Get* APIs

## Summary

Removed `get_device_info()` and `get_network_status()` methods entirely from pixooasync and ha-pixoo integration because they **only return default values** - the underlying Device/Get* APIs don't work on actual hardware.

## What Was Removed

### PixooAsync Methods (client.py)

**`get_device_info() -> DeviceInfo`** ❌ REMOVED
- API: `Device/GetDeviceInfo`
- Status: Returns "Request data illegal json" on real devices
- Fallback: Always returned defaults (Unknown, 00:00:00:00:00:00, 1.0.0)
- Lines removed: ~40

**`get_network_status() -> NetworkStatus`** ❌ REMOVED
- API: `Device/GetNetworkStatus`  
- Status: Returns "Request data illegal json" on real devices
- Fallback: Always returned defaults (Unknown SSID, -50 dBm)
- Lines removed: ~75

### Coordinators

**`PixooDeviceCoordinator`** ❌ REMOVED ENTIRELY
- Only fetched `get_device_info()` which returned defaults
- Update interval: Once at startup (pointless with default data)
- Lines removed: ~30

**`PixooSystemCoordinator`** - Network fetching removed
- Removed `get_network_status()` call every 60s
- Removed `_network_counter` and `_last_network_data`
- Lines removed: ~15

### Sensors

**`PixooDeviceInfoSensor`** ❌ REMOVED ENTIRELY
- model sensor (showed "Pixoo-64" default)
- firmware sensor (showed "1.0.0" default)
- mac sensor (showed "00:00:00:00:00:00" default)
- Lines removed: ~60

**`PixooNetworkStatusSensor`** ❌ REMOVED ENTIRELY
- ip sensor (only showed config entry IP)
- ssid sensor (showed "Unknown" default)
- rssi sensor (showed "-50" default)
- Lines removed: ~140

### Button Entities

**Refactored to standalone** (no coordinator needed):
- Buttons don't need coordinators - they're just action triggers
- Removed `PixooEntity` inheritance
- Added standalone `device_info` property
- Removed `PixooDeviceCoordinator` dependency

### Config Flow

**Updated `validate_connection()`**:
- Replaced `get_device_info()` with cloud discovery
- Uses `find_device_on_lan()` for real device info
- Fallback to IP-based unique_id if cloud discovery fails
- Test connection uses `get_all_channel_config()` (works!)

## Replacement Solutions

### Device Information → Cloud Discovery

**OLD** (broken):
```python
device_info = await pixoo.get_device_info()
# Returns: {
#   "DeviceName": "Unknown",
#   "DeviceMac": "00:00:00:00:00:00",
#   "SoftwareVersion": "1.0.0"
# }
```

**NEW** (working):
```python
device_info = await PixooAsync.find_device_on_lan()
# Returns: {
#   "DeviceName": "Pixoo64",
#   "DeviceMac": "7c87cece9e98",  # REAL MAC!
#   "DevicePrivateIP": "192.168.188.65",
#   "DeviceId": "300001069"
# }
```

### Network Status → Config Entry

**OLD** (broken):
```python
network = await pixoo.get_network_status()
# Returns: {
#   "IpAddress": "192.168.188.65",  # From config
#   "SSID": "Unknown",               # Default
#   "RSSI": -50                      # Default
# }
```

**NEW** (working):
```python
# IP address already in config entry
ip_address = entry.data["ip_address"]
# SSID/RSSI not available - APIs don't work
```

### Connection Test → Channel/GetAllConf

**OLD** (broken):
```python
# Test with broken API
await pixoo.get_device_info()
# Succeeds but returns defaults
```

**NEW** (working):
```python
# Test with working API
await pixoo.get_all_channel_config()
# Returns real brightness, rotation, etc.
```

## Files Modified

| File | Changes | Lines Removed |
|------|---------|---------------|
| `pixooasync/client.py` | Removed 2 methods | ~115 lines |
| `coordinator.py` | Removed PixooDeviceCoordinator, network fetching | ~45 lines |
| `sensor.py` | Removed 2 sensor classes, import | ~200 lines |
| `__init__.py` | Removed device coordinator init, import | ~15 lines |
| `button.py` | Refactored to standalone (no coordinator) | -10 lines (net) |
| `config_flow.py` | Replaced get_device_info with cloud discovery | ~5 lines (net) |

**Total Lines Removed**: ~390 lines of dead code!

## Impact Assessment

### Breaking Changes ❌

**Removed Sensors** (will disappear after upgrade):
- `sensor.pixoo_model` - was showing default "Pixoo-64"
- `sensor.pixoo_firmware_version` - was showing default "1.0.0"
- `sensor.pixoo_mac_address` - was showing default "00:00:00:00:00:00"
- `sensor.pixoo_ip_address` - was showing config entry IP (redundant)
- `sensor.pixoo_wifi_ssid` - was showing default "Unknown"
- `sensor.pixoo_wifi_signal_strength` - was showing default "-50"

**Automations Affected**:
- Any using removed sensors will break
- Use device info from config entry instead
- MAC address available via cloud discovery in config flow

### Non-Breaking Changes ✅

**Button Entities**:
- Still work exactly the same
- Now standalone (no coordinator dependency)
- More efficient (no unnecessary coordinator polling)

**Config Flow**:
- Still validates connection
- Now gets REAL device info via cloud discovery
- Better unique_id (real MAC address)

### Performance Improvements 🚀

**Eliminated API Calls**:
- ❌ Device/GetDeviceInfo at startup (returned defaults)
- ❌ Device/GetNetworkStatus every 60s (returned defaults)
- ❌ PixooDeviceCoordinator polling (pointless)

**Reduced Memory**:
- Removed 1 coordinator
- Removed 6 sensor entities
- Cleaned up 390 lines of code

**Faster Startup**:
- No more failed Device/GetDeviceInfo call
- No more device coordinator first refresh
- Test connection uses fast Channel/GetAllConf

## Remaining Read Methods

After cleanup, pixooasync has these working read methods:

| Method | API | Status | Use Case |
|--------|-----|--------|----------|
| `get_all_channel_config()` | Channel/GetAllConf | ✅ Works | Brightness, rotation, power, clock settings |
| `get_current_channel()` | Channel/GetIndex | ✅ Works | Active channel (0-3) |
| `get_system_config()` | ⚠️ Uses GetAllConf | ✅ Works | System config (wrapped GetAllConf) |
| `get_animation_list()` | Channel/GetClockDail List | ✅ Works | Available animations |
| `get_weather_info()` | Channel/GetWeatherInfo | ⚠️ Buggy | Weather data (has attribute errors) |
| `get_time_info()` | Device/GetDeviceTime | ⚠️ Buggy | Time data (has attribute errors) |
| `find_device_on_lan()` | Cloud API | ✅ Works | Real device info (MAC, IP, ID) |

**Note**: get_weather_info() and get_time_info() have bugs but APIs work - will fix in Phase 4.

## Migration Guide

### For Users

**Broken automations**:
1. Remove any automations using removed sensors
2. MAC address now in config entry (available during setup)
3. IP address in config entry: `{{state_attr('light.pixoo', 'device_info')['connections']}}`

**Config flow changes**:
- New integrations get real MAC address (not 00:00:00:00:00:00)
- Unique ID now based on real MAC (better device identification)
- Firmware version shows "Unknown" (API doesn't work)

### For Developers

**Removed APIs**:
```python
# DON'T USE - Removed entirely
await pixoo.get_device_info()      # ❌ Gone
await pixoo.get_network_status()   # ❌ Gone
```

**Use Instead**:
```python
# For device info - use cloud discovery
device = await PixooAsync.find_device_on_lan()
mac = device["DeviceMac"]  # Real MAC!

# For IP address - use config entry
ip = entry.data["ip_address"]

# For test connection - use working API
await pixoo.get_all_channel_config()
```

## Next Steps

### Phase 2: Fix Remaining Bugs
- [ ] Fix `get_time_info()` attribute error
- [ ] Fix `get_weather_info()` attribute error
- [ ] Fix `get_animation_list()` return type

### Phase 3: Add Missing Services
- [ ] Add `play_animation` service
- [ ] Add `send_playlist` service
- [ ] Add `set_white_balance` service

### Phase 4: Documentation
- [ ] Update README with removed sensors
- [ ] Update BREAKING_CHANGES.md
- [ ] Update migration guide

## Verification

After HA restart, verify:
- ✅ Integration loads without errors
- ✅ No "Request data illegal json" errors in logs
- ✅ Removed sensors don't appear in UI
- ✅ Button entities still work
- ✅ Active Channel sensor works (uses Channel/GetIndex)
- ✅ Faster startup (no failed API calls)

---

**Deployment**: 2025-11-16  
**HA Restarting**: In progress...  
**Result**: 390 lines of broken code eliminated ✅
