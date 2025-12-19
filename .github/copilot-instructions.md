# pixoo-ha Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-10

## Active Technologies

- Python 3.12+ (001-pixoo-integration)
- Home Assistant Core 2024.1+
- pixooasync v1.0.0+ (async Pixoo device client, import as `from pixooasync import PixooAsync`)
- Pydantic v2.0+ (data validation)
- aiohttp 3.9+ (async HTTP client)
- Pillow 10.0+ (image processing)

## Project Structure

```text
custom_components/pixoo/
├── __init__.py              # Integration setup, service registration
├── manifest.json            # Integration metadata, dependencies
├── config_flow.py           # Config/options flow with SSDP discovery
├── const.py                 # Constants, enums, defaults
├── coordinator.py           # Data update coordinators (4 tiers)
├── entity.py                # Base entity class
├── light.py                 # Light platform (1 entity: power, brightness)
├── media_player.py          # Media player platform (1 entity: image gallery/slideshow)
├── number.py                # Number entities (8 entities)
├── switch.py                # Switch entities (7 entities)
├── select.py                # Select entities (7 entities)
├── sensor.py                # Sensor entities (10 entities)
├── button.py                # Button entities (4 entities)
├── services.yaml            # Service definitions (25 services)
├── strings.json             # UI strings and translations
└── translations/            # Localization files

tests/
├── conftest.py              # Test fixtures (hass, config_entry, mock_pixoo)
├── test_config_flow.py      # Config flow tests
├── test_coordinator.py      # Coordinator tests
├── test_media_player.py     # Media player tests
├── test_*.py                # Entity platform tests

specs/001-pixoo-integration/
├── spec.md                  # Feature specification (756 lines, 13 user stories)
├── plan.md                  # Implementation plan
├── research.md              # Research findings
├── data-model.md            # Entity and coordinator models
├── contracts/               # Service schemas
│   ├── display-services.md  # Display services (4)
│   └── media-player-services.md  # Media player services (7)
├── ENTITY_MAPPING.md        # pixooasync to HA entity mapping
└── quickstart.md            # Developer guide
```

## Commands

```bash
# Development environment
uv venv && source .venv/bin/activate
uv pip install homeassistant pytest pytest-homeassistant-custom-component

# Run tests
pytest
pytest tests/test_config_flow.py
pytest --cov=custom_components.pixoo --cov-report=html

# Code quality
ruff check custom_components/pixoo/ --fix
ruff format custom_components/pixoo/
mypy custom_components/pixoo/ --strict

# Start HA dev server
hass -c config --debug

# Manual testing
curl http://192.168.1.100/post  # Test Pixoo device connectivity
```

## Code Style

**Python 3.12+**: Follow Home Assistant coding standards

### Key Patterns

1. **Async-First Architecture**
   - All device operations use `PixooAsync` from pixooasync
   - Use `hass.async_add_executor_job()` for CPU-bound operations (Pillow)
   - No blocking operations in event loop

2. **Entity Conventions**
   - Inherit from `PixooEntity` base class
   - Use `coordinator.data` for state updates
   - Set `should_poll = False` (coordinator notifies)
   - Implement `device_info` property for device registry

3. **Coordinator Pattern**
   - 4 coordinators with tiered update intervals:
     - DeviceCoordinator: Once (device info)
     - SystemCoordinator: 30s (network, system) + 5min (weather)
     - ToolCoordinator: 1s (active channel, tool states)
     - GalleryCoordinator: 10s (animations, clocks)
   - Use `DataUpdateCoordinator` from `homeassistant.helpers.update_coordinator`
   - Raise `UpdateFailed` on errors

4. **Service Implementation**
   - Define voluptuous schemas for validation
   - Use `async_get_entities()` to resolve entity_id targets
   - Queue service calls per device (FIFO)
   - Log warning at 20+ queue depth
   - Use `ServiceValidationError` for parameter errors
   - Use `HomeAssistantError` for device communication errors

5. **Image Processing**
   - Download with aiohttp (async, 30s timeout, 10MB limit)
   - Validate content-type: `image/*` or `application/octet-stream`
   - Process with Pillow in executor (resize, convert)
   - Use LANCZOS resampling for quality
   - Convert to RGB (remove alpha channel)

6. **Config Flow**
   - Support SSDP discovery (manufacturer: "Divoom")
   - Fallback to manual IP entry
   - Options flow for feature toggles (FR-005)
   - Store unique_id from MAC address
   - Validate connectivity with `pixoo.get_device_info()`

7. **Media Player Pattern** (Image Gallery/Slideshow)
   - Inherit from `MediaPlayerEntity` (not coordinator-based)
   - Internal playlist state management (no coordinator)
   - Playlist format: JSON array `[{"url": "...", "duration": 10}, ...]`
   - Support media-source:// URLs via `media_source.async_resolve_media()`
   - Support external https:// URLs directly
   - Auto-advance timer: `hass.loop.call_later(duration, _auto_advance)`
   - Shuffle: Generate shuffled indices, navigate via shuffle_order
   - Repeat: Loop playlist infinitely or stop at end
   - State: PLAYING (auto-advance), PAUSED (manual only), IDLE (stopped), OFF (no playlist)

   ```python
   async def async_play_media(self, media_type: str, media_id: str):
       if media_type == "playlist":
           playlist_data = json.loads(media_id)
           self._playlist = [PixooPlaylistItem(**item) for item in playlist_data]
           self._position = 0
           await self._display_current_image()
           self._schedule_next()  # Auto-advance timer
       else:
           # Single image
           image_data = await download_image(self.hass, media_id)
           await self.pixoo.display_image_from_bytes(image_data)
   
   def _schedule_next(self):
       if self._timer_handle:
           self._timer_handle.cancel()
       item = self._playlist[self._position]
       self._timer_handle = self.hass.loop.call_later(
           item.duration,
           lambda: asyncio.create_task(self._auto_advance())
       )
   ```

### Pydantic Models (from pixooasync)

Use these models directly for type safety:

```python
from pixooasync.models import (
    DeviceInfo,           # IP, MAC, model, firmware
    NetworkStatus,        # SSID, signal strength
    SystemConfig,         # Brightness, rotation, mirror
    WeatherInfo,          # Temperature, condition
    TimeInfo,             # Current time, timezone
    AlarmConfig,          # Hour, minute, enabled
    TimerConfig,          # Minutes, seconds, running
    StopwatchConfig,      # Elapsed time
    ScoreboardConfig,     # Red/blue scores
    NoiseMeterConfig,     # Sensitivity
)

from pixooasync.enums import (
    Channel,              # CLOCK, CLOUD, VISUALIZER, etc.
    Rotation,             # NORMAL, ROTATE_90, ROTATE_180, ROTATE_270
    TemperatureMode,      # CELSIUS, FAHRENHEIT
    TextScrollDirection,  # LEFT, RIGHT, UP, DOWN
)
```

### Testing Patterns

```python
# Fixture example (conftest.py)
@pytest.fixture
async def mock_pixoo():
    """Mock PixooAsync client."""
    with patch("custom_components.pixoo.PixooAsync") as mock:
        mock.return_value.get_device_info.return_value = DeviceInfo(
            ip_address="192.168.1.100",
            mac_address="AA:BB:CC:DD:EE:FF",
            model="Pixoo64",
            firmware_version="2.0",
        )
        yield mock.return_value

# Entity test example
async def test_light_turn_on(hass, config_entry, mock_pixoo):
    """Test light entity turn_on."""
    coordinator = PixooSystemCoordinator(hass, mock_pixoo, config_entry)
    light = PixooLight(coordinator, config_entry)
    
    await light.async_turn_on(brightness=128)
    
    mock_pixoo.set_brightness.assert_called_once_with(50)  # 128/255 * 100
    mock_pixoo.turn_on.assert_called_once()

# Service test example
async def test_display_image_service(hass, config_entry, mock_pixoo):
    """Test display_image service."""
    await async_setup_entry(hass, config_entry)
    
    with patch("custom_components.pixoo._download_image") as mock_download:
        mock_download.return_value = b"fake_image_data"
        
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DISPLAY_IMAGE,
            {
                ATTR_ENTITY_ID: "light.pixoo_test",
                ATTR_URL: "http://example.com/image.jpg",
            },
            blocking=True,
        )
    
    mock_pixoo.display_image_from_bytes.assert_called_once()
```

## Recent Changes

- 001-pixoo-integration: Added Python 3.12+, Home Assistant integration, pixooasync package
- Media player enhancement: Added image gallery/slideshow entity (User Story 13)
- Package rename: Renamed from `pixoo` to `pixooasync` for clarity

## Constitution Principles

This project follows 7 core principles (see `.specify/memory/constitution.md`):

1. **Async-First Architecture**: All operations use async/await, PixooAsync client
2. **HA Native Integration**: Config flow, entity registry, device registry, SSDP
3. **Python Package Dependency**: Uses pixooasync exclusively (no direct protocol)
4. **Modern Python Standards**: Python 3.12+, Pydantic v2, type hints
5. **AI Agent Friendly Code**: Comprehensive docs, clear structure, type safety
6. **Test-Driven Development**: 35 success criteria, pytest fixtures, 100% coverage goal
7. **Maintainability & Simplicity**: Single integration, no overengineering, HA patterns

## Entity Reference

**40+ entities per device**:

- **Light (1)**: Power and brightness control
- **Media Player (1)**: Image gallery/slideshow with playlist, shuffle, repeat
- **Number (8)**: Brightness, timer (min/sec), alarm (hour/min), scoreboard (red/blue), gallery interval
- **Switch (7)**: Timer, alarm, stopwatch, scoreboard, noise meter, mirror mode, 24h format
- **Select (7)**: Channel, rotation, temperature unit, time format, custom page, clock face, visualizer
- **Sensor (10)**: IP, MAC, Wi-Fi (SSID, strength), brightness, temperature, weather, time, channel, tool state
- **Button (4)**: Dismiss notification, buzzer, reset buffer, push buffer

## Service Reference

**32 services total**:

### Integration Services (25 services)

1. **Display (4)**: display_image, display_gif, display_text, clear_display
2. **Drawing (7)**: draw_pixel, draw_text, draw_line, draw_rectangle, draw_image, reset_buffer, push_buffer
3. **Tool (6)**: set_timer, set_alarm, start_stopwatch, reset_stopwatch, set_scoreboard, play_buzzer
4. **Configuration (4)**: set_white_balance, set_weather_location, set_timezone, set_time
5. **Animation (4)**: play_animation, stop_animation, set_playlist, list_animations

### Media Player Services (7 services)

Standard HA media_player services with custom implementation:

- **play_media**: Display single image or start playlist slideshow
- **media_play**: Resume paused slideshow
- **media_pause**: Pause slideshow (keeps current image)
- **media_stop**: Stop slideshow and clear display
- **media_next_track**: Display next image (respects shuffle)
- **media_previous_track**: Display previous image
- **shuffle_set**: Enable/disable shuffle mode
- **repeat_set**: Enable/disable repeat mode

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
