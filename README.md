# Pixoo Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

Modern Home Assistant integration for **Divoom Pixoo** LED displays (Pixoo 16, Pixoo 64, Pixoo Max, Timebox Evo). Display images, animated GIFs, scrolling text, and more on your Pixoo device directly from Home Assistant.

## ✨ What Can You Do?

Transform your Pixoo into a powerful smart display:

- 🎵 **Media Player Display** - Show album art and track info from Spotify, Apple Music, etc.
- 📸 **Photo Frame** - Display photo slideshows with shuffle and repeat
- 🔔 **Smart Notifications** - Washing machine done, doorbell alerts, reminders
- ⏰ **Kitchen Timer** - Visual countdown with buzzer alerts
- 🏀 **Sports Scoreboard** - Track game scores with red/blue teams
- 🌡️ **Weather Display** - Real-time weather conditions
- 🎨 **Custom Animations** - Upload your own pixel art and GIFs
- 📱 **iOS Shortcuts** - Send photos directly from iPhone/iPad

## 🎯 Features

### Device Control
- Power on/off and brightness adjustment (0-100%)
- Channel selection (Clock, Cloud Gallery, Visualizer, Custom)
- Screen rotation (0°, 90°, 180°, 270°)
- Mirror mode (horizontal flip)

### Display Content
- Display images from URLs, media library, or base64-encoded data
- Display animated GIFs with automatic looping
- Display scrolling text with color, speed, and direction control
- Clear display to black

### Image Gallery & Slideshow
- Media player entity for photo frame functionality
- Playlist support with custom duration per image
- Shuffle and repeat modes
- Manual navigation (next/previous image)
- Supports media-source:// URLs and http(s):// URLs

### Tool Modes
- **Timer** - Minutes and seconds control with on/off switch
- **Alarm** - Hour and minute configuration with enable/disable
- **Stopwatch** - Start, stop, and reset functionality
- **Scoreboard** - Red and blue team scores (0-999)
- **Noise Meter** - Microphone visualization

### Clock & Visualizer
- Select from 100+ cloud clock faces
- Select visualizer effects for music playback
- Switch between custom channel pages (1, 2, 3)

### Sensors & Monitoring
- Device info (model, firmware version, MAC address)
- Network status (IP address, Wi-Fi SSID, signal strength)
- System config (brightness, rotation, active channel)
- Weather and time information
- Tool states (timer countdown, alarm time, stopwatch elapsed)

### Drawing Primitives (Advanced)
- Draw pixels, lines, rectangles, and text directly to display
- Buffer management for complex animations
- Batch drawing operations for performance

## Requirements

- Home Assistant 2024.1 or newer
- Divoom Pixoo device (Pixoo 16, Pixoo 64, Pixoo Max, or Timebox Evo)
- Device connected to same network as Home Assistant
- Python 3.12 or newer

## Supported Devices

This integration automatically detects and configures the correct display size for:

- **Pixoo 16** - 16x16 pixel display
- **Pixoo 64** - 64x64 pixel display (most common)
- **Pixoo Max** - 32x32 pixel display

All features work across different device sizes. Images are automatically resized to match your device's resolution.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add repository URL: `https://github.com/YOUR_USERNAME/pixoo-ha`
6. Category: "Integration"
7. Click "Add"
8. Search for "Pixoo" and install

### Manual Installation

1. Copy the `custom_components/pixoo` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

### Automatic Discovery (Recommended)

The integration supports automatic device discovery via the Divoom cloud API:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Pixoo"
4. Choose **Scan for devices** to automatically discover Pixoo devices on your network
5. Select your device from the list
6. Click **Submit**

The integration will automatically detect your device model (Pixoo 16, Pixoo 64, etc.) and configure the correct display size. This ensures images are properly resized for your screen.

### Manual Configuration

If automatic discovery doesn't work:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Pixoo"
4. Choose **Manual setup**
5. Enter the IP address of your Pixoo device
6. Click **Submit**

**Note:** Manual setup attempts to detect the device model from the cloud API. If detection fails, it defaults to 64x64 resolution. You can verify the detected model in the device information page.

## 📋 Available Services

The integration provides 25+ services for controlling your Pixoo device. All services require targeting a light entity (e.g., `light.pixoo_display`).

### Page Engine (Pages, Rotation, Messages)

The Page Engine lets you render structured “pages” (text/rectangles/images) and optionally rotate through a list of pages.

**Getting Started with Page Rotation:**

1. Create a `pixoo_pages.yaml` file in your Home Assistant config directory
2. Configure the integration to use it (Settings → Devices & Services → Pixoo → Configure)
3. Set `pages_yaml_path` to `pixoo_pages.yaml` and enable rotation
4. See [`examples/page_templates/`](examples/page_templates/) for ready-to-use templates

> **Note:** Rotation prefers your YAML pages file when `pages_yaml_path` is configured. If no YAML pages are available, rotation falls back to pages stored in the integration options (if any). There are no built-in default pages.

**Services**:

- `pixoo.render_page`: render a single page (full render: clear/fill → draw → push)
- `pixoo.render_page_by_name`: render a specific named page from your YAML file
- `pixoo.show_message`: temporary override page (last-wins), then resume rotation (if it was running)
- `pixoo.rotation_enable`: enable/disable rotation
- `pixoo.rotation_next`: advance to next active page
- `pixoo.rotation_reload_pages`: reload YAML-defined pages (if configured)
- `pixoo.set_rotation_config`: configure rotation settings (YAML path, duration, allowlist mode)

**Page Types**:

- `components`: Draw text, rectangles, images, progress bars, and graphs at specific positions
- `template`: Jinja2 template that renders to a components page
- `channel`: Switch to a native Pixoo channel (clock, visualizer, cloud, custom)

**Component Types**:

- `text`: Render text with color and alignment
- `rectangle`: Draw filled or outlined rectangles
- `image`: Display images from URL, path, or base64
- `progress_bar`: Horizontal/vertical progress bar with threshold-based coloring
- `graph`: Line/bar/area graph displaying entity history with color thresholds
- `icon`: MDI icon with dynamic size and color (requires `cairosvg` for SVG rendering)

All components support an optional `enabled` field (boolean or Jinja2 template) for conditional visibility.

**Security note**: image `url`/`path` sources are allowlisted by Home Assistant in `allowlist_mode: strict` (default). Use `permissive` only if you understand the risk.

Example: render a page with a text component

```yaml
service: pixoo.render_page
target:
  entity_id: light.pixoo_display
data:
  page:
    page_type: components
    background: "#000000"
    components:
      - type: text
        x: 0
        y: 0
        text: "Hallo!"
        color: "#00FF00"
```

Example: show a message for 10 seconds

```yaml
service: pixoo.show_message
target:
  entity_id: light.pixoo_display
data:
  duration: 10
  page:
    page_type: components
    components:
      - type: text
        x: 0
        y: 0
        text: "Tür offen"
        color: "red"
```

Example: enable rotation (configured via entry options) and skip to next page

```yaml
service: pixoo.rotation_enable
target:
  entity_id: light.pixoo_display
data:
  enabled: true

---

service: pixoo.rotation_next
target:
  entity_id: light.pixoo_display
```

Example: configure rotation with YAML pages file

```yaml
service: pixoo.set_rotation_config
target:
  entity_id: light.pixoo_display
data:
  enabled: true
  default_duration: 10
  pages_yaml_path: "/config/pixoo_pages.yaml"
  allowlist_mode: permissive
```

Example: display native Pixoo clock channel

```yaml
service: pixoo.render_page
target:
  entity_id: light.pixoo_display
data:
  page:
    page_type: channel
    channel_name: clock
    clock_id: 182  # Optional: specific clock face
```

### Progress Bar with Color Thresholds

```yaml
service: pixoo.render_page
target:
  entity_id: light.pixoo_display
data:
  page:
    page_type: components
    background: "#111111"
    components:
      - type: text
        x: 0
        y: 0
        text: "Battery"
      - type: progress_bar
        x: 0
        y: 10
        width: 64
        height: 8
        progress: sensor.battery_soc  # Entity ID or template
        color_thresholds:
          - value: 80
            color: "#00FF00"  # Green above 80%
          - value: 50
            color: "#FFFF00"  # Yellow 50-80%
          - value: 20
            color: "#FF0000"  # Red below 20%
        color_thresholds_transition: smooth  # or "hard" for step changes
```

### MDI Icon with Threshold Coloring

Display Material Design Icons with dynamic colors based on sensor values:

```yaml
service: pixoo.render_page
target:
  entity_id: light.pixoo_display
data:
  page:
    page_type: components
    background: "#000000"
    components:
      - type: icon
        x: 24
        y: 16
        icon: "mdi:battery"  # Or just "battery"
        size: 32  # 8, 16, 24, or 32 pixels
        value: sensor.battery_soc
        color_thresholds:
          - value: 80
            color: green
          - value: 50
            color: yellow
          - value: 20
            color: red
      - type: text
        x: 32
        y: 52
        text: "{{ states('sensor.battery_soc') }}%"
        color: white
        align: center
```

**Note**: Icon rendering requires `cairosvg`. Install with:
```bash
pip install cairosvg
```

### Conditional Component Visibility

Components can be shown/hidden based on entity states using the `enabled` field:

```yaml
service: pixoo.render_page
target:
  entity_id: light.pixoo_display
data:
  page:
    page_type: components
    background: "#000000"
    components:
      # Only show when binary sensor is on
      - type: icon
        x: 0
        y: 0
        icon: mdi:alert
        size: 16
        color: red
        enabled: "{{ is_state('binary_sensor.alarm', 'on') }}"
      
      # Always hidden (useful for testing)
      - type: text
        x: 0
        y: 20
        text: "Debug"
        enabled: false
```

### Display Services

| Service | Description | Parameters |
|---------|-------------|------------|
| `pixoo.display_image` | Display an image from URL or media library | `url` |
| `pixoo.display_image_data` | Display base64-encoded image (perfect for iOS Shortcuts) | `image_data` |
| `pixoo.display_gif` | Display an animated GIF | `url` |
| `pixoo.display_text` | Display scrolling text | `text`, `color`, `x`, `y`, `font`, `speed`, `text_id`, `scroll_direction` |
| `pixoo.clear_display` | Clear display to black | - |

### Tool Services

| Service | Description | Parameters |
|---------|-------------|------------|
| `pixoo.set_timer` | Configure timer | `minutes`, `seconds`, `running` |
| `pixoo.set_alarm` | Configure alarm | `hour`, `minute`, `enabled` |
| `pixoo.play_buzzer` | Play buzzer alert | `active_time`, `off_time`, `total_time` |

### Configuration Services

| Service | Description | Parameters |
|---------|-------------|------------|
| `pixoo.set_white_balance` | Adjust color temperature | `r`, `g`, `b` |

### Animation Services

| Service | Description | Parameters |
|---------|-------------|------------|
| `pixoo.list_animations` | List available cloud animations | - |
| `pixoo.send_playlist` | Send custom animation playlist | `playlist` (JSON) |

### Drawing Services (Advanced)

| Service | Description | Parameters |
|---------|-------------|------------|
| `pixoo.reset_buffer` | Clear drawing buffer | - |
| `pixoo.push_buffer` | Push buffer to display | - |

See [IOS_SHORTCUTS_GUIDE.md](IOS_SHORTCUTS_GUIDE.md) for iOS Shortcuts integration examples.

## 📖 Usage Examples

### Basic Display Control

```yaml
# Turn on device and set brightness to 80%
service: light.turn_on
target:
  entity_id: light.pixoo_display
data:
  brightness: 204  # 0-255 scale (80% = 204)

# Turn off device
service: light.turn_off
target:
  entity_id: light.pixoo_display

# Change to clock channel (using select)
service: select.select_option
target:
  entity_id: select.pixoo_channel
data:
  option: "faces"  # Options: faces, cloud, visualizer, custom

# Change to cloud channel (using button - always works!)
service: button.press
target:
  entity_id: button.pixoo_switch_to_cloud_channel
```

### Display Images & GIFs

```yaml
# Display image from URL
service: pixoo.display_image
target:
  entity_id: light.pixoo_display
data:
  url: "https://example.com/image.jpg"

# Display local media file
service: pixoo.display_image
target:
  entity_id: light.pixoo_display
data:
  url: "media-source://media_source/local/images/birthday.png"

# Display animated GIF
service: pixoo.display_gif
target:
  entity_id: light.pixoo_display
data:
  url: "https://example.com/animation.gif"

# Display image from iOS Shortcuts (base64)
service: pixoo.display_image_data
target:
  entity_id: light.pixoo_display
data:
  image_data: "iVBORw0KGgoAAAANSUhEUgAA..."  # Base64 encoded PNG/JPG
```

### Display Scrolling Text

```yaml
# Display white scrolling text
service: pixoo.display_text
target:
  entity_id: light.pixoo_display
data:
  text: "Hello Home Assistant!"
  color: "#FFFFFF"  # White color
  x: 0
  y: 32  # Vertical position (0-63)
  font: 2  # Font size (1-7)
  speed: 50  # Scroll speed (0-100)
  text_id: 1  # Text layer ID (1-20)
  scroll_direction: "left"  # left, right, up, down

# Display colored text at bottom
service: pixoo.display_text
target:
  entity_id: light.pixoo_display
data:
  text: "Temperature: 22°C"
  color: [255, 0, 0]  # Red (can use RGB list or hex string)
  x: 0
  y: 55
  font: 1
  speed: 0  # Static text (no scrolling)
  text_id: 2
  scroll_direction: "left"
```

### Timer & Alarm

```yaml
# Start 5-minute timer
service: pixoo.set_timer
target:
  entity_id: light.pixoo_display
data:
  minutes: 5
  seconds: 0
  running: true

# Set alarm for 7:30 AM
service: pixoo.set_alarm
target:
  entity_id: light.pixoo_display
data:
  hour: 7
  minute: 30
  enabled: true

# Play buzzer alert (3 beeps)
service: pixoo.play_buzzer
target:
  entity_id: light.pixoo_display
data:
  active_time: 500  # 500ms beep
  off_time: 500     # 500ms silence
  total_time: 3000  # Total 3 seconds (3 beeps)
```

### Media Player Display (Real Automation Example)

This automation displays album art and track info from media players:

```yaml
alias: Display Title Artist and CoverArt on Pixoo
description: Display media player info using native ha-pixoo integration
triggers:
  - entity_id:
      - media_player.kitchen
      - media_player.receiver
      - media_player.appletv
    attribute: entity_picture
    for:
      seconds: 3
    trigger: state
  - entity_id:
      - media_player.kitchen
      - media_player.receiver
      - media_player.appletv
    attribute: media_title
    for:
      seconds: 3
    trigger: state
conditions:
  - condition: template
    value_template: >-
      {{ trigger.entity_id in ['media_player.kitchen', 'media_player.receiver',
      'media_player.appletv'] and state_attr(trigger.entity_id, 'source') != 'HDMI ARC' }}
actions:
  # Clear display first
  - action: pixoo.clear_display
    target:
      entity_id: light.pixoo_display
  
  # Display album art if available
  - condition: template
    value_template: '{{ state_attr(trigger.entity_id, "entity_picture") is not none }}'
  - action: pixoo.display_image
    data:
      url: >-
        http://homeassistant.local:8123{{ state_attr(trigger.entity_id, "entity_picture") }}
    target:
      entity_id: light.pixoo_display
  
  # Wait 1 second
  - delay:
      seconds: 1
  
  # Display scrolling artist and title
  - action: pixoo.display_text
    data:
      text: >-
        {{ state_attr(trigger.entity_id, "media_artist") }}   {{ state_attr(trigger.entity_id, "media_title") }}
      color: "#FFFFFF"
      x: 0
      y: 48
      font: 2
      speed: 60
      text_id: 1
      scroll_direction: left
    target:
      entity_id: light.pixoo_display
mode: single
```

### Channel Switching

**Important**: Use button entities for reliable channel switching, especially when returning to a channel that's already selected:

```yaml
# Switch to Cloud Gallery (button - always works!)
service: button.press
target:
  entity_id: button.pixoo_switch_to_cloud_channel

# Switch to Clock Faces (button)
service: button.press
target:
  entity_id: button.pixoo_switch_to_clock_channel

# Switch to Visualizer (button)
service: button.press
target:
  entity_id: button.pixoo_switch_to_visualizer_channel

# Switch to Custom (button)
service: button.press
target:
  entity_id: button.pixoo_switch_to_custom_channel

# Alternative: Use select (doesn't work if already on that channel)
service: select.select_option
target:
  entity_id: select.pixoo_channel
data:
  option: "cloud"
```

**Why use buttons instead of select?**
- ✅ **Always triggers** - Even when channel is already selected
- ✅ **Escapes overlays** - Returns from stopwatch/timer/alarm back to channel
- ✅ **Automation-friendly** - Guaranteed to restore your display state
- ✅ **No conditional logic** - Just press and it works

### Display Text Messages

```yaml
# Display scrolling text
service: pixoo.display_text
target:
  entity_id: light.pixoo_living_room
data:
  text: "Hello World!"
  color: "#FF0000"
  scroll_direction: "left"

# Multi-line positioned text
service: pixoo.display_text
target:
  entity_id: light.pixoo_living_room
data:
  text: "Line 1\nLine 2\nLine 3"
  x: 10
  y: 20
  color: "#00FF00"
```

### Image Gallery Slideshow

```yaml
# Play slideshow with 3 images (10 seconds each)
service: media_player.play_media
target:
  entity_id: media_player.pixoo_living_room
data:
  media_content_type: playlist
  media_content_id: >
    [
      {"url": "https://example.com/img1.jpg", "duration": 10},
      {"url": "https://example.com/img2.jpg", "duration": 15},
      {"url": "media-source://media_source/local/img3.png", "duration": 8}
    ]

# Enable shuffle
service: media_player.shuffle_set
target:
  entity_id: media_player.pixoo_living_room
data:
  shuffle: true

# Enable repeat (loop playlist)
service: media_player.repeat_set
target:
  entity_id: media_player.pixoo_living_room
data:
  repeat: all
```

### Notification with Buzzer

```yaml
# Play buzzer alert (3 cycles, 500ms on, 200ms off)
service: pixoo.play_buzzer
target:
  entity_id: light.pixoo_living_room
data:
  active_ms: 500
  off_ms: 200
  count: 3

# Dismiss notification (restore previous display)
service: button.press
target:
  entity_id: button.pixoo_living_room_dismiss_notification
```

### Tool Modes

```yaml
# Set 5-minute timer
service: number.set_value
target:
  entity_id: number.pixoo_living_room_timer_minutes
data:
  value: 5

service: switch.turn_on
target:
  entity_id: switch.pixoo_living_room_timer

# Set alarm for 7:30 AM
service: number.set_value
target:
  entity_id: number.pixoo_living_room_alarm_hour
data:
  value: 7

service: number.set_value
target:
  entity_id: number.pixoo_living_room_alarm_minute
data:
  value: 30

service: switch.turn_on
target:
  entity_id: switch.pixoo_living_room_alarm
```

### Automation Examples

#### Washing Machine Alert

```yaml
automation:
  - alias: "Washing Machine Done"
    trigger:
      - platform: state
        entity_id: binary_sensor.washing_machine_door
        from: "on"
        to: "off"
    action:
      - service: pixoo.display_text
        target:
          entity_id: light.pixoo_kitchen
        data:
          text: "Washing Done!"
          color: "#00FF00"
      - service: pixoo.play_buzzer
        target:
          entity_id: light.pixoo_kitchen
        data:
          count: 5
```

#### Birthday Reminder

```yaml
automation:
  - alias: "Birthday Reminder"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: template
        value_template: >
          {{ now().month == 6 and now().day == 15 }}
    action:
      - service: pixoo.display_image
        target:
          entity_id: light.pixoo_living_room
        data:
          url: "media-source://media_source/local/birthday_cake.gif"
```

#### Doorbell Integration

```yaml
automation:
  - alias: "Doorbell Pressed"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_button
        to: "on"
    action:
      - service: pixoo.display_text
        target:
          entity_id: light.pixoo_hallway
        data:
          text: "Someone at the door!"
          color: "#FF0000"
      - service: pixoo.play_buzzer
        target:
          entity_id: light.pixoo_hallway
        data:
          count: 3
```

## Entity Reference

### Platforms

| Platform | Entities | Description |
|----------|----------|-------------|
| **Light** | 1 | Power control and brightness |
| **Media Player** | 1 | Image gallery/slideshow |
| **Number** | 8 | Brightness, timer, alarm, scoreboard, gallery interval |
| **Switch** | 7 | Timer, alarm, stopwatch, scoreboard, noise meter, mirror mode |
| **Select** | 7 | Channel, rotation, temperature, time format, clock face, visualizer, custom page |
| **Sensor** | 10 | Device info, network status, system config, weather, time, tool states |
| **Button** | 8 | Dismiss notification, buzzer, reset buffer, push buffer, channel switches (4) |

**Total**: 44 entities per device

### Button Entities

| Button Entity | Description | Use Case |
|---------------|-------------|----------|
| `button.*_dismiss_notification` | Dismiss notification | Clear alert overlay |
| `button.*_buzzer` | Play buzzer | Quick alert sound |
| `button.*_reset_stopwatch` | Reset stopwatch | Clear stopwatch time |
| `button.*_reset_buffer` | Clear drawing buffer | Reset canvas |
| `button.*_push_buffer` | Push buffer to display | Apply drawings |
| `button.*_switch_to_cloud_channel` | Switch to Cloud Gallery | Restore cloud display |
| `button.*_switch_to_clock_channel` | Switch to Clock Faces | Show clock |
| `button.*_switch_to_visualizer_channel` | Switch to Visualizer | Show music viz |
| `button.*_switch_to_custom_channel` | Switch to Custom | Show custom content |

**Channel Button Benefits:**
- ✅ **Reliable** - Always triggers even if channel already selected
- ✅ **Overlay Escape** - Returns from tool modes (timer/alarm/stopwatch) to normal channel
- ✅ **Automation Perfect** - Use in automations to restore display state
- ✅ **Simple** - No need to check current state

### Services

#### Display Services

- `pixoo.display_image` - Display static image
- `pixoo.display_gif` - Display animated GIF
- `pixoo.display_text` - Display scrolling or positioned text
- `pixoo.clear_display` - Clear screen

#### Drawing Services

- `pixoo.draw_pixel` - Draw single pixel
- `pixoo.draw_line` - Draw line between two points
- `pixoo.draw_rectangle` - Draw rectangle (filled or outline)
- `pixoo.draw_text` - Draw text at position
- `pixoo.draw_image` - Draw image at position
- `pixoo.reset_buffer` - Clear drawing buffer
- `pixoo.push_buffer` - Send buffer to display

#### Tool Services

- `pixoo.play_buzzer` - Play buzzer alert
- `pixoo.list_animations` - Get available animations

#### Media Player Services

Standard Home Assistant media player services:
- `media_player.play_media` - Display image or start slideshow
- `media_player.media_play` - Resume slideshow
- `media_player.media_pause` - Pause slideshow
- `media_player.media_stop` - Stop slideshow and clear
- `media_player.media_next_track` - Next image
- `media_player.media_previous_track` - Previous image
- `media_player.shuffle_set` - Enable/disable shuffle
- `media_player.repeat_set` - Enable/disable repeat

## Troubleshooting

## Known Limitations (Write-Only API & Optimistic State)

Certain Pixoo device features do not expose read-back methods in the underlying API (write-only operations). The integration uses **optimistic state** and marks affected entities with `assumed_state = true` to provide responsive UI feedback:

| Feature | Entities | Read Method Present | Strategy |
|---------|----------|---------------------|----------|
| Channel selection | `select.*_channel` | No | Track last selected option (optimistic) |
| Timer (minutes/seconds, running) | `number.*_timer_*`, `switch.*_timer` | No | Store last configured duration & running flag |
| Alarm (hour/minute, enabled) | `number.*_alarm_*`, `switch.*_alarm` | No | Store last configured alarm time & enabled flag |
| Stopwatch (running) | `switch.*_stopwatch` | No | Optimistic running state only (no elapsed time) |
| Scoreboard (scores, enabled) | `number.*_scoreboard_*`, `switch.*_scoreboard` | No | Track last written scores & enabled flag |
| Noise Meter (enabled) | `switch.*_noise_meter` | No | Track enabled flag |

### What This Means
- States may **drift** if changed outside Home Assistant (e.g., mobile app, hardware button).
- State is **restored** after Home Assistant restarts from the last known value.
- These entities will not show "Unavailable"—instead they reflect the last command you sent.
- For absolute accuracy, manually re-send your desired state after external changes.

### Why Not Sensors for These States?
The PixooAsync library currently offers only these read methods: `get_device_info`, `get_network_status`, `get_system_config`, `get_animation_list`, `get_weather_info`, `get_time_info`. Timer/alarm/stopwatch/channel/scoreboard/noise meter states cannot be queried.

### Planned Enhancements
If upstream API support is added for:
```python
async def get_current_channel()
async def get_timer_config()
async def get_alarm_config()
async def get_stopwatch_config()
async def get_scoreboard_config()
async def get_noise_meter_config()
```
the integration will migrate from optimistic to authoritative state reporting.

### Workaround Patterns
- Automations can rely on your own input helpers if strict persistence is required.
- Use scripts to reassert desired state on startup (`homeassistant` start event).
- For stopwatch elapsed time, prefer external timing in automations until read API exists.

### Identifying Optimistic Entities
In the UI, these entities allow toggling even if the device is offline; failure logs will appear if a command cannot be delivered.

### Reliability Notes
- Brightness, rotation, mirror mode, weather, time, and basic system info are **authoritative** (queried periodically).
- Screen power (on/off) is reported by the device but may not always reflect rapid changes—brightness + optimistic channel provide better contextual cues.

### Device Not Discovered

1. Ensure device is powered on and connected to Wi-Fi
2. Check that Home Assistant and Pixoo are on same network
3. Try manual configuration with device IP address
4. Check firewall rules allow access to Divoom cloud API

### Connection Timeout Errors

1. Verify device IP address hasn't changed
2. Check network connectivity between HA and device
3. Try power cycling the Pixoo device
4. Use **Settings** → **Devices & Services** → **Pixoo** → **Reconfigure**

### Pixoo 16 Specific Issues

**On/Off State Not Syncing:**
- The integration now uses `async_refresh()` to immediately update state after power changes
- If state still doesn't update, enable debug logging to see API responses:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.pixoo: debug
  ```
- Check logs for "System config updated" messages showing `screen_power` value
- If physical button presses don't update state in HA, this is expected due to polling interval (30s)

**Device Size Detection:**
- The integration automatically detects Pixoo 16 from the device model name
- Verify correct detection in **Settings** → **Devices & Services** → **Pixoo** → Device info
- Model should show "Pixoo-16" (not "Pixoo-64")
- If wrong size detected, delete integration and re-add with discovery or manual setup

**Image Display Issues:**
- Images are automatically resized to 16x16 pixels for Pixoo 16
- Very small images may lose detail when scaled down
- Use pixel art style images for best results on 16x16 display
- GIFs are also automatically resized to match device resolution

### Image Display Issues

1. Check image URL is accessible from Home Assistant
2. Verify image size (max 10MB)
3. Ensure image format is supported (JPEG, PNG, GIF)
4. Check Home Assistant logs for detailed error messages
5. For Pixoo 16, ensure images are recognizable at 16x16 resolution

### Slideshow Not Auto-Advancing

1. Verify media player state is "playing" (not "paused")
2. Check playlist items have `duration > 0`
3. Ensure repeat mode is enabled if you want continuous playback
4. Check Home Assistant logs for timer errors

## Development

### Running Tests

```bash
# Install dependencies
pip install -r requirements_test.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=custom_components.pixoo --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format custom_components/pixoo/

# Lint code
ruff check custom_components/pixoo/ --fix

# Type check
mypy custom_components/pixoo/ --strict
```

## 📬 Notify Service

The integration provides a `notify` platform for simple message notifications, similar to LaMetric:

```yaml
# Simple notification
service: notify.pixoo_DEVICENAME
data:
  message: "Washing machine done!"

# Notification with title
service: notify.pixoo_DEVICENAME
data:
  message: "Cycle complete"
  title: "Washing Machine"

# Notification with image and buzzer
service: notify.pixoo_DEVICENAME
data:
  message: "Someone at the door!"
  title: "Doorbell"
  data:
    image: "https://example.com/doorbell.png"
    color: "#FF0000"
    font: 3
    buzzer: true
    buzzer_active_time: 1000
    buzzer_off_time: 500
    buzzer_total_time: 3000
```

### Notify Data Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image` | URL to display before text | - |
| `color` | Text color (hex or RGB list) | `#FFFFFF` |
| `font` | Font size (1-7) | `2` |
| `speed` | Scroll speed (0-100) | `50` |
| `x`, `y` | Text position | `0, 32` |
| `scroll_direction` | Scroll direction | `left` |
| `text_id` | Text layer ID (1-20) | `1` |
| `buzzer` | Play buzzer alert | `false` |
| `buzzer_active_time` | Buzzer beep duration (ms) | `500` |
| `buzzer_off_time` | Buzzer silence duration (ms) | `500` |
| `buzzer_total_time` | Total buzzer duration (ms) | `2000` |

## 🆚 Notify Service vs Direct Services

### Notify Platform (Simple)
```yaml
# Quick notification - title + message
service: notify.pixoo_display
data:
  message: "Hello!"
  title: "Alert"
  data:
    color: "#00FF00"
    buzzer: true
```

### Direct Services (Advanced)
```yaml
# Fine-grained control - separate services
service: pixoo.display_image
target:
  entity_id: light.pixoo_display
data:
  url: "https://example.com/icon.png"

service: pixoo.display_text
target:
  entity_id: light.pixoo_display
data:
  text: "Hello!"
  color: "#FFFFFF"
  x: 10
  y: 20
  font: 2
  speed: 50
  text_id: 2
```

**Use notify for:** Quick notifications, automation alerts, simple messages  
**Use direct services for:** Complex layouts, multiple text layers, drawing operations, precise control

## More Automation Examples

### Washing Machine Alert

```yaml
alias: Washing Machine Done - Display on Pixoo
triggers:
  - platform: state
    entity_id: sensor.washing_machine_power
    to: "0"
    for:
      minutes: 2
conditions:
  - condition: state
    entity_id: input_boolean.washing_machine_running
    state: "on"
actions:
  # Display alert image
  - service: pixoo.display_image
    target:
      entity_id: light.pixoo_display
    data:
      url: "media-source://media_source/local/icons/washing_done.png"
  
  # Display text message
  - service: pixoo.display_text
    target:
      entity_id: light.pixoo_display
    data:
      text: "Washing Done!"
      color: "#00FF00"
      x: 0
      y: 48
      font: 3
      speed: 0
      text_id: 1
  
  # Play buzzer alert (3 beeps)
  - service: pixoo.play_buzzer
    target:
      entity_id: light.pixoo_display
    data:
      active_time: 500
      off_time: 500
      total_time: 3000
  
  # Return to cloud channel after 30 seconds
  - delay:
      seconds: 30
  - service: button.press
    target:
      entity_id: button.pixoo_switch_to_cloud_channel
  
  - service: input_boolean.turn_off
    target:
      entity_id: input_boolean.washing_machine_running
mode: single
```

### Weather Display

```yaml
alias: Show Weather on Pixoo
triggers:
  - platform: time
    at: "07:00:00"
actions:
  # Display weather icon
  - service: pixoo.display_image
    target:
      entity_id: light.pixoo_display
    data:
      url: >-
        {{ 'https://example.com/weather/' + states('weather.home') + '.png' }}
  
  # Display temperature
  - delay:
      seconds: 1
  - service: pixoo.display_text
    target:
      entity_id: light.pixoo_display
    data:
      text: "{{ state_attr('weather.home', 'temperature') }}°C"
      color: "#FFAA00"
      x: 0
      y: 50
      font: 4
      speed: 0
      text_id: 1
mode: single
```

### Doorbell Alert

```yaml
alias: Doorbell - Show Camera on Pixoo
triggers:
  - platform: state
    entity_id: binary_sensor.front_door_button
    to: "on"
variables:
  # Store the current channel before we change it
  saved_channel: "{{ states('select.pixoo_channel') }}"
actions:
  # Show doorbell camera snapshot
  - service: camera.snapshot
    target:
      entity_id: camera.front_door
    data:
      filename: "/media/doorbell_snapshot.jpg"
  
  - delay:
      seconds: 1
  
  - service: pixoo.display_image
    target:
      entity_id: light.pixoo_display
    data:
      url: "media-source://media_source/local/doorbell_snapshot.jpg"
  
  # Display text overlay
  - service: pixoo.display_text
    target:
      entity_id: light.pixoo_display
    data:
      text: "DOORBELL"
      color: "#FF0000"
      x: 0
      y: 2
      font: 2
      speed: 0
      text_id: 1
      scroll_direction: "left"
  
  # Play buzzer
  - service: pixoo.play_buzzer
    target:
      entity_id: light.pixoo_display
    data:
      active_time: 1000
      off_time: 500
      total_time: 2000
  
  # Restore previous channel after 30 seconds using button (always works!)
  - delay:
      seconds: 30
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ saved_channel == 'cloud' }}"
        sequence:
          - service: button.press
            target:
              entity_id: button.pixoo_switch_to_cloud_channel
      - conditions:
          - condition: template
            value_template: "{{ saved_channel == 'faces' }}"
        sequence:
          - service: button.press
            target:
              entity_id: button.pixoo_switch_to_clock_channel
      - conditions:
          - condition: template
            value_template: "{{ saved_channel == 'visualizer' }}"
        sequence:
          - service: button.press
            target:
              entity_id: button.pixoo_switch_to_visualizer_channel
      - conditions:
          - condition: template
            value_template: "{{ saved_channel == 'custom' }}"
        sequence:
          - service: button.press
            target:
              entity_id: button.pixoo_switch_to_custom_channel
    default:
      # Fallback to cloud if unknown channel
      - service: button.press
        target:
          entity_id: button.pixoo_switch_to_cloud_channel
mode: single
```

### Birthday Reminder

```yaml
alias: Birthday Reminder on Pixoo
triggers:
  - platform: time
    at: "09:00:00"
conditions:
  - condition: template
    value_template: >-
      {{ now().strftime('%m-%d') == '03-15' }}  # March 15
actions:
  - service: pixoo.display_gif
    target:
      entity_id: light.pixoo_display
    data:
      url: "media-source://media_source/local/animations/birthday.gif"
  
  - delay:
      seconds: 3
  
  - service: pixoo.display_text
    target:
      entity_id: light.pixoo_display
    data:
      text: "🎂 Happy Birthday John! 🎉"
      color: "#FF69B4"
      x: 0
      y: 50
      font: 2
      speed: 40
      text_id: 1
      scroll_direction: "left"
mode: single
```

### Random Photo Frame

```yaml
alias: Pixoo Random Photo Frame
triggers:
  - platform: time_pattern
    minutes: "/15"  # Every 15 minutes
actions:
  - service: media_player.play_media
    target:
      entity_id: media_player.pixoo_display
    data:
      media_content_type: playlist
      media_content_id: >
        [
          {"url": "media-source://media_source/local/photos/photo1.jpg", "duration": 900},
          {"url": "media-source://media_source/local/photos/photo2.jpg", "duration": 900},
          {"url": "media-source://media_source/local/photos/photo3.jpg", "duration": 900},
          {"url": "media-source://media_source/local/photos/photo4.jpg", "duration": 900},
          {"url": "media-source://media_source/local/photos/photo5.jpg", "duration": 900}
        ]
  
  # Enable shuffle for random order
  - service: media_player.shuffle_set
    target:
      entity_id: media_player.pixoo_display
    data:
      shuffle: true
mode: restart
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Built with [pixooasync](https://github.com/kmplngj/pixoo) Python library
- Inspired by the [original pixoo library](https://github.com/SomethingWithComputers/pixoo) by Ron Talman
- Community feedback from [Home Assistant forums](https://community.home-assistant.io/)

## Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/pixoo-ha/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/pixoo-ha/discussions)
- **Home Assistant Community**: [Pixoo Integration Thread](https://community.home-assistant.io/t/divoom-pixoo-64/)

---

**Status**: ✨ Production Ready  
**Version**: 1.0.0  
**Maintainer**: Jan Kampling (@kmplngj)  
**Date**: November 10, 2025
