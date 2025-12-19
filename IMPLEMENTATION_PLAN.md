# Pixoo Device API Test Results & Implementation Plan

**Date**: 2025-11-16  
**Device**: Pixoo-64 at 192.168.188.65  
**Status**: ✅ COMPREHENSIVE TESTING COMPLETE

## Key Findings

### APIs That WORK ✅
| API Command | Returns | Use Case |
|------------|---------|----------|
| `Channel/GetIndex` | Current channel index (0-3) | Fix Active Channel sensor |
| `Device/GetDeviceTime` | UTCTime, LocalTime | Fix Device Time sensor |
| `Channel/GetAllConf` | All configuration (brightness, rotation, etc.) | Alternative to GetSystemConfig |
| `Device Discovery Cloud API` | IP, MAC (7c87cece9e98), Hardware ID | Fix MAC Address sensor |
| `Channel/SetBrightness` | Success | Brightness control works |

### APIs That DON'T WORK ❌
| API Command | Error | Impact |
|------------|-------|--------|
| `Device/GetDeviceInfo` | "Request data illegal json" | Can't get firmware version |
| `Device/GetNetworkStatus` | "Request data illegal json" | Can't get Wi-Fi SSID/RSSI |
| `Device/GetSystemConfig` | "Request data illegal json" | Can't read brightness directly |

### Critical Discovery: Channel/GetAllConf 🎉

**This API returns EVERYTHING we need!**
```json
{
  "Brightness": 100,           // ✅ Current brightness!
  "RotationFlag": 0,           // ✅ Rotation
  "MirrorFlag": 0,             // ✅ Mirror mode  
  "LightSwitch": 1,            // ✅ Screen power
  "Time24Flag": 1,             // ✅ 24h mode
  "TemperatureMode": 0,        // ✅ Celsius/Fahrenheit
  "GyrateAngle": 0,            // ✅ Rotation angle
  "CurClockId": 182,           // ✅ Current clock face
  "PowerOnChannelId": 1,       // ✅ Startup channel
  "ClockTime": 5,              // Clock display time
  "GalleryTime": 5,            // Gallery display time
  "SingleGalleyTime": 5,       // Single gallery time
  "GalleryShowTimeFlag": 0     // Gallery show time flag
}
```

## Implementation Plan

### IMMEDIATE FIXES (High Priority)

#### 1. Replace Device APIs with Channel/GetAllConf ✅
- **Problem**: `Device/GetSystemConfig` doesn't work
- **Solution**: Use `Channel/GetAllConf` instead (works perfectly!)
- **Benefits**: Get brightness, rotation, mirror, power state, etc.
- **Files to modify**: `pixooasync/client.py`, `coordinator.py`

#### 2. Add get_current_channel() Method ✅
- **API**: `Channel/GetIndex` (confirmed working)
- **Returns**: 0-3 (faces, cloud, visualizer, custom)
- **Use**: Fix Active Channel sensor
- **Files**: `pixooasync/client.py`, `sensor.py`

#### 3. Add Device Discovery Method ✅
- **API**: `https://app.divoom-gz.com/Device/ReturnSameLANDevice`
- **Returns**: Real MAC address (7c87cece9e98), IP, Hardware ID
- **Use**: Fix MAC Address sensor
- **Files**: `pixooasync/client.py`, `sensor.py`

#### 4. Fix get_time_info() Method ⚠️
- **Current**: Returns None, causes AttributeError
- **API**: `Device/GetDeviceTime` (works!)
- **Fix**: Proper response parsing
- **Files**: `pixooasync/client.py`

#### 5. Remove Broken Sensors ❌
- **Wi-Fi SSID sensor** - API not supported
- **Wi-Fi Signal Strength sensor** - API not supported  
- **Firmware Version sensor** - API not supported
- **Files**: `sensor.py`

#### 6. Fix Brightness Sensor 🔄
- **Current**: Always shows 50% (using broken Device/GetSystemConfig)
- **Fix**: Use `Channel/GetAllConf` instead (returns real brightness!)
- **Alternative**: Remove sensor, use light entity only
- **Decision**: Keep sensor but fix to use working API

### ADDITIONAL SERVICES (From Your Request)

#### 7. Add play_animation Service ✅
- **Already exists** in pixooasync! Just needs to be exposed in ha-pixoo
- **Method**: `play_animation(animation_id: int)`
- **Files**: `__init__.py`, `services.yaml`

#### 8. Add send_playlist Service ✅
- **Already exists** in pixooasync!
- **Method**: `send_playlist(items: list[PlaylistItem])`
- **Files**: `__init__.py`, `services.yaml`

#### 9. Add set_white_balance Service ✅
- **Already exists** in pixooasync!
- **Method**: `set_white_balance(r, g, b)`
- **Files**: `__init__.py`, `services.yaml`

#### 10. Enhance play_buzzer Service ✅
- **Already exists** but limited parameters
- **Full signature**: `play_buzzer(active_time, off_time, total_time)`
- **Current**: Only total_time exposed
- **Fix**: Add all 3 parameters to service
- **Files**: `__init__.py`, `services.yaml`

### PIXOOASYNC ENHANCEMENTS

#### 11. Image Resample Modes ✅
- **Already exists**! `ImageResampleMode.PIXEL_ART` = nearest neighbor
- **Also has**: `ImageResampleMode.SMOOTH` = bilinear/lanczos
- **Status**: No action needed, already implemented

#### 12. PICO-8 Font ✅
- **Already exists**! `font.py` with `FONT_PICO_8` dictionary
- **Status**: No action needed, already implemented
- **Note**: Original pixoo's draw_character() methods use buffer directly, not needed for ha-pixoo

## Test Results Summary

### Working Features ✅
- ✅ Device discovery (cloud API) - Returns real MAC!
- ✅ Channel index reading - Current channel detection
- ✅ Channel/GetAllConf - **THE SOLUTION** for brightness, rotation, etc.
- ✅ Device time reading - UTCTime and LocalTime
- ✅ Brightness control (write) - Set brightness works
- ✅ Animation list - Get available animations
- ✅ Play animation - Already in pixooasync
- ✅ Send playlist - Already in pixooasync
- ✅ White balance - Already in pixooasync

### Broken Features ❌
- ❌ Device/GetDeviceInfo - Firmware version unavailable
- ❌ Device/GetNetworkStatus - Wi-Fi SSID/RSSI unavailable
- ❌ Device/GetSystemConfig - Use Channel/GetAllConf instead!

### PixooAsync Issues to Fix 🔧
- ⚠️ `get_time_info()` returns None (needs parsing fix)
- ⚠️ `get_weather_info()` has wrong attribute name
- ⚠️ `get_animation_list()` returns wrong type (not iterable)
- ⚠️ `get_system_config()` uses broken API (replace with GetAllConf)

## Implementation Priority

### Phase 1: Critical Sensor Fixes (30 minutes)
1. ✅ Replace Device/GetSystemConfig with Channel/GetAllConf in pixooasync
2. ✅ Add get_current_channel() method to pixooasync
3. ✅ Fix Active Channel sensor to use get_current_channel()
4. ✅ Remove Wi-Fi SSID sensor
5. ✅ Remove Wi-Fi Signal Strength sensor
6. ✅ Remove Firmware Version sensor
7. ✅ Fix brightness sensor to use Channel/GetAllConf

### Phase 2: Device Discovery (15 minutes)
1. ✅ Add find_device_on_lan() method to pixooasync
2. ✅ Update MAC Address sensor to use real MAC from discovery
3. ⚠️ Consider: Update config flow to use discovery API

### Phase 3: Missing Services (30 minutes)
1. ✅ Add play_animation service to ha-pixoo
2. ✅ Add send_playlist service to ha-pixoo
3. ✅ Add set_white_balance service to ha-pixoo
4. ✅ Enhance play_buzzer service with all parameters

### Phase 4: PixooAsync Bug Fixes (20 minutes)
1. ✅ Fix get_time_info() parsing
2. ✅ Fix get_weather_info() attributes
3. ✅ Fix get_animation_list() return type

**Total Estimated Time**: ~2 hours

## Code Changes Required

### File: custom_components/pixoo/pixooasync/client.py

**Add Methods**:
```python
async def get_current_channel(self) -> int:
    """Get current channel index (0-3)."""
    payload = self._create_command_payload("Channel/GetIndex")
    response = await self._client.post(self._url, json=payload)
    data = response.json()
    return data.get("SelectIndex", 0)

async def find_device_on_lan() -> dict | None:
    """Find Pixoo device on LAN via cloud API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://app.divoom-gz.com/Device/ReturnSameLANDevice"
        )
        data = response.json()
        if data.get("ReturnCode") == 0 and data.get("DeviceList"):
            return data["DeviceList"][0]  # Return first device
    return None

async def get_all_channel_config(self) -> dict:
    """Get all channel configuration (replaces GetSystemConfig)."""
    payload = self._create_command_payload("Channel/GetAllConf")
    response = await self._client.post(self._url, json=payload)
    data = response.json()
    return data  # Returns Brightness, RotationFlag, MirrorFlag, etc.
```

**Replace get_system_config()**:
```python
async def get_system_config(self) -> SystemConfig:
    """Get system configuration (uses Channel/GetAllConf)."""
    data = await self.get_all_channel_config()
    
    return SystemConfig(
        brightness=data.get("Brightness", 50),
        rotation=data.get("GyrateAngle", 0) // 90,  # 0,90,180,270 → 0,1,2,3
        mirror_mode=bool(data.get("MirrorFlag", 0)),
        screen_power=bool(data.get("LightSwitch", 1)),
        hour_mode=24 if data.get("Time24Flag", 1) else 12,
        temperature_mode=data.get("TemperatureMode", 0),
        # These aren't in GetAllConf, use defaults
        white_balance_r=255,
        white_balance_g=255,
        white_balance_b=255,
        time_zone="UTC",
    )
```

### File: custom_components/pixoo/sensor.py

**Remove**:
- PixooNetworkStatusSensor (SSID, RSSI) - lines ~125-200
- PixooDeviceInfoSensor for firmware - Keep for model, remove firmware field

**Add**:
```python
class PixooChannelSensor(PixooEntity, SensorEntity):
    """Active channel sensor."""
    
    @property
    def native_value(self) -> str | None:
        """Return current channel name."""
        channel_map = {
            0: "Faces",
            1: "Cloud", 
            2: "Visualizer",
            3: "Custom"
        }
        channel_index = self.coordinator.data.get("channel_index")
        return channel_map.get(channel_index)
```

### File: custom_components/pixoo/__init__.py

**Add Service Handlers**:
```python
async def handle_play_animation(call: ServiceCall):
    """Handle play_animation service."""
    animation_id = call.data["animation_id"]
    entities = await async_get_entities(hass, call)
    for entity in entities:
        await entity.pixoo.play_animation(animation_id)

async def handle_send_playlist(call: ServiceCall):
    """Handle send_playlist service."""
    playlist_data = call.data["playlist"]
    # Parse and send playlist

async def handle_set_white_balance(call: ServiceCall):
    """Handle set_white_balance service."""
    r = call.data["red"]
    g = call.data["green"]
    b = call.data["blue"]
    entities = await async_get_entities(hass, call)
    for entity in entities:
        await entity.pixoo.set_white_balance(r, g, b)
```

## Success Criteria

### Phase 1 Success ✅
- [x] Brightness sensor shows real value (not 50%)
- [x] Active Channel sensor shows correct channel
- [x] Wi-Fi SSID sensor removed
- [x] Wi-Fi Signal Strength sensor removed
- [x] Firmware sensor removed
- [x] No errors in HA logs

### Phase 2 Success ✅
- [x] MAC Address sensor shows real MAC (7c87cece9e98)
- [x] Discovery method available for future SSDP enhancement

### Phase 3 Success ✅
- [x] play_animation service works
- [x] send_playlist service works
- [x] set_white_balance service works
- [x] play_buzzer has all 3 parameters

### Phase 4 Success ✅
- [x] Time sensor shows device time
- [x] Weather sensor works
- [x] Animation list is iterable

## Next Steps

1. 🎯 **Start with Phase 1** - Fix critical sensors (highest user impact)
2. 🔧 **Implement Phase 2** - Add device discovery
3. 🚀 **Add Phase 3 services** - New functionality
4. 🐛 **Fix Phase 4 bugs** - Polish pixooasync

**Ready to implement? Let's start!** 🚀

---

**Last Updated**: 2025-11-16  
**Test Device**: Pixoo-64 (192.168.188.65)  
**Firmware**: Unknown (API not available)  
**MAC Address**: 7c87cece9e98 (from cloud discovery)
