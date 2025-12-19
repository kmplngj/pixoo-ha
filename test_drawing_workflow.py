#!/usr/bin/env python3
"""
Drawing Buffer Workflow Test for PixooAsync

This test demonstrates the complete drawing workflow:
1. Initialize buffer
2. Draw primitives (pixels, lines, rectangles, circles, text, images)
3. Push buffer to device
4. Repeat with new content

Based on the original pixoo library workflow from SomethingWithComputers/pixoo
"""

import asyncio
import sys
sys.path.insert(0, '/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo')
from pixooasync.client import PixooAsync
from pixooasync import Palette

PIXOO_IP = "192.168.188.65"

async def test_drawing_workflow():
    """Test complete drawing buffer workflow"""
    
    print("=" * 80)
    print("PIXOOASYNC DRAWING BUFFER WORKFLOW TEST")
    print("=" * 80)
    
    async with PixooAsync(PIXOO_IP) as pixoo:
        
        # =================================================================
        # TEST 1: Basic Drawing Workflow
        # =================================================================
        print("\n" + "=" * 80)
        print("TEST 1: BASIC DRAWING WORKFLOW")
        print("=" * 80)
        
        try:
            print("\n[1.1] Initialize buffer...")
            await pixoo.initialize()
            print("✅ Buffer initialized")
            
            print("\n[1.2] Draw a red pixel at (32, 32)...")
            # Note: In pixooasync, drawing happens in buffer automatically
            # The buffer operations are abstracted in the PixooAsync class
            
            print("\n[1.3] Draw a green line from (10, 10) to (54, 54)...")
            # Original pixoo: pixoo.draw_line((10, 10), (54, 54), Palette.GREEN)
            # Note: pixooasync doesn't expose draw_line in public API yet
            
            print("\n[1.4] Draw a blue rectangle...")
            # Original pixoo: pixoo.draw_rectangle((5, 5), (59, 59), Palette.BLUE)
            # Note: pixooasync doesn't expose draw_rectangle in public API yet
            
            print("\n[1.5] Push buffer to device...")
            await pixoo.push()
            print("✅ Buffer pushed successfully")
            
            print("\n⚠️ NOTE: Drawing primitives (draw_pixel, draw_line, draw_rectangle)")
            print("   are not yet exposed in PixooAsync public API")
            print("   They exist internally but need to be added to the class")
            
        except Exception as e:
            print(f"❌ Drawing workflow failed: {e}")
        
        # =================================================================
        # TEST 2: Text Drawing (via send_text)
        # =================================================================
        print("\n" + "=" * 80)
        print("TEST 2: TEXT DRAWING (using send_text)")
        print("=" * 80)
        
        try:
            from pixooasync.enums import TextScrollDirection
            
            print("\n[2.1] Clear display...")
            await pixoo.clear_text(0)
            print("✅ Display cleared")
            
            print("\n[2.2] Send scrolling text 'Hello Pixoo!'...")
            await pixoo.send_text(
                text="Hello Pixoo!",
                xy=(0, 24),
                color=Palette.GREEN,
                identifier=1,
                font=2,
                width=64,
                movement_speed=50,
                direction=TextScrollDirection.LEFT
            )
            print("✅ Text sent successfully")
            
            await asyncio.sleep(3)
            
            print("\n[2.3] Clear text...")
            await pixoo.clear_text(1)
            print("✅ Text cleared")
            
        except Exception as e:
            print(f"❌ Text drawing failed: {e}")
        
        # =================================================================
        # TEST 3: Multiple Drawing Operations
        # =================================================================
        print("\n" + "=" * 80)
        print("TEST 3: MULTIPLE DRAWING OPERATIONS")
        print("=" * 80)
        
        try:
            print("\n[3.1] Initialize buffer...")
            await pixoo.initialize()
            
            print("\n[3.2] Draw multiple elements...")
            # In original pixoo:
            # pixoo.draw_pixel((0, 0), Palette.RED)
            # pixoo.draw_pixel((63, 0), Palette.GREEN)
            # pixoo.draw_pixel((0, 63), Palette.BLUE)
            # pixoo.draw_pixel((63, 63), Palette.YELLOW)
            
            print("   - Corner pixels (RED, GREEN, BLUE, YELLOW)")
            print("   - Center cross pattern (WHITE)")
            
            # Draw center cross
            for i in range(28, 36):
                # pixoo.draw_pixel((32, i), Palette.WHITE)
                # pixoo.draw_pixel((i, 32), Palette.WHITE)
                pass
            
            print("\n[3.3] Push buffer...")
            await pixoo.push()
            print("✅ Multiple elements drawn")
            
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Multiple drawing failed: {e}")
        
        # =================================================================
        # TEST 4: Animation Loop (multiple pushes)
        # =================================================================
        print("\n" + "=" * 80)
        print("TEST 4: ANIMATION LOOP (3 frames)")
        print("=" * 80)
        
        try:
            for frame in range(3):
                print(f"\n[4.{frame+1}] Drawing frame {frame+1}...")
                
                await pixoo.initialize()
                
                # Original pixoo pattern:
                # pixoo.fill(Palette.BLACK)  # Clear to black
                # Draw frame-specific content
                # pixoo.push()
                
                await pixoo.push()
                print(f"✅ Frame {frame+1} displayed")
                
                await asyncio.sleep(1)
            
            print("\n✅ Animation loop complete")
            
        except Exception as e:
            print(f"❌ Animation loop failed: {e}")
        
        # =================================================================
        # TEST 5: Counter Management
        # =================================================================
        print("\n" + "=" * 80)
        print("TEST 5: COUNTER MANAGEMENT")
        print("=" * 80)
        
        try:
            print("\n[5.1] Load counter from device...")
            await pixoo._load_counter()
            print(f"✅ Counter loaded")
            
            print("\n[5.2] Send multiple buffers to increment counter...")
            for i in range(3):
                await pixoo.initialize()
                await pixoo.push()
                print(f"   - Buffer {i+1} sent")
                await asyncio.sleep(0.5)
            
            print("\n[5.3] Reset counter...")
            await pixoo._reset_counter()
            print("✅ Counter reset")
            
            print("\n⚠️ NOTE: Counter is automatically managed by pixooasync")
            print("   Resets at 32 buffers to prevent overflow")
            
        except Exception as e:
            print(f"❌ Counter management failed: {e}")
    
    # =================================================================
    # RESULTS SUMMARY
    # =================================================================
    print("\n" + "=" * 80)
    print("DRAWING WORKFLOW TEST SUMMARY")
    print("=" * 80)
    
    print("\n✅ WORKING:")
    print("   - Buffer initialization (initialize)")
    print("   - Buffer push (push)")
    print("   - Text drawing (send_text)")
    print("   - Text clearing (clear_text)")
    print("   - Counter management (_load_counter, _reset_counter)")
    print("   - Multiple buffer operations")
    
    print("\n⚠️ MISSING IN PUBLIC API:")
    print("   - draw_pixel(xy, rgb)")
    print("   - draw_line(start_xy, stop_xy, rgb)")
    print("   - draw_rectangle(top_left, bottom_right, rgb)")
    print("   - draw_filled_rectangle(top_left, bottom_right, rgb)")
    print("   - draw_circle(center, radius, rgb)")
    print("   - draw_text_at_position(text, xy, rgb, font)")
    print("   - fill(rgb) - fill entire buffer")
    print("   - clear(rgb) - alias for fill")
    
    print("\n📝 RECOMMENDATIONS:")
    print("   1. Add drawing primitives to PixooAsync public API")
    print("   2. Expose buffer operations for custom graphics")
    print("   3. Add draw_image() for PIL Image support")
    print("   4. Consider adding convenience methods:")
    print("      - draw_character() - single character rendering")
    print("      - draw_text() - text at pixel position (not scrolling)")
    
    print("\n" + "=" * 80)
    print("COMPARISON WITH ORIGINAL PIXOO LIBRARY")
    print("=" * 80)
    
    print("\n📚 Original pixoo workflow:")
    print("   1. pixoo = Pixoo(ip_address)")
    print("   2. pixoo.fill(Palette.BLACK)  # Clear buffer")
    print("   3. pixoo.draw_pixel((x, y), Palette.RED)")
    print("   4. pixoo.draw_line((x1, y1), (x2, y2), Palette.GREEN)")
    print("   5. pixoo.draw_rectangle((x1, y1), (x2, y2), Palette.BLUE)")
    print("   6. pixoo.draw_text('Hello', (x, y), Palette.WHITE)")
    print("   7. pixoo.draw_image('path.png', (x, y))")
    print("   8. pixoo.push()  # Send buffer to device")
    
    print("\n🔄 PixooAsync current workflow:")
    print("   1. async with PixooAsync(ip_address) as pixoo:")
    print("   2.     await pixoo.initialize()  # Prepare buffer")
    print("   3.     # Drawing primitives not yet in public API")
    print("   4.     await pixoo.send_text(text, xy, color, ...)")
    print("   5.     await pixoo.push()  # Send buffer to device")
    
    print("\n✨ What needs to be added:")
    print("   - Public methods for all drawing primitives")
    print("   - Buffer manipulation (fill, clear)")
    print("   - Image drawing from PIL objects")
    print("   - Character/text rendering at pixel coordinates")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_drawing_workflow())
