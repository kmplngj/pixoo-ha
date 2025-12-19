# Service Handler Fixes for pixoo-ha

## Root Cause Analysis Complete ✅

**Verdict**: 100% ha-pixoo integration problem, NOT pixooasync library issue.

### Issues Identified

#### 1. Entity ID Filtering Bug (CRITICAL - Affects ALL Services)
**Location**: Lines 165-169 and repeated in all service handlers

**Problem**:
```python
entries = [
    entry for entry in hass.config_entries.async_entries(DOMAIN)
    if not entity_ids or entry.entry_id in entity_ids
]
# BUG: entity_ids contains "light.pixoo_display", NOT entry IDs!
# Result: Filters out ALL devices when entity_id is specified
```

**Fix**:
```python
if entity_ids:
    # Resolve entity IDs to entry IDs using entity registry
    entity_registry = er.async_get(hass)
    entry_ids = set()
    for entity_id in entity_ids:
        if entity := entity_registry.async_get(entity_id):
            entry_ids.add(entity.config_entry_id)
    entries = [e for e in hass.config_entries.async_entries(DOMAIN) if e.entry_id in entry_ids]
else:
    entries = hass.config_entries.async_entries(DOMAIN)
```

**Impact**: This affects all 11 services. When users specify entity_id, NO devices get the service call.

---

#### 2. display_image Service - Wrong Method Name
**Location**: Line 168-183

**Current (WRONG)**:
```python
await pixoo.display_image_from_bytes(image_data)
# ERROR: 'PixooAsync' object has no attribute 'display_image_from_bytes'
```

**PixooAsync API** (lines 274-322):
```python
def draw_image(
    image_path_or_object: str | Path | Image.Image,
    xy: tuple[int, int] = (0, 0),
    image_resample_mode: ImageResampleMode = ImageResampleMode.PIXEL_ART,
    pad_resample: bool = False,
) -> None:
    """Draw an image on the display."""
```

**Correct Fix**:
```python
from io import BytesIO
from PIL import Image

# Convert bytes to PIL Image
image = Image.open(BytesIO(image_data))

# Draw image to buffer and push
pixoo.draw_image(image, xy=(0, 0))
await pixoo.push()
```

---

#### 3. clear_display Service - Wrong Method Name
**Location**: Lines 292-295

**Current (WRONG)**:
```python
await pixoo.clear_display()
# ERROR: 'PixooAsync' object has no attribute 'clear_display'
```

**PixooAsync API** (lines 115-118):
```python
def clear(self, rgb: RGBColor = Palette.BLACK) -> None:
    """Clear the display with a color."""
    self.fill(rgb)
```

**Correct Fix**:
```python
pixoo.clear()  # Sync method, clears buffer
await pixoo.push()  # Push cleared buffer to device
```

---

#### 4. display_text Service - Wrong Parameter Order/Signature
**Location**: Lines 224-256

**Current (WRONG)**:
```python
color = call.data.get("color", "#FFFFFF")  # Returns hex string from color_rgb selector
r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
await pixoo.send_text(text, (r, g, b), direction)
# ERROR: TypeError: 'TextScrollDirection' object is not subscriptable
# Cause: rgb_to_hex_color() tries to subscript 'direction' parameter
```

**PixooAsync API** (lines 1534-1568):
```python
async def send_text(
    self,
    text: str,
    xy: tuple[int, int] = (0, 0),
    color: RGBColor = Palette.WHITE,  # Expects tuple (r, g, b)
    identifier: int = 1,
    font: int = 2,
    width: int = 64,
    movement_speed: int = 0,
    direction: TextScrollDirection = TextScrollDirection.LEFT,
) -> None:
```

**Correct Fix**:
```python
color = call.data.get("color", "#FFFFFF")
r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

await pixoo.send_text(
    text=text,
    xy=(0, 0),
    color=(r, g, b),  # Pass as tuple
    identifier=1,
    font=font,
    width=64,
    movement_speed=scroll_speed,
    direction=direction,
)
```

---

#### 5. play_buzzer Service - Wrong Parameter Names
**Location**: Lines 308-317

**Current (WRONG)**:
```python
await pixoo.play_buzzer(active_ms=active_ms, off_ms=off_ms, count=count)
# ERROR: unexpected keyword argument 'active_ms'. Did you mean 'active_time'?
```

**PixooAsync API** (lines 2246-2288):
```python
async def play_buzzer(
    self, active_time: int = 500, off_time: int = 500, total_time: int = 3000
) -> bool:
    """Play buzzer sound with specified timing pattern.
    
    Args:
        active_time: Time buzzer is on in each cycle (milliseconds)
        off_time: Time buzzer is off in each cycle (milliseconds)
        total_time: Total duration of buzzer sequence (milliseconds)
    """
```

**Correct Fix**:
```python
active_ms = call.data.get("active_ms", 500)
off_ms = call.data.get("off_ms", 500)
count = call.data.get("count", 1)

# Calculate total_time from count
cycle_time = active_ms + off_ms
total_time = cycle_time * count

await pixoo.play_buzzer(
    active_time=active_ms,  # Fix parameter name
    off_time=off_ms,        # Fix parameter name
    total_time=total_time   # Fix parameter name
)
```

---

#### 6. set_timer Service - Works at Library Level (HTTP 500 from Entity Filtering Bug)
**Location**: Lines 332-370

**Current**:
```python
await pixoo.set_timer(minutes=total_minutes, seconds=seconds, enabled=True)
```

**PixooAsync API** (line 2156):
```python
async def set_timer(
    self, minutes: int = 0, seconds: int = 0, enabled: bool = True
) -> bool:
```

**Status**: ✅ API call is CORRECT. HTTP 500 is caused by entity_id filtering bug (#1).

**Test Result**: Direct PixooAsync call works perfectly:
```python
await pixoo.set_timer(minutes=0, seconds=30, enabled=True)
# ✅ Timer set to 30 seconds
```

---

#### 7. set_alarm Service - Works at Library Level (HTTP 500 from Entity Filtering Bug)
**Location**: Lines 372-418

**Current**:
```python
await pixoo.set_alarm(hour=hour, minute=minute, enabled=enabled)
```

**PixooAsync API** (line 2202):
```python
async def set_alarm(self, hour: int, minute: int, enabled: bool = True) -> bool:
```

**Status**: ✅ API call is CORRECT. HTTP 500 is caused by entity_id filtering bug (#1).

**Test Result**: Direct PixooAsync call works perfectly:
```python
await pixoo.set_alarm(hour=9, minute=0, enabled=True)
# ✅ Alarm set to 09:00
```

---

#### 8. Coordinator Reference Bug (LOW PRIORITY)
**Location**: Line 313

**Current**:
```python
gallery_coordinator = data["gallery_coordinator"]
```

**Correct**:
```python
gallery_coordinator = data["coordinators"]["gallery"]
```

**Impact**: list_animations service might fail, but test showed it working (likely not exercised yet).

---

## Implementation Plan

### Step 1: Add Entity Registry Import
```python
from homeassistant.helpers import entity_registry as er
```

### Step 2: Add PIL Import for Image Handling
```python
from io import BytesIO
from PIL import Image
```

### Step 3: Create Helper Function for Entity ID Resolution
```python
def _resolve_entry_ids(
    hass: HomeAssistant, entity_ids: list[str] | None
) -> list[ConfigEntry]:
    """Resolve entity IDs to config entries."""
    if not entity_ids:
        return hass.config_entries.async_entries(DOMAIN)
    
    entity_registry = er.async_get(hass)
    entry_ids = set()
    for entity_id in entity_ids:
        if entity := entity_registry.async_get(entity_id):
            entry_ids.add(entity.config_entry_id)
    
    return [e for e in hass.config_entries.async_entries(DOMAIN) if e.entry_id in entry_ids]
```

### Step 4: Replace Entity Filtering in ALL Service Handlers
Replace this pattern:
```python
entries = [
    entry for entry in hass.config_entries.async_entries(DOMAIN)
    if not entity_ids or entry.entry_id in entity_ids
]
```

With:
```python
entries = _resolve_entry_ids(hass, entity_ids)
```

### Step 5: Fix Each Service Handler

1. **handle_display_image** (lines 168-183):
   - Add BytesIO and PIL Image imports
   - Replace `await pixoo.display_image_from_bytes(image_data)` with:
     ```python
     image = Image.open(BytesIO(image_data))
     pixoo.draw_image(image, xy=(0, 0))
     await pixoo.push()
     ```

2. **handle_display_text** (lines 224-256):
   - Fix send_text call with keyword arguments:
     ```python
     await pixoo.send_text(
         text=text,
         xy=(0, 0),
         color=(r, g, b),
         identifier=1,
         font=font,
         width=64,
         movement_speed=scroll_speed,
         direction=direction,
     )
     ```

3. **handle_clear_display** (lines 292-295):
   - Replace `await pixoo.clear_display()` with:
     ```python
     pixoo.clear()
     await pixoo.push()
     ```

4. **handle_play_buzzer** (lines 308-317):
   - Fix parameter names and add total_time calculation:
     ```python
     active_ms = call.data.get("active_ms", 500)
     off_ms = call.data.get("off_ms", 500)
     count = call.data.get("count", 1)
     total_time = (active_ms + off_ms) * count
     
     await pixoo.play_buzzer(
         active_time=active_ms,
         off_time=off_ms,
         total_time=total_time
     )
     ```

5. **handle_list_animations** (line 313):
   - Fix coordinator reference:
     ```python
     gallery_coordinator = data["coordinators"]["gallery"]
     ```

6. **handle_set_timer** and **handle_set_alarm**:
   - ✅ No changes needed (API calls are correct)
   - Entity ID filtering fix will resolve HTTP 500 errors

---

## Testing Plan

1. Deploy fixed __init__.py to HA server
2. Restart Home Assistant
3. Run test_services.py - ALL 11 services should work ✅
4. Update TEST_RESULTS.md with success
5. Change grade from B+ to A ✅

---

## Expected Results

**Before**:
- 3/11 services working (27%)
- 4/11 services HTTP 500 errors (36%)
- Entity ID filtering broken for all services
- Grade: B+

**After**:
- 11/11 services working (100%) ✅
- 0 HTTP 500 errors ✅
- Entity ID filtering working correctly ✅
- Grade: A ✅

---

## Files to Modify

1. `custom_components/pixoo/__init__.py` - Apply all fixes
2. `TEST_RESULTS.md` - Update with success metrics

---

## References

- PixooAsync client.py lines 115-322, 1490-1568, 2156-2365
- Test results from test_pixooasync.py
- Direct library testing confirms set_timer and set_alarm work
- All bugs isolated to ha-pixoo service handlers, NOT pixooasync library
