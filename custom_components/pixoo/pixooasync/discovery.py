"""Device discovery utilities for finding Pixoo devices on the local network."""

from typing import TYPE_CHECKING

import httpx

from .models import DiscoveredDevice

if TYPE_CHECKING:
    from .client import Pixoo, PixooAsync

DIVOOM_API_URL = "https://app.divoom-gz.com"


def discover_devices(timeout: float = 5.0) -> list[DiscoveredDevice]:
    """Discover Pixoo devices on the local network.

    Uses the Divoom cloud API to find devices on the same LAN.

    Args:
        timeout: Request timeout in seconds

    Returns:
        List of discovered devices

    Example:
        >>> from .discovery import discover_devices
        >>> devices = discover_devices()
        >>> for device in devices:
        ...     print(f"{device.device_name} at {device.device_private_ip}")
        Pixoo-64 at 192.168.1.100

    Raises:
        httpx.HTTPError: If the request fails
    """
    with httpx.Client(timeout=timeout) as client:
        response = client.post(f"{DIVOOM_API_URL}/Device/ReturnSameLANDevice")
        data = response.json()

        # Parse device list
        device_list = data.get("DeviceList", [])
        return [
            DiscoveredDevice(
                device_name=device.get("DeviceName", "Unknown"),
                device_id=device.get("DeviceId", 0),
                device_private_ip=device.get("DevicePrivateIP", ""),
                device_mac=device.get("DeviceMac", ""),
            )
            for device in device_list
        ]


async def discover_devices_async(timeout: float = 5.0) -> list[DiscoveredDevice]:
    """Discover Pixoo devices on the local network (async version).

    Uses the Divoom cloud API to find devices on the same LAN.

    Args:
        timeout: Request timeout in seconds

    Returns:
        List of discovered devices

    Example:
        >>> import asyncio
        >>> from .discovery import discover_devices_async
        >>> devices = asyncio.run(discover_devices_async())
        >>> for device in devices:
        ...     print(f"{device.device_name} at {device.device_private_ip}")
        Pixoo-64 at 192.168.1.100

    Raises:
        httpx.HTTPError: If the request fails
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(f"{DIVOOM_API_URL}/Device/ReturnSameLANDevice")
        data = response.json()

        # Parse device list
        device_list = data.get("DeviceList", [])
        return [
            DiscoveredDevice(
                device_name=device.get("DeviceName", "Unknown"),
                device_id=device.get("DeviceId", 0),
                device_private_ip=device.get("DevicePrivateIP", ""),
                device_mac=device.get("DeviceMac", ""),
            )
            for device in device_list
        ]


def create_pixoo_from_discovery(
    timeout: float = 5.0,
    device_index: int = 0,
    size: int = 64,
    debug: bool = False,
) -> "Pixoo":
    """Create a Pixoo client by auto-discovering devices.

    Discovers devices on the local network and creates a Pixoo client
    for the specified device (default: first device found).

    Args:
        timeout: Discovery timeout in seconds
        device_index: Index of device to connect to (0 = first device)
        size: Display size (16, 32, or 64)
        debug: Enable debug logging

    Returns:
        Configured Pixoo client

    Raises:
        RuntimeError: If no devices found or index out of range

    Example:
        >>> # Connect to first discovered device
        >>> pixoo = create_pixoo_from_discovery()
        >>> pixoo.draw_text("Auto-discovered!", (0, 0))
        >>> pixoo.push()

        >>> # Connect to second device
        >>> pixoo = create_pixoo_from_discovery(device_index=1)
    """
    from .client import Pixoo

    devices = discover_devices(timeout=timeout)

    if not devices:
        raise RuntimeError("No Pixoo devices found on network")

    if device_index >= len(devices):
        raise RuntimeError(
            f"Device index {device_index} out of range (found {len(devices)} devices)"
        )

    device = devices[device_index]
    return Pixoo(device.device_private_ip, size=size, debug=debug)


async def create_pixoo_from_discovery_async(
    timeout: float = 5.0,
    device_index: int = 0,
    size: int = 64,
    debug: bool = False,
) -> "PixooAsync":
    """Create a PixooAsync client by auto-discovering devices (async version).

    Discovers devices on the local network and creates a PixooAsync client
    for the specified device (default: first device found).

    Args:
        timeout: Discovery timeout in seconds
        device_index: Index of device to connect to (0 = first device)
        size: Display size (16, 32, or 64)
        debug: Enable debug logging

    Returns:
        Configured PixooAsync client

    Raises:
        RuntimeError: If no devices found or index out of range

    Example:
        >>> import asyncio
        >>> async def main():
        ...     pixoo = await create_pixoo_from_discovery_async()
        ...     await pixoo.draw_text_async("Auto-discovered!", (0, 0))
        ...     await pixoo.push_async()
        ...     await pixoo.close_async()
        >>> asyncio.run(main())
    """
    from .client import PixooAsync

    devices = await discover_devices_async(timeout=timeout)

    if not devices:
        raise RuntimeError("No Pixoo devices found on network")

    if device_index >= len(devices):
        raise RuntimeError(
            f"Device index {device_index} out of range (found {len(devices)} devices)"
        )

    device = devices[device_index]
    return PixooAsync(device.device_private_ip, size=size, debug=debug)
