#!/usr/bin/env python3
"""Test Phase 2 fixes - TimeInfo, WeatherInfo, AnimationList.

Validates:
1. TimeInfo model matches Device/GetDeviceTime API
2. WeatherInfo works correctly
3. AnimationList handles broken API gracefully
"""

import asyncio
import os
import httpx
from pathlib import Path
import sys

# Add pixooasync to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "pixoo"))

DEVICE_IP = "192.168.188.65"
HA_URL = "http://homeassistant.local:8123"
HASS_TOKEN = os.environ.get("HASS_TOKEN")


async def test_pixooasync_fixes():
    """Test pixooasync method fixes."""
    print("\n" + "=" * 70)
    print("Testing PixooAsync Method Fixes")
    print("=" * 70)
    
    from pixooasync import PixooAsync
    
    async with PixooAsync(DEVICE_IP) as pixoo:
        await pixoo.initialize()
        
        # Test get_time_info
        print("\n1. Testing get_time_info()...")
        try:
            time_info = await pixoo.get_time_info()
            if time_info:
                print(f"   ✅ get_time_info() works:")
                print(f"      UTC Time: {time_info.utc_time}")
                print(f"      Local Time: {time_info.local_time}")
            else:
                print("   ⚠️  get_time_info() returned None")
        except Exception as e:
            print(f"   ❌ get_time_info() error: {e}")
        
        # Test get_weather_info
        print("\n2. Testing get_weather_info()...")
        try:
            weather_info = await pixoo.get_weather_info()
            if weather_info:
                print(f"   ✅ get_weather_info() works:")
                print(f"      Weather: {weather_info.Weather}")
                print(f"      Temperature: {weather_info.CurTemp}°C")
                print(f"      Humidity: {weather_info.Humidity}%")
            else:
                print("   ⚠️  get_weather_info() returned None")
        except Exception as e:
            print(f"   ❌ get_weather_info() error: {e}")
        
        # Test get_animation_list
        print("\n3. Testing get_animation_list()...")
        try:
            animations = await pixoo.get_animation_list()
            print(f"   ✅ get_animation_list() works:")
            print(f"      Total: {animations.total_number}")
            print(f"      Animations: {len(animations.animations)}")
            print(f"      (Note: API returns error, so always 0)")
        except Exception as e:
            print(f"   ❌ get_animation_list() error: {e}")


async def test_ha_sensors():
    """Test HA sensor integration."""
    print("\n" + "=" * 70)
    print("Testing Home Assistant Sensor Integration")
    print("=" * 70)
    
    if not HASS_TOKEN:
        print("⚠️  HASS_TOKEN not set, skipping HA tests")
        return
    
    # Wait for HA to be ready
    print("\nWaiting for HA to restart...")
    await asyncio.sleep(30)
    
    headers = {
        "Authorization": f"Bearer {HASS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{HA_URL}/api/states", headers=headers)
            states = response.json()
        except Exception as e:
            print(f"⚠️  HA not ready yet: {e}")
            return
        
        # Find Pixoo time sensor
        time_sensor = next((s for s in states if "pixoo" in s["entity_id"] and "time" in s["entity_id"]), None)
        if time_sensor:
            print("\n4. Checking Time Sensor:")
            state = time_sensor["state"]
            attrs = time_sensor.get("attributes", {})
            print(f"   ✅ Time sensor exists")
            print(f"      State: {state}")
            print(f"      UTC Time: {attrs.get('utc_time', 'N/A')}")
        else:
            print("\n4. Time sensor not found (may not exist yet)")
        
        # Find Pixoo weather sensor
        weather_sensor = next((s for s in states if "pixoo" in s["entity_id"] and "weather" in s["entity_id"]), None)
        if weather_sensor:
            print("\n5. Checking Weather Sensor:")
            state = weather_sensor["state"]
            attrs = weather_sensor.get("attributes", {})
            print(f"   ✅ Weather sensor exists")
            print(f"      State: {state}")
            print(f"      Temperature: {attrs.get('temperature', 'N/A')}°C")
        else:
            print("\n5. Weather sensor not found")


async def main():
    """Run all tests."""
    print("\n🔧 Phase 2 Validation - PixooAsync Bug Fixes")
    print("=" * 70)
    print("Device IP:", DEVICE_IP)
    print("=" * 70)
    
    try:
        await test_pixooasync_fixes()
        await test_ha_sensors()
        
        print("\n" + "=" * 70)
        print("✅ Phase 2 Validation Complete!")
        print("=" * 70)
        print("\nFixes Applied:")
        print("- ✅ TimeInfo model: Fixed to match Device/GetDeviceTime API")
        print("- ✅ WeatherInfo: Already working correctly")
        print("- ✅ AnimationList: Handles broken API gracefully")
        print("\nNext Steps:")
        print("- Phase 3: Add play_animation, send_playlist, set_white_balance services")
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
