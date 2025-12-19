#!/usr/bin/env python3
"""
Test actual Pixoo device API responses and pixooasync functionality.
This validates what works and what doesn't.
"""
import asyncio
import sys
sys.path.insert(0, '/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo')

from pixooasync import PixooAsync
import httpx


async def test_raw_apis():
    """Test raw API endpoints."""
    print("\n" + "="*80)
    print("  RAW API ENDPOINT TESTS")
    print("="*80 + "\n")
    
    url = "http://192.168.188.65/post"
    
    tests = [
        ("Channel/GetIndex", "Get current channel index"),
        ("Device/GetDeviceTime", "Get device time"),
        ("Device/GetDeviceInfo", "Get device info"),
        ("Device/GetNetworkStatus", "Get network status"),
        ("Device/GetSystemConfig", "Get system config"),
        ("Channel/GetAllConf", "Get all channel configs"),
    ]
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for command, description in tests:
            print(f"\n{command}")
            print(f"  Description: {description}")
            
            try:
                payload = {"Command": command}
                response = await client.post(url, json=payload)
                data = response.json()
                
                if "error_code" in data:
                    if data["error_code"] == 0:
                        print(f"  ✅ SUCCESS")
                        # Print response keys
                        keys = [k for k in data.keys() if k != "error_code"]
                        if keys:
                            print(f"  Response keys: {', '.join(keys)}")
                    else:
                        error_msg = data.get("error_code", "unknown")
                        print(f"  ❌ ERROR: {error_msg}")
                else:
                    print(f"  ⚠️  UNEXPECTED RESPONSE FORMAT")
                    
            except Exception as e:
                print(f"  ❌ EXCEPTION: {e}")


async def test_pixooasync_methods():
    """Test pixooasync client methods."""
    print("\n" + "="*80)
    print("  PIXOOASYNC METHOD TESTS")
    print("="*80 + "\n")
    
    async with PixooAsync(address="192.168.188.65") as pixoo:
        
        # Test get_device_info
        print("\n1. get_device_info()")
        try:
            device_info = await pixoo.get_device_info()
            print(f"   Device Name: {device_info.device_name}")
            print(f"   Device Model: {device_info.device_model}")
            print(f"   MAC Address: {device_info.device_mac}")
            print(f"   Firmware: {device_info.software_version}")
            print(f"   Brightness: {device_info.brightness}%")
            
            if device_info.device_mac == "00:00:00:00:00:00":
                print(f"   ⚠️  Using default MAC (API not supported)")
            if device_info.software_version == "1.0.0":
                print(f"   ⚠️  Using default firmware (API not supported)")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test get_network_status
        print("\n2. get_network_status()")
        try:
            network = await pixoo.get_network_status()
            print(f"   IP: {network.ip_address}")
            print(f"   MAC: {network.mac_address}")
            print(f"   SSID: {network.ssid}")
            print(f"   RSSI: {network.rssi} dBm")
            print(f"   Connected: {network.connected}")
            
            if network.ssid == "Unknown":
                print(f"   ⚠️  Using default SSID (API not supported)")
            if network.mac_address == "00:00:00:00:00:00":
                print(f"   ⚠️  Using default MAC (API not supported)")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test get_system_config
        print("\n3. get_system_config()")
        try:
            system = await pixoo.get_system_config()
            print(f"   Brightness: {system.brightness}%")
            print(f"   Rotation: {system.rotation} ({system.rotation * 90}°)")
            print(f"   Mirror Mode: {system.mirror_mode}")
            print(f"   Screen Power: {system.screen_power}")
            print(f"   Hour Mode: {system.hour_mode}h")
            print(f"   Temperature Mode: {system.temperature_mode}")
            
            if system.brightness == 50:
                print(f"   ⚠️  Brightness might be default value")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test get_time_info
        print("\n4. get_time_info()")
        try:
            time_info = await pixoo.get_time_info()
            print(f"   UTC Time: {time_info.utc_time}")
            print(f"   Local Time: {time_info.local_time}")
            print(f"   ✅ Time API works!")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test get_weather_info
        print("\n5. get_weather_info()")
        try:
            weather = await pixoo.get_weather_info()
            print(f"   Temperature: {weather.temperature}°")
            print(f"   Weather: {weather.weather}")
            print(f"   ✅ Weather API works!")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test get_animation_list
        print("\n6. get_animation_list()")
        try:
            animations = await pixoo.get_animation_list()
            print(f"   Total animations: {len(animations)}")
            if animations:
                print(f"   First 3: {[a.name for a in animations[:3]]}")
            print(f"   ✅ Animation list works!")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")


async def test_device_discovery():
    """Test device discovery API."""
    print("\n" + "="*80)
    print("  DEVICE DISCOVERY API TEST")
    print("="*80 + "\n")
    
    print("Testing: https://app.divoom-gz.com/Device/ReturnSameLANDevice")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post("https://app.divoom-gz.com/Device/ReturnSameLANDevice")
            data = response.json()
            
            if data.get("ReturnCode") == 0:
                print("✅ SUCCESS - Device discovery API works!")
                devices = data.get("DeviceList", [])
                print(f"\nFound {len(devices)} device(s):")
                
                for i, device in enumerate(devices, 1):
                    print(f"\n  Device {i}:")
                    print(f"    Name: {device.get('DeviceName')}")
                    print(f"    IP: {device.get('DevicePrivateIP')}")
                    print(f"    MAC: {device.get('DeviceMac')}")
                    print(f"    Hardware ID: {device.get('DeviceId')}")
            else:
                print(f"❌ ERROR: ReturnCode = {data.get('ReturnCode')}")
                
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")


async def test_channel_get_index():
    """Test Channel/GetIndex API."""
    print("\n" + "="*80)
    print("  CHANNEL GET INDEX TEST")
    print("="*80 + "\n")
    
    url = "http://192.168.188.65/post"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload = {"Command": "Channel/GetIndex"}
            response = await client.post(url, json=payload)
            data = response.json()
            
            if data.get("error_code") == 0:
                index = data.get("SelectIndex")
                channel_names = {
                    0: "Faces (Clock)",
                    1: "Cloud Channel",
                    2: "Visualizer",
                    3: "Custom Pages"
                }
                print(f"✅ SUCCESS - Current channel index: {index}")
                print(f"   Channel name: {channel_names.get(index, 'Unknown')}")
            else:
                print(f"❌ ERROR: {data.get('error_code')}")
                
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")


async def test_brightness_api():
    """Test brightness read/write."""
    print("\n" + "="*80)
    print("  BRIGHTNESS API TEST")
    print("="*80 + "\n")
    
    async with PixooAsync(address="192.168.188.65") as pixoo:
        # Try to read brightness
        print("1. Reading brightness from get_system_config()...")
        try:
            system = await pixoo.get_system_config()
            print(f"   Current brightness: {system.brightness}%")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Try to write brightness
        print("\n2. Setting brightness to 75%...")
        try:
            await pixoo.set_brightness(75)
            print("   ✅ Brightness set successfully")
            
            # Read again
            await asyncio.sleep(0.5)
            system = await pixoo.get_system_config()
            print(f"   New brightness: {system.brightness}%")
            
            if system.brightness == 75:
                print("   ✅ Brightness change confirmed!")
            elif system.brightness == 50:
                print("   ⚠️  Still shows 50% - read API might not work")
            else:
                print(f"   ⚠️  Shows {system.brightness}% - unexpected value")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  PIXOO DEVICE API & PIXOOASYNC VALIDATION")
    print("  Device: 192.168.188.65 (Pixoo-64)")
    print("="*80)
    
    await test_raw_apis()
    await test_pixooasync_methods()
    await test_device_discovery()
    await test_channel_get_index()
    await test_brightness_api()
    
    print("\n" + "="*80)
    print("  ALL TESTS COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
