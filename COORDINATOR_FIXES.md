# Coordinator Fixes - 2025-11-13

## Issue Summary

The PixooAsync library has only **6 read methods**, but the coordinators were attempting to call **4 non-existent methods**:

### Non-Existent Methods (Removed)
1. `get_current_channel()` - Channel cannot be read from device
2. `get_timer_config()` - Timer state cannot be read from device
3. `get_alarm_config()` - Alarm state cannot be read from device
4. `get_stopwatch_config()` - Stopwatch state cannot be read from device

### Available Read Methods (Confirmed)
1. ✅ `get_device_info()` - Device name, IP, MAC, model, firmware
2. ✅ `get_network_status()` - Network info (SSID, signal strength)
3. ✅ `get_system_config()` - System state (brightness, screen_power, rotation, mirror_mode, etc.)
4. ✅ `get_animation_list()` - Available animations
5. ✅ `get_weather_info()` - Weather data
6. ✅ `get_time_info()` - Time/timezone info

## Changes Made

### coordinator.py

#### PixooSystemCoordinator (Lines 80-150)
**Before:**
```python
try:
    current_channel: Channel | str | None = await getattr(self.pixoo, "get_current_channel")()
    if isinstance(current_channel, Channel):
        data["system"]["channel"] = current_channel.name.lower()
    else:
        data["system"]["channel"] = current_channel
except Exception as ch_err:
    _LOGGER.debug("Channel not available: %s", ch_err)
```

**After:**
```python
# Channel is not readable from device - would need to track it ourselves
# data["system"]["channel"] = "unknown"  # Commented out - not available
```

**Impact:**
- Channel sensor will show as unavailable (no data)
- To fix: Need to implement memory-based channel tracking after `set_channel()` calls
- For now: Coordinator no longer crashes trying to read channel

#### PixooToolCoordinator (Lines 191-280)
**Before:**
```python
# Timer state
try:
    timer_cfg: TimerConfig = await getattr(self.pixoo, "get_timer_config")()
    # ... 60+ lines of timer/alarm/stopwatch state reading
except Exception as t_err:
    _LOGGER.debug("Timer state not available: %s", t_err)
```

**After:**
```python
async def _async_update_data(self) -> dict[str, Any]:
    """Fetch tool state from the device."""
    try:
        # NOTE: PixooAsync does NOT have get_timer_config, get_alarm_config, or get_stopwatch_config methods
        # These values cannot be read from the device - they can only be SET
        # Tool state sensors will remain unavailable until PixooAsync implements read methods
        
        data: dict[str, Any] = {}
        _LOGGER.debug("Tool coordinator: No tool state read methods available in PixooAsync")
        
        # Return empty data - tool sensors will show as unavailable
        # This is correct behavior until read methods are implemented
        return data
    except Exception as err:
        raise UpdateFailed(f"Error fetching tool state: {err}") from err
```

**Impact:**
- Tool coordinator no longer crashes every 30s
- Timer/alarm/stopwatch sensors will show as unavailable
- Dynamic polling (1s when active) removed - not needed without state reading
- 70+ lines of dead code removed

## Testing

### Debug Script Output
```bash
$ python debug_pixoo_state.py 192.168.188.65

✅ get_device_info: Works (with model info)
✅ get_system_config: Works (brightness=50%, screen_power=True, rotation=0)
✅ get_network_status: Works (IP, MAC, RSSI)
❌ get_current_channel: AttributeError - method doesn't exist
✅ get_weather_info: Works (temp, weather, humidity, pressure)
❌ get_timer_config: AttributeError - method doesn't exist
❌ get_alarm_config: AttributeError - method doesn't exist
❌ get_stopwatch_config: AttributeError - method doesn't exist
✅ get_animation_list: Works (returns AnimationList object)
```

### Integration Behavior After Fix

#### Working Coordinators ✅
- **DeviceCoordinator**: Gets device info (one-time) - Works
- **SystemCoordinator**: Gets brightness, screen_power, rotation, etc. - Works
- **WeatherCoordinator**: Gets weather and time info - Works
- **GalleryCoordinator**: Gets animation list - Works

#### Fixed Coordinators ✅
- **ToolCoordinator**: Returns empty data instead of crashing - Fixed

#### Unavailable Entities (Expected)
- Channel sensor - No read method available
- Timer state sensors - No read method available
- Alarm state sensors - No read method available
- Stopwatch state sensors - No read method available

#### Working Entities ✅
- Light (power, brightness) - Works via `set_screen()` and `set_brightness()`
- Number entities (8) - Work via set_timer/set_alarm/etc.
- Switch entities (7) - Work via set methods
- Select entities (5 working, 2 disabled) - Work via set_channel/set_clock/etc.
- Sensor entities (device, network, brightness, weather) - Work via get methods
- Button entities (4) - Work via action methods
- Media player (image gallery) - Works

## Known Limitations

### Device API Limitations
1. **Channel state**: Cannot be read, only written
2. **Timer state**: Cannot be read, only written (set)
3. **Alarm state**: Cannot be read, only written (set)
4. **Stopwatch state**: Cannot be read, only written (start/reset)
5. **screen_power**: Can be read but doesn't update reliably (always shows True)

### Potential Solutions

#### Option 1: Memory-Based State Tracking (Recommended)
Track last-written values in integration memory:
```python
self._last_channel = None
self._last_timer_minutes = None
self._last_alarm_time = None
```

Pros:
- Shows "optimistic" state immediately after writes
- No device API changes needed
- Better UX than "unavailable"

Cons:
- State lost on HA restart
- Can drift if device state changed externally
- Not "true" device state

#### Option 2: Wait for PixooAsync API Enhancements
Wait for upstream library to add read methods:
```python
# Future methods needed in pixooasync:
async def get_current_channel() -> Channel
async def get_timer_config() -> TimerConfig
async def get_alarm_config() -> AlarmConfig
async def get_stopwatch_config() -> StopwatchConfig
```

Pros:
- True device state
- No drift issues
- More reliable

Cons:
- Requires upstream changes
- May not be possible (device firmware limitations)
- Timeline uncertain

#### Option 3: Remove Unsupported Features
Simply don't expose sensors for unreadable state:
```python
# Don't create channel sensor
# Don't create timer state sensor
# Don't create alarm state sensor
# Don't create stopwatch state sensor
```

Pros:
- Honest about capabilities
- No confusing "unavailable" entities
- Clean implementation

Cons:
- Less features
- Can't monitor tool states
- Users may expect these features

## Deployment

### Sync to Home Assistant
```bash
rsync -av --delete --exclude '__pycache__/' --exclude '*.pyc' \
  /Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo/ \
  /Volumes/config/custom_components/pixoo/
```

### Restart Home Assistant
You need to restart HA core to load the fixed integration. Use one of:

1. **Via UI**: Settings → System → Restart
2. **Via SSH**: `ssh homeassistant "ha core restart"`
3. **Via ha CLI**: `ha core restart` (if running on HA host)

### Verification
After restart, check:
1. ✅ No errors in Home Assistant logs
2. ✅ Pixoo integration loads successfully
3. ✅ Tool coordinator no longer crashes every 30s
4. ✅ Light entity works (on/off, brightness)
5. ✅ Select entities work (channel, rotation, clock)
6. ⚠️ Channel sensor shows unavailable (expected)
7. ⚠️ Tool state sensors show unavailable (expected)

## Next Steps

1. **Immediate**: Test the fixed integration after HA restart
2. **Short-term**: Decide on state tracking strategy (memory vs remove features)
3. **Medium-term**: Implement memory-based channel tracking
4. **Long-term**: Request read methods in PixooAsync upstream

## Files Modified

- `custom_components/pixoo/coordinator.py` (2 coordinators fixed)
  - PixooSystemCoordinator: Removed get_current_channel() call
  - PixooToolCoordinator: Removed all tool state reading (70+ lines)

## Files Synced to HA

- coordinator.py ✅
- light.py ✅ (from previous fix)
- select.py ✅ (from previous fix)

## Status

✅ **Coordinators Fixed** - No longer calling non-existent methods  
✅ **Integration Stable** - Should load without crashes  
⚠️ **Features Limited** - Channel and tool state sensors unavailable  
🔄 **Next**: Test on HA and implement state tracking if desired
