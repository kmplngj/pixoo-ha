# Service Contracts Index

**Feature**: Divoom Pixoo Home Assistant Integration  
**Total Services**: 25 integration services + 7 media player services

## Service Categories

### 0. Media Player Services (7 services)

**File**: `media-player-services.md` ✅

Standard Home Assistant media player services with custom implementation for image gallery/slideshow:

| Service | Description | Key Parameters |
|---------|-------------|----------------|
| `media_player.play_media` | Display image or start slideshow | media_content_type, media_content_id (URL or playlist JSON) |
| `media_player.media_play` | Resume paused slideshow | - |
| `media_player.media_pause` | Pause slideshow | - |
| `media_player.media_stop` | Stop slideshow and clear display | - |
| `media_player.media_next_track` | Display next image | - |
| `media_player.media_previous_track` | Display previous image | - |
| `media_player.shuffle_set` | Enable/disable shuffle | shuffle (bool) |
| `media_player.repeat_set` | Enable/disable repeat | repeat ("off" or "all") |

**Note**: Media player uses standard HA services (namespace: `media_player`), not custom `pixoo` services.

### 1. Display Services (4 services)

**File**: `display-services.md` ✅

| Service | Description | Key Parameters |
|---------|-------------|----------------|
| `pixoo.display_image` | Display static image from URL | url, max_size_mb, timeout |
| `pixoo.display_gif` | Display animated GIF | url, max_size_mb, timeout |
| `pixoo.display_text` | Display scrolling/static text | text, x, y, color, scroll_direction |
| `pixoo.clear_display` | Clear display and reset | - |

### 2. Drawing Services (7 services)

**Status**: To be defined in `drawing-services.md`

| Service | Description | Key Parameters |
|---------|-------------|----------------|
| `pixoo.draw_pixel` | Draw single pixel | x, y, color |
| `pixoo.draw_text` | Draw text at position | text, x, y, color, font_size |
| `pixoo.draw_line` | Draw line between points | x1, y1, x2, y2, color |
| `pixoo.draw_rectangle` | Draw filled/outlined rectangle | x, y, width, height, color, filled |
| `pixoo.draw_image` | Draw image at position | url, x, y, width, height |
| `pixoo.reset_buffer` | Clear drawing buffer | - |
| `pixoo.push_buffer` | Push buffer to display | - |

### 3. Tool Services (6 services)

**Status**: To be defined in `tool-services.md`

| Service | Description | Key Parameters |
|---------|-------------|----------------|
| `pixoo.set_timer` | Configure timer | minutes, seconds |
| `pixoo.set_alarm` | Configure alarm | hour, minute, enabled |
| `pixoo.start_stopwatch` | Start stopwatch | - |
| `pixoo.reset_stopwatch` | Reset stopwatch | - |
| `pixoo.set_scoreboard` | Update scoreboard scores | red_score, blue_score |
| `pixoo.play_buzzer` | Play buzzer sound | duration_ms, cycles |

### 4. Configuration Services (4 services)

**Status**: To be defined in `config-services.md`

| Service | Description | Key Parameters |
|---------|-------------|----------------|
| `pixoo.set_white_balance` | Adjust white balance | red, green, blue |
| `pixoo.set_weather_location` | Set weather location | latitude, longitude, city |
| `pixoo.set_timezone` | Set device timezone | timezone |
| `pixoo.set_time` | Sync device time | timestamp |

### 5. Animation Services (4 services)

**Status**: To be defined in `animation-services.md`

| Service | Description | Key Parameters |
|---------|-------------|----------------|
| `pixoo.play_animation` | Play animation by ID | animation_id |
| `pixoo.stop_animation` | Stop current animation | - |
| `pixoo.set_playlist` | Configure animation playlist | items, shuffle, loop |
| `pixoo.list_animations` | Get available animations | category |

## Service Call Patterns

### Basic Service Call (YAML)

```yaml
service: pixoo.display_image
data:
  entity_id: light.pixoo_bedroom
  url: "http://example.com/image.jpg"
```

### Advanced Service Call with Options

```yaml
service: pixoo.display_text
data:
  entity_id: light.pixoo_bedroom
  text: "Hello World!"
  x: 10
  y: 20
  color: "#FF0000"
  scroll_direction: "left"
  scroll_speed: 50
```

### Multi-Entity Service Call

```yaml
service: pixoo.clear_display
target:
  entity_id:
    - light.pixoo_bedroom
    - light.pixoo_living_room
```

## Error Handling

All services follow HA error handling conventions:

### Service Call Errors

| Error Type | Condition | User Message |
|------------|-----------|--------------|
| `ServiceValidationError` | Invalid parameters | "Invalid parameter: {param}" |
| `HomeAssistantError` | Device unreachable | "Failed to communicate with device" |
| `ValueError` | Business logic error | "Image exceeds 10MB limit" |
| `TimeoutError` | Operation timeout | "Operation timed out after {timeout}s" |

### Error Response Format

```python
try:
    await pixoo.display_image_from_url(url)
except aiohttp.ClientError as err:
    raise HomeAssistantError(f"Failed to download image: {err}") from err
except ValueError as err:
    raise ServiceValidationError(str(err)) from err
```

## Service Registration

### Integration Setup

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pixoo from config entry."""
    
    # Register all services
    await _register_services(hass)
    
    return True

async def _register_services(hass: HomeAssistant) -> None:
    """Register Pixoo services."""
    
    # Display services
    hass.services.async_register(
        DOMAIN,
        SERVICE_DISPLAY_IMAGE,
        async_display_image,
        schema=SERVICE_DISPLAY_IMAGE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_DISPLAY_GIF,
        async_display_gif,
        schema=SERVICE_DISPLAY_GIF_SCHEMA,
    )
    
    # ... register other services
```

## Testing Checklist

### Service Testing Strategy

Each service requires:

- [ ] Unit test for parameter validation
- [ ] Unit test for successful execution
- [ ] Unit test for error conditions (network, timeout, invalid params)
- [ ] Integration test with mock PixooAsync
- [ ] Manual test with real device

### Example Test

```python
async def test_display_image_service(hass, mock_pixoo, config_entry):
    """Test display_image service call."""
    
    # Setup
    await async_setup_entry(hass, config_entry)
    
    # Call service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISPLAY_IMAGE,
        {
            ATTR_ENTITY_ID: "light.pixoo_test",
            ATTR_URL: "http://example.com/test.jpg",
            ATTR_MAX_SIZE_MB: 5,
        },
        blocking=True,
    )
    
    # Verify
    mock_pixoo.display_image_from_bytes.assert_called_once()
```

## Documentation Requirements

Each service contract must include:

1. **Description**: Clear explanation of what the service does
2. **Parameters**: Table with type, required/optional, validation rules
3. **Voluptuous Schema**: Python schema definition
4. **Service YAML**: HA service definition with selectors
5. **Implementation**: Reference implementation code
6. **Examples**: YAML examples for common use cases
7. **Error Handling**: Expected errors and messages

## Contract Status

| Category | Status | File | Progress |
|----------|--------|------|----------|
| Display | ✅ Complete | `display-services.md` | 4/4 services |
| Drawing | 🔄 Pending | `drawing-services.md` | 0/7 services |
| Tool | 🔄 Pending | `tool-services.md` | 0/6 services |
| Configuration | 🔄 Pending | `config-services.md` | 0/4 services |
| Animation | 🔄 Pending | `animation-services.md` | 0/4 services |

**Total Progress**: 4/25 services (16%)

---

**Index Version**: 1.0  
**Last Updated**: 2025-11-10  
**Next**: Complete remaining service contract definitions
