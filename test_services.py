#!/usr/bin/env python3
"""Test Pixoo services via Home Assistant API."""

import asyncio
import os
import sys

import httpx


async def test_services():
    """Test Pixoo services."""
    
    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    ha_token = os.getenv("HASS_TOKEN")
    
    if not ha_token:
        print("❌ Error: HASS_TOKEN environment variable not set")
        return False
    
    headers = {
        "Authorization": f"Bearer {ha_token}",
        "Content-Type": "application/json",
    }
    
    print(f"🧪 Testing Pixoo Services at {ha_url}")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        try:
            # Find a Pixoo entity to use as target
            print("\n📍 Finding Pixoo device...")
            response = await client.get(f"{ha_url}/api/states", headers=headers)
            response.raise_for_status()
            states = response.json()
            
            pixoo_entities = [s for s in states if "pixoo" in s.get("entity_id", "").lower()]
            light_entity = next((e["entity_id"] for e in pixoo_entities if e["entity_id"].startswith("light.")), None)
            
            if not light_entity:
                print("❌ No Pixoo light entity found")
                return False
            
            print(f"   Using entity: {light_entity}")
            
            # Test 1: Display Text Service
            print("\n✅ Test 1: pixoo.display_text")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/pixoo/display_text",
                    headers=headers,
                    json={
                        "entity_id": light_entity,
                        "text": "API Test ✓",
                        "color": [0, 255, 0],
                        "position": [0, 24],
                    },
                )
                if response.status_code == 200:
                    print("   ✅ Service call successful")
                    print(f"   Response: {response.json()}")
                else:
                    print(f"   ❌ Service call failed: {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as err:
                print(f"   ❌ Error: {err}")
            
            await asyncio.sleep(2)
            
            # Test 2: Clear Display Service
            print("\n✅ Test 2: pixoo.clear_display")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/pixoo/clear_display",
                    headers=headers,
                    json={
                        "entity_id": light_entity,
                    },
                )
                if response.status_code == 200:
                    print("   ✅ Service call successful")
                else:
                    print(f"   ❌ Service call failed: {response.status_code}")
            except Exception as err:
                print(f"   ❌ Error: {err}")
            
            await asyncio.sleep(1)
            
            # Test 3: Display Image Service (with URL)
            print("\n✅ Test 3: pixoo.display_image")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/pixoo/display_image",
                    headers=headers,
                    json={
                        "entity_id": light_entity,
                        "url": "https://raw.githubusercontent.com/home-assistant/brands/master/custom_integrations/pixoo/icon.png",
                    },
                )
                if response.status_code == 200:
                    print("   ✅ Service call successful")
                else:
                    print(f"   ❌ Service call failed: {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as err:
                print(f"   ❌ Error: {err}")
            
            await asyncio.sleep(2)
            
            # Test 4: Set Timer Service
            print("\n✅ Test 4: pixoo.set_timer")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/pixoo/set_timer",
                    headers=headers,
                    json={
                        "entity_id": light_entity,
                        "minutes": 0,
                        "seconds": 10,
                    },
                )
                if response.status_code == 200:
                    print("   ✅ Service call successful")
                else:
                    print(f"   ❌ Service call failed: {response.status_code}")
            except Exception as err:
                print(f"   ❌ Error: {err}")
            
            # Test 5: Set Alarm Service
            print("\n✅ Test 5: pixoo.set_alarm")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/pixoo/set_alarm",
                    headers=headers,
                    json={
                        "entity_id": light_entity,
                        "hour": 8,
                        "minute": 30,
                    },
                )
                if response.status_code == 200:
                    print("   ✅ Service call successful")
                else:
                    print(f"   ❌ Service call failed: {response.status_code}")
            except Exception as err:
                print(f"   ❌ Error: {err}")
            
            # Test 6: Play Buzzer Service
            print("\n✅ Test 6: pixoo.play_buzzer")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/pixoo/play_buzzer",
                    headers=headers,
                    json={
                        "entity_id": light_entity,
                        "duration": 500,
                    },
                )
                if response.status_code == 200:
                    print("   ✅ Service call successful (buzzer should beep)")
                else:
                    print(f"   ❌ Service call failed: {response.status_code}")
            except Exception as err:
                print(f"   ❌ Error: {err}")
            
            await asyncio.sleep(1)
            
            # Test 7: List Animations Service
            print("\n✅ Test 7: pixoo.list_animations")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/pixoo/list_animations",
                    headers=headers,
                    json={
                        "entity_id": light_entity,
                    },
                )
                if response.status_code == 200:
                    print("   ✅ Service call successful")
                    print("   (Check HA logs for animation list)")
                else:
                    print(f"   ❌ Service call failed: {response.status_code}")
            except Exception as err:
                print(f"   ❌ Error: {err}")
            
            # Test Entity Controls
            print("\n✅ Test 8: Entity State Changes")
            
            # Test select entity
            print("\n   Testing select.pixoo_channel:")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/select/select_option",
                    headers=headers,
                    json={
                        "entity_id": "select.pixoo_channel",
                        "option": "faces",
                    },
                )
                if response.status_code == 200:
                    print("      ✅ Changed to 'faces'")
                else:
                    print(f"      ❌ Failed: {response.status_code}")
            except Exception as err:
                print(f"      ❌ Error: {err}")
            
            await asyncio.sleep(1)
            
            # Test number entity
            print("\n   Testing number.pixoo_timer_minutes:")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/number/set_value",
                    headers=headers,
                    json={
                        "entity_id": "number.pixoo_timer_minutes",
                        "value": 5,
                    },
                )
                if response.status_code == 200:
                    print("      ✅ Set to 5 minutes")
                else:
                    print(f"      ❌ Failed: {response.status_code}")
            except Exception as err:
                print(f"      ❌ Error: {err}")
            
            # Test switch entity
            print("\n   Testing switch.pixoo_timer:")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/switch/turn_on",
                    headers=headers,
                    json={
                        "entity_id": "switch.pixoo_timer",
                    },
                )
                if response.status_code == 200:
                    print("      ✅ Timer started")
                else:
                    print(f"      ❌ Failed: {response.status_code}")
            except Exception as err:
                print(f"      ❌ Error: {err}")
            
            await asyncio.sleep(2)
            
            # Turn off timer
            try:
                response = await client.post(
                    f"{ha_url}/api/services/switch/turn_off",
                    headers=headers,
                    json={
                        "entity_id": "switch.pixoo_timer",
                    },
                )
                if response.status_code == 200:
                    print("      ✅ Timer stopped")
            except Exception as err:
                print(f"      ❌ Error: {err}")
            
            # Test light control
            print("\n   Testing light.pixoo_display:")
            try:
                response = await client.post(
                    f"{ha_url}/api/services/light/turn_on",
                    headers=headers,
                    json={
                        "entity_id": light_entity,
                        "brightness": 200,
                    },
                )
                if response.status_code == 200:
                    print("      ✅ Brightness set to 200")
                else:
                    print(f"      ❌ Failed: {response.status_code}")
            except Exception as err:
                print(f"      ❌ Error: {err}")
            
            print("\n" + "=" * 80)
            print("✅ Service testing complete!")
            print("\nNote: Check the Pixoo display to verify visual changes.")
            print("      Check HA logs for any error messages.")
            
            return True
            
        except httpx.HTTPError as err:
            print(f"\n❌ HTTP Error: {err}")
            return False
        except Exception as err:
            print(f"\n❌ Error: {err}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Run the service tests."""
    success = await test_services()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
