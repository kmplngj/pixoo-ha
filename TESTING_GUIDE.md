# Pixoo Integration - Quick Test Guide

**Date**: November 13, 2025  
**Version**: Phase 1 Complete

## ⚡ Quick Start

### 1. Restart Home Assistant
**Required**: Load fixed light entity with `screen_power` support

From HA UI:
- Developer Tools → YAML → Restart Home Assistant Core

### 2. Verify Integration Status

Check: Settings → Devices & Services → Pixoo

Expected:
- ✅ Integration active
- ✅ Device registered
- ✅ 40+ entities visible

## 🔍 Test Checklist

### Light Entity (CRITICAL - Just Fixed)
- [ ] Toggle light on/off via UI
- [ ] Adjust brightness slider (0-255)
- [ ] Verify display responds to commands
- [ ] Check logs for errors: `grep -i "pixoo.*error"`

### Sensor Entities
- [ ] Device info sensors show MAC, model, firmware
- [ ] Network sensors show SSID, RSSI
- [ ] System sensors show brightness, channel
- [ ] Tool state sensors update (timer, alarm, stopwatch)

### Select Entities
- [ ] Channel selector works (clock, visualizer, etc.)
- [ ] Rotation selector changes display orientation
- [ ] Clock/visualizer selectors populate dynamically

### Number Entities
- [ ] Brightness number matches light brightness
- [ ] Timer/alarm minute/second controls work
- [ ] Scoreboard red/blue score adjustable

### Switch Entities
- [ ] Timer switch enables/disables countdown
- [ ] Alarm switch enables/disables alarm
- [ ] Mirror mode switch flips display

### Button Entities
- [ ] Buzzer button plays sound
- [ ] Reset buffer clears drawing buffer
- [ ] Push buffer displays buffered content

## 🚀 Service Testing

### Display Services

#### Display Image
```yaml
service: pixoo.display_image
target:
  entity_id: light.pixoo_your_device
data:
  url: "https://picsum.photos/64"
```

#### Display GIF
```yaml
service: pixoo.display_gif
target:
  entity_id: light.pixoo_your_device
data:
  url: "https://example.com/animation.gif"
```

#### Display Text
```yaml
service: pixoo.display_text
target:
  entity_id: light.pixoo_your_device
data:
  text: "Hello World!"
  color: "#FF0000"
  scroll_direction: "left"
```

#### Clear Display
```yaml
service: pixoo.clear_display
target:
  entity_id: light.pixoo_your_device
```

### Tool Services

#### Set Timer
```yaml
service: pixoo.set_timer
target:
  entity_id: light.pixoo_your_device
data:
  duration: "05:30"  # 5 minutes 30 seconds
```

#### Set Alarm
```yaml
service: pixoo.set_alarm
target:
  entity_id: light.pixoo_your_device
data:
  time: "07:30"  # 7:30 AM
  enabled: true
```

### Utility Services

#### Play Buzzer
```yaml
service: pixoo.play_buzzer
target:
  entity_id: light.pixoo_your_device
data:
  active_ms: 1000
  off_ms: 500
  count: 3
```

#### List Animations
```yaml
service: pixoo.list_animations
target:
  entity_id: light.pixoo_your_device
```
*Check logs for output*

## 🐛 Troubleshooting

### Light Not Responding

**Check**: System coordinator data
```python
# Developer Tools → Template
{{ state_attr('light.pixoo_your_device', 'coordinator_data') }}
```

Expected keys:
- `screen_power`: true/false
- `brightness`: 0-100
- `channel`: "clock", "visualizer", etc.

### Service Errors

**Check logs**:
```bash
ssh homeassistant 'cat /config/home-assistant.log | grep -i pixoo'
```

Common issues:
- Image download timeout (30s limit)
- Invalid color format (use hex: #RRGGBB)
- Invalid time format (use HH:MM or HH:MM:SS)

### Coordinator Not Updating

**Check update intervals**:
- Device: One-time (doesn't update)
- System: 30s
- Weather: 5 minutes
- Tool: 1s (active) / 30s (idle)
- Gallery: 10s

**Force refresh**: Restart integration or call service

### Entity Not Available

**Possible causes**:
1. Device offline/unreachable
2. Coordinator fetch failed
3. Integration reload needed

**Solution**: Check device connectivity, restart integration

## 📊 Diagnostics

### Export Diagnostic Data

Settings → Devices & Services → Pixoo → Device → Download Diagnostics

**Includes**:
- All coordinator data
- Dynamic polling state
- Redacted sensitive info (IP, MAC, SSID)

### Check Coordinator Health

```python
# Developer Tools → Template
{% for entry_id, data in integration_entities('pixoo') | map('device_id') | unique | map('device_attr', 'identifiers') | list %}
Coordinators:
- Device: {{ states('sensor.pixoo_device_model') }}
- System Brightness: {{ states('sensor.pixoo_brightness') }}
- Weather: {{ states('sensor.pixoo_weather_condition') }}
- Tool Timer: {{ states('sensor.pixoo_timer_state') }}
{% endfor %}
```

## ✅ Success Criteria

### Phase 1 Complete When:
- [ ] Light entity on/off works
- [ ] Brightness slider responsive
- [ ] All 8 services callable without errors
- [ ] Sensors update within expected intervals
- [ ] No Pixoo errors in logs after 10 minutes
- [ ] Diagnostics export successful

### Ready for Phase 2 When:
- [ ] All Phase 1 services tested and working
- [ ] Integration stable for 24+ hours
- [ ] No memory leaks or performance issues
- [ ] User feedback collected

## 📝 Reporting Issues

### Information to Include:
1. Home Assistant version
2. Pixoo device model (16/32/64/Max/Planet)
3. Integration version (check manifest.json)
4. Relevant log entries
5. Diagnostic data (Settings → Download Diagnostics)
6. Steps to reproduce

### Where to Report:
- GitHub Issues: `/Users/jankampling/Repositories/pixoo-ha/`
- Include STATUS_REPORT.md for context

## 🎯 Next Steps After Testing

### If All Tests Pass ✅
1. Run integration for 24 hours
2. Monitor for stability/memory leaks
3. Plan Phase 2 implementation:
   - Drawing primitives (7 services)
   - Animation control (4 services)
   - Advanced config (4 services)

### If Issues Found ⚠️
1. Document issue with logs
2. Check TROUBLESHOOTING section
3. Review STATUS_REPORT.md for known issues
4. File bug report with diagnostic data

---

**Quick Links**:
- Status Report: `STATUS_REPORT.md`
- Service Definitions: `custom_components/pixoo/services.yaml`
- Entity List: `specs/001-pixoo-integration/ENTITY_MAPPING.md`
- Feature Roadmap: `FEATURE_COVERAGE.py`
