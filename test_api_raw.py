#!/usr/bin/env python3
"""Test raw API responses from Pixoo device."""
import asyncio
import json
import httpx


async def test():
    """Test API endpoints."""
    url = "http://192.168.188.65/post"
    
    # Test Device Info
    print("=== Device/GetDeviceInfo ===")
    payload = {"Command": "Device/GetDeviceInfo"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()
        print(json.dumps(data, indent=2))
    
    print("\n=== Device/GetNetworkStatus ===")
    payload = {"Command": "Device/GetNetworkStatus"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()
        print(json.dumps(data, indent=2))
    
    print("\n=== Device/GetSystemConfig ===")
    payload = {"Command": "Device/GetSystemConfig"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()
        print(json.dumps(data, indent=2))
    
    print("\n=== Channel/GetIndex ===")
    payload = {"Command": "Channel/GetIndex"}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(test())
