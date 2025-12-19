#!/usr/bin/env python3
"""
Comprehensive PixooAsync API Test (CORRECTED)
Tests all 40+ methods with actual method names from client.py
"""

import asyncio
import sys
sys.path.insert(0, '/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo')
from pixooasync.client import PixooAsync
from pixooasync.enums import Channel, Rotation, TextScrollDirection
from pixooasync.models import PlaylistItem, Location

PIXOO_IP = "192.168.188.65"

async def test_pixooasync():
    """Test all PixooAsync methods"""
    
    results = {
        "passed": [],
        "failed": [],
        "skipped": []
    }
    
    async with PixooAsync(PIXOO_IP) as pixoo:
        print("=" * 80)
        print("PIXOOASYNC COMPREHENSIVE API TEST (CORRECTED)")
        print("=" * 80)
        
        # =================================================================
        # CATEGORY 1: Device Information & Status (7 methods)
        # =================================================================
        print("\n" + "=" * 80)
        print("1. DEVICE INFORMATION & STATUS")
        print("=" * 80)
        
        # 1. get_system_config
        try:
            config = await pixoo.get_system_config()
            print(f"✅ get_system_config: brightness={config.brightness}, rotation={config.rotation}")
            results["passed"].append("get_system_config")
        except Exception as e:
            print(f"❌ get_system_config: {e}")
            results["failed"].append("get_system_config")
        
        # 2. get_all_channel_config
        try:
            config = await pixoo.get_all_channel_config()
            print(f"✅ get_all_channel_config: brightness={config['Brightness']}")
            results["passed"].append("get_all_channel_config")
        except Exception as e:
            print(f"❌ get_all_channel_config: {e}")
            results["failed"].append("get_all_channel_config")
        
        # 3. get_current_channel
        try:
            channel = await pixoo.get_current_channel()
            print(f"✅ get_current_channel: index={channel}")
            results["passed"].append("get_current_channel")
        except Exception as e:
            print(f"❌ get_current_channel: {e}")
            results["failed"].append("get_current_channel")
        
        # 4. get_time_info
        try:
            time_info = await pixoo.get_time_info()
            print(f"✅ get_time_info: utc={time_info.utc_time}, local={time_info.local_time}")
            results["passed"].append("get_time_info")
        except Exception as e:
            print(f"❌ get_time_info: {e}")
            results["failed"].append("get_time_info")
        
        # 5. get_weather_info
        try:
            weather = await pixoo.get_weather_info()
            print(f"✅ get_weather_info: {weather.Weather}, {weather.CurTemp}°C")
            results["passed"].append("get_weather_info")
        except Exception as e:
            print(f"❌ get_weather_info: {e}")
            results["failed"].append("get_weather_info")
        
        # 6. get_animation_list
        try:
            animations = await pixoo.get_animation_list()
            print(f"✅ get_animation_list: {len(animations.animations)} animations")
            results["passed"].append("get_animation_list")
        except Exception as e:
            print(f"❌ get_animation_list: {e}")
            results["failed"].append("get_animation_list")
        
        # 7. find_device_on_lan (static method)
        try:
            device = await PixooAsync.find_device_on_lan()
            if device:
                print(f"✅ find_device_on_lan: found {device['DeviceName']}")
                results["passed"].append("find_device_on_lan")
            else:
                print("⚠️ find_device_on_lan: no device found (not an error)")
                results["skipped"].append("find_device_on_lan")
        except Exception as e:
            print(f"❌ find_device_on_lan: {e}")
            results["failed"].append("find_device_on_lan")
        
        # =================================================================
        # CATEGORY 2: Display Control (9 methods)
        # =================================================================
        print("\n" + "=" * 80)
        print("2. DISPLAY CONTROL")
        print("=" * 80)
        
        # 8. set_brightness
        try:
            await pixoo.set_brightness(50)
            print("✅ set_brightness(50)")
            results["passed"].append("set_brightness")
        except Exception as e:
            print(f"❌ set_brightness: {e}")
            results["failed"].append("set_brightness")
        
        # 9. set_screen_on / set_screen_off / set_screen
        try:
            await pixoo.set_screen_on()
            print("✅ set_screen_on")
            results["passed"].append("set_screen_on")
        except Exception as e:
            print(f"❌ set_screen_on: {e}")
            results["failed"].append("set_screen_on")
        
        try:
            await pixoo.set_screen(on=True)
            print("✅ set_screen(on=True)")
            results["passed"].append("set_screen")
        except Exception as e:
            print(f"❌ set_screen: {e}")
            results["failed"].append("set_screen")
        
        # 10. set_rotation
        try:
            await pixoo.set_rotation(Rotation.NORMAL)
            print("✅ set_rotation(NORMAL)")
            results["passed"].append("set_rotation")
        except Exception as e:
            print(f"❌ set_rotation: {e}")
            results["failed"].append("set_rotation")
        
        # 11. set_mirror_mode
        try:
            await pixoo.set_mirror_mode(enabled=False)
            print("✅ set_mirror_mode(False)")
            results["passed"].append("set_mirror_mode")
        except Exception as e:
            print(f"❌ set_mirror_mode: {e}")
            results["failed"].append("set_mirror_mode")
        
        # 12. set_channel
        try:
            await pixoo.set_channel(Channel.FACES)
            print("✅ set_channel(FACES)")
            results["passed"].append("set_channel")
        except Exception as e:
            print(f"❌ set_channel: {e}")
            results["failed"].append("set_channel")
        
        # 13. send_text (replaces display_text)
        try:
            await pixoo.send_text(
                text="API Test",
                xy=(0, 16),
                color=(0, 255, 0),
                identifier=0,
                font=2,
                width=64,
                movement_speed=50,
                direction=TextScrollDirection.LEFT
            )
            print("✅ send_text('API Test')")
            results["passed"].append("send_text")
        except Exception as e:
            print(f"❌ send_text: {e}")
            results["failed"].append("send_text")
        
        # 14. clear_text
        try:
            await pixoo.clear_text(text_id=0)
            print("✅ clear_text(0)")
            results["passed"].append("clear_text")
        except Exception as e:
            print(f"❌ clear_text: {e}")
            results["failed"].append("clear_text")
        
        # =================================================================
        # CATEGORY 3: Drawing Primitives (8 methods) - SKIPPED
        # =================================================================
        print("\n" + "=" * 80)
        print("3. DRAWING PRIMITIVES (NOT TESTED - require buffer operations)")
        print("=" * 80)
        print("⚠️ Skipping: initialize, push, _send_buffer, draw_pixel, draw_line,")
        print("   draw_rectangle, draw_filled_rectangle, draw_circle, draw_text_at_position")
        results["skipped"].extend([
            "initialize", "push", "_send_buffer", "_load_counter", "_reset_counter"
        ])
        
        # =================================================================
        # CATEGORY 4: Tool Modes (10 methods)
        # =================================================================
        print("\n" + "=" * 80)
        print("4. TOOL MODES")
        print("=" * 80)
        
        # 15. set_timer
        try:
            await pixoo.set_timer(minutes=5, seconds=30, enabled=True)
            print("✅ set_timer(5:30)")
            results["passed"].append("set_timer")
        except Exception as e:
            print(f"❌ set_timer: {e}")
            results["failed"].append("set_timer")
        
        # 16. set_alarm
        try:
            await pixoo.set_alarm(hour=8, minute=30, enabled=True)
            print("✅ set_alarm(08:30)")
            results["passed"].append("set_alarm")
        except Exception as e:
            print(f"❌ set_alarm: {e}")
            results["failed"].append("set_alarm")
        
        # 17. set_stopwatch (replaces reset_stopwatch)
        try:
            await pixoo.set_stopwatch(enabled=True)
            print("✅ set_stopwatch(enabled=True)")
            results["passed"].append("set_stopwatch")
        except Exception as e:
            print(f"❌ set_stopwatch: {e}")
            results["failed"].append("set_stopwatch")
        
        # 18. set_scoreboard
        try:
            await pixoo.set_scoreboard(red_score=10, blue_score=15)
            print("✅ set_scoreboard(10-15)")
            results["passed"].append("set_scoreboard")
        except Exception as e:
            print(f"❌ set_scoreboard: {e}")
            results["failed"].append("set_scoreboard")
        
        # 19. set_noise_meter (replaces set_noise_meter_mode)
        try:
            await pixoo.set_noise_meter(enabled=True)
            print("✅ set_noise_meter(enabled=True)")
            results["passed"].append("set_noise_meter")
        except Exception as e:
            print(f"❌ set_noise_meter: {e}")
            results["failed"].append("set_noise_meter")
        
        # 20. play_buzzer
        try:
            await pixoo.play_buzzer(active_time=500, off_time=500, total_time=1000)
            print("✅ play_buzzer(500ms on, 500ms off, 1000ms total)")
            results["passed"].append("play_buzzer")
        except Exception as e:
            print(f"❌ play_buzzer: {e}")
            results["failed"].append("play_buzzer")
        
        # 21. set_clock (set_clock_face)
        try:
            await pixoo.set_clock(clock_id=0)
            print("✅ set_clock(0)")
            results["passed"].append("set_clock")
        except Exception as e:
            print(f"❌ set_clock: {e}")
            results["failed"].append("set_clock")
        
        # 22. set_face (similar to set_clock)
        try:
            await pixoo.set_face(face_id=0)
            print("✅ set_face(0)")
            results["passed"].append("set_face")
        except Exception as e:
            print(f"❌ set_face: {e}")
            results["failed"].append("set_face")
        
        # 23. set_visualizer
        try:
            await pixoo.set_visualizer(equalizer_position=0)
            print("✅ set_visualizer(0)")
            results["passed"].append("set_visualizer")
        except Exception as e:
            print(f"❌ set_visualizer: {e}")
            results["failed"].append("set_visualizer")
        
        # 24. set_custom_page / set_custom_channel
        try:
            await pixoo.set_custom_page(index=0)
            print("✅ set_custom_page(0)")
            results["passed"].append("set_custom_page")
        except Exception as e:
            print(f"❌ set_custom_page: {e}")
            results["failed"].append("set_custom_page")
        
        # =================================================================
        # CATEGORY 5: Animation & Playlists (6 methods)
        # =================================================================
        print("\n" + "=" * 80)
        print("5. ANIMATION & PLAYLISTS")
        print("=" * 80)
        
        # 25. play_animation (may fail with "Request data illegal json")
        try:
            await pixoo.play_animation(pic_id=1)
            print("✅ play_animation(1)")
            results["passed"].append("play_animation")
        except Exception as e:
            print(f"⚠️ play_animation: {e}")
            print("   (Known issue: Device returns 'Request data illegal json')")
            results["failed"].append("play_animation")
        
        # 26. stop_animation (may fail with same error)
        try:
            await pixoo.stop_animation()
            print("✅ stop_animation")
            results["passed"].append("stop_animation")
        except Exception as e:
            print(f"⚠️ stop_animation: {e}")
            print("   (Known issue: Device returns 'Request data illegal json')")
            results["failed"].append("stop_animation")
        
        # 27. send_playlist (may fail with same error)
        try:
            playlist = [
                PlaylistItem(type=0, pic_id=1, duration=5000),
                PlaylistItem(type=0, pic_id=2, duration=5000)
            ]
            await pixoo.send_playlist(playlist)
            print("✅ send_playlist(2 items)")
            results["passed"].append("send_playlist")
        except Exception as e:
            print(f"⚠️ send_playlist: {e}")
            print("   (Known issue: Device returns 'Request data illegal json')")
            results["failed"].append("send_playlist")
        
        # =================================================================
        # CATEGORY 6: Configuration (8 methods)
        # =================================================================
        print("\n" + "=" * 80)
        print("6. CONFIGURATION")
        print("=" * 80)
        
        # 28. set_white_balance
        try:
            await pixoo.set_white_balance(red=100, green=100, blue=100)
            print("✅ set_white_balance(100, 100, 100)")
            results["passed"].append("set_white_balance")
        except Exception as e:
            print(f"❌ set_white_balance: {e}")
            results["failed"].append("set_white_balance")
        
        # 29. set_weather_location
        try:
            location = Location(longitude="-73.935242", latitude="40.730610")  # NYC
            await pixoo.set_weather_location(location)
            print("✅ set_weather_location(NYC)")
            results["passed"].append("set_weather_location")
        except Exception as e:
            print(f"❌ set_weather_location: {e}")
            results["failed"].append("set_weather_location")
        
        # 30. set_time
        try:
            import time
            utc_timestamp = int(time.time())
            await pixoo.set_time(utc_timestamp)
            print(f"✅ set_time({utc_timestamp})")
            results["passed"].append("set_time")
        except Exception as e:
            print(f"❌ set_time: {e}")
            results["failed"].append("set_time")
        
        # 31. set_timezone
        try:
            await pixoo.set_timezone("America/New_York")
            print("✅ set_timezone(America/New_York)")
            results["passed"].append("set_timezone")
        except Exception as e:
            print(f"❌ set_timezone: {e}")
            results["failed"].append("set_timezone")
        
        # Note: set_temperature_mode and set_time_format don't exist as separate methods
        print("ℹ️ Note: temperature_mode and time_format are set via SystemSettings,")
        print("   not as separate methods in PixooAsync")
        
    # =================================================================
    # RESULTS SUMMARY
    # =================================================================
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ PASSED: {len(results['passed'])} methods")
    for method in results["passed"]:
        print(f"   - {method}")
    
    print(f"\n❌ FAILED: {len(results['failed'])} methods")
    for method in results["failed"]:
        print(f"   - {method}")
    
    print(f"\n⚠️ SKIPPED: {len(results['skipped'])} methods (not testable or drawing primitives)")
    
    total_tested = len(results["passed"]) + len(results["failed"])
    if total_tested > 0:
        success_rate = (len(results["passed"]) / total_tested) * 100
        print(f"\n📊 Success Rate: {success_rate:.1f}% ({len(results['passed'])}/{total_tested})")
    
    print("\n" + "=" * 80)
    
    return results

if __name__ == "__main__":
    asyncio.run(test_pixooasync())
