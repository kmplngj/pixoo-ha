# Pixoo API Capabilities Analysis

**Generated**: 2025-01-14  
**Device Tested**: Pixoo-64 at 192.168.188.65  
**Library**: PixooAsync (from pixooasync)  
**Purpose**: Document read/write capabilities to inform HA integration architecture

## Executive Summary

The Pixoo device API has **mixed read/write capabilities**:
- Some properties are **fully readable** (device_info, system_config, network_status, brightness)
- Some properties are **write-only** (channel, timer, alarm, stopwatch)
- Write-only properties have no read methods and are not included in system config

**Critical Finding**: Using `CoordinatorEntity` for write-only properties is architecturally wrong. There is no data to coordinate.

## Test Results

### ✅ Readable Properties

| Property | PixooAsync Method | Read From | Notes |
|----------|------------------|-----------|-------|
| Device Info | `get_device_info()` | Direct call | Model, firmware, brightness |
| System Config | `get_system_config()` | Direct call | Brightness, rotation, mirror, screen_power |
| Network Status | `get_network_status()` | Direct call | IP, MAC, SSID, RSSI |
| Brightness | `get_system_config().brightness` | SystemConfig | Readable but may lag after write |

**HA Integration Pattern**: Use `CoordinatorEntity` with appropriate coordinators.

### ❌ Write-Only Properties

| Property | Write Method | Read Method | In SystemConfig? |
|----------|-------------|-------------|------------------|
| Channel | `set_channel()` | ❌ None | ❌ No |
| Timer | `set_timer()` | ❌ None | ❌ No |
| Alarm | `set_alarm()` | ❌ None | ❌ No |
| Stopwatch | ❌ Missing | ❌ None | ❌ No |

**HA Integration Pattern**: Use `RestoreEntity` + local state storage, NOT `CoordinatorEntity`.

### ⚠️ Mixed Behavior

**Brightness Lag**:
- Brightness is readable via `get_system_config().brightness`
- After write, device may not immediately reflect new value
- Test showed: wrote 75%, read back 50% (old value)
- **Recommendation**: Use optimistic state updates + coordinator refresh

**Channel Selection**:
- Channel can be written via `set_channel(Channel.FACES)`
- Channel is NOT in SystemConfig response
- No way to read current channel from device
- **Recommendation**: Write-only entity with RestoreEntity

## PixooAsync Library Gaps

### Missing Methods

1. **`get_timer_config()`** - Not implemented
   - Write: `set_timer(minutes, seconds)` ✅
   - Read: ❌ No method available

2. **`get_alarm_config()`** - Not implemented
   - Write: `set_alarm(hour, minute, enabled)` ✅
   - Read: ❌ No method available

3. **`get_stopwatch_config()`** - Not implemented
   - Write: ❌ Missing `start_stopwatch()` method
   - Read: ❌ No method available
   - Available: `reset_stopwatch()` ✅

4. **`start_stopwatch()`** - Not implemented
   - Error: `'PixooAsync' object has no attribute 'start_stopwatch'`
   - Only `reset_stopwatch()` is available

### SystemConfig Fields

**Available in SystemConfig**:
```python
['brightness', 'rotation', 'mirror_mode', 'white_balance_r', 
 'white_balance_g', 'white_balance_b', 'time_zone', 'hour_mode', 
 'temperature_mode', 'screen_power']
```

**NOT in SystemConfig**:
- channel (current channel selection)
- timer state (running, time remaining)
- alarm state (enabled, time)
- stopwatch state (running, elapsed)
- scoreboard state (red/blue scores)
- noise_meter state (enabled, sensitivity)

## Device Test Output

```
Model: Pixoo-64
Firmware: 1.0.0
Brightness: 50%
Rotation: 0°
Mirror mode: False
Screen power: True
IP: 192.168.188.65
MAC: 00:00:00:00:00:00
SSID: Unknown
RSSI: -50 dBm
```

## Recommendations for HA Integration

### 1. Readable Properties → CoordinatorEntity

**Entities**:
- Light (brightness, power)
- Select (rotation, temperature_mode, hour_mode)
- Switch (mirror_mode, screen_power)
- Sensor (device_info, network_status, system_config)

**Pattern**:
```python
class PixooBrightnessNumber(CoordinatorEntity, NumberEntity):
    """Brightness control with coordinator."""
    
    @property
    def native_value(self) -> int:
        """Read from coordinator data."""
        return self.coordinator.data.get("brightness", 50)
    
    async def async_set_native_value(self, value: int) -> None:
        """Write to device + refresh coordinator."""
        await self.pixoo.set_brightness(value)
        await self.coordinator.async_request_refresh()
```

### 2. Write-Only Properties → RestoreEntity (NO Coordinator)

**Entities**:
- Select: channel_select, clock_face_select, visualizer_select, custom_page_select
- Number: timer_minutes, timer_seconds, alarm_hour, alarm_minute
- Switch: timer_running, alarm_enabled, stopwatch_running
- Number: scoreboard_red, scoreboard_blue
- Switch: scoreboard_enabled, noise_meter_enabled

**Pattern**:
```python
class PixooChannelSelect(PixooEntity, SelectEntity, RestoreEntity):
    """Channel selection - write-only with state restoration."""
    
    _attr_assumed_state = True
    
    def __init__(self, ...):
        super().__init__(...)
        self._current_option = None  # Local state
    
    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state:
            self._current_option = last_state.state
    
    @property
    def current_option(self) -> str | None:
        """Read from local state."""
        return self._current_option
    
    @property
    def available(self) -> bool:
        """Always available (write-only)."""
        return True
    
    async def async_select_option(self, option: str) -> None:
        """Write to device + update local state."""
        await self.pixoo.set_channel(Channel[option.upper()])
        self._current_option = option
        self.async_write_ha_state()
```

### 3. LaMetric-Style Entity Descriptions

**Pattern from LaMetric**:
```python
@dataclass(frozen=True, kw_only=True)
class PixooSelectEntityDescription(SelectEntityDescription):
    """Description for Pixoo select entities."""
    
    # For readable properties:
    current_fn: Callable[[SystemConfig], str] | None = None
    
    # For write-only properties:
    restore_state: bool = False
    
    # Write function:
    select_fn: Callable[[PixooAsync, str], Awaitable[Any]]
    
    # Availability check:
    available_fn: Callable[[CoordinatorEntity], bool] = lambda _: True
```

**Usage**:
```python
CHANNEL_SELECT = PixooSelectEntityDescription(
    key="channel",
    name="Channel",
    icon="mdi:television",
    options=[c.value for c in Channel],
    restore_state=True,  # Write-only
    current_fn=None,  # No read method
    select_fn=lambda pixoo, opt: pixoo.set_channel(Channel[opt.upper()]),
    available_fn=lambda entity: True,  # Always available
)
```

### 4. Coordinator Architecture

**Current Structure** (correct):
```
DeviceCoordinator (once)    → device_info
SystemCoordinator (30s)     → system_config, brightness, rotation, mirror, power
WeatherCoordinator (5min)   → weather_info
ToolCoordinator (1s/30s)    → No readable data (write-only tools)
GalleryCoordinator (10s)    → animations list
```

**ToolCoordinator Issues**:
- Currently runs every 1 second
- Has no readable data (timer/alarm/stopwatch are write-only)
- Should be removed or converted to event-based updates
- DEBUG log: "No tool state read methods available" is expected

**Recommendation**: Remove ToolCoordinator, store tool states locally in entities.

## Implementation Checklist

### Phase 1: Fix Write-Only Entities ✅ CRITICAL

- [ ] Remove CoordinatorEntity from write-only entities
- [ ] Add RestoreEntity to all write-only entities
- [ ] Store state in instance variables (`self._state`)
- [ ] Override `available` property to return `True`
- [ ] Add state restoration in `async_added_to_hass()`
- [ ] Remove `_attr_available = True` from `__init__` (not needed)

**Files to modify**:
- `select.py`: channel, clock_face, visualizer, custom_page (4 entities)
- `number.py`: timer_minutes, timer_seconds, alarm_hour, alarm_minute, scoreboard_red, scoreboard_blue (6 entities)
- `switch.py`: timer, alarm, stopwatch, scoreboard, noise_meter (5 entities)

### Phase 2: Apply LaMetric Patterns 🔄 HIGH

- [ ] Create entity description dataclasses
- [ ] Add lambda functions for value extraction
- [ ] Chain `available` property: `super().available and check`
- [ ] Implement write → refresh pattern for readable entities
- [ ] Clean separation of read/write logic

### Phase 3: Coordinator Cleanup 🔄 MEDIUM

- [ ] Keep DeviceCoordinator (once)
- [ ] Keep SystemCoordinator (30s)
- [ ] Keep WeatherCoordinator (5min)
- [ ] Keep GalleryCoordinator (10s)
- [ ] Remove ToolCoordinator (no readable data)

### Phase 4: Testing 🔄 LOW

- [ ] Test write-only entities show as available
- [ ] Test state restoration across HA restarts
- [ ] Test brightness lag handling
- [ ] Monitor for state flapping (should be gone)
- [ ] Verify all entities stable for 5+ minutes

## Code Examples

### Example 1: Write-Only Select Entity

```python
"""channel_select.py - Write-only channel selection."""
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import PixooEntity
from .const import Channel

class PixooChannelSelect(PixooEntity, SelectEntity, RestoreEntity):
    """Channel selection entity (write-only)."""
    
    _attr_assumed_state = True
    _attr_options = [c.value for c in Channel]
    
    def __init__(self, coordinator, entry):
        """Initialize."""
        super().__init__(coordinator, entry)
        self._current_option = None
    
    async def async_added_to_hass(self) -> None:
        """Restore state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state:
            self._current_option = last_state.state
            _LOGGER.debug("Restored channel: %s", self._current_option)
    
    @property
    def current_option(self) -> str | None:
        """Return current channel (from local state)."""
        return self._current_option
    
    @property
    def available(self) -> bool:
        """Channel selection always available."""
        return True
    
    async def async_select_option(self, option: str) -> None:
        """Select channel (write-only)."""
        try:
            await self.pixoo.set_channel(Channel[option.upper()])
            self._current_option = option
            self.async_write_ha_state()
            _LOGGER.info("Channel set to: %s", option)
        except Exception as err:
            _LOGGER.error("Failed to set channel: %s", err)
            raise
```

### Example 2: Readable Number Entity with Lag Handling

```python
"""brightness_number.py - Readable brightness with optimistic updates."""
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class PixooBrightnessNumber(CoordinatorEntity, NumberEntity):
    """Brightness control (readable but may lag)."""
    
    def __init__(self, coordinator, entry):
        """Initialize."""
        super().__init__(coordinator)
        self._optimistic_value = None
    
    @property
    def native_value(self) -> int:
        """Return brightness (optimistic or coordinator)."""
        if self._optimistic_value is not None:
            return self._optimistic_value
        return self.coordinator.data.get("brightness", 50)
    
    @property
    def available(self) -> bool:
        """Available if coordinator has data."""
        return super().available and "brightness" in self.coordinator.data
    
    async def async_set_native_value(self, value: int) -> None:
        """Set brightness with optimistic update."""
        self._optimistic_value = value
        self.async_write_ha_state()
        
        try:
            await self.pixoo.set_brightness(value)
            await self.coordinator.async_request_refresh()
        finally:
            # Clear optimistic value after refresh
            self._optimistic_value = None
            self.async_write_ha_state()
```

### Example 3: LaMetric-Style Entity Description

```python
"""entity_descriptions.py - Dataclass descriptors like LaMetric."""
from dataclasses import dataclass
from typing import Callable, Awaitable, Any

from homeassistant.components.select import SelectEntityDescription

@dataclass(frozen=True, kw_only=True)
class PixooSelectEntityDescription(SelectEntityDescription):
    """Description for Pixoo select entity."""
    
    # Read function (None for write-only)
    current_fn: Callable[[dict], str] | None = None
    
    # Write function
    select_fn: Callable[[PixooAsync, str], Awaitable[Any]]
    
    # Availability check
    available_fn: Callable[[CoordinatorEntity], bool] = lambda _: True
    
    # State restoration
    restore_state: bool = False


# Write-only entity
CHANNEL_SELECT = PixooSelectEntityDescription(
    key="channel",
    name="Channel",
    icon="mdi:television",
    options=[c.value for c in Channel],
    current_fn=None,  # Write-only
    select_fn=lambda pixoo, opt: pixoo.set_channel(Channel[opt.upper()]),
    restore_state=True,
    available_fn=lambda _: True,
)

# Readable entity
ROTATION_SELECT = PixooSelectEntityDescription(
    key="rotation",
    name="Rotation",
    icon="mdi:rotate-right",
    options=["0", "90", "180", "270"],
    current_fn=lambda data: str(data.get("rotation", 0)),
    select_fn=lambda pixoo, opt: pixoo.set_rotation(int(opt)),
    restore_state=False,
    available_fn=lambda entity: entity.coordinator.last_update_success,
)
```

## Performance Expectations

### Coordinator Update Times

From production logs:
```
System coordinator: 100-200ms every 30s ✅
Weather coordinator: ~150ms every 5min ✅
Gallery coordinator: 36-174ms every 10s ✅
Tool coordinator: 0.000s every 1s ⚠️ (no data, remove)
```

### Entity Availability

**Before (current state)**:
- ❌ All write-only entities: "unavailable"
- ✅ Readable entities: stable
- ⚠️ IP sensor: flapping fixed by caching

**After (expected)**:
- ✅ All write-only entities: "available" always
- ✅ All readable entities: stable
- ✅ No flapping on any entity
- ✅ State persists across HA restarts

## Conclusion

The Pixoo device API has **fundamental write-only limitations** that require architectural changes:

1. **Write-only entities**: Use `RestoreEntity` + local state, NOT `CoordinatorEntity`
2. **Readable entities**: Keep using `CoordinatorEntity`
3. **ToolCoordinator**: Remove (no readable data)
4. **LaMetric patterns**: Apply entity descriptions for cleaner code

**Next Steps**:
1. ✅ Document API capabilities (this file)
2. 🔄 Create implementation plan
3. 🔄 Refactor write-only entities
4. 🔄 Apply LaMetric patterns
5. 🔄 Test and deploy

---

**Generated by**: debug_pixoo_api.py  
**Test Duration**: ~5 seconds  
**Device**: Pixoo-64 at 192.168.188.65  
**Status**: ✅ Complete and accurate
