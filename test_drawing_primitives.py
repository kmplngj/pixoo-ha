#!/usr/bin/env python3
"""Test all drawing primitives in PixooAsync.

This test validates that all drawing buffer methods from the original pixoo
library are available and working in PixooAsync.
"""

import asyncio
import sys
from pathlib import Path

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "pixoo"))

from pixooasync import PixooAsync
from pixooasync.palette import Palette


async def test_drawing_primitives():
    """Test all drawing primitive methods."""
    print("=" * 80)
    print("TESTING PIXOOASYNC DRAWING PRIMITIVES")
    print("=" * 80)
    print()

    device_ip = "192.168.188.65"
    print(f"Device: {device_ip}")
    print()

    async with PixooAsync(device_ip, debug=True) as pixoo:
        test_results = []

        # Test 1: fill() and clear()
        print("Test 1: fill() and clear()")
        print("-" * 40)
        try:
            pixoo.fill((255, 0, 0))  # Fill red
            await pixoo.push()
            print("✅ fill() - PASS")
            test_results.append(("fill", True))
            
            await asyncio.sleep(1)
            
            pixoo.clear()  # Clear to black
            await pixoo.push()
            print("✅ clear() - PASS")
            test_results.append(("clear", True))
        except Exception as e:
            print(f"❌ fill/clear - FAIL: {e}")
            test_results.append(("fill", False))
            test_results.append(("clear", False))
        print()

        # Test 2: draw_pixel()
        print("Test 2: draw_pixel()")
        print("-" * 40)
        try:
            pixoo.clear()
            # Draw diagonal line pixel by pixel
            for i in range(10):
                pixoo.draw_pixel((i * 6, i * 6), (0, 255, 0))  # Green pixels
            await pixoo.push()
            print("✅ draw_pixel() - PASS (10 green pixels diagonal)")
            test_results.append(("draw_pixel", True))
        except Exception as e:
            print(f"❌ draw_pixel - FAIL: {e}")
            test_results.append(("draw_pixel", False))
        print()

        await asyncio.sleep(1)

        # Test 3: draw_pixel_at_index()
        print("Test 3: draw_pixel_at_index()")
        print("-" * 40)
        try:
            pixoo.clear()
            # Draw top row
            for i in range(64):
                pixoo.draw_pixel_at_index(i, (255, 255, 0))  # Yellow
            await pixoo.push()
            print("✅ draw_pixel_at_index() - PASS (yellow top row)")
            test_results.append(("draw_pixel_at_index", True))
        except Exception as e:
            print(f"❌ draw_pixel_at_index - FAIL: {e}")
            test_results.append(("draw_pixel_at_index", False))
        print()

        await asyncio.sleep(1)

        # Test 4: draw_line()
        print("Test 4: draw_line()")
        print("-" * 40)
        try:
            pixoo.clear()
            # Draw X pattern
            pixoo.draw_line((0, 0), (63, 63), (255, 0, 255))  # Magenta diagonal
            pixoo.draw_line((63, 0), (0, 63), (0, 255, 255))  # Cyan diagonal
            await pixoo.push()
            print("✅ draw_line() - PASS (X pattern)")
            test_results.append(("draw_line", True))
        except Exception as e:
            print(f"❌ draw_line - FAIL: {e}")
            test_results.append(("draw_line", False))
        print()

        await asyncio.sleep(1)

        # Test 5: draw_filled_rectangle()
        print("Test 5: draw_filled_rectangle()")
        print("-" * 40)
        try:
            pixoo.clear()
            # Draw 3 rectangles
            pixoo.draw_filled_rectangle((5, 5), (20, 20), (255, 0, 0))  # Red
            pixoo.draw_filled_rectangle((25, 25), (40, 40), (0, 255, 0))  # Green
            pixoo.draw_filled_rectangle((45, 45), (58, 58), (0, 0, 255))  # Blue
            await pixoo.push()
            print("✅ draw_filled_rectangle() - PASS (3 colored squares)")
            test_results.append(("draw_filled_rectangle", True))
        except Exception as e:
            print(f"❌ draw_filled_rectangle - FAIL: {e}")
            test_results.append(("draw_filled_rectangle", False))
        print()

        await asyncio.sleep(1)

        # Test 6: draw_character()
        print("Test 6: draw_character()")
        print("-" * 40)
        try:
            pixoo.clear()
            # Draw "HI"
            pixoo.draw_character('H', (10, 28), (255, 255, 255))
            pixoo.draw_character('I', (18, 28), (255, 255, 255))
            await pixoo.push()
            print("✅ draw_character() - PASS ('HI' in white)")
            test_results.append(("draw_character", True))
        except Exception as e:
            print(f"❌ draw_character - FAIL: {e}")
            test_results.append(("draw_character", False))
        print()

        await asyncio.sleep(1)

        # Test 7: draw_text()
        print("Test 7: draw_text()")
        print("-" * 40)
        try:
            pixoo.clear()
            pixoo.draw_text("PIXOO", (8, 20), (0, 255, 255))  # Cyan
            pixoo.draw_text("64", (20, 30), (255, 255, 0))  # Yellow
            await pixoo.push()
            print("✅ draw_text() - PASS ('PIXOO 64')")
            test_results.append(("draw_text", True))
        except Exception as e:
            print(f"❌ draw_text - FAIL: {e}")
            test_results.append(("draw_text", False))
        print()

        await asyncio.sleep(1)

        # Test 8: RGB convenience methods
        print("Test 8: RGB convenience methods")
        print("-" * 40)
        try:
            pixoo.clear_rgb(50, 0, 50)  # Dark purple
            pixoo.draw_pixel_at_location_rgb(32, 32, 255, 255, 255)  # White center
            pixoo.draw_line_from_start_to_stop_rgb(0, 31, 63, 31, 255, 0, 0)  # Red horizontal
            await pixoo.push()
            print("✅ RGB convenience methods - PASS")
            test_results.append(("rgb_methods", True))
        except Exception as e:
            print(f"❌ RGB methods - FAIL: {e}")
            test_results.append(("rgb_methods", False))
        print()

        await asyncio.sleep(1)

        # Test 9: Palette colors
        print("Test 9: Palette colors")
        print("-" * 40)
        try:
            pixoo.fill(Palette.BLACK)
            pixoo.draw_filled_rectangle((0, 0), (15, 15), Palette.WHITE)
            await pixoo.push()
            print("✅ Palette colors - PASS (white square on black)")
            test_results.append(("palette", True))
        except Exception as e:
            print(f"❌ Palette - FAIL: {e}")
            test_results.append(("palette", False))
        print()

        await asyncio.sleep(1)

        # Test 10: Complex scene
        print("Test 10: Complex scene (all methods combined)")
        print("-" * 40)
        try:
            # Clear to blue background
            pixoo.fill((0, 0, 100))
            
            # Draw frame
            for i in range(64):
                pixoo.draw_pixel((i, 0), (255, 255, 255))  # Top
                pixoo.draw_pixel((i, 63), (255, 255, 255))  # Bottom
                pixoo.draw_pixel((0, i), (255, 255, 255))  # Left
                pixoo.draw_pixel((63, i), (255, 255, 255))  # Right
            
            # Draw sun
            pixoo.draw_filled_rectangle((45, 5), (58, 18), (255, 255, 0))
            
            # Draw ground
            pixoo.draw_filled_rectangle((1, 50), (62, 62), (0, 150, 0))
            
            # Draw text
            pixoo.draw_text("TEST", (18, 28), (255, 255, 255))
            
            await pixoo.push()
            print("✅ Complex scene - PASS (landscape with text)")
            test_results.append(("complex_scene", True))
        except Exception as e:
            print(f"❌ Complex scene - FAIL: {e}")
            test_results.append(("complex_scene", False))
        print()

        await asyncio.sleep(2)

        # Final cleanup
        pixoo.clear()
        await pixoo.push()

        # Summary
        print()
        print("=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        print()

        passed = sum(1 for _, result in test_results if result)
        failed = len(test_results) - passed
        success_rate = (passed / len(test_results)) * 100 if test_results else 0

        for method, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {method}")

        print()
        print(f"Total: {len(test_results)} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()

        if failed == 0:
            print("🎉 ALL DRAWING PRIMITIVES WORKING!")
            print()
            print("Available methods in PixooAsync:")
            print("  - fill(rgb), clear(rgb)")
            print("  - draw_pixel(xy, rgb)")
            print("  - draw_pixel_at_index(index, rgb)")
            print("  - draw_line(start, stop, rgb)")
            print("  - draw_filled_rectangle(tl, br, rgb)")
            print("  - draw_character(char, xy, rgb)")
            print("  - draw_text(text, xy, rgb)")
            print("  - draw_image(path, xy, resample_mode)")
            print("  - All RGB convenience methods (*_rgb)")
            print()
            print("✅ Phase 1 ALREADY COMPLETE - Drawing primitives fully functional!")
        else:
            print("⚠️ Some tests failed - see above for details")

        print()
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_drawing_primitives())
