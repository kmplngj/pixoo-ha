# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **IconComponent** - MDI icon component with:
  - Material Design Icons fetched from CDN at runtime
  - Size options: 8, 16, 24, or 32 pixels
  - Static color or threshold-based dynamic coloring
  - Value source from entity_id or template for threshold calculation
  - Requires `cairosvg` for SVG-to-PNG rendering
- **Component-level `enabled` field** - All components now support conditional visibility:
  - Boolean value (`true`/`false`) for static enable/disable
  - Jinja2 template string for dynamic visibility based on states
  - Disabled components are skipped during rendering
- **ProgressBarComponent** - Native progress bar component with:
  - Horizontal and vertical orientation
  - Direct value, entity_id, or template-based progress source
  - Threshold-based dynamic coloring (like mini-graph-card)
  - Smooth or hard color transitions between thresholds
  - Optional border and customizable colors
- **GraphComponent** - Entity history graph component with:
  - Line, bar, and area chart styles
  - Automatic data aggregation (avg, min, max, last)
  - Auto-calculated points from component width
  - Threshold-based segment coloring for dynamic visualization
  - Configurable time range (hours of history)
  - Optional fill under line for area charts
- **Color threshold system** - Shared `color_thresholds` support for progress bars and graphs:
  - Define value/color pairs for dynamic coloring
  - `smooth` transition interpolates colors between thresholds
  - `hard` transition uses step-based color changes
- **ChannelPage support** - New page type `channel` for switching to native Pixoo channels (clock, visualizer, cloud, custom) within rotation. Supports optional `clock_id`, `visualizer_id`, and `custom_page_id` parameters.
- **`set_rotation_config` service** - Configure all rotation settings in a single service call:
  - `enabled` - Start/stop rotation
  - `default_duration` - Default page display duration (seconds)
  - `pages_yaml_path` - Path to YAML file with page definitions
  - `allowlist_mode` - Security mode for image URLs (`strict` or `permissive`)
- **YAML-based page rotation** - Define rotation pages in an external YAML file for easier maintenance and version control
- **Conditional pages** - Pages can have an `enabled` template that evaluates to show/hide the page dynamically
- **Per-page duration override** - Each page can specify its own `duration` to override the default

### Changed

- **Improved rotation controller** - Better handling of YAML page reloading and runtime configuration changes
- **Enhanced service documentation** - Updated `services.yaml` with clearer descriptions and all new parameters

### Fixed

- **Rate limiting for rotation** - Minimum 1-second delay between page transitions to prevent display flickering
- **Offline device handling** - Services now gracefully handle offline devices and only raise errors if all targets fail

## [1.0.0] - 2025-01-02

### Added

- Initial release with full Pixoo device support
- **Light entity** - Power control and brightness adjustment
- **Media player entity** - Image gallery/slideshow with playlist, shuffle, repeat
- **Number entities** (8) - Brightness, timer, alarm, scoreboard, gallery interval
- **Switch entities** (7) - Timer, alarm, stopwatch, scoreboard, noise meter, mirror, 24h format
- **Select entities** (7) - Channel, rotation, temperature unit, time format, custom page, clock face, visualizer
- **Sensor entities** (10) - Device info, network status, weather, time, tool states
- **Button entities** (4) - Channel shortcuts, buzzer control
- **25+ services** - Display, drawing, tool, configuration, and animation services
- **Page Engine** - Declarative page rendering with components (text, rectangle, image)
- **Template pages** - Jinja2 templates with Home Assistant state access
- **Rotation controller** - Automatic page cycling with configurable intervals
- **iOS Shortcuts support** - Base64 image display for direct iPhone/iPad integration
- **SSDP discovery** - Automatic device detection on local network
- **Drawing primitives** - Pixel, line, rectangle, and text drawing with buffer management
