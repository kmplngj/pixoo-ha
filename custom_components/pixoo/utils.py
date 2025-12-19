"""Utility functions for Pixoo integration."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import aiohttp
from PIL import Image
import io

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from .const import DOWNLOAD_TIMEOUT, DOWNLOAD_MAX_SIZE

if TYPE_CHECKING:
    from pixooasync import PixooAsync

_LOGGER = logging.getLogger(__name__)


async def download_image(
    hass: HomeAssistant,
    url: str,
    target_size: tuple[int, int] = (64, 64),
) -> bytes:
    """
    Download and process an image from a URL.
    
    Args:
        hass: Home Assistant instance
        url: URL to download image from
        target_size: Target size to resize image to (width, height)
    
    Returns:
        Processed image as bytes (RGB format)
    
    Raises:
        ServiceValidationError: If download fails or file is invalid
    """
    try:
        # Download image with aiohttp (async, with timeout and size limit)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT),
            ) as response:
                response.raise_for_status()
                
                # Validate content-type
                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("image/") and content_type != "application/octet-stream":
                    raise ServiceValidationError(
                        f"Invalid content type: {content_type}. Expected image/*"
                    )
                
                # Download with size limit
                content = bytearray()
                async for chunk in response.content.iter_chunked(8192):
                    content.extend(chunk)
                    if len(content) > DOWNLOAD_MAX_SIZE:
                        raise ServiceValidationError(
                            f"Image size exceeds {DOWNLOAD_MAX_SIZE / 1024 / 1024:.1f}MB limit"
                        )
                
                image_data = bytes(content)
        
        # Process image with Pillow in executor (blocking operation)
        def process_image(data: bytes) -> bytes:
            """Process image data in executor."""
            try:
                # Open image
                img = Image.open(io.BytesIO(data))
                
                # Convert to RGB (remove alpha channel)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Resize with high-quality resampling
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                
                # Convert to bytes
                output = io.BytesIO()
                img.save(output, format="PNG")
                return output.getvalue()
            except Exception as err:
                raise ServiceValidationError(f"Failed to process image: {err}") from err
        
        processed_image = await hass.async_add_executor_job(process_image, image_data)
        return processed_image
        
    except aiohttp.ClientError as err:
        raise ServiceValidationError(f"Failed to download image: {err}") from err
    except asyncio.TimeoutError as err:
        raise ServiceValidationError(
            f"Image download timeout after {DOWNLOAD_TIMEOUT}s"
        ) from err
    except Exception as err:
        if isinstance(err, ServiceValidationError):
            raise
        raise ServiceValidationError(f"Error processing image: {err}") from err
