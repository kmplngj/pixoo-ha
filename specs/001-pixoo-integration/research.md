# Research Phase: Pixoo Integration

**Date**: 2025-11-10  
**Feature**: Divoom Pixoo Home Assistant Integration  
**Branch**: 001-pixoo-integration

## Research Topics

### 1. Home Assistant Config Flow Patterns

**Status**: ✅ RESEARCHED

**Question**: What are the best practices for config flow with SSDP discovery?

**Findings**:
- SSDP discovery requires `manifest.json` configuration with `ssdp` key
- Discovery flow should populate unique_id from device MAC address
- Config flow should support both discovery and manual entry
- Options flow allows runtime feature toggles without re-adding device
- Example: ESPHome integration uses SSDP with fallback to manual IP entry

**References**:
- Home Assistant Developer Docs: Config Flow
- Example integrations: esphome, hue, sonos (SSDP discovery)

**Impact on Spec**: FR-002 (SSDP discovery), FR-005 (feature toggles)

**Implementation Notes**:
```python
# manifest.json
{
  "ssdp": [
    {
      "manufacturer": "Divoom",
      "modelName": "Pixoo64"
    }
  ]
}

# config_flow.py
async def async_step_ssdp(self, discovery_info: SsdpServiceInfo):
    # Extract IP from discovery_info.ssdp_location
    # Set unique_id from MAC or serial
    # Show confirmation form
```

### 2. Device Discovery Methods for Pixoo

**Status**: ✅ RESEARCHED

**Question**: Does pixooasync support device discovery, or do we need to implement SSDP ourselves?

**Findings**:
- pixooasync does NOT include discovery methods
- Divoom Pixoo devices broadcast SSDP advertisements on local network
- SSDP service type: `urn:schemas-upnp-org:device:Basic:1`
- Manufacturer: "Divoom"
- Model: "Pixoo64" / "Pixoo32" / "Pixoo16"
- HA provides `homeassistant.helpers.ssdp` for SSDP handling

**References**:
- pixooasync package inspection: No discovery methods in client.py
- Divoom API research: SSDP confirmed in community forum threads
- HA SSDP helper: `homeassistant.helpers.ssdp.async_register_callback`

**Impact on Spec**: FR-002 implementation approach

**Implementation Notes**:
- Use HA's built-in SSDP integration (declare in manifest.json)
- Parse SSDP location header for device IP
- Validate connectivity by calling `pixoo.get_device_info()`
- Store IP in config entry data

### 3. Coordinator Update Strategies for Tiered Polling

**Status**: ✅ RESEARCHED

**Question**: How do we implement different polling intervals for different sensor types?

**Findings**:
- HA's `DataUpdateCoordinator` supports single interval only
- Solution: Create multiple coordinators with different intervals
- Alternative: Use single coordinator with internal timing logic
- Best practice: Group sensors by update frequency into separate coordinators

**References**:
- Home Assistant Developer Docs: Data Update Coordinator
- Example: Neato integration uses multiple coordinators
- Example: Tesla integration uses tiered polling with internal timing

**Impact on Spec**: FR-046-055 (sensor polling), Internal Components architecture

**Implementation Notes**:
```python
# Option A: Multiple coordinators (cleaner)
class PixooDeviceCoordinator(DataUpdateCoordinator):
    """Updates device info once on startup."""
    update_interval = None  # Manual updates only

class PixooNetworkCoordinator(DataUpdateCoordinator):
    """Updates network/system every 30-60s."""
    update_interval = timedelta(seconds=60)

class PixooToolCoordinator(DataUpdateCoordinator):
    """Updates active tool state every 1s."""
    update_interval = timedelta(seconds=1)

# Option B: Single coordinator with internal timing
class PixooCoordinator(DataUpdateCoordinator):
    """Unified coordinator with tiered updates."""
    update_interval = timedelta(seconds=1)  # Minimum interval
    
    async def _async_update_data(self):
        now = time.time()
        data = {}
        
        # Tool state: every 1s
        data["tool"] = await self.pixoo.get_current_channel()
        
        # Network/system: every 60s
        if now - self._last_network_update > 60:
            data["network"] = await self.pixoo.get_network_status()
            self._last_network_update = now
        
        # Weather: every 5min
        if now - self._last_weather_update > 300:
            data["weather"] = await self.pixoo.get_weather()
            self._last_weather_update = now
        
        return data
```

**Recommendation**: Option A (multiple coordinators) for clarity and separation of concerns

### 4. Button Entity Implementation Patterns

**Status**: ✅ RESEARCHED

**Question**: How do button entities work in HA, and what's the pattern for device-triggered buttons?

**Findings**:
- Button entities are stateless - pressing triggers action, no persistent state
- Use `ButtonEntity` base class from `homeassistant.components.button`
- `async_press()` method executes the action
- Button appears in UI as pressable button, shows last-pressed timestamp
- Example: Neato vacuum "Dismiss Alert" button clears device notifications

**References**:
- HA Developer Docs: Button Entity
- Neato integration: `button.py` with dismiss_alert button
- ESPHome integration: Multiple button entities for device actions

**Impact on Spec**: FR-035 (notification dismissal), Button Entities subsection

**Implementation Notes**:
```python
class PixooDismissNotificationButton(PixooEntity, ButtonEntity):
    """Button to dismiss notification on Pixoo device."""
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Dismiss Notification"
        self._attr_unique_id = f"{entry.entry_id}_dismiss_notification"
        self._attr_icon = "mdi:bell-off"
    
    async def async_press(self) -> None:
        """Handle button press."""
        # Switch to previous channel stored in entry data
        previous_channel = self.coordinator.data.get("previous_channel", Channel.CLOCK)
        await self.coordinator.pixoo.set_channel(previous_channel)
        
        # Request coordinator refresh
        await self.coordinator.async_request_refresh()
```

### 5. Service Schema Validation with Pydantic

**Status**: ✅ RESEARCHED

**Question**: Can we use Pydantic models for service parameter validation in HA?

**Findings**:
- HA uses voluptuous for service schema validation (not Pydantic)
- Pydantic models can be used internally for data validation
- Service schemas defined in `services.yaml` use voluptuous syntax
- Workaround: Define voluptuous schema, convert to Pydantic internally for validation

**References**:
- HA Developer Docs: Services
- Voluptuous documentation
- Integration example: HomeKit uses voluptuous schemas with internal Pydantic models

**Impact on Spec**: FR-026 (Pydantic validation), Service definitions

**Implementation Notes**:
```python
# services.yaml (voluptuous)
display_image:
  description: Display an image on the Pixoo device
  fields:
    entity_id:
      description: Entity ID of the Pixoo device
      required: true
      selector:
        entity:
          domain: light
    url:
      description: URL of the image to display
      required: true
      example: "http://example.com/image.jpg"
    max_size_mb:
      description: Maximum file size in MB
      default: 10
      selector:
        number:
          min: 1
          max: 50

# __init__.py (Pydantic validation internally)
from pixooasync.models import ImageConfig

async def async_display_image(call: ServiceCall) -> None:
    """Handle display_image service call."""
    # Extract parameters
    url = call.data["url"]
    max_size_mb = call.data.get("max_size_mb", 10)
    
    # Validate with Pydantic (optional, for extra safety)
    config = ImageConfig(url=url, max_size_mb=max_size_mb)
    
    # Execute
    await pixoo.display_image_from_url(config.url, max_size_bytes=config.max_size_mb * 1024 * 1024)
```

**Recommendation**: Use voluptuous for service schemas (HA standard), optionally use Pydantic internally for complex validation

### 6. Image Processing with Pillow in Async Context

**Status**: ✅ RESEARCHED

**Question**: How do we safely use Pillow (synchronous) in HA's async context?

**Findings**:
- Pillow operations are CPU-bound and synchronous (blocking)
- HA provides `hass.async_add_executor_job()` to run sync code in thread pool
- Image downloads should use aiohttp (async), processing in executor
- Best practice: Download async → process in executor → upload async

**References**:
- HA Developer Docs: Working with async
- Camera integration: Uses Pillow with `async_add_executor_job`
- aiohttp docs: Downloading large files

**Impact on Spec**: FR-006 (image download), FR-020 (Pillow downsampling)

**Implementation Notes**:
```python
async def async_display_image_from_url(self, hass, pixoo: PixooAsync, url: str):
    """Download, process, and display image from URL."""
    
    # Step 1: Download image (async)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.content_type not in ["image/jpeg", "image/png", "image/gif"]:
                raise ValueError(f"Invalid content type: {response.content_type}")
            
            content = await response.read()
            
            if len(content) > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError("Image exceeds 10MB limit")
    
    # Step 2: Process image (sync in executor)
    def _process_image(data: bytes) -> bytes:
        """Resize image to 64x64 using Pillow."""
        from PIL import Image
        import io
        
        # Open image
        img = Image.open(io.BytesIO(data))
        
        # Resize to device dimensions (64x64 for Pixoo64)
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        
        # Convert to RGB (remove alpha if present)
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85)
        return output.getvalue()
    
    processed_data = await hass.async_add_executor_job(_process_image, content)
    
    # Step 3: Upload to device (async)
    await pixoo.display_image_from_bytes(processed_data)
```

**Recommendation**: Always use executor for Pillow operations, validate content before processing

## Research Summary

**Total Topics**: 6  
**Status**: All topics researched ✅

**Key Decisions**:
1. **Discovery**: Use HA's SSDP integration with manifest.json configuration
2. **Coordinators**: Implement multiple coordinators for tiered polling (cleaner architecture)
3. **Button Entities**: Use ButtonEntity base class with async_press() method
4. **Service Schemas**: Use voluptuous (HA standard), optionally Pydantic internally
5. **Image Processing**: Download with aiohttp, process with Pillow in executor
6. **Polling Strategy**: Multiple coordinators (device, network, tool, weather) with appropriate intervals

**Constitution Compliance**:
- ✅ All decisions align with Async-First principle (executor for blocking ops)
- ✅ All decisions use HA native patterns (coordinators, config flow, SSDP)
- ✅ All decisions leverage pixooasync package (no protocol reimplementation)

**Next Phase**: Data Model Definition (Phase 1)

---

**Research completed**: 2025-11-10  
**Ready for data model design**: ✅
