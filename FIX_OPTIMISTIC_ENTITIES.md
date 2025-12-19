# Fix for Optimistic Entity Availability

## Root Cause
Optimistic entities (channel, timer, alarm, scoreboard, etc.) show "unavailable" because:
1. They return `None` from their state properties when optimistic values are None
2. Home Assistant treats `None` state as "unavailable"
3. Even though we added defaults (0, "faces", False), entities still unavailable

## Real Issue
The base `PixooEntity.available` property returns `self.coordinator.last_update_success`, which is correct.
But optimistic entities that access coordinator data via properties like `self.coordinator.data.get("system")` 
may find the data dict exists but specific keys return None, then the property returns None, making entity unavailable.

## Solution (HA Best Practices)
Per HA developer documentation:
1. **Never return None from state properties** - return actual values or use STATE_UNKNOWN constant
2. **Optimistic entities should override `available`** to be True when coordinator succeeds
3. **Use `_attr_assumed_state = True`** on all optimistic entities
4. **Return sensible defaults** (0 for numbers, first option for selects, False for switches)

## Files to Fix

### 1. select.py
Add to ALL optimistic select entities:
- `_attr_assumed_state = True`
- Override `available` property to return `self.coordinator.last_update_success`
- Ensure `current_option` never returns None (return default value)

Affected classes:
- PixooChannelSelect ✅ (partially done)
- PixooClockFaceSelect ❌
- PixooVisualizerSelect ❌
- PixooCustomPageSelect ❌

### 2. number.py  
Add to ALL optimistic number entities:
- `_attr_assumed_state = True`
- Override `available` property
- Ensure `native_value` returns 0 instead of None ✅ (already done)

Affected classes:
- PixooTimerMinutesNumber
- PixooTimerSecondsNumber
- PixooAlarmHourNumber
- PixooAlarmMinuteNumber
- PixooScoreboardRedNumber
- PixooScoreboardBlueNumber

### 3. switch.py
Add to ALL optimistic switch entities:
- `_attr_assumed_state = True` ✅ (already done)
- Override `available` property ❌
- Ensure `is_on` returns False instead of None ✅ (already done)

Affected classes:
- PixooTimerSwitch
- PixooAlarmSwitch
- PixooStopwatchSwitch
- PixooScoreboardSwitch  
- PixooNoiseMeterSwitch

## Implementation Pattern

```python
class MyOptimisticEntity(PixooEntity, SelectEntity):
    \"\"\"Optimistic entity example.\"\"\"
    
    _attr_assumed_state = True  # Mark as optimistic
    
    @property
    def available(self) -> bool:
        \"\"\"Return True if entity is available.
        
        Optimistic entities are available as long as the coordinator
        is functioning, regardless of whether specific data fields are None.
        \"\"\"
        return self.coordinator.last_update_success
    
    @property
    def current_option(self) -> str:
        \"\"\"Return current value - NEVER return None.\"\"\"
        value = self.coordinator.data.get("value") if self.coordinator.data else None
        return value if value is not None else "default"  # Always return a value
```

## Why This Works
1. Coordinator succeeds even with None optimistic values (returns empty dict)
2. Entity `available` = True because coordinator succeeded
3. Entity state properties return sensible defaults, not None
4. Entity shows in UI with default value, not "unavailable"
5. Users can then set values which become the new optimistic state
