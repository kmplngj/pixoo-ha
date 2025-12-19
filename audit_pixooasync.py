#!/usr/bin/env python3
"""
Comprehensive audit of pixooasync vs original pixoo library.
Tests what features are missing and validates API endpoints.
"""
import asyncio
import json
from pathlib import Path


# Key findings from comparison:
FINDINGS = {
    "device_discovery": {
        "original": "find_local_device_ip() - uses https://app.divoom-gz.com/Device/ReturnSameLANDevice",
        "pixooasync": "❌ MISSING - could use for SSDP discovery enhancement",
        "returns": "IP, MAC, Hardware ID from cloud API"
    },
    "pico_font": {
        "original": "FONT_PICO_8 dict with 3x5 pixel glyphs for all chars",
        "pixooasync": "Need to check if font.py or palette.py exists",
        "note": "Used for draw_character() method"
    },
    "image_resample_modes": {
        "original": "ImageResampleMode enum - PIXEL_ART, etc.",
        "pixooasync": "Need to check enums.py",
        "note": "Uses PIL Image.Resampling for downscaling"
    },
    "drawing_primitives": {
        "original": [
            "draw_character(character, xy, rgb)",
            "draw_text(text, xy, rgb)",  # Uses PICO font
            "draw_pixel(xy, rgb)",
            "draw_line(start_xy, stop_xy, rgb)",
            "draw_filled_rectangle(top_left, bottom_right, rgb)",
            "draw_image(path, xy, resample_mode, pad_resample)"
        ],
        "pixooasync": "Need to check client.py for these methods"
    },
    "missing_methods": {
        "get_device_time": "Device/GetDeviceTime - returns UTCTime, LocalTime",
        "reboot": "Device/SysReboot - reboots the device",
        "get_all_device_configurations": "Channel/GetAllConf - all channel configs",
    }
}


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def check_pixooasync_files():
    """Check what files exist in pixooasync."""
    print_section("PixooAsync File Structure Check")
    
    pixoo_dir = Path("/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo/pixooasync")
    
    if not pixoo_dir.exists():
        print(f"❌ Directory not found: {pixoo_dir}")
        return
    
    files = {
        "client.py": "Main client implementation",
        "models.py": "Pydantic data models",
        "enums.py": "Type-safe enumerations",
        "font.py": "PICO-8 font glyphs (MISSING?)",
        "palette.py": "Color palette definitions",
        "utils.py": "Utility functions",
    }
    
    for filename, description in files.items():
        filepath = pixoo_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {filename:15} - {description} ({size:,} bytes)")
        else:
            print(f"❌ {filename:15} - {description} (NOT FOUND)")


def check_pico_font():
    """Check if PICO font exists in pixooasync."""
    print_section("PICO-8 Font Check")
    
    pixoo_font = Path("/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo/pixooasync/font.py")
    palette_font = Path("/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo/pixooasync/palette.py")
    
    if pixoo_font.exists():
        print(f"✅ Font file exists: {pixoo_font}")
        with open(pixoo_font) as f:
            content = f.read()
            if "FONT_PICO" in content:
                print("✅ FONT_PICO_8 dictionary found")
            else:
                print("⚠️  Font file exists but FONT_PICO_8 not found")
    else:
        print(f"❌ font.py not found in pixooasync")
        print("   Original pixoo has font.py with PICO-8 3x5 glyphs")
        print("   Used by draw_character() and draw_text() methods")


def check_image_resample_modes():
    """Check if ImageResampleMode enum exists."""
    print_section("Image Resample Modes Check")
    
    enums_file = Path("/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo/pixooasync/enums.py")
    
    if enums_file.exists():
        with open(enums_file) as f:
            content = f.read()
            if "ImageResampleMode" in content:
                print("✅ ImageResampleMode enum found")
                # Extract enum values
                import re
                matches = re.findall(r'class ImageResampleMode.*?(?=\nclass|\Z)', content, re.DOTALL)
                if matches:
                    print("\nEnum definition:")
                    print(matches[0][:500])
            else:
                print("❌ ImageResampleMode not found in enums.py")
                print("\nOriginal pixoo uses:")
                print("- ImageResampleMode.PIXEL_ART (for pixel art - nearest neighbor)")
                print("- PIL Image.Resampling modes (NEAREST, BOX, BILINEAR, HAMMING, BICUBIC, LANCZOS)")
    else:
        print(f"❌ enums.py not found")


def check_client_methods():
    """Check what methods exist in PixooAsync client."""
    print_section("PixooAsync Client Methods Audit")
    
    client_file = Path("/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo/pixooasync/client.py")
    
    if not client_file.exists():
        print("❌ client.py not found")
        return
    
    with open(client_file) as f:
        content = f.read()
    
    # Extract method definitions
    import re
    methods = re.findall(r'async def ([a-z_]+)\(', content)
    
    print(f"Found {len(methods)} async methods:\n")
    
    # Categorize methods
    categories = {
        "Drawing": ["draw_", "fill_", "clear_", "push", "reset"],
        "Display": ["display_", "show_"],
        "Text": ["send_text", "clear_text"],
        "Image": ["load_image", "draw_image"],
        "Device Info": ["get_device", "get_network", "get_system"],
        "Configuration": ["set_brightness", "set_rotation", "set_white_balance", "set_timezone"],
        "Channels": ["set_channel", "set_clock", "set_visualizer", "set_custom"],
        "Tools": ["set_timer", "set_alarm", "set_stopwatch", "set_scoreboard", "set_noise_meter"],
        "Animation": ["play_animation", "stop_animation", "get_animation", "send_playlist"],
        "Weather/Time": ["get_weather", "get_time", "set_weather", "set_time"],
        "Other": ["play_buzzer", "initialize", "close"],
    }
    
    categorized = {cat: [] for cat in categories}
    uncategorized = []
    
    for method in methods:
        found = False
        for cat, keywords in categories.items():
            if any(kw in method for kw in keywords):
                categorized[cat].append(method)
                found = True
                break
        if not found:
            uncategorized.append(method)
    
    for cat, methods_list in categorized.items():
        if methods_list:
            print(f"\n{cat}:")
            for method in sorted(set(methods_list)):
                print(f"  - {method}")
    
    if uncategorized:
        print(f"\nUncategorized:")
        for method in sorted(set(uncategorized)):
            print(f"  - {method}")


def compare_with_original():
    """Compare original pixoo methods with pixooasync."""
    print_section("Feature Comparison: Original vs PixooAsync")
    
    original_unique = {
        "Device Discovery": {
            "method": "find_local_device_ip()",
            "api": "https://app.divoom-gz.com/Device/ReturnSameLANDevice",
            "returns": "IP, MAC, HardwareID",
            "priority": "HIGH - needed for sensor fixes"
        },
        "PICO Font Drawing": {
            "methods": "draw_character(), draw_text()",
            "uses": "FONT_PICO_8 dictionary (3x5 pixel glyphs)",
            "priority": "MEDIUM - nice for pixel art text"
        },
        "Advanced Drawing": {
            "methods": "draw_line(), draw_filled_rectangle()",
            "note": "Not in current pixooasync",
            "priority": "LOW - can use buffer directly"
        },
        "Device Time": {
            "method": "get_device_time()",
            "api": "Device/GetDeviceTime",
            "priority": "HIGH - needed for time sensor"
        },
        "Reboot": {
            "method": "reboot()",
            "api": "Device/SysReboot",
            "priority": "LOW - rarely used"
        },
        "Get All Configs": {
            "method": "get_all_device_configurations()",
            "api": "Channel/GetAllConf",
            "priority": "LOW - not essential"
        },
    }
    
    for feature, details in original_unique.items():
        print(f"\n{feature}:")
        for key, value in details.items():
            print(f"  {key}: {value}")


def print_recommendations():
    """Print recommendations for what to add."""
    print_section("Recommendations for PixooAsync Enhancement")
    
    print("""
HIGH PRIORITY (Implement First):
1. Device Discovery API
   - Add method to call app.divoom-gz.com/Device/ReturnSameLANDevice
   - Returns: IP, MAC address, Hardware ID
   - Use for: Fixing MAC address sensor, SSDP discovery enhancement

2. Channel/GetIndex Working API
   - Already works! Just need to add the method
   - Returns: Current channel index (0-3)
   - Use for: Fixing Active Channel sensor

3. Device/GetDeviceTime API
   - Get current device time (UTCTime, LocalTime)
   - Use for: Fixing Device Time sensor

MEDIUM PRIORITY:
4. PICO-8 Font Support
   - Copy FONT_PICO_8 dictionary from original pixoo
   - Add draw_character() and draw_text() methods
   - Use for: Pixel-perfect text rendering

5. ImageResampleMode Enum
   - Already exists? Check enums.py
   - Ensure PIXEL_ART mode for nearest-neighbor scaling
   - Use for: Better pixel art image display

6. Missing Services (from earlier audit):
   - play_animation (HIGH - users want this)
   - send_playlist (HIGH - slideshow feature)
   - set_white_balance (MEDIUM - color calibration)
   - set_time / set_timezone (LOW - usually auto-synced)
   - stop_animation (LOW - animation control)

LOW PRIORITY:
7. Advanced Drawing Primitives
   - draw_line(), draw_filled_rectangle()
   - Can wait - users can use buffer directly

8. Device Management
   - reboot() - rarely needed
   - get_all_device_configurations() - not essential
""")


def main():
    """Main execution."""
    print("\n" + "="*80)
    print("  PIXOOASYNC vs ORIGINAL PIXOO - COMPREHENSIVE AUDIT")
    print("="*80)
    
    check_pixooasync_files()
    check_pico_font()
    check_image_resample_modes()
    check_client_methods()
    compare_with_original()
    print_recommendations()
    
    print("\n" + "="*80)
    print("  AUDIT COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
