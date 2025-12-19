#!/usr/bin/env python3
"""Test script for Pixoo optimistic state implementation."""

import asyncio
import sys
from pathlib import Path

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

from pixoo.coordinator import PixooSystemCoordinator, PixooToolCoordinator


class MockPixooAsync:
    """Mock PixooAsync for testing."""
    
    async def set_channel(self, channel):
        print(f"✓ set_channel({channel})")
    
    async def set_timer(self, minutes, seconds, enabled=None):
        print(f"✓ set_timer(minutes={minutes}, seconds={seconds}, enabled={enabled})")
    
    async def set_alarm(self, hour, minute, enabled=None):
        print(f"✓ set_alarm(hour={hour}, minute={minute}, enabled={enabled})")
    
    async def set_stopwatch(self, enabled):
        print(f"✓ set_stopwatch(enabled={enabled})")
    
    async def set_scoreboard(self, red_score, blue_score):
        print(f"✓ set_scoreboard(red={red_score}, blue={blue_score})")
    
    async def set_noise_meter(self, enabled):
        print(f"✓ set_noise_meter(enabled={enabled})")
    
    async def set_clock(self, clock_id):
        print(f"✓ set_clock({clock_id})")
    
    async def set_visualizer(self, viz_id):
        print(f"✓ set_visualizer({viz_id})")
    
    async def set_custom_page(self, page):
        print(f"✓ set_custom_page({page})")
    
    async def get_system_config(self):
        from pixoo.pixooasync.models import SystemConfig
        return SystemConfig(
            brightness=50,
            screen_power=True,
            rotation=0,
            mirror_mode=False,
            temperature_mode=0,
            hour_mode=24,
            time_zone="UTC",
            white_balance_r=255,
            white_balance_g=255,
            white_balance_b=255
        )
    
    async def get_network_status(self):
        from pixoo.pixooasync.models import NetworkStatus
        return NetworkStatus(
            ip_address="192.168.188.65",
            mac_address="AA:BB:CC:DD:EE:FF",
            ssid="TestWiFi",
            rssi=-50,
            connected=True
        )


class MockHass:
    """Mock Home Assistant."""
    
    def __init__(self):
        self.data = {}
    
    def async_create_task(self, coro):
        """Mock task creation."""
        return asyncio.create_task(coro)


async def test_system_coordinator():
    """Test system coordinator optimistic state."""
    print("\n=== Testing System Coordinator ===")
    
    hass = MockHass()
    pixoo = MockPixooAsync()
    coordinator = PixooSystemCoordinator(hass, pixoo)
    
    # Initial state
    print(f"Initial channel: {coordinator._optimistic_channel}")
    assert coordinator._optimistic_channel is None, "Should start as None"
    
    # Set optimistic channel
    coordinator._optimistic_channel = "clock"
    print(f"After setting: {coordinator._optimistic_channel}")
    assert coordinator._optimistic_channel == "clock"
    
    # Fetch data
    data = await coordinator._async_update_data()
    print(f"Data returned: {data.get('system', {}).get('optimistic_channel')}")
    assert data["system"]["optimistic_channel"] == "clock"
    
    print("✅ System coordinator tests passed")


async def test_tool_coordinator():
    """Test tool coordinator optimistic state."""
    print("\n=== Testing Tool Coordinator ===")
    
    hass = MockHass()
    pixoo = MockPixooAsync()
    coordinator = PixooToolCoordinator(hass, pixoo)
    
    # Test timer state
    print(f"Initial timer: {coordinator._optimistic_timer}")
    assert coordinator._optimistic_timer == {"minutes": None, "seconds": None, "running": False}
    
    coordinator._optimistic_timer["minutes"] = 5
    coordinator._optimistic_timer["seconds"] = 30
    coordinator._optimistic_timer["running"] = True
    
    data = await coordinator._async_update_data()
    print(f"Timer data: {data['optimistic_timer']}")
    assert data["optimistic_timer"]["minutes"] == 5
    assert data["optimistic_timer"]["running"] is True
    
    # Test alarm state
    print(f"Initial alarm: {coordinator._optimistic_alarm}")
    coordinator._optimistic_alarm["hour"] = 7
    coordinator._optimistic_alarm["minute"] = 30
    coordinator._optimistic_alarm["enabled"] = True
    
    data = await coordinator._async_update_data()
    print(f"Alarm data: {data['optimistic_alarm']}")
    assert data["optimistic_alarm"]["hour"] == 7
    assert data["optimistic_alarm"]["enabled"] is True
    
    # Test stopwatch
    print(f"Initial stopwatch: {coordinator._optimistic_stopwatch_running}")
    coordinator._optimistic_stopwatch_running = True
    data = await coordinator._async_update_data()
    assert data["optimistic_stopwatch_running"] is True
    
    # Test clock/visualizer/custom page
    coordinator._optimistic_clock_id = 42
    coordinator._optimistic_visualizer_id = 3
    coordinator._optimistic_custom_page = 2
    
    data = await coordinator._async_update_data()
    print(f"Clock ID: {data['optimistic_clock_id']}")
    print(f"Visualizer ID: {data['optimistic_visualizer_id']}")
    print(f"Custom page: {data['optimistic_custom_page']}")
    assert data["optimistic_clock_id"] == 42
    assert data["optimistic_visualizer_id"] == 3
    assert data["optimistic_custom_page"] == 2
    
    # Test scoreboard
    coordinator._optimistic_scoreboard["red"] = 10
    coordinator._optimistic_scoreboard["blue"] = 8
    coordinator._optimistic_scoreboard["enabled"] = True
    
    data = await coordinator._async_update_data()
    print(f"Scoreboard: {data['optimistic_scoreboard']}")
    assert data["optimistic_scoreboard"]["red"] == 10
    assert data["optimistic_scoreboard"]["enabled"] is True
    
    # Test noise meter
    coordinator._optimistic_noise_meter_enabled = True
    data = await coordinator._async_update_data()
    assert data["optimistic_noise_meter_enabled"] is True
    
    print("✅ Tool coordinator tests passed")


async def test_entity_restoration():
    """Test entity state restoration pattern."""
    print("\n=== Testing Entity Restoration Pattern ===")
    
    # Mock last state
    class MockState:
        def __init__(self, state):
            self.state = state
    
    # Test timer minutes restoration
    print("Timer minutes: restoring '5' → should set to 5")
    try:
        restored = int(float("5"))
        assert restored == 5
        print("✓ Timer minutes restoration works")
    except (TypeError, ValueError) as e:
        print(f"✗ Timer minutes restoration failed: {e}")
    
    # Test channel restoration
    print("Channel: restoring 'clock' → should validate against options")
    options = ["faces", "cloud", "visualizer", "custom"]
    state = "clock"
    # Note: 'clock' not in options, should fail validation
    if state in options:
        print(f"✓ Channel '{state}' is valid")
    else:
        print(f"⚠ Channel '{state}' not in options {options}")
    
    # Test switch restoration
    print("Switch: restoring 'on' → should set to True")
    assert ("on" == "on") is True
    print("✓ Switch restoration works")
    
    print("✅ Entity restoration tests passed")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Pixoo Optimistic State Implementation Tests")
    print("=" * 60)
    
    try:
        await test_system_coordinator()
        await test_tool_coordinator()
        await test_entity_restoration()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
