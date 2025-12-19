# Optimistic Entity Availability Issue - Summary

## Problem
All optimistic entities (select, number, switch) show as "unavailable" in Home Assistant despite multiple fix attempts.

## Entities Affected
- **Select (4)**: channel, clock_face, visualizer, custom_page  
- **Number (6)**: timer_minutes, timer_seconds, alarm_hour, alarm_minute, scoreboard_red, scoreboard_blue
- **Switch (5)**: timer, alarm, stopwatch, scoreboard, noise_meter

## Attempted Fixes

### 1. ✅ Set `_attr_assumed_state = True`
- Added to all 15 optimistic entities
- Marks entities as having assumed/optimistic state

### 2. ✅ Fixed state property return values
- Changed return types from `str | None` to `str`
- Changed return types from `float | None` to `float`  
- Changed return types from `bool | None` to `bool`
- All properties return sensible defaults (0, "faces", False) instead of None

### 3. ✅ Set `_attr_available = True` in `__init__`
- Added `self._attr_available = True` after `super().__init__()`
- Should make entities always available according to HA docs

### 4. ✅ Override `available` property
- Added `@property def available(self) -> bool: return self._attr_available`
- Should force availability to True

### 5. ✅ Added debug logging
- Added `_LOGGER.info/debug()` calls in `__init__`, `available`, and `current_option`
- **Result**: No log output at all despite debug logging configured

### 6. ✅ Fixed coordinator caching
- Network data cached between updates
- IP sensor stable (was flapping, now fixed)

### 7. ⚠️  Deleted and re-added integration
- Removed integration from HA UI
- Restarted HA
- Re-added integration
- **Result**: Entities went from "unavailable" → empty string → "unavailable"

## Current State

**File**: `/Volumes/config/custom_components/pixoo/select.py` (and number.py, switch.py)

**PixooChannelSelect example**:
```python
class PixooChannelSelect(PixooEntity, SelectEntity):
    _attr_translation_key = "channel"
    _attr_options = ["faces", "cloud", "visualizer", "custom"]
    _attr_assumed_state = True

    def __init__(self, coordinator, pixoo, entry_id, device_name):
        super().__init__(coordinator, entry_id, device_name)
        self._attr_available = True  # Should make entity available
        self._pixoo = pixoo
        self._attr_name = "Channel"
        _LOGGER.info("PixooChannelSelect.__init__: _attr_available = %s", self._attr_available)

    @property
    def available(self) -> bool:
        """Optimistic entities are always available."""
        result = self._attr_available
        _LOGGER.info("PixooChannelSelect.available called: returning %s", result)
        return result  # Always returns True

    @property
    def current_option(self) -> str:
        """Return the current channel (optimistic)."""
        _LOGGER.debug("PixooChannelSelect.current_option called")
        system_data = self.coordinator.data.get("system") if self.coordinator.data else None
        if system_data is None:
            return "faces"  # Default
        return system_data.get("optimistic_channel") or "faces"
```

## Diagnostic Findings

1. **No log output**: Despite `_LOGGER.info()` calls in `__init__` and `available`, logs show nothing
2. **No errors**: HA logs show no errors or exceptions during integration load
3. **No setup messages**: No "Setup platform pixoo.select" messages in logs
4. **Entities exist**: Test script can query entities, they return "unavailable" state
5. **Non-optimistic entities work**: rotation select (non-optimistic) shows "normal" correctly
6. **Light entity works**: Shows "on" state correctly

## Theories

### Theory 1: CoordinatorEntity Incompatibility
- `CoordinatorEntity.available` may not respect `_attr_available`
- Even with override, something marks entities unavailable
- **Solution**: Refactor optimistic entities to not inherit from CoordinatorEntity

### Theory 2: Logger Configuration Issue
- Debug logging not working despite configuration
- Cannot see what's actually happening in code
- **Solution**: Try `print()` statements or check logger setup

### Theory 3: Entity Registry Caching
- Entity registry may have cached "unavailable" state
- Deletion didn't fully clear cache
- **Solution**: Manually edit `.storage/core.entity_registry`

### Theory 4: State Property Returns Empty
- Despite defaults, properties somehow return empty/invalid values
- HA interprets this as "unavailable"
- **Solution**: Add more defensive checks, ensure non-empty returns

## Next Steps (Priority Order)

### 1. **Check HA UI Directly** 
- Open HA → Settings → Devices & Services → Pixoo
- Check if entities show any error messages
- Look at entity details for availability info

### 2. **Enable More Verbose Logging**
Check `/Volumes/config/configuration.yaml` for logger config:
```yaml
logger:
  default: info
  logs:
    custom_components.pixoo: debug
    homeassistant.helpers.entity: debug  # Add this
    homeassistant.helpers.update_coordinator: debug  # And this
```

### 3. **Try Non-Coordinator Approach**
Refactor one entity (e.g., PixooChannelSelect) to:
- Inherit from `SelectEntity` only (not `PixooEntity`)
- Manually implement `device_info`
- Store state in instance variable
- No coordinator dependency

### 4. **Check Entity Registry**
```bash
ssh homeassistant 'cat /config/.storage/core.entity_registry' | grep pixoo_channel -A20
```
Look for:
- `disabled_by`: Should be `null`
- `hidden_by`: Should be `null`  
- `entity_category`: Should be `null` or appropriate value

### 5. **Nuclear Option: Fresh Install**
1. Backup `/config/.storage/core.entity_registry`
2. Remove all Pixoo entities from registry
3. Remove integration
4. Restart HA
5. Re-add integration from scratch

## Files Modified

- ✅ `custom_components/pixoo/coordinator.py` - Network caching
- ✅ `custom_components/pixoo/select.py` - All fixes applied
- ✅ `custom_components/pixoo/number.py` - All fixes applied
- ✅ `custom_components/pixoo/switch.py` - All fixes applied
- ✅ `custom_components/pixoo/icon.png` - Added logo
- ✅ `custom_components/pixoo/logo.png` - Added logo
- ✅ `/Volumes/config/integrations/logger.yaml` - Debug logging enabled

## Test Command

```bash
cd /Users/jankampling/Repositories/pixoo-ha
./test_pixoo_entities.fish
```

Expected: Optimistic entities show actual values (not "unavailable")  
Actual: All show "unavailable"

---

**Status**: Blocked - needs direct HA UI access or alternative debugging approach
**Last Updated**: 2025-11-15
