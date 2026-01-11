# Pixoo Page Engine - Example Templates

This directory contains example page configurations for the Pixoo Page Engine rotation feature.

## Quick Start

1. **Copy a template to your Home Assistant config directory:**
   ```bash
   cp pixoo_pages_complete.yaml /config/pixoo_pages.yaml
   ```

2. **Configure the integration** to use your pages file:
   - Go to Settings → Devices & Services → Pixoo
   - Click "Configure" on your device
   - Set `pages_yaml_path` to `pixoo_pages.yaml`
   - Enable rotation

3. **Reload pages** after editing:
   ```yaml
   service: pixoo.rotation_reload_pages
   target:
     entity_id: light.pixoo64_display
   ```

## Available Examples

### `pixoo_pages_complete.yaml`
A complete rotation configuration with:
- **Solar/PV Dashboard** - Real-time solar production, battery status, home consumption
- **Now Playing Pages** - Media player cover art with scrolling title/artist (Apple TV, Sonos, etc.)
- **Pi-hole Dashboard** - Ad blocking statistics and status
- **Native Pixoo Cloud** - Fallback to Pixoo's built-in cloud channel

### `pihole_dashboard.yaml`
Pi-hole network ad blocker dashboard showing:
- Pi-hole status (active/disabled with shield icon)
- Ads blocked today (with thousands separator)
- Blocking percentage with progress bar
- Total DNS queries
- Dynamic colors based on blocking effectiveness

### `now_playing.yaml`
Simple now-playing template for media players with:
- Cover art display
- Title and artist overlay
- Customizable colors

### `progress_bar.yaml`
Generic progress bar template with modern round-cap design for:
- Download/upload progress
- Timer countdowns
- Any percentage-based visualization

### `battery_gauge.yaml` ⭐ NEW
Circular battery gauge with:
- 12-segment circular progress indicator using circle components
- Color thresholds (red < 20%, yellow < 50%, green >= 50%)
- Large center icon and percentage display
- Demonstrates advanced circle component usage

### `network_activity.yaml` ⭐ NEW
Network activity bar chart with:
- Vertical bar visualization using thick line components
- RX/TX rates with color thresholds
- Scale indicators and baseline
- Shows how to use lines for data visualization

### `weather_radar.yaml` ⭐ NEW
Weather radar visualization with:
- Concentric circle radar display
- Cardinal direction markers (N, E, S, W)
- Rain/cloud indicators using circle components
- Crosshair lines showing axis divisions
- Demonstrates combining lines and circles for complex layouts

### `compass_navigation.yaml` ⭐ NEW
Compass/navigation display with:
- Full compass rose with cardinal markers
- Directional arrow using arrow component
- Optional value gauge using arc component
- Perfect for wind direction, GPS heading
- Shows arc and arrow component integration

### `weather_dashboard.yaml` ⭐ NEW
Complete weather dashboard with:
- Temperature as circular progress ring using arc component
- Wind direction compass with arrow component
- Weather condition icon (sunny, cloudy, rainy, etc.)
- Humidity percentage display
- Wind speed with color-coded intensity
- Demonstrates real-world arc and arrow usage
- Requires: `weather.*` entity (e.g., `weather.openweathermap`)

### `stock_dashboard.yaml` ⭐ NEW
Stock market dashboard with:
- 2x2 grid layout showing 4 stocks (AAPL, NVDA, ASML, MU)
- S&P 500 index as market indicator (header)
- USD/EUR currency rate (footer)
- Current price and daily % change for each stock
- Green/red color coding (gains/losses)
- Up/down arrow indicators
- Compact design optimized for 64x64 display
- Requires: Yahoo Finance integration (`sensor.yahoofinance_*`)

## Page Types

### Components Page
```yaml
- page_type: components
  duration: 15              # Seconds to display
  enabled: "{{ ... }}"      # Optional: Jinja2 condition
  background: "#000000"
  variables:
    my_var: "{{ states('sensor.something') }}"
  components:
    - type: text
      x: 0
      y: 0
      text: "Hello"
      color: "#FFFFFF"
```

### Channel Page
Switch to native Pixoo channels:
```yaml
- page_type: channel
  duration: 120
  channel_name: clock   # clock, cloud, visualizer, custom
  clock_id: 42          # Optional: specific clock face
```

## Component Types

| Type | Description |
|------|-------------|
| `text` | Static or scrolling text |
| `rectangle` | Filled or outlined rectangle |
| `image` | Image from URL, path, or base64 |
| `icon` | MDI icon (e.g., `mdi:battery`) |
| `line` | Lines with configurable thickness and color thresholds |
| `circle` | Circles/dots, filled or outlined, with color thresholds |
| `arc` | Arc/pie slice for progress rings and gauges |
| `arrow` | Directional arrows for compass, wind, navigation |
| `progress_bar` | Horizontal progress indicator |
| `graph` | Historical sensor data graph |

## Text Component Options

```yaml
- type: text
  x: 0
  y: 0
  text: "{{ title }}"
  color: "#FFFFFF"
  align: left           # left, center, right
  scroll: true          # Enable scrolling for long text
  scroll_speed: 40      # 0-100 (higher = faster)
  scroll_direction: left  # left, right
  text_width: 60        # Scroll area width in pixels
```

## Line Component

Draw lines with configurable thickness and dynamic colors:

```yaml
- type: line
  start: [0, 32]         # [x, y] start coordinates
  end: [64, 32]          # [x, y] end coordinates
  color: "#FFFFFF"
  thickness: 2           # Line thickness in pixels
  value: "{{ sensor.temperature }}"  # Optional: for color thresholds
  color_thresholds:
    - value: 20
      color: "#0088FF"
    - value: 25
      color: "#00FF00"
```

**Use cases:**
- Divider lines between sections
- Vertical bars for bar charts
- Grid lines for graphs
- Crosshairs for radar displays

## Circle Component

Draw circles/dots, filled or outlined:

```yaml
- type: circle
  center: [32, 32]       # [x, y] center coordinates
  radius: 10             # Radius in pixels
  color: "#00FF00"
  filled: true           # true for filled, false for outline
  thickness: 2           # Border thickness (for filled=false)
  value: "{{ sensor.battery }}"  # Optional: for color thresholds
  color_thresholds:
    - value: 20
      color: "#FF0000"
    - value: 50
      color: "#FFAA00"
    - value: 100
      color: "#00FF00"
```

**Use cases:**
- Progress indicators (circle segments)
- Round-cap endings for progress bars
- Data point markers
- Weather indicators (rain drops, sun)
- Gauge dots

## Arc Component

Draw circular arcs or pie slices for gauges and progress rings:

```yaml
- type: arc
  center: [32, 32]       # [x, y] center coordinates
  radius: 20             # Radius in pixels
  start_angle: 0         # Start angle (0 = top, clockwise)
  end_angle: "{{ (battery | float) * 3.6 }}"  # 0-100% -> 0-360°
  color: "#00FF00"
  filled: false          # false = arc outline, true = pie slice
  thickness: 3           # Arc thickness (for filled=false)
  value: "{{ sensor.battery }}"  # Optional: for color thresholds
  color_thresholds:
    - value: 20
      color: "#FF0000"
    - value: 50
      color: "#FFAA00"
    - value: 100
      color: "#00FF00"
```

**Use cases:**
- Battery/fuel gauges (circular progress)
- Timer countdown rings
- Temperature gauges
- Pie charts
- Analog clock hands (with filled pie slice)

## Arrow Component

Draw directional arrows with rotation:

```yaml
- type: arrow
  center: [32, 32]       # [x, y] center/base point
  length: 20             # Arrow length in pixels
  angle: "{{ wind_bearing }}"  # 0 = North, clockwise
  color: "#FFFFFF"
  thickness: 2           # Arrow line thickness
  head_size: 4           # Arrow head size in pixels
  value: "{{ wind_speed }}"  # Optional: for color thresholds
  color_thresholds:
    - value: 10
      color: "#00FF00"
    - value: 20
      color: "#FFAA00"
    - value: 30
      color: "#FF0000"
```

**Use cases:**
- Wind direction (compass)
- Navigation/GPS heading
- Gauge pointers
- Direction indicators
- Flow direction arrows

## Conditional Pages

Pages can be conditionally enabled using Jinja2 templates:

```yaml
- name: now_playing
  page_type: components
  enabled: "{{ is_state('media_player.spotify', 'playing') }}"
  # ... only shown when Spotify is playing
```

## Variables

Define reusable variables that can reference other variables:

```yaml
variables:
  battery_soc: "{{ states('sensor.battery') | float(0) }}"
  battery_color: "{{ '#00FF00' if battery_soc | float > 50 else '#FF0000' }}"
  # battery_color uses the already-rendered battery_soc value
```

## Tips

1. **Use `enabled` conditions** to show pages only when relevant
2. **Set appropriate `duration`** - longer for static info, shorter for dynamic
3. **Test templates** in Developer Tools → Template before using
4. **Reload after changes** with `pixoo.rotation_reload_pages`

## Using TemplatePage (Reusable Templates)

If you want to create reusable templates that can be used with `render_template` service, 
place them in your config directory under `pixoo_templates/`:

```
/config/
  pixoo_templates/
    now_playing.yaml
    progress.yaml
```

Then use the `render_template` service:
```yaml
service: pixoo.render_template
target:
  entity_id: light.pixoo64_display
data:
  template_name: now_playing
  variables:
    title: "My Song"
    artist: "My Artist"
```

This is useful for templates that need dynamic variables passed at render time.

