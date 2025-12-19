#!/usr/bin/env python3
"""
Debug script to test pixooasync API read/write capabilities.

This script tests what state the Pixoo device returns after various operations
to document which properties are readable vs write-only.

Usage:
    python debug_pixoo_api.py 192.168.1.100
"""

import asyncio
import sys
from typing import Any

# Ensure pixooasync is available - adjust path as needed
sys.path.insert(0, '/Users/jankampling/Repositories/pixoo-ha/custom_components/pixoo')

from pixooasync import PixooAsync
from pixooasync.enums import Channel
from pixooasync.models import SystemConfig, NetworkStatus, DeviceInfo


class PixooAPITester:
    """Test Pixoo API to determine read/write capabilities."""
    
    def __init__(self, ip_address: str):
        """Initialize with device IP."""
        self.ip = ip_address
        self.pixoo = PixooAsync(ip_address)
        self.results = {}
        self._client_created = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.pixoo.__aenter__()
        self._client_created = True
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self._client_created:
            await self.pixoo.__aexit__(*args)
    
    async def test_device_info(self):
        """Test device info read."""
        print("\n" + "="*60)
        print("TEST 1: Device Info (READ)")
        print("="*60)
        try:
            info: DeviceInfo = await self.pixoo.get_device_info()
            print(f"✓ Device info readable")
            print(f"  Model: {info.device_model}")
            print(f"  Firmware: {info.software_version}")
            print(f"  Brightness: {info.brightness}")
            self.results['device_info'] = {'readable': True, 'data': info}
        except Exception as e:
            print(f"✗ Device info failed: {e}")
            self.results['device_info'] = {'readable': False, 'error': str(e)}
    
    async def test_system_config(self):
        """Test system config read."""
        print("\n" + "="*60)
        print("TEST 2: System Config (READ)")
        print("="*60)
        try:
            config: SystemConfig = await self.pixoo.get_system_config()
            print(f"✓ System config readable")
            print(f"  Brightness: {config.brightness}")
            print(f"  Rotation: {config.rotation}")
            print(f"  Mirror mode: {config.mirror_mode}")
            print(f"  Screen power: {config.screen_power}")
            self.results['system_config'] = {'readable': True, 'data': config}
        except Exception as e:
            print(f"✗ System config failed: {e}")
            self.results['system_config'] = {'readable': False, 'error': str(e)}
    
    async def test_network_status(self):
        """Test network status read."""
        print("\n" + "="*60)
        print("TEST 3: Network Status (READ)")
        print("="*60)
        try:
            status: NetworkStatus = await self.pixoo.get_network_status()
            print(f"✓ Network status readable")
            print(f"  IP: {status.ip_address}")
            print(f"  MAC: {status.mac_address}")
            print(f"  SSID: {status.ssid}")
            print(f"  RSSI: {status.rssi}")
            self.results['network_status'] = {'readable': True, 'data': status}
        except Exception as e:
            print(f"✗ Network status failed: {e}")
            self.results['network_status'] = {'readable': False, 'error': str(e)}
    
    async def test_channel_write_read(self):
        """Test channel write and subsequent read."""
        print("\n" + "="*60)
        print("TEST 4: Channel (WRITE + READ)")
        print("="*60)
        
        # Read initial state
        try:
            initial_config = await self.pixoo.get_system_config()
            print(f"Initial system config retrieved")
        except Exception as e:
            print(f"✗ Cannot read initial system config: {e}")
            initial_config = None
        
        # Write channel
        try:
            print(f"Writing channel: FACES")
            await self.pixoo.set_channel(Channel.FACES)
            print(f"✓ Channel write succeeded")
            await asyncio.sleep(1)  # Wait for device to process
        except Exception as e:
            print(f"✗ Channel write failed: {e}")
            self.results['channel'] = {'writable': False, 'readable': False, 'error': str(e)}
            return
        
        # Try to read channel back
        try:
            after_config = await self.pixoo.get_system_config()
            # Check if system config has channel info
            if hasattr(after_config, 'channel'):
                print(f"✓ Channel readable: {after_config.channel}")
                self.results['channel'] = {'writable': True, 'readable': True, 'value': after_config.channel}
            else:
                print(f"✗ Channel NOT in system config")
                print(f"  Available fields: {list(after_config.__dict__.keys())}")
                self.results['channel'] = {'writable': True, 'readable': False, 'note': 'Not in SystemConfig'}
        except Exception as e:
            print(f"✗ Channel read failed: {e}")
            self.results['channel'] = {'writable': True, 'readable': False, 'error': str(e)}
    
    async def test_brightness_write_read(self):
        """Test brightness write and read."""
        print("\n" + "="*60)
        print("TEST 5: Brightness (WRITE + READ)")
        print("="*60)
        
        # Read initial brightness
        try:
            initial_config = await self.pixoo.get_system_config()
            initial_brightness = initial_config.brightness
            print(f"Initial brightness: {initial_brightness}%")
        except Exception as e:
            print(f"✗ Cannot read initial brightness: {e}")
            return
        
        # Write new brightness
        new_brightness = 75 if initial_brightness != 75 else 50
        try:
            print(f"Writing brightness: {new_brightness}%")
            await self.pixoo.set_brightness(new_brightness)
            print(f"✓ Brightness write succeeded")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"✗ Brightness write failed: {e}")
            return
        
        # Read back
        try:
            after_config = await self.pixoo.get_system_config()
            after_brightness = after_config.brightness
            print(f"After brightness: {after_brightness}%")
            if after_brightness == new_brightness:
                print(f"✓ Brightness readable and matches written value")
                self.results['brightness'] = {'writable': True, 'readable': True, 'verified': True}
            else:
                print(f"⚠ Brightness readable but value mismatch (expected {new_brightness}, got {after_brightness})")
                self.results['brightness'] = {'writable': True, 'readable': True, 'verified': False}
        except Exception as e:
            print(f"✗ Brightness read failed: {e}")
    
    async def test_timer_write_read(self):
        """Test timer write and read."""
        print("\n" + "="*60)
        print("TEST 6: Timer (WRITE + READ)")
        print("="*60)
        
        # Try to read timer config
        print("Checking for get_timer_config method...")
        if hasattr(self.pixoo, 'get_timer_config'):
            try:
                timer = await self.pixoo.get_timer_config()
                print(f"✓ Timer config readable: {timer}")
                self.results['timer'] = {'readable': True, 'data': timer}
            except Exception as e:
                print(f"✗ Timer read failed: {e}")
                self.results['timer'] = {'readable': False, 'error': str(e)}
        else:
            print(f"✗ get_timer_config method NOT AVAILABLE in PixooAsync")
            self.results['timer'] = {'readable': False, 'note': 'Method not implemented'}
        
        # Try to write timer
        try:
            print(f"Writing timer: 5 minutes, 30 seconds")
            await self.pixoo.set_timer(minutes=5, seconds=30)
            print(f"✓ Timer write succeeded")
            self.results['timer'] = {**self.results.get('timer', {}), 'writable': True}
        except Exception as e:
            print(f"✗ Timer write failed: {e}")
            self.results['timer'] = {**self.results.get('timer', {}), 'writable': False, 'error': str(e)}
    
    async def test_alarm_write_read(self):
        """Test alarm write and read."""
        print("\n" + "="*60)
        print("TEST 7: Alarm (WRITE + READ)")
        print("="*60)
        
        # Try to read alarm config
        print("Checking for get_alarm_config method...")
        if hasattr(self.pixoo, 'get_alarm_config'):
            try:
                alarm = await self.pixoo.get_alarm_config()
                print(f"✓ Alarm config readable: {alarm}")
                self.results['alarm'] = {'readable': True, 'data': alarm}
            except Exception as e:
                print(f"✗ Alarm read failed: {e}")
                self.results['alarm'] = {'readable': False, 'error': str(e)}
        else:
            print(f"✗ get_alarm_config method NOT AVAILABLE in PixooAsync")
            self.results['alarm'] = {'readable': False, 'note': 'Method not implemented'}
        
        # Try to write alarm
        try:
            print(f"Writing alarm: 7:30")
            await self.pixoo.set_alarm(hour=7, minute=30)
            print(f"✓ Alarm write succeeded")
            self.results['alarm'] = {**self.results.get('alarm', {}), 'writable': True}
        except Exception as e:
            print(f"✗ Alarm write failed: {e}")
            self.results['alarm'] = {**self.results.get('alarm', {}), 'writable': False, 'error': str(e)}
    
    async def test_stopwatch_write_read(self):
        """Test stopwatch write and read."""
        print("\n" + "="*60)
        print("TEST 8: Stopwatch (WRITE + READ)")
        print("="*60)
        
        # Try to read stopwatch config
        print("Checking for get_stopwatch_config method...")
        if hasattr(self.pixoo, 'get_stopwatch_config'):
            try:
                stopwatch = await self.pixoo.get_stopwatch_config()
                print(f"✓ Stopwatch config readable: {stopwatch}")
                self.results['stopwatch'] = {'readable': True, 'data': stopwatch}
            except Exception as e:
                print(f"✗ Stopwatch read failed: {e}")
                self.results['stopwatch'] = {'readable': False, 'error': str(e)}
        else:
            print(f"✗ get_stopwatch_config method NOT AVAILABLE in PixooAsync")
            self.results['stopwatch'] = {'readable': False, 'note': 'Method not implemented'}
        
        # Try to start stopwatch
        try:
            print(f"Starting stopwatch...")
            await self.pixoo.start_stopwatch()
            print(f"✓ Stopwatch start succeeded")
            await asyncio.sleep(2)
            
            print(f"Resetting stopwatch...")
            await self.pixoo.reset_stopwatch()
            print(f"✓ Stopwatch reset succeeded")
            self.results['stopwatch'] = {**self.results.get('stopwatch', {}), 'writable': True}
        except Exception as e:
            print(f"✗ Stopwatch write failed: {e}")
            self.results['stopwatch'] = {**self.results.get('stopwatch', {}), 'writable': False, 'error': str(e)}
    
    async def print_summary(self):
        """Print summary of findings."""
        print("\n" + "="*60)
        print("SUMMARY: Pixoo API Read/Write Capabilities")
        print("="*60)
        
        print("\n✓ READABLE Properties:")
        for key, value in self.results.items():
            if value.get('readable'):
                print(f"  - {key}")
        
        print("\n✗ WRITE-ONLY Properties:")
        for key, value in self.results.items():
            if value.get('writable') and not value.get('readable'):
                note = value.get('note', 'No read method available')
                print(f"  - {key} ({note})")
        
        print("\n⚠ UNREADABLE (Methods Missing):")
        for key, value in self.results.items():
            if value.get('readable') is False and value.get('note'):
                print(f"  - {key}: {value.get('note')}")
        
        print("\n" + "="*60)
        print("RECOMMENDATIONS FOR HA INTEGRATION")
        print("="*60)
        
        write_only_props = [k for k, v in self.results.items() 
                           if v.get('writable') and not v.get('readable')]
        
        if write_only_props:
            print(f"\n✓ For write-only properties ({', '.join(write_only_props)}):")
            print(f"  1. DON'T use CoordinatorEntity - no data to coordinate")
            print(f"  2. Store state in entity instance variables")
            print(f"  3. Use RestoreEntity to persist across restarts")
            print(f"  4. Override available property: return True (always available)")
            print(f"  5. Pattern:")
            print(f"     class MyEntity(PixooEntity, RestoreEntity):")
            print(f"         _attr_assumed_state = True")
            print(f"         self._state = value  # Store locally")
        
        print(f"\n✓ For readable properties (e.g., brightness):")
        print(f"  1. Use CoordinatorEntity normally")
        print(f"  2. Read from coordinator.data")
        print(f"  3. Coordinator polls device periodically")

    async def run_all_tests(self):
        """Run all tests."""
        print(f"Testing Pixoo device at {self.ip}")
        print(f"Using PixooAsync library\n")
        
        await self.test_device_info()
        await self.test_system_config()
        await self.test_network_status()
        await self.test_channel_write_read()
        await self.test_brightness_write_read()
        await self.test_timer_write_read()
        await self.test_alarm_write_read()
        await self.test_stopwatch_write_read()
        await self.print_summary()


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python debug_pixoo_api.py <ip_address>")
        print("Example: python debug_pixoo_api.py 192.168.188.65")
        sys.exit(1)
    
    ip_address = sys.argv[1]
    
    try:
        async with PixooAPITester(ip_address) as tester:
            await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
