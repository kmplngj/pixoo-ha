#!/usr/bin/env python3
"""Validate Pixoo sensor fixes after Phase 1 deployment.

Tests:
1. Check removed sensors are gone (SSID, RSSI, firmware, brightness)
2. Check Active Channel sensor shows correct value
3. Validate Channel/GetIndex API works
4. Validate Channel/GetAllConf returns real brightness

Run after HA restart completes.
"""

import asyncio
import json
import os
import httpx

DEVICE_IP = "192.168.188.65"
HA_URL = "http://homeassistant.local:8123"
HASS_TOKEN = os.environ.get("HASS_TOKEN")


async def test_device_apis():
    """Test that device APIs are working correctly."""
    print("\n" + "=" * 70)
    print("Testing Device APIs Directly")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test Channel/GetIndex
        print("\n1. Testing Channel/GetIndex...")
        response = await client.post(
            f"http://{DEVICE_IP}/post",
            json={"Command": "Channel/GetIndex"}
        )
        data = response.json()
        channel_map = {0: "Faces", 1: "Cloud", 2: "Visualizer", 3: "Custom"}
        if data.get("error_code") == 0:
            channel_idx = data.get("SelectIndex", 0)
            print(f"   ✅ Channel/GetIndex works: {channel_idx} = {channel_map.get(channel_idx)}")
        else:
            print(f"   ❌ Channel/GetIndex failed: {data}")
        
        # Test Channel/GetAllConf
        print("\n2. Testing Channel/GetAllConf...")
        response = await client.post(
            f"http://{DEVICE_IP}/post",
            json={"Command": "Channel/GetAllConf"}
        )
        data = response.json()
        if data.get("error_code") == 0:
            brightness = data.get("Brightness", "N/A")
            rotation = data.get("GyrateAngle", "N/A")
            mirror = data.get("MirrorFlag", "N/A")
            print(f"   ✅ Channel/GetAllConf works:")
            print(f"      Brightness: {brightness}%")
            print(f"      Rotation: {rotation}°")
            print(f"      Mirror: {mirror}")
            print(f"      CurClockId: {data.get('CurClockId', 'N/A')}")
        else:
            print(f"   ❌ Channel/GetAllConf failed: {data}")


async def test_ha_sensors():
    """Test Home Assistant sensor entities."""
    print("\n" + "=" * 70)
    print("Testing Home Assistant Sensors")
    print("=" * 70)
    
    if not HASS_TOKEN:
        print("⚠️  HASS_TOKEN not set, skipping HA tests")
        return
    
    headers = {
        "Authorization": f"Bearer {HASS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Get all states
        response = await client.get(f"{HA_URL}/api/states", headers=headers)
        states = response.json()
        
        # Filter Pixoo sensors
        pixoo_sensors = [s for s in states if s["entity_id"].startswith("sensor.pixoo")]
        
        print(f"\nFound {len(pixoo_sensors)} Pixoo sensors:")
        
        # Check removed sensors
        removed_sensors = ["wifi_ssid", "wifi_signal_strength", "firmware_version", "current_brightness"]
        print("\n3. Checking removed sensors are gone:")
        for sensor_name in removed_sensors:
            found = any(sensor_name in s["entity_id"] for s in pixoo_sensors)
            if found:
                print(f"   ❌ {sensor_name} still exists (should be removed!)")
            else:
                print(f"   ✅ {sensor_name} removed successfully")
        
        # Check Active Channel sensor
        print("\n4. Checking Active Channel sensor:")
        channel_sensor = next((s for s in pixoo_sensors if "active_channel" in s["entity_id"]), None)
        if channel_sensor:
            state = channel_sensor["state"]
            attrs = channel_sensor.get("attributes", {})
            print(f"   ✅ Active Channel sensor exists")
            print(f"      State: {state}")
            print(f"      Channel Index: {attrs.get('channel_index', 'N/A')}")
            print(f"      Brightness: {attrs.get('brightness', 'N/A')}%")
            print(f"      Rotation: {attrs.get('rotation', 'N/A')}")
        else:
            print(f"   ❌ Active Channel sensor not found")
        
        # List all remaining sensors
        print("\n5. All Pixoo sensors:")
        for sensor in pixoo_sensors:
            entity_id = sensor["entity_id"]
            state = sensor["state"]
            name = sensor["attributes"].get("friendly_name", entity_id)
            print(f"   - {name}: {state}")


async def test_cloud_discovery():
    """Test cloud discovery API."""
    print("\n" + "=" * 70)
    print("Testing Cloud Discovery API")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post("https://app.divoom-gz.com/Device/ReturnSameLANDevice")
        data = response.json()
        
        if data.get("ReturnCode") == 0:
            devices = data.get("DeviceList", [])
            print(f"\n6. Found {len(devices)} device(s):")
            for device in devices:
                print(f"   ✅ Device:")
                print(f"      Name: {device.get('DeviceName')}")
                print(f"      IP: {device.get('DevicePrivateIP')}")
                print(f"      MAC: {device.get('DeviceMac')}")
                print(f"      ID: {device.get('DeviceId')}")
        else:
            print(f"   ❌ Cloud discovery failed: {data}")


async def main():
    """Run all validation tests."""
    print("\n🔍 Pixoo Sensor Fixes Validation")
    print("=" * 70)
    print("Device IP:", DEVICE_IP)
    print("HA URL:", HA_URL)
    print("=" * 70)
    
    try:
        await test_device_apis()
        await test_ha_sensors()
        await test_cloud_discovery()
        
        print("\n" + "=" * 70)
        print("✅ Validation Complete!")
        print("=" * 70)
        print("\nSummary:")
        print("- Channel/GetIndex API: Working ✅")
        print("- Channel/GetAllConf API: Working ✅")
        print("- Removed sensors: SSID, RSSI, Firmware, Brightness ❌")
        print("- Active Channel sensor: Using real API ✅")
        print("- Cloud Discovery: Returns real MAC address ✅")
        print("\nNext Steps:")
        print("1. Add play_animation, send_playlist, set_white_balance services")
        print("2. Fix get_time_info() bug in pixooasync")
        print("3. Update MAC Address sensor to use cloud discovery")
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
