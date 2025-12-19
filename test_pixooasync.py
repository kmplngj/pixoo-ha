#!/usr/bin/env python3
"""Test PixooAsync methods directly to isolate issues."""

import asyncio
import sys

# Add parent directory to path to import pixooasync
sys.path.insert(0, "/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo")

from pixooasync import PixooAsync
from pixooasync.enums import TextScrollDirection


async def test_pixooasync():
    """Test PixooAsync methods directly."""
    
    host = "192.168.188.65"
    
    print(f"🧪 Testing PixooAsync directly against {host}")
    print("=" * 80)
    
    async with PixooAsync(host) as pixoo:
        
        # Test 1: Get device info
        print("\n✅ Test 1: get_device_info()")
        try:
            device_info = await pixoo.get_device_info()
            print(f"   Device: {device_info}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
            return False
        
        # Test 2: send_text
        print("\n✅ Test 2: send_text()")
        try:
            await pixoo.send_text("Direct Test", (0, 255, 0), TextScrollDirection.LEFT)
            print("   ✅ Text sent successfully")
        except Exception as err:
            print(f"   ❌ Error: {err}")
            print(f"   Type: {type(err)}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(2)
        
        # Test 3: clear_display
        print("\n✅ Test 3: clear_display()")
        try:
            await pixoo.clear_display()
            print("   ✅ Display cleared")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        # Test 4: set_timer
        print("\n✅ Test 4: set_timer()")
        try:
            await pixoo.set_timer(minutes=0, seconds=30, enabled=True)
            print("   ✅ Timer set to 30 seconds")
        except Exception as err:
            print(f"   ❌ Error: {err}")
            print(f"   Method signature: {pixoo.set_timer.__doc__}")
            import traceback
            traceback.print_exc()
        
        # Test 5: set_alarm
        print("\n✅ Test 5: set_alarm()")
        try:
            await pixoo.set_alarm(hour=9, minute=0, enabled=True)
            print("   ✅ Alarm set to 09:00")
        except Exception as err:
            print(f"   ❌ Error: {err}")
            print(f"   Method signature: {pixoo.set_alarm.__doc__}")
            import traceback
            traceback.print_exc()
        
        # Test 6: display_image_from_bytes (with a small test image)
        print("\n✅ Test 6: display_image_from_bytes()")
        try:
            # Create a simple 64x64 red square PNG
            from PIL import Image
            import io
            img = Image.new('RGB', (64, 64), color=(255, 0, 0))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_data = img_bytes.getvalue()
            
            await pixoo.display_image_from_bytes(img_data)
            print("   ✅ Image displayed")
        except Exception as err:
            print(f"   ❌ Error: {err}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(1)
        
        # Test 7: play_buzzer
        print("\n✅ Test 7: play_buzzer()")
        try:
            await pixoo.play_buzzer(active_ms=500, off_ms=500, count=1)
            print("   ✅ Buzzer played")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        print("\n" + "=" * 80)
        print("✅ PixooAsync testing complete!")
        print("\nThis confirms whether the issue is in PixooAsync or the HA integration layer.")
        
        return True


async def main():
    """Run the tests."""
    try:
        success = await test_pixooasync()
        sys.exit(0 if success else 1)
    except Exception as err:
        print(f"\n❌ Fatal error: {err}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
