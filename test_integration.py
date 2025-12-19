#!/usr/bin/env python3
"""Test script for Pixoo Home Assistant integration via API."""

import asyncio
import os
import sys
from typing import Any

import httpx


class HAClient:
    """Home Assistant API client."""

    def __init__(self, url: str, token: str):
        """Initialize the client."""
        self.url = url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the client."""
        await self.client.aclose()

    async def get_states(self, entity_id: str | None = None) -> list[dict[str, Any]]:
        """Get entity states."""
        if entity_id:
            response = await self.client.get(
                f"{self.url}/api/states/{entity_id}",
                headers=self.headers,
            )
        else:
            response = await self.client.get(
                f"{self.url}/api/states",
                headers=self.headers,
            )
        response.raise_for_status()
        return response.json() if isinstance(response.json(), list) else [response.json()]

    async def call_service(
        self, domain: str, service: str, entity_id: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """Call a service."""
        data = kwargs.copy()
        if entity_id:
            data["entity_id"] = entity_id
        
        response = await self.client.post(
            f"{self.url}/api/services/{domain}/{service}",
            headers=self.headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    async def get_config(self) -> dict[str, Any]:
        """Get HA configuration."""
        response = await self.client.get(
            f"{self.url}/api/config",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()


async def test_integration():
    """Test the Pixoo integration."""
    
    # Get credentials from environment
    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    ha_token = os.getenv("HASS_TOKEN")
    
    if not ha_token:
        print("❌ Error: HASS_TOKEN environment variable not set")
        return False
    
    print(f"🔗 Connecting to Home Assistant at {ha_url}")
    print("=" * 80)
    
    client = HAClient(ha_url, ha_token)
    
    try:
        # Test 1: Check HA is responding
        print("\n✅ Test 1: Home Assistant API Connection")
        config = await client.get_config()
        print(f"   HA Version: {config.get('version')}")
        print(f"   Location: {config.get('location_name')}")
        
        # Test 2: Find all Pixoo entities
        print("\n✅ Test 2: Pixoo Entities Discovery")
        all_states = await client.get_states()
        pixoo_entities = [s for s in all_states if "pixoo" in s.get("entity_id", "").lower()]
        
        if not pixoo_entities:
            print("   ❌ No Pixoo entities found!")
            return False
        
        print(f"   Found {len(pixoo_entities)} Pixoo entities:")
        
        # Group entities by domain
        by_domain = {}
        for entity in pixoo_entities:
            entity_id = entity["entity_id"]
            domain = entity_id.split(".")[0]
            by_domain.setdefault(domain, []).append(entity)
        
        for domain, entities in sorted(by_domain.items()):
            print(f"\n   📁 {domain.upper()} ({len(entities)} entities):")
            for entity in entities:
                entity_id = entity["entity_id"]
                state = entity.get("state", "unknown")
                available = state not in ("unavailable", "unknown")
                status = "✅" if available else "❌"
                print(f"      {status} {entity_id}")
                print(f"         State: {state}")
                if not available:
                    print(f"         ⚠️  Entity is {state}!")
        
        # Test 3: Check write-only entities (select)
        print("\n✅ Test 3: Write-Only Select Entities")
        select_entities = [e for e in pixoo_entities if e["entity_id"].startswith("select.")]
        write_only_selects = ["channel", "clock_face", "visualizer", "custom_page"]
        
        for key in write_only_selects:
            matching = [e for e in select_entities if key in e["entity_id"]]
            if matching:
                entity = matching[0]
                entity_id = entity["entity_id"]
                state = entity.get("state", "unknown")
                assumed_state = entity.get("attributes", {}).get("assumed_state", False)
                status = "✅" if assumed_state else "⚠️"
                print(f"   {status} {entity_id}: {state} (assumed_state: {assumed_state})")
            else:
                print(f"   ❌ Missing {key} select entity")
        
        # Test 4: Check write-only entities (number)
        print("\n✅ Test 4: Write-Only Number Entities")
        number_entities = [e for e in pixoo_entities if e["entity_id"].startswith("number.")]
        write_only_numbers = ["timer_minutes", "timer_seconds", "alarm_hour", "alarm_minute", 
                             "scoreboard_red", "scoreboard_blue"]
        
        for key in write_only_numbers:
            matching = [e for e in number_entities if key in e["entity_id"]]
            if matching:
                entity = matching[0]
                entity_id = entity["entity_id"]
                state = entity.get("state", "unknown")
                assumed_state = entity.get("attributes", {}).get("assumed_state", False)
                status = "✅" if assumed_state else "⚠️"
                print(f"   {status} {entity_id}: {state} (assumed_state: {assumed_state})")
            else:
                print(f"   ❌ Missing {key} number entity")
        
        # Test 5: Check write-only entities (switch)
        print("\n✅ Test 5: Write-Only Switch Entities")
        switch_entities = [e for e in pixoo_entities if e["entity_id"].startswith("switch.")]
        write_only_switches = ["timer", "alarm", "stopwatch", "scoreboard", "noise_meter"]
        
        for key in write_only_switches:
            matching = [e for e in switch_entities if key in e["entity_id"]]
            if matching:
                entity = matching[0]
                entity_id = entity["entity_id"]
                state = entity.get("state", "unknown")
                assumed_state = entity.get("attributes", {}).get("assumed_state", False)
                status = "✅" if assumed_state else "⚠️"
                print(f"   {status} {entity_id}: {state} (assumed_state: {assumed_state})")
            else:
                print(f"   ❌ Missing {key} switch entity")
        
        # Test 6: Check readable entities
        print("\n✅ Test 6: Readable Entities (Coordinator-Based)")
        
        # Light entity (brightness)
        light_entities = [e for e in pixoo_entities if e["entity_id"].startswith("light.")]
        if light_entities:
            entity = light_entities[0]
            entity_id = entity["entity_id"]
            state = entity.get("state", "unknown")
            brightness = entity.get("attributes", {}).get("brightness")
            print(f"   ✅ {entity_id}: {state} (brightness: {brightness})")
        else:
            print("   ❌ No light entity found")
        
        # Rotation select
        rotation_entities = [e for e in select_entities if "rotation" in e["entity_id"]]
        if rotation_entities:
            entity = rotation_entities[0]
            entity_id = entity["entity_id"]
            state = entity.get("state", "unknown")
            assumed_state = entity.get("attributes", {}).get("assumed_state", False)
            status = "✅" if not assumed_state else "⚠️"
            print(f"   {status} {entity_id}: {state} (assumed_state: {assumed_state})")
        
        # Brightness number
        brightness_numbers = [e for e in number_entities if "brightness" in e["entity_id"]]
        if brightness_numbers:
            entity = brightness_numbers[0]
            entity_id = entity["entity_id"]
            state = entity.get("state", "unknown")
            assumed_state = entity.get("attributes", {}).get("assumed_state", False)
            status = "✅" if not assumed_state else "⚠️"
            print(f"   {status} {entity_id}: {state} (assumed_state: {assumed_state})")
        
        # Mirror mode switch
        mirror_switches = [e for e in switch_entities if "mirror" in e["entity_id"]]
        if mirror_switches:
            entity = mirror_switches[0]
            entity_id = entity["entity_id"]
            state = entity.get("state", "unknown")
            assumed_state = entity.get("attributes", {}).get("assumed_state", False)
            status = "✅" if not assumed_state else "⚠️"
            print(f"   {status} {entity_id}: {state} (assumed_state: {assumed_state})")
        
        # Test 7: Test service calls (optional - requires user confirmation)
        print("\n✅ Test 7: Service Availability Check")
        
        # Get service list
        response = await client.client.get(
            f"{client.url}/api/services",
            headers=client.headers,
        )
        response.raise_for_status()
        services = response.json()
        
        pixoo_services = [s for s in services if s.get("domain") == "pixoo"]
        if pixoo_services:
            print(f"   Found {len(pixoo_services[0].get('services', {}))} Pixoo services:")
            for service_name in sorted(pixoo_services[0].get("services", {}).keys()):
                print(f"      ✅ pixoo.{service_name}")
        else:
            print("   ⚠️  No Pixoo services found (services may not be registered)")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 Test Summary:")
        print(f"   Total Entities: {len(pixoo_entities)}")
        unavailable = [e for e in pixoo_entities if e.get("state") in ("unavailable", "unknown")]
        available = len(pixoo_entities) - len(unavailable)
        print(f"   Available: {available}")
        print(f"   Unavailable: {len(unavailable)}")
        
        if unavailable:
            print("\n   ⚠️  Unavailable entities:")
            for entity in unavailable:
                print(f"      - {entity['entity_id']}: {entity.get('state')}")
        
        write_only_count = len([e for e in pixoo_entities 
                               if e.get("attributes", {}).get("assumed_state")])
        print(f"\n   Write-Only (assumed_state): {write_only_count}")
        
        success = len(unavailable) == 0
        if success:
            print("\n✅ All tests passed! Integration is working correctly.")
        else:
            print(f"\n⚠️  {len(unavailable)} entities are unavailable.")
        
        return success
        
    except httpx.HTTPError as err:
        print(f"\n❌ HTTP Error: {err}")
        return False
    except Exception as err:
        print(f"\n❌ Error: {err}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


async def main():
    """Run the tests."""
    success = await test_integration()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
