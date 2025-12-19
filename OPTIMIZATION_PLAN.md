# Pixoo HA Integration Optimization Plan

**Created**: 2025-01-14  
**Status**: Ready for Implementation  
**Priority**: CRITICAL (fixes all "unavailable" entity issues)  
**Estimated Time**: 4-6 hours

## Context

**Problem**: All optimistic entities (15 entities) show as "unavailable" despite multiple fix attempts.

**Root Cause**: Using `CoordinatorEntity` for write-only APIs is architecturally wrong. These APIs have no readable state, so there's nothing to coordinate.

**Solution**: Separate write-only entities from readable entities, apply LaMetric's proven patterns.

**Reference**: See `PIXOO_API_CAPABILITIES.md` for detailed API analysis.

## Architecture Overview

### Current (Broken)

```
All entities → CoordinatorEntity
    ↓
ToolCoordinator (1s) → No readable data ⚠️
    ↓
Entities show "unavailable" ❌
```

### Target (Working)

```
Readable entities → CoordinatorEntity → SystemCoordinator → Real device data ✅
Write-only entities → RestoreEntity + Local state → No coordinator ✅
```

## Phase 1: Fix Write-Only Entities (CRITICAL)

**Goal**: Make 15 write-only entities show as "available"

**Time**: 2-3 hours

### 1.1 Select Entities (4 entities)

**File**: `custom_components/pixoo/select.py`

**Entities to fix**:
- `channel_select`
- `clock_face_select`
- `visualizer_select`
- `custom_page_select`

**Changes**:
```python
# BEFORE (broken)
class PixooChannelSelect(CoordinatorEntity, SelectEntity):
    _attr_available = True  # Doesn't work!
    
    @property
    def current_option(self):
        return self.coordinator.data.get("channel")  # No data!

# AFTER (working)
class PixooChannelSelect(PixooEntity, SelectEntity, RestoreEntity):
    _attr_assumed_state = True
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._current_option = None  # Local state
    
    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state:
            self._current_option = last_state.state
    
    @property
    def current_option(self):
        return self._current_option
    
    @property
    def available(self):
        return True  # Always available
    
    async def async_select_option(self, option: str):
        await self.pixoo.set_channel(Channel[option.upper()])
        self._current_option = option
        self.async_write_ha_state()
```

**Key Points**:
- Remove `CoordinatorEntity` inheritance
- Add `RestoreEntity` for state persistence
- Store state in `self._current_option`
- Override `available` to return `True`
- Remove `_attr_available = True` (doesn't work)

### 1.2 Number Entities (6 entities)

**File**: `custom_components/pixoo/number.py`

**Entities to fix**:
- `timer_minutes`
- `timer_seconds`
- `alarm_hour`
- `alarm_minute`
- `scoreboard_red`
- `scoreboard_blue`

**Changes**:
```python
# BEFORE (broken)
class PixooTimerMinutesNumber(CoordinatorEntity, NumberEntity):
    @property
    def native_value(self):
        return self.coordinator.data.get("timer_minutes")  # No data!

# AFTER (working)
class PixooTimerMinutesNumber(PixooEntity, NumberEntity, RestoreEntity):
    _attr_assumed_state = True
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._native_value = 0
    
    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and last_state.state:
            self._native_value = float(last_state.state)
    
    @property
    def native_value(self):
        return self._native_value
    
    @property
    def available(self):
        return True
    
    async def async_set_native_value(self, value: float):
        self._native_value = value
        self.async_write_ha_state()
        # Actual device write handled by timer switch
```

### 1.3 Switch Entities (5 entities)

**File**: `custom_components/pixoo/switch.py`

**Entities to fix**:
- `timer`
- `alarm`
- `stopwatch`
- `scoreboard`
- `noise_meter`

**Changes**:
```python
# BEFORE (broken)
class PixooTimerSwitch(CoordinatorEntity, SwitchEntity):
    @property
    def is_on(self):
        return self.coordinator.data.get("timer_running")  # No data!

# AFTER (working)
class PixooTimerSwitch(PixooEntity, SwitchEntity, RestoreEntity):
    _attr_assumed_state = True
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._is_on = False
    
    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()):
            self._is_on = last_state.state == "on"
    
    @property
    def is_on(self):
        return self._is_on
    
    @property
    def available(self):
        return True
    
    async def async_turn_on(self):
        # Get timer values from number entities
        minutes = self._get_timer_minutes()
        seconds = self._get_timer_seconds()
        await self.pixoo.set_timer(minutes, seconds)
        self._is_on = True
        self.async_write_ha_state()
    
    async def async_turn_off(self):
        await self.pixoo.set_timer(0, 0)
        self._is_on = False
        self.async_write_ha_state()
```

### 1.4 Summary

**Changes per entity type**:

| Entity Type | Count | CoordinatorEntity → RestoreEntity | Local State | State Restoration |
|-------------|-------|----------------------------------|-------------|-------------------|
| Select | 4 | ✅ | `_current_option` | ✅ |
| Number | 6 | ✅ | `_native_value` | ✅ |
| Switch | 5 | ✅ | `_is_on` | ✅ |
| **Total** | **15** | **15 entities** | **15 fields** | **15 restore methods** |

**Expected Result**: All 15 entities show as "available" ✅

## Phase 2: Apply LaMetric Patterns (HIGH)

**Goal**: Clean, maintainable code using entity descriptions

**Time**: 2-3 hours

### 2.1 Create Entity Descriptions

**New File**: `custom_components/pixoo/entity_descriptions.py`

```python
"""Entity descriptions for Pixoo integration."""
from dataclasses import dataclass
from typing import Callable, Awaitable, Any

from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.number import NumberEntityDescription
from homeassistant.components.switch import SwitchEntityDescription

@dataclass(frozen=True, kw_only=True)
class PixooSelectEntityDescription(SelectEntityDescription):
    """Description for Pixoo select entity."""
    
    # Read function (None for write-only)
    current_fn: Callable[[dict], str] | None = None
    
    # Write function
    select_fn: Callable[[PixooAsync, str], Awaitable[Any]]
    
    # Availability check
    available_fn: Callable[[Any], bool] = lambda _: True
    
    # State restoration
    restore_state: bool = False


@dataclass(frozen=True, kw_only=True)
class PixooNumberEntityDescription(NumberEntityDescription):
    """Description for Pixoo number entity."""
    
    # Read function (None for write-only)
    value_fn: Callable[[dict], float] | None = None
    
    # Write function
    set_value_fn: Callable[[PixooAsync, float], Awaitable[Any]]
    
    # Availability check
    available_fn: Callable[[Any], bool] = lambda _: True
    
    # State restoration
    restore_state: bool = False


@dataclass(frozen=True, kw_only=True)
class PixooSwitchEntityDescription(SwitchEntityDescription):
    """Description for Pixoo switch entity."""
    
    # Read function (None for write-only)
    is_on_fn: Callable[[dict], bool] | None = None
    
    # Turn on function
    turn_on_fn: Callable[[PixooAsync], Awaitable[Any]]
    
    # Turn off function
    turn_off_fn: Callable[[PixooAsync], Awaitable[Any]]
    
    # Availability check
    available_fn: Callable[[Any], bool] = lambda _: True
    
    # State restoration
    restore_state: bool = False
```

### 2.2 Define Descriptors

**Update**: `custom_components/pixoo/select.py`

```python
"""Select entities with descriptors."""

# Write-only descriptors
SELECT_TYPES = [
    PixooSelectEntityDescription(
        key="channel",
        name="Channel",
        icon="mdi:television",
        options=[c.value for c in Channel],
        current_fn=None,  # Write-only
        select_fn=lambda pixoo, opt: pixoo.set_channel(Channel[opt.upper()]),
        restore_state=True,
        available_fn=lambda _: True,
    ),
    PixooSelectEntityDescription(
        key="clock_face",
        name="Clock Face",
        icon="mdi:clock",
        options=[str(i) for i in range(1, 100)],
        current_fn=None,  # Write-only
        select_fn=lambda pixoo, opt: pixoo.set_clock_face(int(opt)),
        restore_state=True,
        available_fn=lambda _: True,
    ),
]

# Readable descriptors
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

### 2.3 Implement Generic Entity Classes

```python
"""Generic entity using descriptions."""

class PixooSelect(SelectEntity):
    """Generic select entity using description."""
    
    entity_description: PixooSelectEntityDescription
    
    def __init__(self, pixoo, entry, description):
        self.pixoo = pixoo
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        
        if description.restore_state:
            # Write-only: use local state
            self._current_option = None
        else:
            # Readable: use coordinator
            # Setup coordinator here
            pass
    
    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if self.entity_description.restore_state:
            if (last_state := await self.async_get_last_state()):
                self._current_option = last_state.state
    
    @property
    def current_option(self):
        if self.entity_description.restore_state:
            return self._current_option
        else:
            return self.entity_description.current_fn(self.coordinator.data)
    
    @property
    def available(self):
        return self.entity_description.available_fn(self)
    
    async def async_select_option(self, option: str):
        await self.entity_description.select_fn(self.pixoo, option)
        if self.entity_description.restore_state:
            self._current_option = option
            self.async_write_ha_state()
        else:
            await self.coordinator.async_request_refresh()
```

## Phase 3: Coordinator Cleanup (MEDIUM)

**Goal**: Remove unused coordinator, optimize polling

**Time**: 30 minutes

### 3.1 Remove ToolCoordinator

**File**: `custom_components/pixoo/coordinator.py`

**Current**:
```python
class PixooToolCoordinator(DataUpdateCoordinator):
    """Coordinator for tool states (timer, alarm, etc)."""
    
    async def _async_update_data(self):
        # No readable data available!
        _LOGGER.debug("No tool state read methods available")
        return {}
```

**Action**: Delete entire class

**Impact**: 
- Remove coordinator that updates every 1 second but has no data
- Reduces unnecessary device polling
- Simplifies architecture

### 3.2 Update Coordinator List

**File**: `custom_components/pixoo/__init__.py`

**BEFORE**:
```python
coordinators = {
    "device": PixooDeviceCoordinator(...),  # Once
    "system": PixooSystemCoordinator(...),  # 30s
    "weather": PixooWeatherCoordinator(...),  # 5min
    "tool": PixooToolCoordinator(...),  # 1s - REMOVE
    "gallery": PixooGalleryCoordinator(...),  # 10s
}
```

**AFTER**:
```python
coordinators = {
    "device": PixooDeviceCoordinator(...),  # Once
    "system": PixooSystemCoordinator(...),  # 30s
    "weather": PixooWeatherCoordinator(...),  # 5min
    "gallery": PixooGalleryCoordinator(...),  # 10s
}
```

### 3.3 Keep Other Coordinators

| Coordinator | Interval | Data | Status |
|-------------|----------|------|--------|
| Device | Once | device_info | ✅ Keep |
| System | 30s | system_config, brightness, rotation | ✅ Keep |
| Weather | 5min | weather_info | ✅ Keep |
| Gallery | 10s | animations list | ✅ Keep |
| ~~Tool~~ | ~~1s~~ | ~~None~~ | ❌ Remove |

## Phase 4: Testing & Validation (LOW)

**Goal**: Verify all entities work correctly

**Time**: 1 hour

### 4.1 Manual Testing

```bash
# Deploy changes
rsync -av --delete --exclude '__pycache__/' --exclude '*.pyc' \
  /Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo/ \
  /Volumes/config/custom_components/pixoo/

# Restart HA
ssh homeassistant "export SUPERVISOR_TOKEN='$TOKEN' && ha core restart"

# Wait 30 seconds for startup

# Test all entities
fish test_pixoo_entities.fish
```

### 4.2 Validation Checklist

**Write-Only Entities**:
- [ ] All 15 entities show as "available"
- [ ] Can change values via UI
- [ ] State persists across HA restart
- [ ] No "unavailable" flapping
- [ ] Assumed state icon visible

**Readable Entities**:
- [ ] Brightness shows correct value
- [ ] Rotation shows correct value
- [ ] Mirror mode shows correct value
- [ ] IP sensor stable (no flapping)
- [ ] Values update after coordinator refresh

**Coordinators**:
- [ ] Device coordinator runs once
- [ ] System coordinator runs every 30s
- [ ] Weather coordinator runs every 5min
- [ ] Gallery coordinator runs every 10s
- [ ] Tool coordinator removed
- [ ] No errors in logs

### 4.3 Testing Script

**File**: `test_pixoo_entities.fish`

```fish
#!/usr/bin/env fish

echo "Testing Pixoo entities..."

# List all entities
echo "\n=== All Pixoo Entities ==="
ha-cli state list | grep pixoo

# Test write-only select entities
echo "\n=== Testing Write-Only Select Entities ==="
ha-cli state get select.pixoo_channel
ha-cli state get select.pixoo_clock_face
ha-cli state get select.pixoo_visualizer
ha-cli state get select.pixoo_custom_page

# Test write-only number entities
echo "\n=== Testing Write-Only Number Entities ==="
ha-cli state get number.pixoo_timer_minutes
ha-cli state get number.pixoo_timer_seconds
ha-cli state get number.pixoo_alarm_hour
ha-cli state get number.pixoo_alarm_minute
ha-cli state get number.pixoo_scoreboard_red
ha-cli state get number.pixoo_scoreboard_blue

# Test write-only switch entities
echo "\n=== Testing Write-Only Switch Entities ==="
ha-cli state get switch.pixoo_timer
ha-cli state get switch.pixoo_alarm
ha-cli state get switch.pixoo_stopwatch
ha-cli state get switch.pixoo_scoreboard
ha-cli state get switch.pixoo_noise_meter

# Test readable entities
echo "\n=== Testing Readable Entities ==="
ha-cli state get light.pixoo_64
ha-cli state get select.pixoo_rotation
ha-cli state get switch.pixoo_mirror_mode
ha-cli state get sensor.pixoo_ip_address

echo "\n✓ All tests complete"
```

## Implementation Order

### Step-by-Step Execution

1. **Phase 1.1**: Fix select entities (30 min)
   - Modify `select.py`
   - Deploy + test 4 entities
   - Verify all show "available"

2. **Phase 1.2**: Fix number entities (30 min)
   - Modify `number.py`
   - Deploy + test 6 entities
   - Verify all show "available"

3. **Phase 1.3**: Fix switch entities (30 min)
   - Modify `switch.py`
   - Deploy + test 5 entities
   - Verify all show "available"

4. **Phase 3**: Remove ToolCoordinator (15 min)
   - Delete class from `coordinator.py`
   - Remove from `__init__.py`
   - Deploy + verify no errors

5. **Phase 4**: Full testing (1 hour)
   - Test all entities
   - Monitor for 30+ minutes
   - Verify no flapping
   - Test HA restart

6. **Phase 2**: Apply LaMetric patterns (2-3 hours, OPTIONAL)
   - Create entity descriptions
   - Refactor to use descriptors
   - Test again
   - Document patterns

## Expected Results

### Before Optimization

```
✗ 15 entities: "unavailable"
✗ ToolCoordinator: Polling every 1s with no data
✗ Debug messages: "No tool state read methods"
✗ User experience: Broken integration
```

### After Optimization

```
✅ 15 entities: "available" always
✅ ToolCoordinator: Removed
✅ No debug messages
✅ State restoration: Works across HA restarts
✅ User experience: Professional, stable integration
```

## Success Criteria

1. ✅ All 15 write-only entities show "available"
2. ✅ No "unavailable" flapping on any entity
3. ✅ State persists across HA restarts
4. ✅ ToolCoordinator removed
5. ✅ No errors in HA logs
6. ✅ Integration stable for 30+ minutes
7. ✅ Values can be changed via UI
8. ✅ Assumed state icon visible on write-only entities

## Rollback Plan

If optimization fails:

1. **Restore original code**:
   ```bash
   git checkout HEAD -- custom_components/pixoo/
   ```

2. **Deploy original**:
   ```bash
   rsync -av --delete --exclude '__pycache__/' \
     /Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo/ \
     /Volumes/config/custom_components/pixoo/
   ```

3. **Restart HA**:
   ```bash
   ssh homeassistant "export SUPERVISOR_TOKEN='$TOKEN' && ha core restart"
   ```

## Documentation Updates

After successful implementation:

1. **Update `README.md`**:
   - Document write-only entities
   - Explain assumed state
   - Add state restoration notes

2. **Update `agents.md`**:
   - Record optimization session
   - Document LaMetric research
   - Add API testing results

3. **Update `OPTIMISTIC_STATE_SUMMARY.md`**:
   - Mark as superseded
   - Link to new architecture
   - Document lessons learned

## References

- **API Analysis**: `PIXOO_API_CAPABILITIES.md`
- **Debug Script**: `debug_pixoo_api.py`
- **LaMetric Integration**: GitHub - home-assistant/core (lametric/)
- **Previous Attempts**: `OPTIMISTIC_ENTITY_DEBUG_SUMMARY.md`
- **HA Documentation**: developers.home-assistant.io (RestoreEntity, assumed_state)

## Time Estimate

| Phase | Task | Time |
|-------|------|------|
| 1.1 | Fix select entities | 30 min |
| 1.2 | Fix number entities | 30 min |
| 1.3 | Fix switch entities | 30 min |
| 3 | Remove ToolCoordinator | 15 min |
| 4 | Testing & validation | 1 hour |
| **Subtotal** | **Core fixes** | **2.5 hours** |
| 2 | LaMetric patterns (optional) | 2-3 hours |
| **Total** | **With optional refactor** | **4.5-5.5 hours** |

## Next Actions

1. 🔄 **Start Phase 1.1**: Fix select entities
2. 🔄 Deploy + test incrementally
3. 🔄 Continue through phases 1.2, 1.3
4. 🔄 Remove ToolCoordinator
5. 🔄 Full testing
6. ✅ **Celebrate**: All entities working!

---

**Status**: ✅ Plan complete, ready for implementation  
**Priority**: 🔴 CRITICAL  
**Confidence**: 🟢 HIGH (based on LaMetric proven patterns)  
**Risk**: 🟡 LOW (can rollback via git)
