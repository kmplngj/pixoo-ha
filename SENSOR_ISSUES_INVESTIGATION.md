# ha-pixoo Integration Issues - Investigation Results

**Date**: 2025-11-16  
**Investigation**: Sensor issues and missing features

## Issue Summary

| # | Issue | Root Cause | Status | Fix Required |
|---|-------|------------|--------|--------------|
| 1 | Wi-Fi SSID not working | Device API doesn't support `Device/GetNetworkStatus` command | ❌ **API Limitation** | Remove sensor or mark unavailable |
| 2 | Wi-Fi Signal Strength not working | Same as #1 - API command not supported | ❌ **API Limitation** | Remove sensor or mark unavailable |
| 3 | Active Channel not working | Device API doesn't support `Device/GetSystemConfig` command | ❌ **API Limitation** | Use `Channel/GetIndex` instead |
| 4 | MAC Address not working | Device API doesn't support `Device/GetDeviceInfo` command | ❌ **API Limitation** | Extract from config entry or remove |
| 5 | Firmware always shows 1.0.0 | Same as #4 - default fallback value used | ❌ **API Limitation** | Remove sensor or mark unavailable |
| 6 | Device Time unavailable | Needs investigation | 🔄 **Investigating** | TBD |
| 7 | Brightness sensor + number + light | Duplicate functionality | ⚠️ **Design Issue** | Remove sensor, keep light entity |
| 8 | Missing pixooasync features | Needs comprehensive audit | 🔄 **Analyzing** | TBD |

## Detailed Investigation

### API Test Results

Tested against device at `192.168.188.65`:

```bash
Command: Device/GetDeviceInfo
Response: {"error_code": "Request data illegal json"}
Status: ❌ NOT SUPPORTED

Command: Device/GetNetworkStatus  
Response: {"error_code": "Request data illegal json"}
Status: ❌ NOT SUPPORTED

Command: Device/GetSystemConfig
Response: {"error_code": "Request data illegal json"}
Status: ❌ NOT SUPPORTED

Command: Channel/GetIndex
Response: {"error_code": 0, "SelectIndex": 1}
Status: ✅ SUPPORTED
```

### Root Cause Analysis

**PixooAsync Client Implementation**:
The `pixooasync` library has fallback logic for unsupported commands:

```python
async def get_device_info(self) -> DeviceInfo:
    payload = self._create_command_payload("Device/GetDeviceInfo")
    response = await self._client.post(self._url, json=payload)
    data = response.json()
    
    # Parse response - uses .get() with defaults
    device_data = data.get("DeviceInfo", {})  # Returns {} if error
    return DeviceInfo(
        device_name=device_data.get("DeviceName", "Unknown"),  # ❌ Default
        device_id=device_data.get("DeviceId", "0"),            # ❌ Default
        device_mac=device_data.get("DeviceMac", "00:00:00:00:00:00"),  # ❌ Default
        hardware_version=device_data.get("HardwareVersion", "1.0"),    # ❌ Default
        software_version=device_data.get("SoftwareVersion", "1.0.0"),  # ❌ Default (Issue #5!)
        device_model=device_data.get("DeviceModel", f"Pixoo-{self.size}"),
        brightness=device_data.get("Brightness", 50),  # ❌ Always 50% (Issue #7!)
    )
```

**The Problem**: When the API returns an error, PixooAsync returns default values instead of raising an exception. This makes sensors show incorrect "Unknown" / "1.0.0" / "50%" values.

### Issue #1 & #2: Wi-Fi SSID and Signal Strength

**Current Implementation**:
```python
# sensor.py
class PixooNetworkStatusSensor(PixooEntity, SensorEntity):
    @property
    def native_value(self) -> str | int | None:
        network_data = self.coordinator.data.get("network")
        if not network_data:
            return None
        
        if self._sensor_type == "ssid":
            return network_data.get("ssid")  # Returns "Unknown"
        elif self._sensor_type == "rssi":
            return network_data.get("rssi")  # Returns -50 (default)
```

**Fix**: Either remove these sensors or check if the API actually returned data:
```python
async def get_network_status(self) -> NetworkStatus | None:
    """Returns None if API doesn't support the command."""
    response = await self._client.post(self._url, json=payload)
    data = response.json()
    
    if "error_code" in data and data["error_code"] != 0:
        return None  # API doesn't support this command
    
    # ... rest of parsing
```

### Issue #3: Active Channel

**Current Implementation**:
```python
# sensor.py - tries to read from system_config
PixooSystemConfigSensor(system_coordinator, entry_id, device_name, "channel")

# But coordinator doesn't fetch it because API doesn't support it
data["system"]["channel"] = "unknown"  # Commented out in coordinator
```

**Fix**: Use the working `Channel/GetIndex` API:
```python
async def get_current_channel(self) -> int:
    """Get currently selected channel index (0-3)."""
    payload = self._create_command_payload("Channel/GetIndex")
    response = await self._client.post(self._url, json=payload)
    data = response.json()
    
    return data.get("SelectIndex", 0)  # Returns 0-3
```

Then map to channel names:
```python
CHANNEL_MAP = {
    0: "faces",  # Clock faces
    1: "cloud",  # Cloud channel
    2: "visualizer",  # Visualizer
    3: "custom",  # Custom pages
}
```

### Issue #4 & #5: MAC Address and Firmware Version

**Current Implementation**:
```python
# sensor.py
class PixooDeviceInfoSensor(PixooEntity, SensorEntity):
    _attr_entity_registry_enabled_default = False  # Disabled by default (good!)
    
    @property
    def native_value(self) -> str | None:
        device_info = self.coordinator.data.get("device_info")
        if not device_info:
            return None
        
        if self._sensor_type == "firmware":
            return device_info.get("software_version")  # Always "1.0.0"
        elif self._sensor_type == "mac":
            return device_info.get("device_mac")  # Always "00:00:00:00:00:00"
```

**Potential Fix**: 
- MAC address might be available from discovery (SSDP provides MAC)
- Firmware version: Remove sensor entirely (no way to get real value)

### Issue #6: Device Time Unavailable

**Current Implementation**:
```python
# sensor.py (lines 280-330)
class PixooTimeSensor(PixooEntity, SensorEntity):
    """Time sensor."""
    
    @property
    def native_value(self) -> str | None:
        """Return the sensor value."""
        time_data = self.coordinator.data.get("time")
        if not time_data:
            return None
        
        # Format time as HH:MM:SS
        hour = time_data.get("hour", 0)
        minute = time_data.get("minute", 0)
        second = time_data.get("second", 0)
        return f"{hour:02d}:{minute:02d}:{second:02d}"
```

**Checking coordinator**:
Need to check if WeatherCoordinator fetches time data correctly.

### Issue #7: Brightness Sensor + Number + Light

**Current State**:
- **Light entity** (`light.py`): Has brightness slider (0-255 → 0-100%)
- **Sensor** (`sensor.py`): Shows brightness as sensor (disabled by default)
- **Number entity**: Not found in number.py

**Analysis**:
```python
# light.py
class PixooLight(CoordinatorEntity, LightEntity):
    @property
    def brightness(self) -> int | None:
        """Return brightness (0-255 scale)."""
        system_config = self.coordinator.data.get("system")
        if not system_config:
            return None
        brightness_pct = system_config.get("brightness", 50)  # 0-100
        return round(brightness_pct * 2.55)  # Convert to 0-255
    
    async def async_turn_on(self, brightness: int | None = None, **kwargs):
        """Turn on and set brightness."""
        if brightness is not None:
            brightness_pct = round(brightness / 2.55)  # 0-255 → 0-100
            await self.pixoo.set_brightness(brightness_pct)
```

**The brightness sensor is redundant** - the light entity already exposes brightness as an attribute.

**Fix**: Remove brightness sensor, users should use light entity only.

### Issue #8: Missing PixooAsync Features

**PixooAsync Methods** (37 total):
```python
clear_text                 # ✅ clear_display service
close                      # 🔧 Internal (connection cleanup)
get_animation_list         # ✅ list_animations service
get_device_info            # ❌ API not supported by device
get_network_status         # ❌ API not supported by device
get_system_config          # ❌ API not supported by device
get_time_info              # ⚠️ Needs investigation (time sensor unavailable)
get_weather_info           # ⚠️ Needs investigation (weather sensor)
initialize                 # 🔧 Internal (connection setup)
play_animation             # ❌ Missing service
play_buzzer                # ✅ play_buzzer service
push                       # 🔧 Internal (buffer push - used by display_image)
send_playlist              # ❌ Missing service
send_text                  # ✅ display_text service
set_alarm                  # ✅ set_alarm service
set_brightness             # ✅ Light entity (async_turn_on with brightness)
set_channel                # ✅ Select entity (select.pixoo_channel)
set_clock                  # ✅ Select entity (select.pixoo_clock_face)
set_custom_channel         # ⚠️ Deprecated? (set_custom_page recommended)
set_custom_page            # ✅ Select entity (select.pixoo_custom_page)
set_face                   # ⚠️ Deprecated? (set_clock recommended)
set_mirror_mode            # ✅ Switch entity (switch.pixoo_mirror_mode)
set_noise_meter            # ✅ Switch entity (switch.pixoo_noise_meter)
set_rotation               # ✅ Select entity (select.pixoo_rotation)
set_scoreboard             # ✅ Number entities (number.pixoo_scoreboard_*)
set_screen                 # ✅ Light entity (async_turn_on/off)
set_screen_off             # ✅ Light entity (async_turn_off)
set_screen_on              # ✅ Light entity (async_turn_on)
set_stopwatch              # ✅ Switch entity (switch.pixoo_stopwatch) 
set_time                   # ❌ Missing service
set_timer                  # ✅ set_timer service + entities
set_timezone               # ❌ Missing service
set_visualizer             # ✅ Select entity (select.pixoo_visualizer)
set_weather_location       # ❌ Missing service
set_white_balance          # ❌ Missing service
stop_animation             # ❌ Missing service
```

**ha-pixoo Services** (11 total):
```yaml
1. clear_display         → clear_text() ✅
2. display_gif           → load_gif() + push() ✅
3. display_image         → load_image() + push() ✅
4. display_text          → send_text() ✅
5. list_animations       → get_animation_list() ✅
6. load_folder           → ❓ What does this do?
7. load_image            → ❓ Draws to buffer without pushing?
8. load_playlist         → ❓ What does this do?
9. play_buzzer           → play_buzzer() ✅
10. set_alarm            → set_alarm() ✅
11. set_timer            → set_timer() ✅
```

**Missing in ha-pixoo** (10 methods):
1. **play_animation** - Play animation by ID from device gallery
2. **send_playlist** - Send playlist of items to display
3. **set_time** - Set device time
4. **set_timezone** - Set device timezone
5. **set_weather_location** - Set weather location (lat/lon or city)
6. **set_white_balance** - Adjust RGB white balance (0-255 each)
7. **stop_animation** - Stop currently playing animation
8. **get_time_info** - Get device time (for time sensor)
9. **get_weather_info** - Get weather info (for weather sensor)
10. **Channel/GetIndex** - Get current channel index (for channel sensor)

**Priority Classification**:

**HIGH PRIORITY** (Commonly used):
- play_animation - Users want to show device animations
- send_playlist - Advanced feature for slideshows
- set_white_balance - Color calibration

**MEDIUM PRIORITY** (Nice to have):
- set_time / set_timezone - Usually synced automatically
- set_weather_location - Configure weather display
- stop_animation - Control animation playback

**LOW PRIORITY** (Rarely used):
- get_time_info - Only needed for sensor (which doesn't work)
- get_weather_info - Only needed for sensor
- Channel/GetIndex - Only needed to fix channel sensor

## Recommendations

### High Priority Fixes

1. **Remove/Fix broken sensors**:
   - Wi-Fi SSID sensor → Remove or mark unavailable
   - Wi-Fi Signal Strength sensor → Remove or mark unavailable
   - Firmware sensor → Remove (no way to get real value)
   - MAC Address sensor → Get from SSDP discovery or config entry

2. **Fix Active Channel sensor**:
   - Add `get_current_channel()` method to PixooAsync using `Channel/GetIndex`
   - Update sensor to use this method
   - Map index (0-3) to channel names

3. **Remove brightness sensor**:
   - Brightness is already available in light entity
   - Sensor is redundant and confusing

4. **Fix Device Time sensor**:
   - Investigate why time data is unavailable
   - Check WeatherCoordinator implementation

### Long-term Improvements

1. **Error Handling in PixooAsync**:
   - Return `None` or raise exception when API returns error
   - Don't use default values that look like real data

2. **Coordinator Architecture**:
   - Only fetch data from supported APIs
   - Mark sensors unavailable if data source doesn't exist

3. **Feature Audit**:
   - Complete audit of pixooasync methods vs ha-pixoo services
   - Document what's missing and prioritize additions

## Next Steps

1. Create fixes for sensors (#1-7)
2. Complete feature audit (#8)  
3. Test fixes with real device
4. Update documentation

---

**Investigation Status**: 🔄 In Progress  
**Next Action**: Implement sensor fixes  
**Last Updated**: 2025-11-16
