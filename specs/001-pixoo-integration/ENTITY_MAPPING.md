# pixooasync to Home Assistant Entity Mapping

**Quick Reference for Developers**

This document provides a clear mapping between pixooasync package methods and Home Assistant entities/services for the Pixoo integration.

## Entity Mapping

### Light Entity

| Entity | pixooasync Method (Get) | pixooasync Method (Set) | Attributes |
|--------|----------------------|----------------------|------------|
| `light.pixoo` | `get_system_config().brightness` | `set_brightness(value)` | brightness (0-255, scaled to 0-100) |
| | N/A (power state) | `set_screen(on=True/False)` | state (on/off) |

**Implementation**:
```python
# Light platform for power and brightness control
async def async_turn_on(self, brightness=None):
    if brightness is not None:
        await self.pixoo.set_brightness(int(brightness / 255 * 100))
    await self.pixoo.set_screen(on=True)

async def async_turn_off(self):
    await self.pixoo.set_screen(on=False)
```

### Media Player Entity

| Entity | pixooasync Method | Implementation | Attributes |
|--------|----------------|----------------|------------|
| `media_player.pixoo` | `display_image_from_url()` | Play single image or playlist slideshow | state, media_content_type, media_content_id |
| | `display_gif_from_url()` | Auto-advance playlist with timer | media_image_url, media_position, media_duration |
| | `display_image_from_bytes()` | Resolve media-source:// URLs | shuffle, repeat |
| | `clear_display()` | Stop service clears display | |

**Implementation**:
```python
# Media player platform for image gallery/slideshow
async def async_play_media(self, media_type, media_id):
    if media_type == "playlist":
        # Parse JSON playlist: [{"url": "...", "duration": 10}, ...]
        playlist = json.loads(media_id)
        self._playlist = [PixooPlaylistItem(**item) for item in playlist]
        self._position = 0
        await self._display_current_image()
        self._schedule_next()  # Auto-advance after duration
    else:
        # Single image
        image_data = await download_image(self.hass, media_id)
        await self.pixoo.display_image_from_bytes(image_data)

async def async_media_next_track(self):
    # Navigate to next image (respects shuffle)
    self._position = (self._position + 1) % len(self._playlist)
    await self._display_current_image()
```

**Playlist Support**:
- Local images: `media-source://media_source/local/photos/photo.jpg`
- External URLs: `https://example.com/image.jpg`
- Mixed playlists: Combine both in same playlist
- Per-image duration: Each item can specify custom duration
- Shuffle/repeat: Internal state management
- Auto-advance: Timer-based progression

**Services**:
- `media_player.play_media`: Display image or start playlist
- `media_player.media_play`: Resume slideshow
- `media_player.media_pause`: Pause slideshow
- `media_player.media_stop`: Stop and clear
- `media_player.media_next_track`: Next image
- `media_player.media_previous_track`: Previous image
- `media_player.shuffle_set`: Enable/disable shuffle
- `media_player.repeat_set`: Enable/disable repeat

### Number Entities

| Entity | pixooasync Method (Get) | pixooasync Method (Set) | Range | Unit |
|--------|----------------------|----------------------|-------|------|
| `number.pixoo_brightness` | `get_system_config().brightness` | `set_brightness(value)` | 0-100 | % |
| `number.pixoo_timer_minutes` | `get_timer_status().minutes` | `set_timer(minutes=value, ...)` | 0-99 | min |
| `number.pixoo_timer_seconds` | `get_timer_status().seconds` | `set_timer(seconds=value, ...)` | 0-59 | sec |
| `number.pixoo_alarm_hour` | `get_alarm_status().hour` | `set_alarm(hour=value, ...)` | 0-23 | hr |
| `number.pixoo_alarm_minute` | `get_alarm_status().minute` | `set_alarm(minute=value, ...)` | 0-59 | min |
| `number.pixoo_scoreboard_red` | `get_scoreboard_status().red` | `set_scoreboard(red=value, ...)` | 0-999 | points |
| `number.pixoo_scoreboard_blue` | `get_scoreboard_status().blue` | `set_scoreboard(blue=value, ...)` | 0-999 | points |
| `number.pixoo_gallery_timing` | `get_system_config().gallery_interval` | `set_gallery_timing(value)` | 5-3600 | sec |

### Switch Entities

| Entity | pixooasync Method (Get) | pixooasync Method (On) | pixooasync Method (Off) |
|--------|----------------------|---------------------|---------------------|
| `switch.pixoo_power` | N/A (stateless) | `set_screen(on=True)` | `set_screen(on=False)` |
| `switch.pixoo_timer` | `get_timer_status().enabled` | `set_timer(enabled=True)` | `set_timer(enabled=False)` |
| `switch.pixoo_alarm` | `get_alarm_status().enabled` | `set_alarm(enabled=True)` | `set_alarm(enabled=False)` |
| `switch.pixoo_stopwatch` | `get_stopwatch_status().enabled` | `set_stopwatch(enabled=True)` | `set_stopwatch(enabled=False)` |
| `switch.pixoo_scoreboard` | `get_scoreboard_status().enabled` | `set_scoreboard(enabled=True)` | `set_scoreboard(enabled=False)` |
| `switch.pixoo_noise_meter` | `get_noise_meter_status().enabled` | `set_noise_meter(enabled=True)` | `set_noise_meter(enabled=False)` |
| `switch.pixoo_mirror_mode` | `get_system_config().mirror_mode` | `set_mirror_mode(True)` | `set_mirror_mode(False)` |

### Select Entities

| Entity | pixooasync Method (Get) | pixooasync Method (Set) | Options |
|--------|----------------------|----------------------|---------|
| `select.pixoo_channel` | `get_system_config().channel` | `set_channel(Channel)` | Faces, Cloud, Visualizer, Custom |
| `select.pixoo_rotation` | `get_system_config().rotation` | `set_rotation(Rotation)` | 0°, 90°, 180°, 270° |
| `select.pixoo_temperature_mode` | `get_system_config().temperature_mode` | `set_temperature_mode(TemperatureMode)` | Celsius, Fahrenheit |
| `select.pixoo_time_format` | `get_system_config().time_format_24h` | `set_time_format(bool)` | 12-hour, 24-hour |
| `select.pixoo_custom_page` | N/A | `set_custom_page(1-3)` | Page 1, Page 2, Page 3 |
| `select.pixoo_clock_face` | N/A | `set_clock(id)` | Dynamic from cloud |
| `select.pixoo_visualizer` | N/A | `set_visualizer(id)` | Dynamic from device |

### Sensor Entities

| Entity | pixooasync Method | Update Interval | Attributes |
|--------|----------------|----------------|------------|
| `sensor.pixoo_device_info` | `get_device_info()` | On startup | model, mac, firmware, hardware |
| `sensor.pixoo_network_status` | `get_network_status()` | 60s | signal, ip, ssid, status |
| `sensor.pixoo_system_config` | `get_system_config()` | 30s | brightness, rotation, mirror, formats |
| `sensor.pixoo_weather` | `get_weather_info()` | 300s | weather_type, temperature, forecast |
| `sensor.pixoo_time_info` | `get_time_info()` | 60s | timezone, utc_offset, local_time |
| `sensor.pixoo_current_channel` | `get_system_config().channel` | 30s | Channel name |
| `sensor.pixoo_timer_remaining` | `get_timer_status()` | 1s (when active) | minutes, seconds |
| `sensor.pixoo_alarm_next` | `get_alarm_status()` | 60s (when enabled) | hour, minute, next_trigger |
| `sensor.pixoo_stopwatch_elapsed` | `get_stopwatch_status()` | 1s (when active) | elapsed_time |
| `sensor.pixoo_animation_list` | `get_animation_list()` | On demand | list of animations |

### Button Entities

| Entity | pixooasync Method | Parameters |
|--------|----------------|------------|
| `button.pixoo_buzzer` | `play_buzzer(active_ms, off_ms, count)` | Configurable via service |
| `button.pixoo_reset_buffer` | `reset_buffer()` | None |
| `button.pixoo_push_buffer` | `push_buffer()` | None |

## Service Mapping

### Display Services

| Service | pixooasync Method | Parameters |
|---------|----------------|------------|
| `pixoo.display_image` | `send_image(path)` | entity_id, file_path OR image_url |
| `pixoo.display_gif` | `send_gif(path)` | entity_id, file_path OR gif_url |
| `pixoo.display_text` | `send_text(text, color, scroll)` | entity_id, text, color, scroll_direction |
| `pixoo.clear_text` | `clear_text()` | entity_id |

### Drawing Services

| Service | pixooasync Method | Parameters |
|---------|----------------|------------|
| `pixoo.draw_pixel` | `draw_pixel(x, y, color)` | entity_id, x, y, color |
| `pixoo.draw_text` | `draw_text(text, pos, color)` | entity_id, text, x, y, color |
| `pixoo.draw_line` | `draw_line(x1, y1, x2, y2, color)` | entity_id, x1, y1, x2, y2, color |
| `pixoo.draw_rectangle` | `draw_filled_rectangle(...)` | entity_id, x1, y1, x2, y2, color |
| `pixoo.draw_image` | `draw_image(image)` | entity_id, image_data |
| `pixoo.reset_buffer` | `reset_buffer()` | entity_id |
| `pixoo.push_buffer` | `push_buffer()` | entity_id |

### Tool Services

| Service | pixooasync Method | Parameters |
|---------|----------------|------------|
| `pixoo.set_timer` | `set_timer(minutes, seconds, enabled)` | entity_id, minutes, seconds, enabled |
| `pixoo.set_alarm` | `set_alarm(hour, minute, enabled)` | entity_id, hour, minute, enabled |
| `pixoo.set_stopwatch` | `set_stopwatch(enabled)` | entity_id, enabled |
| `pixoo.set_scoreboard` | `set_scoreboard(red, blue, enabled)` | entity_id, red_score, blue_score, enabled |
| `pixoo.set_noise_meter` | `set_noise_meter(enabled)` | entity_id, enabled |
| `pixoo.play_buzzer` | `play_buzzer(active_ms, off_ms, count)` | entity_id, active_ms, off_ms, count |

### Configuration Services

| Service | pixooasync Method | Parameters |
|---------|----------------|------------|
| `pixoo.set_white_balance` | `set_white_balance(r, g, b)` | entity_id, red, green, blue |
| `pixoo.set_weather_location` | `set_weather_location(lat, lon)` | entity_id, latitude, longitude |
| `pixoo.set_timezone` | `set_timezone(timezone)` | entity_id, timezone |
| `pixoo.set_time` | `set_time(year, month, day, hour, minute, second)` | entity_id, datetime |

### Animation Services

| Service | pixooasync Method | Parameters |
|---------|----------------|------------|
| `pixoo.play_animation` | `play_animation(id)` | entity_id, animation_id |
| `pixoo.stop_animation` | `stop_animation()` | entity_id |
| `pixoo.send_playlist` | `send_playlist(items, duration)` | entity_id, playlist_items |
| `pixoo.get_animations` | `get_animation_list()` | entity_id |

## Pydantic Model to Entity Attribute Mapping

### DeviceInfo Model → sensor.pixoo_device_info

```python
# pixooasync
device_info = await pixoo.get_device_info()
# device_info.device_name -> attribute: device_name
# device_info.mac_address -> attribute: mac_address
# device_info.firmware_version -> attribute: firmware_version
# device_info.hardware_version -> attribute: hardware_version
```

### NetworkStatus Model → sensor.pixoo_network_status

```python
# pixooasync
network = await pixoo.get_network_status()
# network.signal_strength -> attribute: signal_strength
# network.ip_address -> attribute: ip_address
# network.ssid -> attribute: ssid
# network.connected -> state: connected/disconnected
```

### SystemConfig Model → sensor.pixoo_system_config

```python
# pixooasync
config = await pixoo.get_system_config()
# config.brightness -> number.pixoo_brightness.state
# config.rotation -> select.pixoo_rotation.state
# config.mirror_mode -> switch.pixoo_mirror_mode.state
# config.temperature_mode -> select.pixoo_temperature_mode.state
# config.time_format_24h -> select.pixoo_time_format.state
```

### WeatherInfo Model → sensor.pixoo_weather

```python
# pixooasync
weather = await pixoo.get_weather_info()
# weather.weather_type -> attribute: weather_type
# weather.temperature -> state: temperature value
# weather.forecast -> attribute: forecast data
```

### TimerConfig Model → Tool Entities

```python
# pixooasync
timer = await pixoo.get_timer_status()
# timer.minutes -> number.pixoo_timer_minutes.state
# timer.seconds -> number.pixoo_timer_seconds.state
# timer.enabled -> switch.pixoo_timer.state
# timer.remaining -> sensor.pixoo_timer_remaining.state
```

## Enum to Select Options Mapping

### Channel Enum → select.pixoo_channel

```python
from pixooasync import Channel

# Channel.FACES (0) -> "Faces"
# Channel.CLOUD (1) -> "Cloud"
# Channel.VISUALIZER (2) -> "Visualizer"
# Channel.CUSTOM (3) -> "Custom"
```

### Rotation Enum → select.pixoo_rotation

```python
from pixooasync import Rotation

# Rotation.DEG_0 (0) -> "0°"
# Rotation.DEG_90 (1) -> "90°"
# Rotation.DEG_180 (2) -> "180°"
# Rotation.DEG_270 (3) -> "270°"
```

### TemperatureMode Enum → select.pixoo_temperature_mode

```python
from pixooasync import TemperatureMode

# TemperatureMode.CELSIUS (0) -> "Celsius"
# TemperatureMode.FAHRENHEIT (1) -> "Fahrenheit"
```

## Implementation Pattern

### Basic Entity Update Flow

```python
from pixooasync import PixooAsync
from homeassistant.components.number import NumberEntity

class PixooBrightnessNumber(NumberEntity):
    """Brightness control for Pixoo device."""
    
    def __init__(self, pixoo: PixooAsync):
        self._pixoo = pixoo
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
    
    async def async_update(self):
        """Fetch latest brightness from device."""
        config = await self._pixoo.get_system_config()
        self._attr_native_value = config.brightness
    
    async def async_set_native_value(self, value: float):
        """Set brightness on device."""
        await self._pixoo.set_brightness(int(value))
```

### Service Call Pattern

```python
from pixooasync import PixooAsync

async def async_display_image(call):
    """Handle display_image service call."""
    entity_id = call.data["entity_id"]
    file_path = call.data.get("file_path")
    image_url = call.data.get("image_url")
    
    pixoo = get_pixoo_from_entity_id(entity_id)
    
    if file_path:
        await pixoo.send_image(file_path)
    elif image_url:
        # Download and send
        image_data = await download_image(image_url)
        await pixoo.send_image(image_data)
```

## Coordinator Pattern for Sensors

```python
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class PixooDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Pixoo device data updates."""
    
    def __init__(self, hass, pixoo: PixooAsync):
        super().__init__(
            hass,
            _LOGGER,
            name="Pixoo Device",
            update_interval=timedelta(seconds=30),
        )
        self._pixoo = pixoo
    
    async def _async_update_data(self):
        """Fetch data from device."""
        return {
            "device_info": await self._pixoo.get_device_info(),
            "network_status": await self._pixoo.get_network_status(),
            "system_config": await self._pixoo.get_system_config(),
            "weather_info": await self._pixoo.get_weather_info(),
            "time_info": await self._pixoo.get_time_info(),
        }
```

## Testing Reference

### Method Coverage Checklist

- [ ] Device Information (8 methods)
  - [ ] `get_device_info()`
  - [ ] `get_network_status()`
  - [ ] `get_system_config()`
  - [ ] `get_weather_info()`
  - [ ] `get_time_info()`
  - [ ] `get_animation_list()`
  - [ ] `get_image()`
  - [ ] `ping()`

- [ ] Display Control (12 methods)
  - [ ] `set_brightness()`
  - [ ] `set_screen()`
  - [ ] `set_channel()`
  - [ ] `set_clock()`
  - [ ] `set_face()`
  - [ ] `set_visualizer()`
  - [ ] `set_custom_page()`
  - [ ] `set_rotation()`
  - [ ] `set_mirror_mode()`
  - [ ] `set_white_balance()`
  - [ ] `reset_buffer()`
  - [ ] `push_buffer()`

- [ ] Drawing Primitives (8 methods)
  - [ ] `draw_pixel()`
  - [ ] `draw_character()`
  - [ ] `draw_text()`
  - [ ] `draw_line()`
  - [ ] `draw_filled_rectangle()`
  - [ ] `draw_image()`
  - [ ] `send_text()`
  - [ ] `clear_text()`

- [ ] Tool Modes (10 methods)
  - [ ] `set_timer()`
  - [ ] `set_alarm()`
  - [ ] `set_stopwatch()`
  - [ ] `set_scoreboard()`
  - [ ] `set_noise_meter()`
  - [ ] `play_buzzer()`
  - [ ] `get_timer_status()`
  - [ ] `get_alarm_status()`
  - [ ] `get_stopwatch_status()`
  - [ ] `get_scoreboard_status()`

- [ ] Animation & Playlists (6 methods)
  - [ ] `play_animation()`
  - [ ] `stop_animation()`
  - [ ] `send_playlist()`
  - [ ] `get_animation_list()`
  - [ ] `send_gif()`
  - [ ] `send_image()`

- [ ] Configuration (8 methods)
  - [ ] `set_weather_location()`
  - [ ] `set_time()`
  - [ ] `set_timezone()`
  - [ ] `set_temperature_mode()`
  - [ ] `set_time_format()`
  - [ ] `set_gallery_timing()`
  - [ ] `set_screen_brightness_auto()`
  - [ ] `set_screen_rotation_auto()`

**Total Methods**: 52 primary methods + additional variants = 105+ total methods

---

**Reference Version**: 1.0  
**Last Updated**: 2025-11-10  
**Based on**: pixooasync v1.0.0+  
**Specification**: 001-pixoo-integration
