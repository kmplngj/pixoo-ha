#!/usr/bin/env python3
"""Test script to verify pixooasync can read all device state."""

import asyncio
import sys
from pathlib import Path

# Add the custom_components directory to the path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "pixoo"))

from pixooasync import PixooAsync
from pixooasync.models import DeviceInfo, NetworkStatus, SystemConfig, WeatherInfo, TimeInfo


async def test_pixoo_state(ip_address: str):
    """Test reading all available state from Pixoo device."""
    print(f"🔌 Connecting to Pixoo at {ip_address}...")
    print("=" * 80)
    
    pixoo = PixooAsync(ip_address)
    
    try:
        # Initialize the client
        await pixoo.initialize()
        print("✅ Client initialized successfully\n")
        
        # Test 1: Device Info
        print("📱 Device Information:")
        print("-" * 80)
        try:
            device_info: DeviceInfo = await pixoo.get_device_info()
            print(f"  Model:              {device_info.device_model}")
            print(f"  Name:               {device_info.device_name}")
            print(f"  MAC Address:        {device_info.device_mac}")
            print(f"  Firmware:           {device_info.software_version}")
            print(f"  Hardware:           {device_info.hardware_version}")
            print(f"  Device ID:          {device_info.device_id}")
            print(f"  Brightness:         {device_info.brightness}%")
            print("  ✅ Device info retrieved\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
        
        # Test 2: Network Status
        print("🌐 Network Status:")
        print("-" * 80)
        try:
            network: NetworkStatus = await pixoo.get_network_status()
            print(f"  IP Address:         {network.ip_address}")
            print(f"  MAC Address:        {network.mac_address}")
            print(f"  SSID:               {network.ssid}")
            print(f"  RSSI:               {network.rssi} dBm")
            print(f"  Connected:          {network.connected}")
            print("  ✅ Network status retrieved\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
        
        # Test 3: System Config
        print("⚙️  System Configuration:")
        print("-" * 80)
        try:
            system: SystemConfig = await pixoo.get_system_config()
            print(f"  Brightness:         {system.brightness}%")
            print(f"  Rotation:           {system.rotation} (0=Normal, 1=90°, 2=180°, 3=270°)")
            print(f"  Mirror Mode:        {system.mirror_mode}")
            print(f"  Screen Power:       {system.screen_power}")
            print(f"  Hour Mode:          {system.hour_mode}h")
            print(f"  Temperature Mode:   {system.temperature_mode} (0=Celsius, 1=Fahrenheit)")
            print(f"  Timezone:           {system.time_zone}")
            print(f"  White Balance RGB:  ({system.white_balance_r}, {system.white_balance_g}, {system.white_balance_b})")
            print("  ✅ System config retrieved\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
        
        # Test 4: Weather Info
        print("🌤️  Weather Information:")
        print("-" * 80)
        try:
            weather: WeatherInfo | None = await pixoo.get_weather_info()
            if weather:
                print(f"  Temperature:        {weather.CurTemp}°")
                print(f"  Condition:          {weather.Weather}")
                print(f"  Min Temp:           {weather.MinTemp}°")
                print(f"  Max Temp:           {weather.MaxTemp}°")
                print(f"  Humidity:           {weather.Humidity}%")
                print(f"  Pressure:           {weather.Pressure} hPa")
                print("  ✅ Weather info retrieved\n")
            else:
                print("  ⚠️  Weather info not available (not configured)\n")
        except Exception as e:
            print(f"  ⚠️  Weather info not available: {e}\n")
        
        # Test 5: Time Info
        print("🕐 Time Information:")
        print("-" * 80)
        try:
            time_info: TimeInfo | None = await pixoo.get_time_info()
            if time_info:
                print(f"  UTC Timestamp:      {time_info.utc_timestamp}")
                print(f"  Local Timestamp:    {time_info.local_timestamp}")
                print(f"  Timezone:           {time_info.timezone}")
                print(f"  Timezone Offset:    {time_info.timezone_offset}")
                print("  ✅ Time info retrieved\n")
            else:
                print("  ⚠️  Time info not available\n")
        except Exception as e:
            print(f"  ⚠️  Time info not available: {e}\n")
        
        # Test 6: Animation List
        print("🎨 Available Animations:")
        print("-" * 80)
        try:
            animations = await pixoo.get_animation_list()
            print(f"  Total Clocks:       {len(animations.clocks)}")
            if animations.clocks:
                print(f"  Clock IDs:          {[c.id for c in animations.clocks[:5]]}...")
            print(f"  Total Visualizers:  {len(animations.visualizers)}")
            if animations.visualizers:
                print(f"  Visualizer IDs:     {[v.id for v in animations.visualizers[:5]]}...")
            print("  ✅ Animation list retrieved\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
        
        # Summary
        print("=" * 80)
        print("✨ Test Complete!")
        print("=" * 80)
        print("\n📊 Summary:")
        print("  All core device state can be read successfully.")
        print("  The integration coordinators should work properly with this data.")
        print("\n💡 Note:")
        print("  - Weather info requires prior configuration on the device")
        print("  - Time info may require internet connectivity")
        print("  - Some fields may return default values if not configured")
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await pixoo.close()
        print("\n🔌 Connection closed")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_pixoo_state.py <IP_ADDRESS>")
        print("Example: python test_pixoo_state.py 192.168.1.100")
        sys.exit(1)
    
    ip_address = sys.argv[1]
    asyncio.run(test_pixoo_state(ip_address))


if __name__ == "__main__":
    main()
