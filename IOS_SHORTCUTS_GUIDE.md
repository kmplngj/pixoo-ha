# iOS Shortcuts Guide for Pixoo Display

This guide shows how to send images from your iPhone/iPad to your Pixoo display using the new `display_image_data` service.

## Service Overview

**Service**: `pixoo.display_image_data`

**Purpose**: Display images directly from base64 encoded data without needing a URL. Perfect for:
- iOS Shortcuts sending photos
- Uploading images from apps
- Programmatic image generation
- Clipboard images

## iOS Shortcuts Setup

### Method 1: Simple Photo to Pixoo

1. **Open Shortcuts app** on iOS
2. **Create New Shortcut** (tap +)
3. **Add these actions**:

   ```
   Action 1: Select Photos
   - Allow selecting 1 photo
   
   Action 2: Base64 Encode
   - Input: Selected Photos
   - Line Breaks: None
   
   Action 3: Call Service
   - Service: pixoo.display_image_data
   - Entity: light.pixoo_display (your Pixoo entity)
   - image_data: Base64 Encoded
   ```

4. **Name it**: "Send to Pixoo"
5. **Add to Home Screen** for quick access

### Method 2: Share Sheet Integration

Create a shortcut that appears in the iOS Share Sheet:

1. **Create New Shortcut**
2. **Add Receive** action:
   - Type: Images
   
3. **Add Base64 Encode** action:
   - Input: Shortcut Input
   - Line Breaks: None
   
4. **Add Call Service** action:
   - Service: pixoo.display_image_data
   - Entity: light.pixoo_display
   - image_data: Base64 Encoded

5. **Enable "Show in Share Sheet"**
6. **Set icon and name**

Now you can share any image to Pixoo from Photos, Safari, or any app!

### Method 3: Take Photo and Send

1. **Create New Shortcut**
2. **Add these actions**:

   ```
   Action 1: Take Photo
   - Show Camera Preview: Yes
   
   Action 2: Base64 Encode
   - Input: Photo
   - Line Breaks: None
   
   Action 3: Call Service
   - Service: pixoo.display_image_data
   - Entity: light.pixoo_display
   - image_data: Base64 Encoded
   ```

3. **Add to Home Screen** or **Add to Widget**

### Method 4: Clipboard Image

Send whatever image is in your clipboard:

1. **Create New Shortcut**
2. **Add Get Clipboard** action
3. **Add Base64 Encode** action:
   - Input: Clipboard
   - Line Breaks: None
4. **Add Call Service** action:
   - Service: pixoo.display_image_data
   - Entity: light.pixoo_display
   - image_data: Base64 Encoded

## Advanced Examples

### Screenshot to Pixoo

```
1. Take Screenshot
2. Crop Rectangle (select area)
3. Resize Image (64x64 pixels for Pixoo64)
4. Base64 Encode
5. Call pixoo.display_image_data
```

### Random Photo from Album

```
1. Get Photos from Album "Vacation"
2. Get Random Item
3. Resize to 64x64
4. Base64 Encode
5. Call pixoo.display_image_data
```

### Weather Icon Display

```
1. Get Current Weather
2. Get weather condition
3. If Sunny → use sunny.png
4. If Rainy → use rainy.png
5. Base64 Encode image
6. Call pixoo.display_image_data
```

## YAML Automation Example

You can also use this service in Home Assistant automations:

```yaml
alias: "Display Photo from iOS Upload"
trigger:
  - platform: state
    entity_id: input_text.uploaded_image_data
action:
  - service: pixoo.display_image_data
    target:
      entity_id: light.pixoo_display
    data:
      image_data: "{{ states('input_text.uploaded_image_data') }}"
```

## Python Script Example

For advanced users wanting to send images programmatically:

```python
import base64
from pathlib import Path

# Read image file
image_path = Path("my_image.png")
image_bytes = image_path.read_bytes()

# Encode to base64
image_b64 = base64.b64encode(image_bytes).decode('utf-8')

# Call Home Assistant service
hass.services.call(
    'pixoo',
    'display_image_data',
    {
        'entity_id': 'light.pixoo_display',
        'image_data': image_b64
    }
)
```

## Tips and Best Practices

### Image Optimization

1. **Resize images** to 64x64 pixels before sending (for Pixoo64)
   - Saves bandwidth and processing time
   - Better quality when downscaled on device

2. **Use PNG or JPG** format
   - PNG: Better for graphics, icons, pixel art
   - JPG: Better for photos (smaller file size)

3. **Keep file size reasonable**
   - Target: Under 100KB
   - Large base64 strings can cause issues

### iOS Shortcuts Tips

1. **Add error handling**:
   - Use "If" actions to check if photo was selected
   - Show notification on success/failure

2. **Create widget shortcuts**:
   - Add to Home Screen widget for quick access
   - Use icon picker for visual recognition

3. **Use folders**:
   - Group Pixoo shortcuts in a folder
   - Name them clearly: "Photo → Pixoo", "Screenshot → Pixoo"

### Troubleshooting

**Problem**: Image doesn't appear on Pixoo
- Check base64 encoding has no line breaks
- Verify entity_id is correct
- Check Home Assistant logs for errors

**Problem**: "Invalid base64 data" error
- Ensure Base64 Encode action has "Line Breaks: None"
- Check image format is supported (PNG, JPG, GIF)

**Problem**: Image appears distorted
- Resize to 64x64 pixels before encoding
- Use "Aspect Fill" or "Aspect Fit" in resize action

**Problem**: Shortcut times out
- Image might be too large
- Resize or compress before sending
- Check network connection to Home Assistant

## Service Reference

### display_image_data

**Parameters**:
- `entity_id` (required): Target Pixoo entity (e.g., `light.pixoo_display`)
- `image_data` (required): Base64 encoded image string

**Supported Formats**:
- PNG
- JPG/JPEG
- GIF (displays first frame)
- BMP

**Maximum Size**: 10MB encoded (recommended: < 100KB)

**Response**: None (fire-and-forget service)

## Related Services

- `pixoo.display_image` - Display from URL
- `pixoo.display_gif` - Display animated GIF from URL
- `pixoo.clear_display` - Clear the display

## Examples Repository

For more iOS Shortcuts examples, check:
- [Home Assistant Community Forum - Pixoo Shortcuts](https://community.home-assistant.io)
- Share your shortcuts with the community!

---

**Need Help?** 
- Check Home Assistant logs: Settings → System → Logs
- Test with small images first
- Verify base64 encoding with online decoder
