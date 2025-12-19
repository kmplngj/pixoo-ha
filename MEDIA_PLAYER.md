# Pixoo Media Player Integration

The Pixoo Media Player entity provides a complete image gallery and slideshow system for your Divoom Pixoo device.

## Features

- ✅ Display single images or animated GIFs
- ✅ Create playlists from folders or custom lists
- ✅ Playback controls (play, pause, stop, next, previous)
- ✅ Shuffle and repeat modes
- ✅ Auto-advance with configurable durations
- ✅ Browse media through Home Assistant's media browser
- ✅ Support for local files and external URLs

## Entity

**Entity ID**: `media_player.pixoo_gallery`

### Supported Features

- **Play**: Resume slideshow playback
- **Pause**: Pause slideshow (keeps current image)
- **Stop**: Stop slideshow and clear display
- **Next Track**: Display next image in playlist
- **Previous Track**: Display previous image
- **Shuffle**: Randomize playlist order
- **Repeat**: Loop playlist infinitely
- **Play Media**: Load and play images/playlists
- **Browse Media**: Browse media through HA's media browser

### States

- **IDLE**: No playlist loaded or single image displayed
- **PLAYING**: Slideshow actively playing with auto-advance
- **PAUSED**: Slideshow paused on current image

## Services

### 1. Load Image

Display a single image on the Pixoo device.

**Service**: `pixoo.load_image`

```yaml
service: pixoo.load_image
target:
  entity_id: media_player.pixoo_gallery
data:
  url: "https://example.com/image.jpg"
  duration: 0  # 0 = no auto-advance
```

**Parameters**:
- `url` (required): Image URL (http://, https://, file://, media-source://)
- `duration` (optional, default: 0): Display duration in seconds (0 = stay on screen)

**Examples**:

```yaml
# Display static image
service: pixoo.load_image
target:
  entity_id: media_player.pixoo_gallery
data:
  url: "/config/www/my-image.jpg"
  duration: 0

# Display image for 30 seconds then clear
service: pixoo.load_image
target:
  entity_id: media_player.pixoo_gallery
data:
  url: "https://picsum.photos/64/64"
  duration: 30

# Display from media library
service: pixoo.load_image
target:
  entity_id: media_player.pixoo_gallery
data:
  url: "media-source://media_source/local/my-photo.jpg"
  duration: 0
```

### 2. Load Folder

Load all images from a folder as a slideshow playlist.

**Service**: `pixoo.load_folder`

```yaml
service: pixoo.load_folder
target:
  entity_id: media_player.pixoo_gallery
data:
  path: "media-source://media_source/local/images"
  duration: 10  # seconds per image
  shuffle: false
```

**Parameters**:
- `path` (required): Folder path (media-source:// protocol)
- `duration` (optional, default: 10): Display duration per image in seconds
- `shuffle` (optional, default: false): Randomize image order

**Examples**:

```yaml
# Load folder as slideshow
service: pixoo.load_folder
target:
  entity_id: media_player.pixoo_gallery
data:
  path: "media-source://media_source/local/vacation-photos"
  duration: 15
  shuffle: true

# Birthday slideshow
service: pixoo.load_folder
target:
  entity_id: media_player.pixoo_gallery
data:
  path: "media-source://media_source/local/birthday-2024"
  duration: 8
  shuffle: false
```

### 3. Load Playlist

Load a custom playlist with individual image URLs and durations.

**Service**: `pixoo.load_playlist`

```yaml
service: pixoo.load_playlist
target:
  entity_id: media_player.pixoo_gallery
data:
  items:
    - url: "https://example.com/img1.jpg"
      duration: 10
    - url: "https://example.com/img2.jpg"
      duration: 5
  shuffle: false
```

**Parameters**:
- `items` (required): List of `{url, duration}` objects
- `shuffle` (optional, default: false): Randomize playlist order

**Examples**:

```yaml
# Weather dashboard playlist
service: pixoo.load_playlist
target:
  entity_id: media_player.pixoo_gallery
data:
  items:
    - url: "https://weather.com/forecast.jpg"
      duration: 15
    - url: "https://weather.com/radar.jpg"
      duration: 10
    - url: "https://weather.com/satellite.jpg"
      duration: 10
  shuffle: false

# News headlines rotation
service: pixoo.load_playlist
target:
  entity_id: media_player.pixoo_gallery
data:
  items:
    - url: "{{ state_attr('sensor.news_headline_1', 'image') }}"
      duration: 20
    - url: "{{ state_attr('sensor.news_headline_2', 'image') }}"
      duration: 20
  shuffle: false
```

### 4. Standard Media Player Services

All standard Home Assistant media player services are supported:

```yaml
# Play/resume slideshow
service: media_player.media_play
target:
  entity_id: media_player.pixoo_gallery

# Pause slideshow
service: media_player.media_pause
target:
  entity_id: media_player.pixoo_gallery

# Stop and clear
service: media_player.media_stop
target:
  entity_id: media_player.pixoo_gallery

# Next image
service: media_player.media_next_track
target:
  entity_id: media_player.pixoo_gallery

# Previous image
service: media_player.media_previous_track
target:
  entity_id: media_player.pixoo_gallery

# Enable shuffle
service: media_player.shuffle_set
target:
  entity_id: media_player.pixoo_gallery
data:
  shuffle: true

# Enable repeat
service: media_player.repeat_set
target:
  entity_id: media_player.pixoo_gallery
data:
  repeat: "all"  # or "off"
```

## Automation Examples

### Doorbell Camera Snapshot

Display camera snapshot when doorbell is pressed:

```yaml
automation:
  - alias: "Doorbell - Show on Pixoo"
    trigger:
      - platform: state
        entity_id: binary_sensor.doorbell
        to: "on"
    action:
      - service: pixoo.load_image
        target:
          entity_id: media_player.pixoo_gallery
        data:
          url: "{{ state_attr('camera.front_door', 'entity_picture') }}"
          duration: 30
```

### Daily Photo Slideshow

Start slideshow at 9 AM:

```yaml
automation:
  - alias: "Morning Photo Slideshow"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: pixoo.load_folder
        target:
          entity_id: media_player.pixoo_gallery
        data:
          path: "media-source://media_source/local/family-photos"
          duration: 12
          shuffle: true
      - service: media_player.media_play
        target:
          entity_id: media_player.pixoo_gallery
```

### Weather Display Rotation

Show weather forecast and radar:

```yaml
automation:
  - alias: "Weather Dashboard"
    trigger:
      - platform: time_pattern
        minutes: "/30"  # Every 30 minutes
    action:
      - service: pixoo.load_playlist
        target:
          entity_id: media_player.pixoo_gallery
        data:
          items:
            - url: "{{ state_attr('weather.home', 'entity_picture') }}"
              duration: 20
            - url: "https://radar.weather.gov/ridge/standard/CONUS_loop.gif"
              duration: 15
```

### Birthday Animation

Show birthday message and photos:

```yaml
automation:
  - alias: "Birthday Surprise"
    trigger:
      - platform: time
        at: "00:00:01"
    condition:
      - condition: template
        value_template: "{{ now().month == 6 and now().day == 15 }}"
    action:
      - service: pixoo.display_text
        target:
          entity_id: light.pixoo
        data:
          text: "🎉 Happy Birthday! 🎂"
          color: "#FF69B4"
      - delay:
          seconds: 5
      - service: pixoo.load_folder
        target:
          entity_id: media_player.pixoo_gallery
        data:
          path: "media-source://media_source/local/birthday-memories"
          duration: 10
          shuffle: true
```

### Album Art Display

Display currently playing music album art:

```yaml
automation:
  - alias: "Show Album Art"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    condition:
      - condition: state
        entity_id: media_player.spotify
        state: "playing"
    action:
      - service: pixoo.load_image
        target:
          entity_id: media_player.pixoo_gallery
        data:
          url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          duration: 0
```

### Random Image on Motion

Show random image when motion detected:

```yaml
automation:
  - alias: "Motion - Random Image"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_sensor
        to: "on"
    action:
      - service: pixoo.load_image
        target:
          entity_id: media_player.pixoo_gallery
        data:
          url: "https://picsum.photos/64/64?random={{ now().timestamp() | int }}"
          duration: 60
```

## Tips & Best Practices

### Image Recommendations

- **Resolution**: Images are automatically scaled to 64x64 (or 16x16, 32x32 depending on device)
- **Format**: Supports JPG, PNG, GIF
- **Size**: Keep images under 10MB for faster loading
- **URLs**: Use HTTPS for external images

### Slideshow Performance

- **Duration**: Recommended 5-30 seconds per image
- **Playlist Size**: Works well with 10-50 images
- **Auto-advance**: Images with `duration: 0` won't auto-advance

### Media Browser Integration

The media player integrates with Home Assistant's media browser:

1. Open Home Assistant UI
2. Navigate to Media Browser
3. Browse your media folders
4. Click on an image to display it on Pixoo

### Shuffle & Repeat

- **Shuffle ON**: Images play in random order
- **Shuffle OFF**: Images play sequentially
- **Repeat ON**: Playlist loops infinitely
- **Repeat OFF**: Stops at end of playlist

### State Management

- Single images (duration=0): State = IDLE
- Slideshows (duration>0): State = PLAYING
- Manual pause: State = PAUSED
- After stop: State = IDLE, display cleared

## Troubleshooting

### Images not displaying

- Check URL is accessible from Home Assistant
- Verify image format (JPG, PNG, GIF)
- Check Home Assistant logs for download errors
- Ensure device is online and responsive

### Slideshow not auto-advancing

- Check duration > 0 for auto-advance
- Verify state is PLAYING (not PAUSED)
- Check repeat mode if stuck at end

### Media browser not working

- Ensure `media_source` integration is enabled
- Check media folder permissions
- Verify path uses `media-source://` protocol

## Advanced Usage

### Dynamic Playlists with Templates

```yaml
service: pixoo.load_playlist
target:
  entity_id: media_player.pixoo_gallery
data:
  items: >
    {% set images = namespace(list=[]) %}
    {% for i in range(1, 6) %}
      {% set images.list = images.list + [
        {
          'url': 'https://example.com/image' ~ i ~ '.jpg',
          'duration': 10
        }
      ] %}
    {% endfor %}
    {{ images.list }}
```

### Conditional Folder Loading

```yaml
service: pixoo.load_folder
target:
  entity_id: media_player.pixoo_gallery
data:
  path: >
    {% if is_state('sun.sun', 'above_horizon') %}
      media-source://media_source/local/daytime-photos
    {% else %}
      media-source://media_source/local/nighttime-photos
    {% endif %}
  duration: 15
  shuffle: true
```

### Playlist from Sensor Data

```yaml
service: pixoo.load_playlist
target:
  entity_id: media_player.pixoo_gallery
data:
  items: "{{ state_attr('sensor.photo_gallery', 'images') }}"
  shuffle: false
```

## See Also

- [Main Integration Documentation](README.md)
- [Service Definitions](services.yaml)
- [Home Assistant Media Player](https://www.home-assistant.io/integrations/media_player/)
- [Media Source Integration](https://www.home-assistant.io/integrations/media_source/)
