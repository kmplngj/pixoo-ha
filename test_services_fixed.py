#!/usr/bin/env python3
"""Test Pixoo services via Home Assistant API with correct parameters."""

import asyncio
import os
from io import BytesIO

import httpx
from PIL import Image, ImageDraw


async def test_services():
    """Test all Pixoo services with correct HA API format."""
    
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
        
        # Test 1: clear_display (no parameters needed)
        print("\n✅ Test 1: pixoo.clear_display")
        try:
            response = await client.post(
                f"{ha_url}/api/services/pixoo/clear_display",
                headers=headers,
                json={},
            )
            if response.status_code == 200:
                print("   ✅ Clear display successful")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        await asyncio.sleep(2)
        
        # Test 2: display_text
        print("\n✅ Test 2: pixoo.display_text")
        try:
            response = await client.post(
                f"{ha_url}/api/services/pixoo/display_text",
                headers=headers,
                json={
                    "text": "Hello HA! ✓",
                    "color": "#00FF00",  # Green
                    "scroll_direction": "left",
                },
            )
            if response.status_code == 200:
                print("   ✅ Display text successful")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        await asyncio.sleep(3)
        
        # Test 3: set_timer
        print("\n✅ Test 3: pixoo.set_timer")
        try:
            response = await client.post(
                f"{ha_url}/api/services/pixoo/set_timer",
                headers=headers,
                json={
                    "duration": "00:30",  # 30 seconds
                },
            )
            if response.status_code == 200:
                print("   ✅ Set timer to 30 seconds")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        await asyncio.sleep(2)
        
        # Test 4: set_alarm
        print("\n✅ Test 4: pixoo.set_alarm")
        try:
            response = await client.post(
                f"{ha_url}/api/services/pixoo/set_alarm",
                headers=headers,
                json={
                    "time": "09:00",
                    "enabled": True,
                },
            )
            if response.status_code == 200:
                print("   ✅ Set alarm to 09:00")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        await asyncio.sleep(2)
        
        # Test 5: play_buzzer
        print("\n✅ Test 5: pixoo.play_buzzer")
        try:
            response = await client.post(
                f"{ha_url}/api/services/pixoo/play_buzzer",
                headers=headers,
                json={
                    "active_ms": 200,
                    "off_ms": 200,
                    "count": 3,
                },
            )
            if response.status_code == 200:
                print("   ✅ Play buzzer (3 beeps)")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        await asyncio.sleep(2)
        
        # Test 6: display_image (with generated test image)
        print("\n✅ Test 6: pixoo.display_image")
        try:
            # Create a simple 64x64 test image
            img = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, 54, 54], fill='yellow')
            draw.ellipse([20, 20, 44, 44], fill='red')
            
            # Save to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # For this test, we'd need to upload to a URL first
            # For now, just use a public URL
            response = await client.post(
                f"{ha_url}/api/services/pixoo/display_image",
                headers=headers,
                json={
                    "url": "https://raw.githubusercontent.com/home-assistant/brands/master/core_integrations/homeassistant/icon.png",
                },
            )
            if response.status_code == 200:
                print("   ✅ Display image successful")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        await asyncio.sleep(2)
        
        # Test 7: list_animations
        print("\n✅ Test 7: pixoo.list_animations")
        try:
            response = await client.post(
                f"{ha_url}/api/services/pixoo/list_animations",
                headers=headers,
                json={},
            )
            if response.status_code == 200:
                print("   ✅ List animations successful (check HA logs)")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
        await asyncio.sleep(1)
        
        # Test 8: Final clear
        print("\n✅ Test 8: Final clear_display")
        try:
            response = await client.post(
                f"{ha_url}/api/services/pixoo/clear_display",
                headers=headers,
                json={},
            )
            if response.status_code == 200:
                print("   ✅ Clear display successful")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as err:
            print(f"   ❌ Error: {err}")
        
    print("\n" + "=" * 80)
    print("✅ All service tests complete!")
    print("\nResults:")
    print("  - All 7 core services tested")
    print("  - Check Pixoo display for visual confirmation")
    print("  - Check HA logs for animation list output")
    return True


if __name__ == "__main__":
    asyncio.run(test_services())
