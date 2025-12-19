# Media Player Service Contracts

**Date**: 2025-11-10  
**Feature**: Image Gallery & Slideshow  
**Platform**: Media Player

## Overview

The media player platform uses standard Home Assistant media player services but with custom implementation for image playlist management and slideshow functionality.

## Standard Media Player Services

### play_media

**Service**: `media_player.play_media`

**Description**: Display a single image or start an image slideshow from a playlist.

**Parameters**:

```yaml
service: media_player.play_media
target:
  entity_id: media_player.pixoo_bedroom
data:
  media_content_type: string  # Required: "image", "url", or "playlist"
  media_content_id: string    # Required: image URL or playlist JSON
```

**Voluptuous Schema**:

```python
import voluptuous as vol
from homeassistant.components.media_player import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    SERVICE_PLAY_MEDIA,
)

PLAY_MEDIA_SCHEMA = vol.Schema({
    vol.Required(ATTR_MEDIA_CONTENT_TYPE): vol.In(["image", "url", "playlist"]),
    vol.Required(ATTR_MEDIA_CONTENT_ID): str,
})
```

**Media Content Types**:

#### Single Image (image/url)

```yaml
# Local image via media source
media_content_type: image
media_content_id: "media-source://media_source/local/photos/family.jpg"

# External URL
media_content_type: url
media_content_id: "https://picsum.photos/64"
```

**Behavior**:
- Displays single image immediately
- State becomes `IDLE` (no auto-advance)
- Playlist contains 1 item with duration=0

#### Playlist (playlist)

```yaml
# Playlist JSON format
media_content_type: playlist
media_content_id: >
  [
    {"url": "media-source://media_source/local/photos/photo1.jpg", "duration": 30},
    {"url": "https://example.com/photo2.jpg", "duration": 15},
    {"url": "media-source://media_source/local/photos/photo3.jpg", "duration": 45}
  ]
```

**Playlist Item Schema**:

```python
PLAYLIST_ITEM_SCHEMA = vol.Schema({
    vol.Required("url"): str,  # media-source:// or http(s)://
    vol.Optional("duration", default=10): vol.All(
        vol.Coerce(int),
        vol.Range(min=1, max=3600)
    ),
})

PLAYLIST_SCHEMA = vol.Schema([PLAYLIST_ITEM_SCHEMA])
```

**Behavior**:
- Parses JSON array of playlist items
- Validates each URL (media-source:// or http(s)://)
- State becomes `PLAYING`
- Auto-advances after each item's duration
- Respects shuffle and repeat settings

**Validation**:

```python
async def async_play_media(self, media_type: str, media_id: str) -> None:
    """Play media content."""
    if media_type == "playlist":
        # Parse and validate playlist
        try:
            playlist_data = json.loads(media_id)
            playlist_items = PLAYLIST_SCHEMA(playlist_data)
        except (json.JSONDecodeError, vol.Invalid) as err:
            raise ServiceValidationError(f"Invalid playlist format: {err}")
        
        # Validate URLs
        for item in playlist_items:
            url = item["url"]
            if not (url.startswith("media-source://") or url.startswith(("http://", "https://"))):
                raise ServiceValidationError(f"Invalid URL format: {url}")
        
        # Load playlist
        self._playlist = [PixooPlaylistItem(**item) for item in playlist_items]
        self._position = 0
        self._state = MediaPlayerState.PLAYING
        
        # Apply shuffle if enabled
        if self._shuffle:
            self._shuffle_order = list(range(len(self._playlist)))
            random.shuffle(self._shuffle_order)
        
        # Display first image
        await self._display_current_image()
        self._schedule_next()
        
    elif media_type in ["image", "url"]:
        # Single image
        self._playlist = [PixooPlaylistItem(url=media_id, duration=0)]
        self._position = 0
        self._state = MediaPlayerState.IDLE
        await self._display_current_image()
    
    else:
        raise ServiceValidationError(f"Unsupported media type: {media_type}")
    
    self.async_write_ha_state()
```

**Error Handling**:

- Invalid JSON: `ServiceValidationError("Invalid playlist format")`
- Invalid URL scheme: `ServiceValidationError("Invalid URL format")`
- Download failure: `HomeAssistantError("Failed to download image")`
- Media source error: `HomeAssistantError("Failed to resolve media source")`
- Image too large: `ServiceValidationError("Image exceeds 10MB limit")`

### media_play

**Service**: `media_player.media_play`

**Description**: Resume paused slideshow.

**Parameters**: None (uses entity_id from target)

**Behavior**:
- Changes state from `PAUSED` to `PLAYING`
- Resumes auto-advance timer from current position
- No effect if already playing or no playlist loaded

### media_pause

**Service**: `media_player.media_pause`

**Description**: Pause slideshow (keeps current image).

**Parameters**: None

**Behavior**:
- Changes state from `PLAYING` to `PAUSED`
- Cancels auto-advance timer
- Current image remains on display
- Position preserved

### media_stop

**Service**: `media_player.media_stop`

**Description**: Stop slideshow and clear display.

**Parameters**: None

**Behavior**:
- Changes state to `IDLE`
- Cancels auto-advance timer
- Clears playlist
- Calls `pixoo.clear_display()` to blank screen

### media_next_track

**Service**: `media_player.media_next_track`

**Description**: Display next image in playlist.

**Parameters**: None

**Behavior**:
- Advances position by 1 (wraps to 0 if at end)
- Respects shuffle order if enabled
- Displays new image immediately
- Restarts auto-advance timer if playing
- No effect if playlist empty

**Shuffle Logic**:

```python
if self._shuffle:
    # Find current position in shuffle order
    current_index = self._shuffle_order.index(self._position)
    # Get next index (wrap around)
    next_index = (current_index + 1) % len(self._shuffle_order)
    self._position = self._shuffle_order[next_index]
else:
    # Sequential order
    self._position = (self._position + 1) % len(self._playlist)
```

### media_previous_track

**Service**: `media_player.media_previous_track`

**Description**: Display previous image in playlist.

**Parameters**: None

**Behavior**:
- Decreases position by 1 (wraps to end if at start)
- Respects shuffle order if enabled
- Displays new image immediately
- Restarts auto-advance timer if playing

### shuffle_set

**Service**: `media_player.shuffle_set`

**Description**: Enable or disable shuffle mode.

**Parameters**:

```yaml
service: media_player.shuffle_set
target:
  entity_id: media_player.pixoo_bedroom
data:
  shuffle: true  # or false
```

**Behavior**:
- Updates `_shuffle` attribute
- If enabling shuffle, generates new shuffle order
- If disabling shuffle, clears shuffle order
- Does not change current position
- Affects future next/previous navigation

**Shuffle Order Generation**:

```python
if shuffle and not self._shuffle_order:
    self._shuffle_order = list(range(len(self._playlist)))
    random.shuffle(self._shuffle_order)
elif not shuffle:
    self._shuffle_order = None
```

### repeat_set

**Service**: `media_player.repeat_set`

**Description**: Enable or disable repeat mode.

**Parameters**:

```yaml
service: media_player.repeat_set
target:
  entity_id: media_player.pixoo_bedroom
data:
  repeat: all  # or "off"
```

**Voluptuous Schema**:

```python
REPEAT_SET_SCHEMA = vol.Schema({
    vol.Required("repeat"): vol.In(["off", "all"]),
})
```

**Behavior**:
- Updates `_repeat` attribute (True for "all", False for "off")
- When enabled, playlist loops infinitely
- When disabled, playlist stops at end
- Does not affect current playback position

## Implementation Notes

### Media Source Resolution

Local images use Home Assistant's media_source integration:

```python
from homeassistant.components import media_source

async def _display_current_image(self):
    """Display current playlist image."""
    item = self._playlist[self._position]
    
    if item.url.startswith("media-source://"):
        # Resolve media source to accessible URL
        resolved = await media_source.async_resolve_media(
            self.hass,
            item.url,
            None  # target entity
        )
        url = resolved.url
    else:
        # External URL - use directly
        url = item.url
    
    # Download and display
    image_data = await download_image(self.hass, url)
    await self.coordinator.pixoo.display_image_from_bytes(image_data)
    
    self._media_image_url = url
    self.async_write_ha_state()
```

### Playlist State Management

State tracked internally (not in coordinator):

```python
@dataclass
class PixooMediaPlayerState:
    """Internal playlist state."""
    playlist: list[PixooPlaylistItem]
    position: int = 0
    shuffle: bool = False
    repeat: bool = False
    state: MediaPlayerState = MediaPlayerState.IDLE
    shuffle_order: list[int] | None = None
    timer_handle: asyncio.TimerHandle | None = None
```

### Auto-Advance Timer

```python
def _schedule_next(self):
    """Schedule automatic advance to next image."""
    if self._timer_handle:
        self._timer_handle.cancel()
    
    item = self._playlist[self._position]
    self._timer_handle = self.hass.loop.call_later(
        item.duration,
        lambda: asyncio.create_task(self._auto_advance())
    )

async def _auto_advance(self):
    """Automatically advance to next image."""
    if self._state != MediaPlayerState.PLAYING:
        return
    
    # Check if at end
    is_last = self._is_last_item()
    
    if is_last and not self._repeat:
        # Stop at end of playlist
        self._state = MediaPlayerState.IDLE
        self.async_write_ha_state()
        return
    
    # Continue to next
    await self.async_media_next_track()

def _is_last_item(self) -> bool:
    """Check if current item is last in playlist."""
    if self._shuffle:
        current_index = self._shuffle_order.index(self._position)
        return current_index == len(self._shuffle_order) - 1
    else:
        return self._position == len(self._playlist) - 1
```

### Image Download & Display

Reuse existing image download utility:

```python
from .utils import download_image

async def _display_current_image(self):
    """Display current playlist image."""
    item = self._playlist[self._position]
    
    # Resolve URL (media source or direct)
    if item.url.startswith("media-source://"):
        resolved = await media_source.async_resolve_media(self.hass, item.url)
        url = resolved.url
    else:
        url = item.url
    
    try:
        # Download with validation (10MB limit, 30s timeout)
        image_data = await download_image(self.hass, url)
        
        # Display on device
        await self.coordinator.pixoo.display_image_from_bytes(image_data)
        
        # Update state
        self._media_image_url = url
        self.async_write_ha_state()
        
    except Exception as err:
        _LOGGER.error("Failed to display image %s: %s", url, err)
        raise HomeAssistantError(f"Failed to display image: {err}")
```

## Testing Checklist

- [ ] Single image (media-source://) displays correctly
- [ ] Single image (https://) displays correctly
- [ ] Playlist with 3+ items auto-advances
- [ ] Playlist respects custom duration per item
- [ ] Shuffle mode randomizes order correctly
- [ ] Repeat mode loops playlist infinitely
- [ ] Pause/resume maintains position
- [ ] Stop clears display
- [ ] Next/previous navigation works in sequential mode
- [ ] Next/previous navigation works in shuffle mode
- [ ] Invalid JSON raises ServiceValidationError
- [ ] Invalid URL scheme raises ServiceValidationError
- [ ] Mixed media-source + https playlist works
- [ ] Image download timeout (>30s) raises error
- [ ] Image too large (>10MB) raises error
- [ ] Media source resolution failure handled

## Example Automations

### Morning Photo Frame

```yaml
automation:
  - alias: "Morning Family Photos"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.pixoo_bedroom
        data:
          media_content_type: playlist
          media_content_id: >
            [
              {"url": "media-source://media_source/local/family/photo1.jpg", "duration": 30},
              {"url": "media-source://media_source/local/family/photo2.jpg", "duration": 30},
              {"url": "media-source://media_source/local/family/photo3.jpg", "duration": 30}
            ]
      - service: media_player.shuffle_set
        target:
          entity_id: media_player.pixoo_bedroom
        data:
          shuffle: true
      - service: media_player.repeat_set
        target:
          entity_id: media_player.pixoo_bedroom
        data:
          repeat: all
```

### Rotating Art Gallery

```yaml
automation:
  - alias: "Art Gallery Mode"
    trigger:
      - platform: state
        entity_id: input_boolean.art_mode
        to: "on"
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.pixoo_living_room
        data:
          media_content_type: playlist
          media_content_id: >
            [
              {"url": "https://museum.example.com/art1.jpg", "duration": 60},
              {"url": "https://museum.example.com/art2.jpg", "duration": 60},
              {"url": "media-source://media_source/local/art/painting.jpg", "duration": 90}
            ]
```

---

**Status**: ✅ Complete  
**Implementation**: `custom_components/pixoo/media_player.py`  
**Tests**: `tests/test_media_player.py`
