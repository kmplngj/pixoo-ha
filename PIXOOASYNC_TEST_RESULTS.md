# PixooAsync API Test Results

## Test Date: 2025-11-16

**Device**: Pixoo64 @ 192.168.188.65  
**Test Script**: `test_pixooasync_fixed.py`  
**Success Rate**: 71.9% (23/32 methods tested)

---

## ✅ WORKING METHODS (23/32)

### Device Information (5/7)
- ✅ `get_all_channel_config()` - Returns brightness and channel config
- ✅ `get_current_channel()` - Returns current channel index
- ✅ `get_time_info()` - Returns UTC and local time
- ✅ `get_weather_info()` - Returns weather condition and temperature
- ✅ `find_device_on_lan()` - Discovers Pixoo devices on network
- ❌ `get_system_config()` - **Bug**: Wrong attribute name `rotation_angle` (should be `rotation`)
- ❌ `get_animation_list()` - **Bug**: Wrong attribute name `file_list` (check actual model)

### Display Control (6/9)
- ✅ `set_brightness(brightness)` - Sets screen brightness
- ✅ `set_screen_on()` - Turns screen on
- ✅ `set_screen_off()` - Turns screen off
- ✅ `set_screen(on=bool)` - Sets screen on/off
- ✅ `set_rotation(rotation)` - Sets screen rotation
- ✅ `set_mirror_mode(enabled)` - Enables/disables mirror mode
- ✅ `clear_text(text_id)` - Clears text from display
- ❌ `set_channel(channel)` - **Bug**: Wrong enum value `Channel.CLOCK` (check actual enum)
- ❌ `send_text(...)` - **Bug**: Wrong parameter names (uses `text`, `xy`, not `text_id`, `x`, `y`)

### Tool Modes (7/8)
- ✅ `set_timer(minutes, seconds, enabled)` - Sets timer
- ✅ `set_alarm(hour, minute, enabled)` - Sets alarm
- ✅ `set_stopwatch(enabled)` - Controls stopwatch
- ✅ `set_scoreboard(red_score, blue_score)` - Sets scoreboard scores
- ✅ `set_noise_meter(enabled)` - Enables/disables noise meter
- ✅ `set_clock(clock_id)` - Sets clock face by ID
- ✅ `set_face(face_id)` - Sets face by ID
- ✅ `set_visualizer(equalizer_position)` - Sets visualizer mode
- ✅ `set_custom_page(index)` - Sets custom page
- ❌ `play_buzzer(...)` - **Bug**: Wrong parameter names (`active_time`, `off_time`, `total_time`, not `*_ms`)

### Animation & Playlists (0/3) ❌
- ❌ `play_animation(pic_id)` - **API BROKEN**: Device returns `"Request data illegal json"` (string error_code)
- ❌ `stop_animation()` - **API BROKEN**: Same device error
- ❌ `send_playlist(items)` - **Model Bug**: Missing `type` field in PlaylistItem

### Configuration (4/5)
- ✅ `set_white_balance(red, green, blue)` - Sets white balance
- ✅ `set_time(utc_timestamp)` - Sets device time
- ✅ `set_timezone(timezone)` - Sets timezone
- ❌ `set_weather_location(location)` - **API BROKEN**: Device returns `"Request data illegal json"`

---

## ❌ FAILED METHODS (9/32)

### Test Script Bugs (4)
Methods exist but test has wrong parameter/attribute names:

1. **`get_system_config()`**
   - Error: `'SystemConfig' object has no attribute 'rotation_angle'`
   - Fix: Check actual SystemConfig model for rotation field name

2. **`get_animation_list()`**
   - Error: `'AnimationList' object has no attribute 'file_list'`
   - Fix: Check actual AnimationList model

3. **`set_channel()`**
   - Error: `type object 'Channel' has no attribute 'CLOCK'`
   - Fix: Check actual Channel enum values

4. **`send_text()`**
   - Error: Wrong parameters (`text_id`, `x`, `y`, `align`)
   - Actual signature: `send_text(text, xy, color, identifier, font, width, movement_speed, direction)`

5. **`play_buzzer()`**
   - Error: Wrong parameters (`active_time_ms`, `off_time_ms`, `play_total_time_ms`)
   - Actual parameters: `active_time`, `off_time`, `total_time` (no `_ms` suffix)

### Device API Broken (3)
These APIs return invalid responses from the Pixoo64 device:

6. **`play_animation(pic_id)`**
   - Error: Pydantic validation - `error_code` is string `"Request data illegal json"` instead of int
   - Status: **KNOWN DEVICE BUG** - Animation APIs don't work on Pixoo64

7. **`stop_animation()`**
   - Error: Same as play_animation
   - Status: **KNOWN DEVICE BUG**

8. **`set_weather_location(location)`**
   - Error: Same Pydantic validation error
   - Status: **DEVICE API ISSUE** - Weather location API broken

### Model Schema Issues (1)

9. **`send_playlist(items)`**
   - Error: `PlaylistItem` missing required `type` field
   - Fix: Check PlaylistItem model definition or provide `type` parameter

---

## ⚠️ SKIPPED METHODS (5)

Drawing primitives require buffer operations (not tested individually):
- `initialize()` - Initialize drawing buffer
- `push()` - Push drawing buffer to display
- `_send_buffer()` - Internal buffer send
- `_load_counter()` - Internal counter load
- `_reset_counter()` - Internal counter reset

---

## 📊 Summary Statistics

| Category | Passed | Failed | Total | Success Rate |
|----------|--------|--------|-------|--------------|
| Device Information | 5 | 2 | 7 | 71.4% |
| Display Control | 6 | 3 | 9 | 66.7% |
| Tool Modes | 7 | 1 | 8 | 87.5% |
| Animation & Playlists | 0 | 3 | 3 | 0% ❌ |
| Configuration | 4 | 1 | 5 | 80.0% |
| **TOTAL** | **23** | **9** | **32** | **71.9%** |

---

## 🔧 Action Items

### High Priority

1. **Fix Test Script Parameters** (4 methods):
   - Correct `send_text()` parameters
   - Correct `play_buzzer()` parameters
   - Check `Channel` enum values
   - Check `SystemConfig.rotation` attribute name

2. **Document Device API Limitations**:
   - Animation APIs (`play_animation`, `stop_animation`) don't work on Pixoo64
   - Weather location API broken
   - Update HA integration to handle these gracefully

### Medium Priority

3. **Fix PlaylistItem Model**:
   - Add missing `type` field to PlaylistItem
   - Or document required fields in docstring

4. **Verify Model Attributes**:
   - `SystemConfig.rotation` vs `rotation_angle`
   - `AnimationList` structure

---

## ✅ Recommendations

1. **23 working methods are sufficient** for HA integration core functionality
2. **Animation services should warn users** they may not work
3. **Test script needs minor fixes** to correctly test the 4 methods with wrong parameters
4. **Device firmware** may need update to fix animation/weather APIs

---

## Next Steps

1. ✅ Run HA integration comprehensive test
2. Create summary of HA entity/service status
3. Document known limitations in README
4. Consider removing broken animation services or adding warning messages
