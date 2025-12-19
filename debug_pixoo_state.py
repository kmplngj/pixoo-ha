#!/usr/bin/env python3
"""Debug script to test Pixoo device state reading.

This script tests all the methods used by the HA integration to read device state.
Run this to verify the device is responding correctly before debugging HA integration.

Usage:
    python debug_pixoo_state.py <IP_ADDRESS>
    python debug_pixoo_state.py 192.168.1.100
"""

import asyncio
import sys
from pathlib import Path

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "pixoo"))

from pixooasync import PixooAsync
from pixooasync.enums import Channel


async def test_device_state(ip_address: str):
    """Test all device state reading methods."""
    print(f"\n{'='*60}")
    print(f"Testing Pixoo Device at {ip_address}")
    print(f"{'='*60}\n")

    async with PixooAsync(ip_address) as pixoo:
        
        # Test 1: Device Info
        print("1. Testing get_device_info()...")
        try:
            device_info = await pixoo.get_device_info()
            print("   ✅ Device Info:")
            print(f"      - IP: {device_info.ip_address}")
            print(f"      - MAC: {device_info.mac_address}")
            print(f"      - Model: {device_info.device_model}")
            print(f"      - Firmware: {device_info.software_version}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 2: System Config (includes brightness, screen_power, rotation, etc.)
        print("\n2. Testing get_system_config()...")
        try:
            system_config = await pixoo.get_system_config()
            print("   ✅ System Config:")
            print(f"      - Brightness: {system_config.brightness}%")
            print(f"      - Screen Power: {system_config.screen_power}")
            print(f"      - Rotation: {system_config.rotation} (0=normal, 1=90°, 2=180°, 3=270°)")
            print(f"      - Mirror Mode: {system_config.mirror_mode}")
            print(f"      - Hour Mode: {system_config.hour_mode}h")
            print(f"      - Temperature Mode: {system_config.temperature_mode} (0=Celsius, 1=Fahrenheit)")
            print(f"      - Time Zone: {system_config.time_zone}")
            print(f"      - White Balance: R={system_config.white_balance_r}, G={system_config.white_balance_g}, B={system_config.white_balance_b}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 3: Network Status
        print("\n3. Testing get_network_status()...")
        try:
            network = await pixoo.get_network_status()
            print(f"   ✅ Network Status:")
            print(f"      - SSID: {network.ssid}")
            print(f"      - IP: {network.ip_address}")
            print(f"      - MAC: {network.mac_address}")
            print(f"      - RSSI: {network.rssi} dBm")
            print(f"      - Connected: {network.connected}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 4: Current Channel
        print("\n4. Testing get_current_channel()...")
        try:
            channel = await pixoo.get_current_channel()
            print(f"   ✅ Current Channel: {channel}")
            if isinstance(channel, Channel):
                print(f"      - Enum value: {channel.value}")
                print(f"      - Name: {channel.name}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 5: Weather Info
        print("\n5. Testing get_weather_info()...")
        try:
            weather = await pixoo.get_weather_info()
            print(f"   ✅ Weather Info:")
            print(f"      - Temperature: {weather.temperature}°")
            print(f"      - Condition: {weather.condition}")
            print(f"      - Weather Type: {weather.weather_type}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 6: Time Info
        print("\n6. Testing get_time_info()...")
        try:
            time_info = await pixoo.get_time_info()
            print(f"   ✅ Time Info:")
            print(f"      - UTC Timestamp: {time_info.utc_timestamp}")
            print(f"      - Local Timestamp: {time_info.local_timestamp}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 7: Timer Config
        print("\n7. Testing get_timer_config()...")
        try:
            timer = await pixoo.get_timer_config()
            print(f"   ✅ Timer Config:")
            print(f"      - Minutes: {timer.minutes}")
            print(f"      - Seconds: {timer.seconds}")
            print(f"      - Enabled: {timer.enabled}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 8: Alarm Config
        print("\n8. Testing get_alarm_config()...")
        try:
            alarm = await pixoo.get_alarm_config()
            print(f"   ✅ Alarm Config:")
            print(f"      - Hour: {alarm.hour}")
            print(f"      - Minute: {alarm.minute}")
            print(f"      - Enabled: {alarm.enabled}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 9: Stopwatch Config
        print("\n9. Testing get_stopwatch_config()...")
        try:
            stopwatch = await pixoo.get_stopwatch_config()
            print(f"   ✅ Stopwatch Config:")
            print(f"      - Elapsed Time: {stopwatch.elapsed_time}s")
            print(f"      - Running: {stopwatch.running}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 10: Animation List
        print("\n10. Testing get_animation_list()...")
        try:
            animations = await pixoo.get_animation_list()
            print(f"   ✅ Animation List:")
            print(f"      - Total animations: {len(animations)}")
            if animations:
                print(f"      - First animation: ID={animations[0].id}, Name={animations[0].name}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 11: Test state refresh by toggling screen
        print("\n11. Testing state refresh after screen toggle...")
        try:
            # Get current state
            config_before = await pixoo.get_system_config()
            print(f"   📊 Before: screen_power={config_before.screen_power}, brightness={config_before.brightness}%")
            
            # Toggle screen off
            print(f"   🔄 Turning screen OFF...")
            await pixoo.set_screen(on=False)
            await asyncio.sleep(1)
            
            # Read state again
            config_after_off = await pixoo.get_system_config()
            print(f"   📊 After OFF: screen_power={config_after_off.screen_power}, brightness={config_after_off.brightness}%")
            
            # Toggle screen on
            print(f"   🔄 Turning screen ON...")
            await pixoo.set_screen(on=True)
            await asyncio.sleep(1)
            
            # Read state again
            config_after_on = await pixoo.get_system_config()
            print(f"   📊 After ON: screen_power={config_after_on.screen_power}, brightness={config_after_on.brightness}%")
            
            # Verify state changes
            if config_after_off.screen_power != config_before.screen_power:
                print(f"   ✅ Screen power state changes correctly!")
            else:
                print(f"   ⚠️  Screen power state did NOT change (might be expected if already off)")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n{'='*60}")
    print("Test Complete!")
    print(f"{'='*60}\n")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python debug_pixoo_state.py <IP_ADDRESS>")
        print("Example: python debug_pixoo_state.py 192.168.1.100")
        sys.exit(1)

    ip_address = sys.argv[1]
    asyncio.run(test_device_state(ip_address))


if __name__ == "__main__":
    main()
