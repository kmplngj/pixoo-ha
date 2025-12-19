# Write-Only API Implementation Strategy

## Problem Statement

The Pixoo device API has **write-only operations** for several features:
- **Channel**: Can set via `set_channel()` but cannot read current channel
- **Timer**: Can set via `set_timer()` but cannot read timer state
- **Alarm**: Can set via `set_alarm()` but cannot read alarm state  
- **Stopwatch**: Can start/reset via `set_stopwatch()` but cannot read elapsed time

This creates challenges for Home Assistant integration where users expect to see current state.

## Home Assistant Best Practices Research

Based on research from Home Assistant core repository and developer documentation:

### 1. **Optimistic State Updates** (Recommended)

**Pattern**: Update entity state immediately after sending command, before receiving confirmation.

**Examples from HA Core**:
- **MQTT Lights**: Set `_optimistic = True`, update `_attr_is_on` immediately in `async_turn_on()`
- **Matter Locks**: Use optimistic updates with timeout timer to reset if no acknowledgment
- **Z-Wave JS Lights**: Optimistic brightness updates for better UX
- **Growatt Number**: Update `coordinator.data` after successful write to prevent immediate refresh

**Implementation Pattern**:
```python
async def async_turn_on(self, **kwargs):
    """Turn on with optimistic update."""
    await self.device.turn_on()
    self._attr_is_on = True
    self.async_write_ha_state()
```

### 2. **Assumed State Flag**

**Pattern**: Mark entity with `_attr_assumed_state = True` to indicate state is not from device.

**Examples from HA Core**:
- **ISY994 Backlight Entities**: Use `_assumed_state = True` for write-only settings
- **Xiaomi Aqara Switches**: Update state after `_write_to_hub()` success

**Implementation Pattern**:
```python
class MyEntity(SwitchEntity):
    _attr_assumed_state = True  # Tells HA state is optimistic
    
    @property
    def is_on(self):
        return self._is_on  # Track in memory
```

### 3. **Button vs Switch Decision**

**Use Button When**:
- Action is **momentary** (no persistent state)
- Device doesn't maintain on/off state
- Examples: "Reboot", "Trigger Scene", "Start Timer"

**Use Switch When**:
- Device has **binary state** concept (even if unreadable)
- State persists over time
- Examples: "Power", "Enabled/Disabled", "Alarm On/Off"

**ButtonEntity Characteristics**:
- Tracks only `last_pressed` timestamp
- Implements `async_press()` method
- No state property needed

## Recommended Solution for Pixoo Integration

### Option A: Optimistic State with Memory Tracking (RECOMMENDED)

**Best for**: Channel, Timer, Alarm states

**Implementation**:

1. **Track last-written values in integration memory**:
```python
class PixooDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, ...):
        self._optimistic_channel = None
        self._optimistic_timer_minutes = None
        self._optimistic_alarm_time = None
        self._optimistic_stopwatch_running = False
```

2. **Update optimistically after successful writes**:
```python
async def async_set_channel(self, channel: Channel):
    await self.pixoo.set_channel(channel)
    self._optimistic_channel = channel
    self.async_set_updated_data(self.data)  # Trigger update
```

3. **Mark entities as assumed state**:
```python
class PixooChannelSelect(CoordinatorEntity, SelectEntity):
    _attr_assumed_state = True
    
    @property
    def current_option(self) -> str | None:
        # Return optimistic value from coordinator
        return self.coordinator._optimistic_channel
```

4. **Restore state on startup** (optional enhancement):
```python
async def async_added_to_hass(self):
    """Restore last known state."""
    await super().async_added_to_hass()
    if last_state := await self.async_get_last_state():
        self._optimistic_channel = last_state.state
```

**Pros**:
- ✅ Immediate UI feedback
- ✅ Shows "last known state" to users
- ✅ No confusing "unavailable" entities
- ✅ Standard HA pattern (used in MQTT, ISY994, etc.)
- ✅ Can restore state after HA restart

**Cons**:
- ⚠️ State can drift if changed externally (phone app, physical buttons)
- ⚠️ Lost on HA restart (unless restored from last state)
- ⚠️ Not "true" device state

### Option B: Button Entities for Momentary Actions

**Best for**: Stopwatch start/reset, Timer start, Alarm trigger

**Implementation**:
```python
class PixooTimerStartButton(CoordinatorEntity, ButtonEntity):
    async def async_press(self) -> None:
        """Start timer with last configured minutes."""
        minutes = self.coordinator._optimistic_timer_minutes or 5
        await self.coordinator.pixoo.set_timer(minutes=minutes)
        # No state to track - just an action
```

**When to use**:
- Stopwatch: "Start", "Reset" buttons (not toggle)
- Timer: "Start" button (separate from minute/second number entities)
- Alarm: "Trigger Test" button

**Pros**:
- ✅ Honest about capabilities (no fake state)
- ✅ Clear user intent (press = action)
- ✅ No state drift issues
- ✅ Simple implementation

**Cons**:
- ⚠️ No visual indication of "running" state
- ⚠️ Users can't see if timer/alarm is active
- ⚠️ Less intuitive than toggle switches

### Option C: Hybrid Approach (BEST)

**Combine both strategies**:

1. **Channel Select**: Optimistic state (users need to see current channel)
2. **Timer**: Number entity for minutes + Button to start + Switch for "running" state (optimistic)
3. **Alarm**: Number entities for hour/minute + Switch for "enabled" state (optimistic)
4. **Stopwatch**: Button entities for "Start" and "Reset" only

**Example for Timer**:
```python
# Number entity: Set timer duration (always works)
class PixooTimerMinutesNumber(NumberEntity):
    async def async_set_native_value(self, value: float) -> None:
        self.coordinator._timer_config["minutes"] = int(value)
        
# Switch entity: Start/stop timer (optimistic state)
class PixooTimerSwitch(SwitchEntity):
    _attr_assumed_state = True
    
    async def async_turn_on(self, **kwargs):
        minutes = self.coordinator._timer_config.get("minutes", 5)
        await self.coordinator.pixoo.set_timer(minutes=minutes, seconds=0)
        self._is_on = True  # Optimistic
        self.async_write_ha_state()
    
    async def async_turn_off(self, **kwargs):
        await self.coordinator.pixoo.set_timer(minutes=0, seconds=0)
        self._is_on = False  # Optimistic
        self.async_write_ha_state()
```

## Implementation Plan

### Phase 1: Core Optimistic State (Immediate)

1. **Add memory tracking to coordinators**:
   - `PixooSystemCoordinator`: `_optimistic_channel` field
   - `PixooToolCoordinator`: `_optimistic_timer`, `_optimistic_alarm`, `_optimistic_stopwatch`

2. **Update select entities** (channel, custom_page):
   ```python
   _attr_assumed_state = True
   
   async def async_select_option(self, option: str) -> None:
       await self.pixoo.set_channel(Channel[option.upper()])
       self.coordinator._optimistic_channel = option
       self.async_write_ha_state()
   ```

3. **Update number entities** (timer, alarm):
   ```python
   async def async_set_native_value(self, value: float) -> None:
       await self.pixoo.set_timer(minutes=int(value))
       self.coordinator._optimistic_timer_minutes = int(value)
       self.async_write_ha_state()
   ```

4. **Update switch entities**:
   ```python
   _attr_assumed_state = True
   
   @property
   def is_on(self) -> bool:
       return self.coordinator._optimistic_timer_running
   ```

### Phase 2: State Restoration (Enhancement)

Add `async_added_to_hass()` to restore last state:
```python
async def async_added_to_hass(self):
    await super().async_added_to_hass()
    if last_state := await self.async_get_last_state():
        self.coordinator._optimistic_channel = last_state.state
```

### Phase 3: Documentation (Required)

Update `README.md` and `STATUS_REPORT.md`:
```markdown
## Known Limitations

### Optimistic State Updates

The following entities use **optimistic state** because the Pixoo device 
API does not support reading current state:

- **Channel**: Shows last selected channel (may drift if changed via phone app)
- **Timer**: Shows last set timer duration and running state
- **Alarm**: Shows last set alarm time and enabled state

These entities are marked with `assumed_state=true` in Home Assistant.
State is preserved across restarts but may not reflect external changes.
```

## Code Examples

### Example 1: Channel Select with Optimistic State

```python
class PixooChannelSelect(CoordinatorEntity, SelectEntity):
    """Select entity for channel with optimistic state."""
    
    _attr_assumed_state = True
    _attr_options = ["clock", "cloud", "visualizer", "custom"]
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_channel"
    
    @property
    def current_option(self) -> str | None:
        """Return optimistic channel value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("optimistic_channel")
    
    async def async_select_option(self, option: str) -> None:
        """Set channel optimistically."""
        channel = Channel[option.upper()]
        await self.coordinator.pixoo.set_channel(channel)
        
        # Update optimistic state immediately
        self.coordinator.data["optimistic_channel"] = option
        self.async_write_ha_state()
        
        _LOGGER.debug("Channel set optimistically to %s", option)
    
    async def async_added_to_hass(self):
        """Restore last channel on startup."""
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            # Initialize optimistic state from last known value
            if self.coordinator.data is not None:
                self.coordinator.data["optimistic_channel"] = last_state.state
                _LOGGER.debug("Restored channel: %s", last_state.state)
```

### Example 2: Timer Switch with Optimistic State

```python
class PixooTimerSwitch(CoordinatorEntity, SwitchEntity):
    """Switch entity for timer with optimistic state."""
    
    _attr_assumed_state = True
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_timer"
    
    @property
    def is_on(self) -> bool:
        """Return optimistic timer running state."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("timer_running", False)
    
    async def async_turn_on(self, **kwargs):
        """Start timer with configured duration."""
        # Get duration from number entity state
        minutes = self.coordinator.data.get("timer_minutes", 5)
        seconds = self.coordinator.data.get("timer_seconds", 0)
        
        await self.coordinator.pixoo.set_timer(minutes=minutes, seconds=seconds)
        
        # Update optimistic state
        self.coordinator.data["timer_running"] = True
        self.async_write_ha_state()
        
        _LOGGER.debug("Timer started optimistically: %dm %ds", minutes, seconds)
    
    async def async_turn_off(self, **kwargs):
        """Stop timer."""
        await self.coordinator.pixoo.set_timer(minutes=0, seconds=0)
        
        # Update optimistic state
        self.coordinator.data["timer_running"] = False
        self.async_write_ha_state()
        
        _LOGGER.debug("Timer stopped optimistically")
```

### Example 3: Stopwatch Button (No State Tracking)

```python
class PixooStopwatchStartButton(CoordinatorEntity, ButtonEntity):
    """Button to start stopwatch (no state tracking)."""
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_stopwatch_start"
        self._attr_name = "Start Stopwatch"
        self._attr_icon = "mdi:play"
    
    async def async_press(self) -> None:
        """Start stopwatch."""
        await self.coordinator.pixoo.set_stopwatch(start=True)
        _LOGGER.debug("Stopwatch started")

class PixooStopwatchResetButton(CoordinatorEntity, ButtonEntity):
    """Button to reset stopwatch (no state tracking)."""
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_stopwatch_reset"
        self._attr_name = "Reset Stopwatch"
        self._attr_icon = "mdi:restart"
    
    async def async_press(self) -> None:
        """Reset stopwatch."""
        await self.coordinator.pixoo.set_stopwatch(reset=True)
        _LOGGER.debug("Stopwatch reset")
```

## Comparison Table

| Feature | Current (Broken) | Option A: Optimistic | Option B: Buttons | Option C: Hybrid |
|---------|-----------------|---------------------|-------------------|------------------|
| **Channel** | ❌ Always unavailable | ✅ Shows last set | ⚠️ Not applicable | ✅ Shows last set |
| **Timer** | ❌ Always unavailable | ✅ Shows last set | ⚠️ Only start button | ✅ Duration number + Running switch |
| **Alarm** | ❌ Always unavailable | ✅ Shows last set | ⚠️ Only trigger button | ✅ Hour/minute numbers + Enabled switch |
| **Stopwatch** | ❌ Always unavailable | ⚠️ State drifts | ✅ Start/Reset buttons | ✅ Start/Reset buttons |
| **User Experience** | ❌ Confusing | ✅ Intuitive | ⚠️ Limited | ✅ Best |
| **State Accuracy** | N/A | ⚠️ Can drift | ✅ No false state | ⚠️ Can drift |
| **Implementation** | N/A | ⭐⭐⭐ Medium | ⭐ Easy | ⭐⭐⭐⭐ Complex |

## Recommendation

**Implement Option C: Hybrid Approach**

1. **Channel Select**: Optimistic state (users need visual feedback)
2. **Timer**: 
   - Number entities for minutes/seconds (configuration)
   - Switch entity for running state (optimistic)
3. **Alarm**:
   - Number entities for hour/minute (configuration)
   - Switch entity for enabled state (optimistic)
4. **Stopwatch**: 
   - Button entities only (Start, Reset)
   - No state tracking (too unreliable)

This provides the best balance of:
- ✅ User experience (immediate feedback)
- ✅ Honesty about limitations (`assumed_state` flag)
- ✅ Standard HA patterns (follows Matter, MQTT examples)
- ✅ State persistence (restore after restart)
- ⚠️ Accept state drift (document limitation)

## Next Steps

1. ✅ Research complete
2. 🔄 Update coordinator.py with optimistic state tracking
3. 🔄 Update select.py with `assumed_state = True`
4. 🔄 Update switch.py with optimistic state
5. 🔄 Add state restoration in `async_added_to_hass()`
6. 🔄 Update documentation with limitations
7. 🔄 Test with real device
8. 🔄 Update STATUS_REPORT.md

## References

- Home Assistant Core: [github.com/home-assistant/core](https://github.com/home-assistant/core)
- DeepWiki Search: Write-only API patterns in HA integrations
- Examples: MQTT Light, Matter Lock, ISY994 Backlight, Growatt Number
- Developer Docs: Entity state management, optimistic updates, assumed state
