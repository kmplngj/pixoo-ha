# Beta Release: ha-pixoo - Native Home Assistant Integration for Divoom Pixoo Displays

Hi everyone!

I'm excited to share a new Home Assistant integration I've been working on for Divoom Pixoo devices (Pixoo64, Pixoo16, PixooMax). This is currently in **alpha/beta stage**, so I'm looking for brave testers who want to help improve it.

**GitHub Repository:** https://github.com/kmplngj/pixoo-ha

## What it does

The integration provides native Home Assistant entities and services for controlling your Pixoo display:
- Light entity for power and brightness control
- 40+ entities for complete device control (channels, timers, alarms, sensors)
- 25+ services for display operations
- Full drawing buffer support for custom animations
- Media player entity for image galleries and slideshows
- Automatic device discovery via SSDP

## Example Automations

Here are some practical examples to get you started:

### 1. Display Media Player Info

Show album art and track information from your Apple TV, amplifier, or HomePod:

```yaml
alias: Display Media Info on Pixoo
description: Display currently playing media with cover art and scrolling title
triggers:
  - entity_id:
      - media_player.appletv
      - media_player.amplifier
      - media_player.homepod
    attribute: entity_picture
    for:
      seconds: 3
    trigger: state
conditions:
  - condition: template
    value_template: >
      {{ state_attr(trigger.entity_id, 'media_title') is not none }}
actions:
  # Clear display
  - action: pixoo.clear_display
    target:
      entity_id: light.pixoo_display

  # Display cover art
  - condition: template
    value_template: >
      {{ state_attr(trigger.entity_id, 'entity_picture') is not none }}
  - action: pixoo.display_image
    data:
      url: >
        http://homeassistant.local:8123{{ state_attr(trigger.entity_id, 'entity_picture') }}
    target:
      entity_id: light.pixoo_display

  # Display artist and title as scrolling text
  - delay:
      seconds: 1
  - action: pixoo.display_text
    data:
      text: >
        {{ state_attr(trigger.entity_id, 'media_artist') }} - {{ state_attr(trigger.entity_id, 'media_title') }}
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

### 2. Doorbell Alert

Show a doorbell notification with buzzer sound:

```yaml
alias: Doorbell Alert on Pixoo
triggers:
  - entity_id: binary_sensor.doorbell
    to: "on"
    trigger: state
actions:
  - action: pixoo.display_text
    data:
      text: "DOORBELL!"
      color: "#FF0000"
      x: 0
      y: 16
      font: 7
      text_id: 0
    target:
      entity_id: light.pixoo_display
  - action: pixoo.play_buzzer
    data:
      active_time: 500
      off_time: 100
      total_time: 3000
    target:
      entity_id: light.pixoo_display
```

### 3. Weather Display

Show current weather on a timer:

```yaml
alias: Update Pixoo Weather Display
triggers:
  - trigger: time_pattern
    minutes: "/30"
conditions:
  - condition: time
    after: "07:00:00"
    before: "23:00:00"
actions:
  - action: pixoo.display_text
    data:
      text: >
        {{ states('sensor.outdoor_temperature') }}°C - {{ states('weather.home') }}
      color: "#00AAFF"
      x: 0
      y: 24
      font: 5
      text_id: 2
    target:
      entity_id: light.pixoo_display
```

### 4. Image Slideshow

Display a rotating collection of images using the media player entity:

```yaml
alias: Start Morning Photo Slideshow
triggers:
  - trigger: time
    at: "08:00:00"
actions:
  - action: media_player.play_media
    target:
      entity_id: media_player.pixoo_gallery
    data:
      media_content_type: playlist
      media_content_id: >
        [
          {"url": "http://example.com/photo1.jpg", "duration": 10},
          {"url": "http://example.com/photo2.jpg", "duration": 10},
          {"url": "http://example.com/photo3.jpg", "duration": 10}
        ]
  - action: media_player.shuffle_set
    target:
      entity_id: media_player.pixoo_gallery
    data:
      shuffle: true
```

## Current Status

This integration is in active development and still has rough edges. Please note:
- This is alpha/beta quality software
- Some features may not work as expected
- Breaking changes may occur before v1.0
- Documentation is still evolving

## How You Can Help

I'm looking for testers who can:
- Try the integration with their Pixoo devices
- Report bugs and issues on GitHub
- Suggest improvements and new features
- Share their automation examples

If you encounter any problems or have suggestions, please open an issue on the GitHub repository: https://github.com/kmplngj/pixoo-ha/issues

## Installation

The integration is available through manual installation (copy to `custom_components/pixoo`) or will soon be available via HACS. Full installation instructions are in the README.

## Thanks

A huge thank you to the original pixoo library authors and the Home Assistant community. Special thanks to anyone who tries this out and provides feedback!

Looking forward to hearing your experiences and making this integration even better together.

Cheers,
Jan
