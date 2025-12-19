# Pixoo Media Player - Quick Reference

## Services

| Service | Purpose | Required Parameters | Optional Parameters |
|---------|---------|---------------------|---------------------|
| `pixoo.load_image` | Display single image | `url` | `duration` (default: 0) |
| `pixoo.load_folder` | Load folder as playlist | `path` | `duration` (default: 10), `shuffle` (default: false) |
| `pixoo.load_playlist` | Load custom playlist | `items` | `shuffle` (default: false) |
| `media_player.media_play` | Resume/start slideshow | - | - |
| `media_player.media_pause` | Pause slideshow | - | - |
| `media_player.media_stop` | Stop and clear | - | - |
| `media_player.media_next_track` | Next image | - | - |
| `media_player.media_previous_track` | Previous image | - | - |
| `media_player.shuffle_set` | Toggle shuffle | `shuffle` | - |
| `media_player.repeat_set` | Toggle repeat | `repeat` | - |

## Entity States

| State | Description |
|-------|-------------|
| `IDLE` | No playlist or single image (no auto-advance) |
| `PLAYING` | Slideshow active with auto-advance |
| `PAUSED` | Slideshow paused on current image |

## Quick Examples

### Single Image
```yaml
service: pixoo.load_image
data:
  url: "https://example.com/image.jpg"
  duration: 0  # No auto-advance
```

### Folder Slideshow
```yaml
service: pixoo.load_folder
data:
  path: "media-source://media_source/local/photos"
  duration: 10
  shuffle: true
```

### Custom Playlist
```yaml
service: pixoo.load_playlist
data:
  items:
    - url: "https://example.com/img1.jpg"
      duration: 15
    - url: "https://example.com/img2.jpg"
      duration: 10
```

### Playback Controls
```yaml
# Play
service: media_player.media_play
# Pause
service: media_player.media_pause
# Stop
service: media_player.media_stop
# Next
service: media_player.media_next_track
# Previous
service: media_player.media_previous_track
```

## URL Formats

| Format | Example | Use Case |
|--------|---------|----------|
| `https://` | `https://example.com/img.jpg` | External images |
| `http://` | `http://192.168.1.100/img.jpg` | Local network images |
| `file://` | `file:///config/www/img.jpg` | Local filesystem |
| `media-source://` | `media-source://media_source/local/photo.jpg` | HA media library |

## Automation Patterns

### On Event
```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.doorbell
    to: "on"
action:
  - service: pixoo.load_image
    data:
      url: "{{ state_attr('camera.front', 'entity_picture') }}"
      duration: 30
```

### Scheduled
```yaml
trigger:
  - platform: time
    at: "09:00:00"
action:
  - service: pixoo.load_folder
    data:
      path: "media-source://media_source/local/morning"
      duration: 15
      shuffle: true
```

### Conditional
```yaml
action:
  - service: pixoo.load_folder
    data:
      path: >
        {% if is_state('sun.sun', 'above_horizon') %}
          media-source://media_source/local/day
        {% else %}
          media-source://media_source/local/night
        {% endif %}
```

## Common Tasks

| Task | Service | Data |
|------|---------|------|
| Show image for 30s | `load_image` | `url`, `duration: 30` |
| Show image until stopped | `load_image` | `url`, `duration: 0` |
| Folder slideshow | `load_folder` | `path`, `duration: 10` |
| Random folder order | `load_folder` | `path`, `shuffle: true` |
| Loop playlist | `load_playlist` + `repeat_set` | `items`, `repeat: "all"` |
| Manual image navigation | `media_next_track` / `media_previous_track` | - |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Image not showing | Check URL accessibility, format (JPG/PNG/GIF), size (<10MB) |
| No auto-advance | Verify `duration > 0` and state is `PLAYING` |
| Slideshow won't start | Check playlist has items, call `media_player.media_play` |
| Stuck at end | Enable repeat mode with `repeat_set` |
| Media browser empty | Verify `media_source` integration enabled |

## Performance Tips

- **Image Size**: Keep under 10MB for fast loading
- **Duration**: 5-30 seconds recommended per image
- **Playlist Size**: 10-50 images works well
- **Resolution**: Auto-scales to 64x64 (or device size)
- **Format**: JPG recommended for photos, PNG for graphics

## Integration Points

- **Cameras**: Display camera snapshots
- **Music Players**: Show album art
- **Weather**: Display forecast images
- **Notifications**: Visual alerts
- **Media Library**: Browse and display media
- **Automations**: Trigger on any HA event

## Developer Notes

- Entity ID: `media_player.pixoo_gallery`
- Domain: `media_player`
- Platform: `custom_components/pixoo/media_player.py`
- Services registered via: `entity_platform.async_register_entity_service()`
- Image download: Uses `utils.download_image()` (10MB limit, 30s timeout)
- Scheduler: `asyncio.TimerHandle` for auto-advance

## See Full Documentation

- [Complete Media Player Guide](MEDIA_PLAYER.md)
- [Implementation Details](MEDIA_PLAYER_IMPLEMENTATION.md)
- [Service Definitions](custom_components/pixoo/services.yaml)
