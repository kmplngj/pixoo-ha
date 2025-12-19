# Data Model: Pixoo Integration

**Date**: 2025-11-10  
**Feature**: Divoom Pixoo Home Assistant Integration  
**Branch**: 001-pixoo-integration

## Overview

This document defines the data models, entity structures, and coordinator data flow for the Pixoo Home Assistant integration.

## Entity Model

### Entity Platforms

The integration implements 40+ entities across 6 platforms:

| Platform | Count | Purpose | Update Method |
|----------|-------|---------|---------------|
| Light | 1 | Power control and brightness | State-based (coordinator) |
| Number | 8 | Numeric configuration values | State-based (coordinator) |
| Switch | 7 | Binary toggles for features | State-based (coordinator) |
| Select | 7 | Enumerated options | State-based (coordinator) |
| Sensor | 10 | Read-only device state | Polled (coordinator) |
| Button | 4 | Stateless actions | Action-only (no state) |

### Base Entity: PixooEntity

All entities inherit from `PixooEntity` which provides common functionality:

```python
class PixooEntity(Entity):
    """Base class for Pixoo entities."""
    
    def __init__(self, coordinator: PixooCoordinator, entry: ConfigEntry):
        """Initialize the entity."""
        self.coordinator = coordinator
        self._entry = entry
        self._device_id = entry.unique_id
        self._device_info = self._build_device_info()
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._entry.title,
            "manufacturer": "Divoom",
            "model": self.coordinator.data.get("device_info", {}).get("model", "Pixoo"),
            "sw_version": self.coordinator.data.get("device_info", {}).get("firmware_version"),
            "via_device": None,
        }
    
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
    
    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False
    
    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
```

### Light Platform (1 entity)

**Entity**: `light.pixoo_{device_name}`

```python
@dataclass
class PixooLightState:
    """State model for Pixoo light entity."""
    is_on: bool  # Power state
    brightness: int  # 0-100 (from pixooasync.models.SystemConfig.brightness)

# Attributes
- brightness: 0-100
- effect: None (no light effects)
- supported_features: SUPPORT_BRIGHTNESS
- supported_color_modes: [ColorMode.BRIGHTNESS]
- color_mode: ColorMode.BRIGHTNESS

# Methods
- async_turn_on(brightness=None): await pixoo.set_brightness(brightness) if brightness else await pixoo.turn_on()
- async_turn_off(): await pixoo.turn_off()

# Updates
- Polls coordinator.data["system"]["power"] and coordinator.data["system"]["brightness"]
```

### Media Player Platform (1 entity)

**Entity**: `media_player.pixoo_{device_name}`

The media player entity handles image gallery/slideshow functionality with playlist support.

```python
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    MediaClass,
)

@dataclass
class PixooPlaylistItem:
    """Playlist item model."""
    url: str  # media-source:// or http(s)://
    duration: int = 10  # seconds per image
    
@dataclass
class PixooMediaPlayerState:
    """State model for media player entity."""
    state: MediaPlayerState  # PLAYING, PAUSED, IDLE, OFF
    media_content_type: str  # MediaType.IMAGE or MediaType.URL
    media_content_id: str | None  # Current image URL or playlist JSON
    media_image_url: str | None  # Currently displayed image
    media_position: int = 0  # Current playlist index
    media_duration: int = 10  # Seconds per image
    shuffle: bool = False  # Random order
    repeat: bool = False  # Loop playlist
    playlist: list[PixooPlaylistItem] = field(default_factory=list)
    _shuffle_order: list[int] | None = None  # Shuffled indices
    _timer_handle: asyncio.TimerHandle | None = None  # Auto-advance timer

# Attributes
- supported_features: 
    PLAY | PAUSE | STOP | NEXT_TRACK | PREVIOUS_TRACK | SHUFFLE_SET | REPEAT_SET
- media_content_type: MediaType.IMAGE or MediaType.URL
- media_content_id: Current image or playlist JSON
- media_image_url: URL of currently displayed image
- media_position: Current index in playlist (0-based)
- media_duration: Seconds per image (default 10)
- shuffle: Boolean shuffle state
- repeat: Boolean repeat state (off=False, all=True)
- media_class: MediaClass.IMAGE

# Methods
- async_play_media(media_type, media_id):
    """Display image or start playlist slideshow.
    
    Single image:
        media_type: MediaType.IMAGE or MediaType.URL
        media_id: "media-source://..." or "https://..."
    
    Playlist:
        media_type: MediaType.PLAYLIST
        media_id: JSON array of playlist items:
            [{"url": "...", "duration": 10}, ...]
    """
    if media_type == MediaType.PLAYLIST:
        self._load_playlist(json.loads(media_id))
        await self._display_current_image()
        self._schedule_next()
    else:
        self._load_single_image(media_id)
        await self._display_current_image()

- async_media_play():
    """Resume slideshow."""
    self._state = MediaPlayerState.PLAYING
    self._schedule_next()

- async_media_pause():
    """Pause slideshow."""
    self._state = MediaPlayerState.PAUSED
    self._cancel_timer()

- async_media_stop():
    """Stop slideshow and clear display."""
    self._state = MediaPlayerState.IDLE
    self._cancel_timer()
    self._playlist = []
    await self.coordinator.pixoo.clear_display()

- async_media_next_track():
    """Display next image in playlist."""
    if self._shuffle:
        self._position = self._shuffle_order[(self._shuffle_order.index(self._position) + 1) % len(self._shuffle_order)]
    else:
        self._position = (self._position + 1) % len(self._playlist)
    await self._display_current_image()
    if self._state == MediaPlayerState.PLAYING:
        self._schedule_next()

- async_media_previous_track():
    """Display previous image in playlist."""
    if self._shuffle:
        self._position = self._shuffle_order[(self._shuffle_order.index(self._position) - 1) % len(self._shuffle_order)]
    else:
        self._position = (self._position - 1) % len(self._playlist)
    await self._display_current_image()
    if self._state == MediaPlayerState.PLAYING:
        self._schedule_next()

- async_set_shuffle(shuffle: bool):
    """Enable/disable shuffle mode."""
    self._shuffle = shuffle
    if shuffle and not self._shuffle_order:
        self._shuffle_order = list(range(len(self._playlist)))
        random.shuffle(self._shuffle_order)
    self.async_write_ha_state()

- async_set_repeat(repeat: bool):
    """Enable/disable repeat mode."""
    self._repeat = repeat
    self.async_write_ha_state()

# Private Methods
- async _display_current_image():
    """Display the current playlist image."""
    item = self._playlist[self._position]
    if item.url.startswith("media-source://"):
        # Resolve media source URL
        resolved = await media_source.async_resolve_media(self.hass, item.url)
        url = resolved.url
    else:
        url = item.url
    
    # Download and display
    image_data = await download_image(self.hass, url)
    await self.coordinator.pixoo.display_image_from_bytes(image_data)
    
    self._media_image_url = url
    self.async_write_ha_state()

- def _schedule_next():
    """Schedule automatic advance to next image."""
    if self._timer_handle:
        self._timer_handle.cancel()
    
    item = self._playlist[self._position]
    self._timer_handle = self.hass.loop.call_later(
        item.duration,
        lambda: asyncio.create_task(self._auto_advance())
    )

- async _auto_advance():
    """Automatically advance to next image."""
    if self._state != MediaPlayerState.PLAYING:
        return
    
    # Check if at end of playlist
    is_last = (self._position == len(self._playlist) - 1 and not self._shuffle) or \
              (self._shuffle and self._shuffle_order.index(self._position) == len(self._shuffle_order) - 1)
    
    if is_last and not self._repeat:
        self._state = MediaPlayerState.IDLE
        self.async_write_ha_state()
        return
    
    await self.async_media_next_track()

- def _load_playlist(items: list[dict]):
    """Load playlist from JSON."""
    self._playlist = [PixooPlaylistItem(**item) for item in items]
    self._position = 0
    self._state = MediaPlayerState.PLAYING
    if self._shuffle:
        self._shuffle_order = list(range(len(self._playlist)))
        random.shuffle(self._shuffle_order)

- def _load_single_image(url: str):
    """Load single image as 1-item playlist."""
    self._playlist = [PixooPlaylistItem(url=url, duration=0)]
    self._position = 0
    self._state = MediaPlayerState.IDLE  # Single images don't auto-advance

# Updates
- No polling needed (playlist managed internally)
- State changes trigger async_write_ha_state()
```

**Example Usage:**

```yaml
# Display single image
service: media_player.play_media
target:
  entity_id: media_player.pixoo_bedroom
data:
  media_content_type: image
  media_content_id: "https://example.com/photo.jpg"

# Play local folder slideshow
service: media_player.play_media
target:
  entity_id: media_player.pixoo_bedroom
data:
  media_content_type: playlist
  media_content_id: >
    [
      {"url": "media-source://media_source/local/photos/photo1.jpg", "duration": 30},
      {"url": "media-source://media_source/local/photos/photo2.jpg", "duration": 30},
      {"url": "media-source://media_source/local/photos/photo3.jpg", "duration": 30}
    ]

# Play mixed URL/local playlist with shuffle
service: media_player.play_media
target:
  entity_id: media_player.pixoo_bedroom
data:
  media_content_type: playlist
  media_content_id: >
    [
      {"url": "https://picsum.photos/64", "duration": 10},
      {"url": "media-source://media_source/local/art/painting.jpg", "duration": 15},
      {"url": "https://example.com/photo.jpg", "duration": 20}
    ]

# Enable shuffle
service: media_player.shuffle_set
target:
  entity_id: media_player.pixoo_bedroom
data:
  shuffle: true

# Navigate playlist
service: media_player.media_next_track
target:
  entity_id: media_player.pixoo_bedroom
```

### Number Platform (8 entities)

Each number entity corresponds to a configurable numeric value:

| Entity ID | Label | Min | Max | Step | Unit | pixooasync Method |
|-----------|-------|-----|-----|------|------|-----------------|
| `number.pixoo_{name}_brightness` | Brightness | 0 | 100 | 1 | % | `set_brightness(value)` |
| `number.pixoo_{name}_timer_minutes` | Timer Minutes | 0 | 60 | 1 | min | `set_timer(minutes, seconds)` |
| `number.pixoo_{name}_timer_seconds` | Timer Seconds | 0 | 59 | 1 | s | `set_timer(minutes, seconds)` |
| `number.pixoo_{name}_alarm_hour` | Alarm Hour | 0 | 23 | 1 | h | `set_alarm(hour, minute)` |
| `number.pixoo_{name}_alarm_minute` | Alarm Minute | 0 | 59 | 1 | min | `set_alarm(hour, minute)` |
| `number.pixoo_{name}_scoreboard_red` | Scoreboard Red Score | 0 | 999 | 1 | - | `set_scoreboard(red, blue)` |
| `number.pixoo_{name}_scoreboard_blue` | Scoreboard Blue Score | 0 | 999 | 1 | - | `set_scoreboard(red, blue)` |
| `number.pixoo_{name}_gallery_interval` | Gallery Change Interval | 5 | 3600 | 5 | s | `set_gallery_interval(seconds)` |

```python
@dataclass
class PixooNumberState:
    """State model for number entities."""
    value: float
    min_value: float
    max_value: float
    step: float
    unit: str | None

# Common attributes
- native_value: Current value from coordinator
- native_min_value: Minimum allowed value
- native_max_value: Maximum allowed value
- native_step: Step increment
- native_unit_of_measurement: Unit string

# Methods
- async_set_native_value(value): Call appropriate pixooasync method
```

### Switch Platform (7 entities)

Binary toggle entities for features:

| Entity ID | Label | Default | pixooasync Method (on) | pixooasync Method (off) |
|-----------|-------|---------|----------------------|-----------------------|
| `switch.pixoo_{name}_timer` | Timer | off | `start_timer()` | `stop_timer()` |
| `switch.pixoo_{name}_alarm` | Alarm | off | `set_alarm_enabled(True)` | `set_alarm_enabled(False)` |
| `switch.pixoo_{name}_stopwatch` | Stopwatch | off | `start_stopwatch()` | `reset_stopwatch()` |
| `switch.pixoo_{name}_scoreboard` | Scoreboard | off | `set_channel(Channel.SCOREBOARD)` | `set_channel(previous_channel)` |
| `switch.pixoo_{name}_noise_meter` | Noise Meter | off | `set_channel(Channel.NOISE_METER)` | `set_channel(previous_channel)` |
| `switch.pixoo_{name}_mirror_mode` | Mirror Mode | off | `set_mirror_mode(True)` | `set_mirror_mode(False)` |
| `switch.pixoo_{name}_24h_mode` | 24-Hour Time | off | `set_24h_mode(True)` | `set_24h_mode(False)` |

```python
@dataclass
class PixooSwitchState:
    """State model for switch entities."""
    is_on: bool

# Attributes
- is_on: Boolean state from coordinator

# Methods
- async_turn_on(): Call on method
- async_turn_off(): Call off method
```

### Select Platform (7 entities)

Dropdown selection entities for enums:

| Entity ID | Label | Options | pixooasync Enum | Method |
|-----------|-------|---------|---------------|--------|
| `select.pixoo_{name}_channel` | Channel | clock, cloud, visualizer, custom, face, gallery | `Channel` | `set_channel(channel)` |
| `select.pixoo_{name}_rotation` | Screen Rotation | 0, 90, 180, 270 | `Rotation` | `set_rotation(angle)` |
| `select.pixoo_{name}_temperature_unit` | Temperature Unit | celsius, fahrenheit | `TemperatureMode` | `set_temperature_unit(mode)` |
| `select.pixoo_{name}_time_format` | Time Format | 12h, 24h | N/A (boolean) | `set_24h_mode(True/False)` |
| `select.pixoo_{name}_custom_page` | Custom Channel Page | 0-2 | N/A (int) | `set_custom_page(index)` |
| `select.pixoo_{name}_clock_face` | Clock Face | Dynamic (fetched) | N/A (int) | `set_clock_face(id)` |
| `select.pixoo_{name}_visualizer` | Visualizer Type | Dynamic (fetched) | N/A (int) | `set_visualizer(id)` |

```python
@dataclass
class PixooSelectState:
    """State model for select entities."""
    current_option: str
    options: list[str]

# Attributes
- current_option: Current selection from coordinator
- options: List of available options (static or dynamic)

# Methods
- async_select_option(option): Map option to enum/int and call pixooasync method
```

### Sensor Platform (10 entities)

Read-only diagnostic and state sensors:

| Entity ID | Label | Device Class | State Class | Update Interval | Source |
|-----------|-------|--------------|-------------|-----------------|--------|
| `sensor.pixoo_{name}_ip_address` | IP Address | None | None | Once | `DeviceInfo.ip_address` |
| `sensor.pixoo_{name}_mac_address` | MAC Address | None | None | Once | `DeviceInfo.mac_address` |
| `sensor.pixoo_{name}_wifi_ssid` | Wi-Fi SSID | None | None | 60s | `NetworkStatus.ssid` |
| `sensor.pixoo_{name}_wifi_strength` | Wi-Fi Strength | signal_strength | measurement | 60s | `NetworkStatus.signal_strength` |
| `sensor.pixoo_{name}_brightness` | Current Brightness | None | measurement | 30s | `SystemConfig.brightness` |
| `sensor.pixoo_{name}_temperature` | Temperature | temperature | measurement | 300s | `WeatherInfo.temperature` |
| `sensor.pixoo_{name}_weather` | Weather Condition | None | None | 300s | `WeatherInfo.condition` |
| `sensor.pixoo_{name}_current_time` | Device Time | timestamp | None | 30s | `TimeInfo.current_time` |
| `sensor.pixoo_{name}_active_channel` | Active Channel | None | None | 1s | `get_current_channel()` |
| `sensor.pixoo_{name}_tool_state` | Tool State | None | None | 1s | Tool coordinator data |

```python
@dataclass
class PixooSensorState:
    """State model for sensor entities."""
    native_value: str | int | float | None
    device_class: SensorDeviceClass | None
    state_class: SensorStateClass | None
    unit_of_measurement: str | None
    extra_attributes: dict[str, Any]

# Attributes
- native_value: Current value from coordinator
- device_class: Type of sensor (signal_strength, temperature, timestamp)
- state_class: measurement (for numeric values)
- native_unit_of_measurement: Unit string (dBm, °C, °F)
- extra_state_attributes: Additional context (e.g., alarm time, timer remaining)

# Methods
- None (read-only)
```

### Button Platform (4 entities)

Stateless action triggers:

| Entity ID | Label | Icon | Action | pixooasync Method |
|-----------|-------|------|--------|-----------------|
| `button.pixoo_{name}_dismiss_notification` | Dismiss Notification | mdi:bell-off | Restore previous channel | `set_channel(previous)` |
| `button.pixoo_{name}_buzzer` | Buzzer | mdi:bell-ring | Play buzzer sound | `play_buzzer(duration, cycles)` |
| `button.pixoo_{name}_reset_buffer` | Reset Drawing Buffer | mdi:eraser | Clear drawing buffer | `reset_buffer()` |
| `button.pixoo_{name}_push_buffer` | Push Buffer to Display | mdi:monitor-arrow-down | Send buffer to screen | `push_buffer()` |

```python
@dataclass
class PixooButtonConfig:
    """Configuration for button entities."""
    entity_id: str
    label: str
    icon: str
    action_method: str  # Name of pixooasync method

# Attributes
- None (stateless)

# Methods
- async_press(): Execute configured action
```

## Coordinator Data Model

### Multiple Coordinators Strategy

Based on research findings, we implement 4 coordinators with different update intervals:

```python
@dataclass
class PixooDeviceData:
    """Device information (fetched once on setup)."""
    device_info: DeviceInfo  # IP, MAC, model, firmware
    capabilities: dict[str, bool]  # Supported features

@dataclass
class PixooSystemData:
    """System data (updated every 30-60s)."""
    network_status: NetworkStatus  # SSID, signal strength
    system_config: SystemConfig    # Brightness, rotation, mirror mode
    weather_info: WeatherInfo      # Temperature, condition (5min)
    time_info: TimeInfo            # Current time, timezone

@dataclass
class PixooToolData:
    """Tool state (updated every 1s)."""
    active_channel: Channel        # Current channel
    timer_state: TimerConfig | None
    alarm_state: AlarmConfig | None
    stopwatch_state: StopwatchConfig | None
    scoreboard_state: ScoreboardConfig | None
    noise_meter_state: NoiseMeterConfig | None

@dataclass
class PixooGalleryData:
    """Gallery data (updated every 10s)."""
    current_animation: str | None
    available_clocks: list[int]
    available_visualizers: list[int]
```

### Coordinator Classes

```python
class PixooDeviceCoordinator(DataUpdateCoordinator[PixooDeviceData]):
    """Coordinator for one-time device information."""
    
    def __init__(self, hass: HomeAssistant, pixoo: PixooAsync, entry: ConfigEntry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Pixoo Device ({entry.title})",
            update_interval=None,  # Manual updates only
        )
        self.pixoo = pixoo
        self.entry = entry
    
    async def _async_update_data(self) -> PixooDeviceData:
        """Fetch device information."""
        try:
            device_info = await self.pixoo.get_device_info()
            capabilities = await self._detect_capabilities()
            return PixooDeviceData(device_info=device_info, capabilities=capabilities)
        except Exception as err:
            raise UpdateFailed(f"Error fetching device data: {err}") from err
    
    async def _detect_capabilities(self) -> dict[str, bool]:
        """Detect which features the device supports."""
        # Query device for supported channels/features
        return {"timer": True, "alarm": True, "weather": True}

class PixooSystemCoordinator(DataUpdateCoordinator[PixooSystemData]):
    """Coordinator for system state (network, config, weather)."""
    
    def __init__(self, hass: HomeAssistant, pixoo: PixooAsync, entry: ConfigEntry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Pixoo System ({entry.title})",
            update_interval=timedelta(seconds=30),  # Base interval
        )
        self.pixoo = pixoo
        self.entry = entry
        self._last_weather_update = 0
    
    async def _async_update_data(self) -> PixooSystemData:
        """Fetch system data."""
        try:
            # Always update network and system
            network = await self.pixoo.get_network_status()
            system = await self.pixoo.get_system_config()
            time_info = await self.pixoo.get_time_info()
            
            # Weather updates every 5 minutes
            now = time.time()
            if now - self._last_weather_update > 300:
                weather = await self.pixoo.get_weather()
                self._last_weather_update = now
            else:
                weather = self.data.weather_info if self.data else None
            
            return PixooSystemData(
                network_status=network,
                system_config=system,
                weather_info=weather,
                time_info=time_info,
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching system data: {err}") from err

class PixooToolCoordinator(DataUpdateCoordinator[PixooToolData]):
    """Coordinator for active tool state (1s updates)."""
    
    def __init__(self, hass: HomeAssistant, pixoo: PixooAsync, entry: ConfigEntry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Pixoo Tool ({entry.title})",
            update_interval=timedelta(seconds=1),
        )
        self.pixoo = pixoo
        self.entry = entry
    
    async def _async_update_data(self) -> PixooToolData:
        """Fetch tool state."""
        try:
            channel = await self.pixoo.get_current_channel()
            
            # Fetch tool-specific state based on channel
            timer = await self.pixoo.get_timer_state() if channel == Channel.TOOLS else None
            alarm = await self.pixoo.get_alarm_config()
            stopwatch = await self.pixoo.get_stopwatch_state() if channel == Channel.STOPWATCH else None
            scoreboard = await self.pixoo.get_scoreboard_config() if channel == Channel.SCOREBOARD else None
            noise = await self.pixoo.get_noise_meter_config() if channel == Channel.NOISE_METER else None
            
            return PixooToolData(
                active_channel=channel,
                timer_state=timer,
                alarm_state=alarm,
                stopwatch_state=stopwatch,
                scoreboard_state=scoreboard,
                noise_meter_state=noise,
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching tool data: {err}") from err

class PixooGalleryCoordinator(DataUpdateCoordinator[PixooGalleryData]):
    """Coordinator for gallery/animation data (10s updates)."""
    
    def __init__(self, hass: HomeAssistant, pixoo: PixooAsync, entry: ConfigEntry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Pixoo Gallery ({entry.title})",
            update_interval=timedelta(seconds=10),
        )
        self.pixoo = pixoo
        self.entry = entry
    
    async def _async_update_data(self) -> PixooGalleryData:
        """Fetch gallery data."""
        try:
            # These lists don't change often, cache aggressively
            clocks = await self.pixoo.get_clock_list() if self.data is None else self.data.available_clocks
            visualizers = await self.pixoo.get_visualizer_list() if self.data is None else self.data.available_visualizers
            current_anim = await self.pixoo.get_current_animation()
            
            return PixooGalleryData(
                current_animation=current_anim,
                available_clocks=clocks,
                available_visualizers=visualizers,
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching gallery data: {err}") from err
```

## pixooasync Models Integration

### Direct Pydantic Model Usage

The integration uses pixooasync's Pydantic models directly where applicable:

```python
from pixooasync.models import (
    DeviceInfo,
    NetworkStatus,
    SystemConfig,
    WeatherInfo,
    TimeInfo,
    AlarmConfig,
    TimerConfig,
    StopwatchConfig,
    ScoreboardConfig,
    NoiseMeterConfig,
)

# Example: Sensor attributes from Pydantic models
class PixooWeatherSensor(PixooEntity, SensorEntity):
    """Weather condition sensor."""
    
    @property
    def native_value(self) -> str:
        """Return current weather condition."""
        weather: WeatherInfo = self.coordinator.data.weather_info
        return weather.condition.value  # Enum to string
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional weather attributes."""
        weather: WeatherInfo = self.coordinator.data.weather_info
        return {
            "temperature": weather.temperature,
            "feels_like": weather.feels_like,
            "humidity": weather.humidity,
            "wind_speed": weather.wind_speed,
        }
```

### Enum Mapping

pixooasync enums are mapped to HA select options:

```python
from pixooasync.enums import Channel, Rotation, TemperatureMode

CHANNEL_OPTIONS = {
    "clock": Channel.CLOCK,
    "cloud": Channel.CLOUD,
    "visualizer": Channel.VISUALIZER,
    "custom": Channel.CUSTOM,
    "face": Channel.FACE,
    "gallery": Channel.GALLERY,
}

ROTATION_OPTIONS = {
    "0": Rotation.NORMAL,
    "90": Rotation.ROTATE_90,
    "180": Rotation.ROTATE_180,
    "270": Rotation.ROTATE_270,
}

TEMP_OPTIONS = {
    "celsius": TemperatureMode.CELSIUS,
    "fahrenheit": TemperatureMode.FAHRENHEIT,
}
```

## Config Entry Data Model

### Entry Data Structure

```python
@dataclass
class PixooConfigEntry:
    """Config entry data stored in HA registry."""
    host: str                       # Device IP address
    unique_id: str                  # MAC address
    title: str                      # User-friendly name
    options: dict[str, Any]         # Feature toggles
    
    # Runtime data (not persisted)
    device_coordinator: PixooDeviceCoordinator
    system_coordinator: PixooSystemCoordinator
    tool_coordinator: PixooToolCoordinator
    gallery_coordinator: PixooGalleryCoordinator
    pixoo_client: PixooAsync

# Entry data keys
CONF_HOST = "host"
CONF_UNIQUE_ID = "unique_id"

# Entry options keys
OPT_ENABLE_TIMER = "enable_timer"
OPT_ENABLE_ALARM = "enable_alarm"
OPT_ENABLE_STOPWATCH = "enable_stopwatch"
OPT_ENABLE_SCOREBOARD = "enable_scoreboard"
OPT_ENABLE_NOISE_METER = "enable_noise_meter"
OPT_ENABLE_WEATHER = "enable_weather"
OPT_ENABLE_DRAWING = "enable_drawing"
```

## Entity State Transitions

### Tool Mode State Machine

Tools are mutually exclusive per device. State transitions:

```
[Any Channel] --turn on timer--> [TOOLS Channel, Timer Active]
[TOOLS Channel, Timer Active] --turn on alarm--> [CLOCK Channel, Alarm Active] + INFO log
[TOOLS Channel, Timer Active] --turn off timer--> [Previous Channel]
[SCOREBOARD Channel] --turn on noise meter--> [NOISE_METER Channel] + INFO log
```

### Notification State Machine

```
[Display Mode] --notification arrives--> [CLOUD Channel (notification display)]
                                         └─> Store previous_channel in entry data

[CLOUD Channel] --press dismiss button--> [Restore previous_channel]

[CLOUD Channel] --notification expires--> [Automatic restore after 30s]
```

## Service Call Data Model

### Service Parameters (Voluptuous Schemas)

Example service schema for `pixoo.display_image`:

```python
SERVICE_DISPLAY_IMAGE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_URL): cv.url,
    vol.Optional(ATTR_MAX_SIZE_MB, default=10): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
    vol.Optional(ATTR_TIMEOUT, default=30): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
})
```

### Service Call Queue

Services are queued per device to prevent conflicts:

```python
@dataclass
class ServiceCallQueueItem:
    """Item in service call queue."""
    service: str                    # Service name
    params: dict[str, Any]          # Service parameters
    call_id: str                    # Unique call ID
    queued_at: float                # Timestamp

class PixooServiceQueue:
    """FIFO queue for service calls per device."""
    
    def __init__(self, max_depth: int = 100):
        """Initialize queue."""
        self._queue: deque[ServiceCallQueueItem] = deque()
        self._max_depth = max_depth
        self._processing = False
    
    async def enqueue(self, item: ServiceCallQueueItem) -> None:
        """Add service call to queue."""
        self._queue.append(item)
        
        # Log warning if queue depth exceeds threshold
        if len(self._queue) > 20:
            _LOGGER.warning(
                "Service call queue depth is %d (warning threshold: 20)",
                len(self._queue)
            )
        
        # Start processing if not already running
        if not self._processing:
            await self._process_queue()
    
    async def _process_queue(self) -> None:
        """Process queued service calls."""
        self._processing = True
        
        while self._queue:
            item = self._queue.popleft()
            await self._execute_service(item)
        
        self._processing = False
```

## Summary

**Entity Count**: 40+ entities per device  
**Coordinators**: 4 (device, system, tool, gallery) with tiered update intervals  
**Pydantic Models**: 15 models from pixooasync used directly  
**Service Queue**: FIFO with warning at 20+ depth  
**State Storage**: HA config entries and entity registry

**Next Phase**: Contract Definition (services.yaml, parameter schemas)

---

**Data model completed**: 2025-11-10  
**Ready for contract definition**: ✅
