# Service Contracts: Display Services

**Category**: Display Operations  
**Services**: 4 services for showing content on Pixoo device

## pixoo.display_image

**Description**: Display an image from URL or local path on the Pixoo device.

### Parameters

| Parameter | Type | Required | Default | Description | Validation |
|-----------|------|----------|---------|-------------|------------|
| `entity_id` | entity_id | Yes | - | Target Pixoo light entity | Must be valid Pixoo entity |
| `url` | string (URL) | Yes | - | HTTP(S) URL or file:// path | Valid URL format |
| `max_size_mb` | number | No | 10 | Maximum file size in MB | 1-50 |
| `timeout` | number | No | 30 | Download timeout in seconds | 5-120 |

### Voluptuous Schema

```python
SERVICE_DISPLAY_IMAGE = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_URL): cv.url,
    vol.Optional(ATTR_MAX_SIZE_MB, default=10): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=50)
    ),
    vol.Optional(ATTR_TIMEOUT, default=30): vol.All(
        vol.Coerce(int), vol.Range(min=5, max=120)
    ),
})
```

### Service YAML

```yaml
display_image:
  name: Display Image
  description: Display an image from URL or file path on the Pixoo device.
  fields:
    entity_id:
      name: Entity
      description: Pixoo device to display image on
      required: true
      selector:
        entity:
          domain: light
          integration: pixoo
    url:
      name: Image URL
      description: HTTP(S) URL or file:// path to the image
      required: true
      example: "http://example.com/image.jpg"
      selector:
        text:
    max_size_mb:
      name: Max Size (MB)
      description: Maximum allowed file size in megabytes
      default: 10
      selector:
        number:
          min: 1
          max: 50
          unit_of_measurement: "MB"
    timeout:
      name: Timeout
      description: Download timeout in seconds
      default: 30
      selector:
        number:
          min: 5
          max: 120
          unit_of_measurement: "s"
```

### Implementation

```python
async def async_display_image(call: ServiceCall) -> None:
    """Handle display_image service call."""
    url = call.data[ATTR_URL]
    max_size_mb = call.data.get(ATTR_MAX_SIZE_MB, 10)
    timeout = call.data.get(ATTR_TIMEOUT, 30)
    
    # Get target entities
    entities = await async_get_entities(hass, call.data[ATTR_ENTITY_ID])
    
    for entity in entities:
        pixoo: PixooAsync = entity.coordinator.pixoo
        
        # Download image (async)
        image_data = await _download_image(hass, url, max_size_mb, timeout)
        
        # Process image in executor (Pillow operations)
        processed = await hass.async_add_executor_job(
            _resize_image, image_data, entity.device_size
        )
        
        # Display on device
        await pixoo.display_image_from_bytes(processed)
```

---

## pixoo.display_gif

**Description**: Display an animated GIF from URL or local path.

### Parameters

| Parameter | Type | Required | Default | Description | Validation |
|-----------|------|----------|---------|-------------|------------|
| `entity_id` | entity_id | Yes | - | Target Pixoo light entity | Must be valid Pixoo entity |
| `url` | string (URL) | Yes | - | HTTP(S) URL or file:// path to GIF | Valid URL format |
| `max_size_mb` | number | No | 10 | Maximum file size in MB | 1-50 |
| `timeout` | number | No | 30 | Download timeout in seconds | 5-120 |

### Voluptuous Schema

```python
SERVICE_DISPLAY_GIF = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_URL): cv.url,
    vol.Optional(ATTR_MAX_SIZE_MB, default=10): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=50)
    ),
    vol.Optional(ATTR_TIMEOUT, default=30): vol.All(
        vol.Coerce(int), vol.Range(min=5, max=120)
    ),
})
```

### Service YAML

```yaml
display_gif:
  name: Display GIF
  description: Display an animated GIF from URL or file path.
  fields:
    entity_id:
      name: Entity
      description: Pixoo device to display GIF on
      required: true
      selector:
        entity:
          domain: light
          integration: pixoo
    url:
      name: GIF URL
      description: HTTP(S) URL or file:// path to the animated GIF
      required: true
      example: "http://example.com/animation.gif"
      selector:
        text:
    max_size_mb:
      name: Max Size (MB)
      description: Maximum allowed file size in megabytes
      default: 10
      selector:
        number:
          min: 1
          max: 50
          unit_of_measurement: "MB"
    timeout:
      name: Timeout
      description: Download timeout in seconds
      default: 30
      selector:
        number:
          min: 5
          max: 120
          unit_of_measurement: "s"
```

### Implementation

```python
async def async_display_gif(call: ServiceCall) -> None:
    """Handle display_gif service call."""
    url = call.data[ATTR_URL]
    max_size_mb = call.data.get(ATTR_MAX_SIZE_MB, 10)
    timeout = call.data.get(ATTR_TIMEOUT, 30)
    
    entities = await async_get_entities(hass, call.data[ATTR_ENTITY_ID])
    
    for entity in entities:
        pixoo: PixooAsync = entity.coordinator.pixoo
        
        # Download GIF
        gif_data = await _download_image(hass, url, max_size_mb, timeout)
        
        # Validate GIF format and process frames in executor
        processed = await hass.async_add_executor_job(
            _process_gif, gif_data, entity.device_size
        )
        
        # Display on device
        await pixoo.display_gif_from_bytes(processed)
```

---

## pixoo.display_text

**Description**: Display scrolling or static text on the Pixoo device.

### Parameters

| Parameter | Type | Required | Default | Description | Validation |
|-----------|------|----------|---------|-------------|------------|
| `entity_id` | entity_id | Yes | - | Target Pixoo light entity | Must be valid Pixoo entity |
| `text` | string | Yes | - | Text to display | 1-256 characters |
| `x` | number | No | 0 | X position (0-63) | 0-63 |
| `y` | number | No | 0 | Y position (0-63) | 0-63 |
| `color` | string | No | "#FFFFFF" | Text color (hex) | Valid hex color |
| `font_size` | number | No | 16 | Font size in pixels | 8-32 |
| `scroll_direction` | select | No | "left" | Scroll direction | left, right, up, down, none |
| `scroll_speed` | number | No | 50 | Scroll speed (pixels/second) | 10-200 |

### Voluptuous Schema

```python
SERVICE_DISPLAY_TEXT = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_TEXT): cv.string,
    vol.Optional(ATTR_X, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=63)),
    vol.Optional(ATTR_Y, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=63)),
    vol.Optional(ATTR_COLOR, default="#FFFFFF"): cv.string,
    vol.Optional(ATTR_FONT_SIZE, default=16): vol.All(vol.Coerce(int), vol.Range(min=8, max=32)),
    vol.Optional(ATTR_SCROLL_DIRECTION, default="left"): vol.In(["left", "right", "up", "down", "none"]),
    vol.Optional(ATTR_SCROLL_SPEED, default=50): vol.All(vol.Coerce(int), vol.Range(min=10, max=200)),
})
```

### Service YAML

```yaml
display_text:
  name: Display Text
  description: Display scrolling or static text on the Pixoo device.
  fields:
    entity_id:
      name: Entity
      description: Pixoo device to display text on
      required: true
      selector:
        entity:
          domain: light
          integration: pixoo
    text:
      name: Text
      description: Text to display
      required: true
      example: "Hello World!"
      selector:
        text:
          multiline: true
    x:
      name: X Position
      description: Horizontal position (0-63)
      default: 0
      selector:
        number:
          min: 0
          max: 63
    y:
      name: Y Position
      description: Vertical position (0-63)
      default: 0
      selector:
        number:
          min: 0
          max: 63
    color:
      name: Text Color
      description: Text color in hex format
      default: "#FFFFFF"
      selector:
        color_rgb:
    font_size:
      name: Font Size
      description: Font size in pixels
      default: 16
      selector:
        number:
          min: 8
          max: 32
    scroll_direction:
      name: Scroll Direction
      description: Direction to scroll the text
      default: "left"
      selector:
        select:
          options:
            - label: Left
              value: "left"
            - label: Right
              value: "right"
            - label: Up
              value: "up"
            - label: Down
              value: "down"
            - label: Static (no scroll)
              value: "none"
    scroll_speed:
      name: Scroll Speed
      description: Scroll speed in pixels per second
      default: 50
      selector:
        number:
          min: 10
          max: 200
          unit_of_measurement: "px/s"
```

### Implementation

```python
async def async_display_text(call: ServiceCall) -> None:
    """Handle display_text service call."""
    text = call.data[ATTR_TEXT]
    x = call.data.get(ATTR_X, 0)
    y = call.data.get(ATTR_Y, 0)
    color = call.data.get(ATTR_COLOR, "#FFFFFF")
    font_size = call.data.get(ATTR_FONT_SIZE, 16)
    scroll_direction = call.data.get(ATTR_SCROLL_DIRECTION, "left")
    scroll_speed = call.data.get(ATTR_SCROLL_SPEED, 50)
    
    entities = await async_get_entities(hass, call.data[ATTR_ENTITY_ID])
    
    for entity in entities:
        pixoo: PixooAsync = entity.coordinator.pixoo
        
        # Map scroll direction to enum
        direction = TEXT_SCROLL_DIRECTION_MAP.get(scroll_direction, TextScrollDirection.LEFT)
        
        # Display text
        await pixoo.draw_text(
            text=text,
            x=x,
            y=y,
            color=color,
            font_size=font_size,
            scroll_direction=direction,
            scroll_speed=scroll_speed,
        )
```

---

## pixoo.clear_display

**Description**: Clear the display and reset to default channel.

### Parameters

| Parameter | Type | Required | Default | Description | Validation |
|-----------|------|----------|---------|-------------|------------|
| `entity_id` | entity_id | Yes | - | Target Pixoo light entity | Must be valid Pixoo entity |

### Voluptuous Schema

```python
SERVICE_CLEAR_DISPLAY = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
})
```

### Service YAML

```yaml
clear_display:
  name: Clear Display
  description: Clear the display and reset to default channel.
  fields:
    entity_id:
      name: Entity
      description: Pixoo device to clear
      required: true
      selector:
        entity:
          domain: light
          integration: pixoo
```

### Implementation

```python
async def async_clear_display(call: ServiceCall) -> None:
    """Handle clear_display service call."""
    entities = await async_get_entities(hass, call.data[ATTR_ENTITY_ID])
    
    for entity in entities:
        pixoo: PixooAsync = entity.coordinator.pixoo
        
        # Clear display by resetting buffer and switching to clock
        await pixoo.reset_buffer()
        await pixoo.set_channel(Channel.CLOCK)
```

---

## Common Helpers

### Image Download Helper

```python
async def _download_image(
    hass: HomeAssistant,
    url: str,
    max_size_mb: int,
    timeout: int,
) -> bytes:
    """Download image from URL with validation."""
    # Handle file:// URLs
    if url.startswith("file://"):
        file_path = url[7:]  # Remove file:// prefix
        return await hass.async_add_executor_job(_read_file, file_path, max_size_mb)
    
    # Download from HTTP(S)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                response.raise_for_status()
                
                # Validate content type
                content_type = response.headers.get("Content-Type", "")
                if not any(t in content_type for t in ["image/", "application/octet-stream"]):
                    raise ValueError(f"Invalid content type: {content_type}")
                
                # Download with size limit
                content = await response.read()
                
                if len(content) > max_size_mb * 1024 * 1024:
                    raise ValueError(f"Image exceeds {max_size_mb}MB limit")
                
                return content
        except aiohttp.ClientError as err:
            raise HomeAssistantError(f"Failed to download image: {err}") from err

def _read_file(file_path: str, max_size_mb: int) -> bytes:
    """Read file from local filesystem (runs in executor)."""
    if not os.path.isfile(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    file_size = os.path.getsize(file_path)
    if file_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"File exceeds {max_size_mb}MB limit")
    
    with open(file_path, "rb") as f:
        return f.read()
```

### Image Processing Helper

```python
def _resize_image(image_data: bytes, target_size: tuple[int, int]) -> bytes:
    """Resize image to target dimensions (runs in executor)."""
    from PIL import Image
    import io
    
    # Open image
    img = Image.open(io.BytesIO(image_data))
    
    # Resize with high-quality resampling
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    
    # Convert to RGB (remove alpha)
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # Save to bytes
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()

def _process_gif(gif_data: bytes, target_size: tuple[int, int]) -> bytes:
    """Process and resize GIF frames (runs in executor)."""
    from PIL import Image
    import io
    
    # Open GIF
    img = Image.open(io.BytesIO(gif_data))
    
    if not getattr(img, "is_animated", False):
        raise ValueError("File is not an animated GIF")
    
    # Process each frame
    frames = []
    try:
        while True:
            frame = img.copy()
            frame = frame.resize(target_size, Image.Resampling.LANCZOS)
            if frame.mode != "RGB":
                frame = frame.convert("RGB")
            frames.append(frame)
            img.seek(img.tell() + 1)
    except EOFError:
        pass  # End of frames
    
    # Save as GIF
    output = io.BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=img.info.get("duration", 100),
        loop=img.info.get("loop", 0),
    )
    return output.getvalue()
```

---

**Contract Version**: 1.0  
**Last Updated**: 2025-11-10  
**Status**: ✅ Complete
