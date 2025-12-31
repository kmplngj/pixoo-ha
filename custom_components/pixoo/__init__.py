"""The Divoom Pixoo integration."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from io import BytesIO
from typing import Any

from PIL import Image

from .pixooasync import PixooAsync
from .pixooasync.enums import TextScrollDirection
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    CONF_DEVICE_SIZE,
    SERVICE_DISPLAY_IMAGE,
    SERVICE_DISPLAY_IMAGE_DATA,
    SERVICE_DISPLAY_GIF,
    SERVICE_DISPLAY_TEXT,
    SERVICE_CLEAR_DISPLAY,
    SERVICE_PLAY_BUZZER,
    SERVICE_LIST_ANIMATIONS,
    SERVICE_PLAY_ANIMATION,
    SERVICE_SEND_PLAYLIST,
    SERVICE_SET_TIMER,
    SERVICE_SET_ALARM,
    SERVICE_SET_WHITE_BALANCE,
    SERVICE_DRAW_PIXEL,
    SERVICE_DRAW_LINE,
    SERVICE_DRAW_RECTANGLE,
    SERVICE_DRAW_TEXT_AT_POSITION,
    SERVICE_FILL_SCREEN,
    SERVICE_CLEAR_BUFFER,
    SERVICE_PUSH_BUFFER,
    SERVICE_QUEUE_WARNING_DEPTH,
)
from .utils import download_image
from .coordinator import (
    PixooSystemCoordinator,
    PixooWeatherCoordinator,
    PixooGalleryCoordinator,
)

_LOGGER = logging.getLogger(__name__)

# Platforms to set up
PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.MEDIA_PLAYER,
    Platform.NOTIFY,
]


def _resolve_entry_ids(
    hass: HomeAssistant, entity_ids: list[str] | None
) -> list[ConfigEntry]:
    """Resolve entity IDs to config entries.
    
    This helper function properly resolves entity IDs (like "light.pixoo_display")
    to their corresponding config entry IDs, then returns the matching entries.
    Without this, entity_id filtering would fail since entity_id != entry_id.
    """
    if not entity_ids:
        return hass.config_entries.async_entries(DOMAIN)
    
    entity_registry = er.async_get(hass)
    entry_ids = set()
    for entity_id in entity_ids:
        if entity := entity_registry.async_get(entity_id):
            entry_ids.add(entity.config_entry_id)
    
    return [e for e in hass.config_entries.async_entries(DOMAIN) if e.entry_id in entry_ids]


class ServiceQueue:
    """FIFO queue for service calls per device."""

    def __init__(self, entry_id: str) -> None:
        """Initialize the service queue."""
        self.entry_id = entry_id
        self._queue: deque = deque()
        self._lock = asyncio.Lock()
        self._processing = False

    async def enqueue(self, coro) -> None:
        """Add a service call to the queue and process if not already processing."""
        async with self._lock:
            self._queue.append(coro)
            queue_depth = len(self._queue)

            if queue_depth >= SERVICE_QUEUE_WARNING_DEPTH:
                _LOGGER.warning(
                    "Service queue depth for %s is %d (>= %d). Consider reducing automation frequency.",
                    self.entry_id,
                    queue_depth,
                    SERVICE_QUEUE_WARNING_DEPTH,
                )

        # Start processing if not already running
        if not self._processing:
            await self._process_queue()

    async def _process_queue(self) -> None:
        """Process queued service calls in FIFO order."""
        self._processing = True

        while True:
            async with self._lock:
                if not self._queue:
                    self._processing = False
                    return
                coro = self._queue.popleft()

            try:
                await coro
            except Exception as err:
                _LOGGER.error("Error processing service call: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pixoo from a config entry."""
    host = entry.data[CONF_HOST]
    device_size = entry.data.get(CONF_DEVICE_SIZE, 64)  # Default to 64 for backward compatibility

    # Create Pixoo client with correct device size
    pixoo = PixooAsync(host, size=device_size)

    # Initialize the client (creates httpx.AsyncClient without blocking)
    await pixoo.initialize()

    # Test connection with working API (Channel/GetAllConf)
    try:
        await pixoo.get_all_channel_config()
    except Exception as err:
        _LOGGER.error("Failed to connect to Pixoo device at %s: %s", host, err)
        raise ConfigEntryNotReady(f"Failed to connect to device: {err}") from err

    # Initialize coordinators (device coordinator removed - API doesn't work)
    system_coordinator = PixooSystemCoordinator(hass, pixoo)
    weather_coordinator = PixooWeatherCoordinator(hass, pixoo)
    gallery_coordinator = PixooGalleryCoordinator(hass, pixoo)

    # Fetch initial data
    await system_coordinator.async_config_entry_first_refresh()
    await weather_coordinator.async_config_entry_first_refresh()

    # Initialize service queue
    service_queue = ServiceQueue(entry.entry_id)

    # Store coordinators in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "pixoo": pixoo,
        "coordinators": {
            "system": system_coordinator,
            "weather": weather_coordinator,
            "gallery": gallery_coordinator,
        },
        "service_queue": service_queue,
        "entry": entry,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass)

    return True


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the Pixoo integration."""

    async def handle_display_image(call: ServiceCall) -> None:
        """Handle display_image service call."""
        url = call.data["url"]
        entity_ids = call.data.get("entity_id")

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        # Queue service calls for each device
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]
            device_size = entry.data.get(CONF_DEVICE_SIZE, 64)

            async def _execute():
                try:
                    # Download image with correct device size
                    image_data = await download_image(hass, url, target_size=(device_size, device_size))
                    # Convert bytes to PIL Image, draw to buffer, then push
                    image = Image.open(BytesIO(image_data))
                    pixoo.draw_image(image, xy=(0, 0))
                    await pixoo.push()
                except Exception as err:
                    _LOGGER.error("Failed to display image on %s: %s", entry.data[CONF_HOST], err)
                    raise HomeAssistantError(f"Failed to display image: {err}") from err

            await service_queue.enqueue(_execute())

    async def handle_display_image_data(call: ServiceCall) -> None:
        """Handle display_image_data service call with base64 encoded image."""
        import base64
        
        image_data_b64 = call.data.get("image_data")
        entity_ids = call.data.get("entity_id")

        # Decode base64 image data
        try:
            image_data = base64.b64decode(image_data_b64)
        except Exception as err:
            raise ServiceValidationError(f"Failed to decode base64 image data: {err}") from err

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        # Queue service calls for each device
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _execute():
                try:
                    # Convert bytes to PIL Image, draw to buffer, then push
                    image = Image.open(BytesIO(image_data))
                    pixoo.draw_image(image, xy=(0, 0))
                    await pixoo.push()
                except Exception as err:
                    _LOGGER.error("Failed to display image data on %s: %s", entry.data[CONF_HOST], err)
                    raise HomeAssistantError(f"Failed to display image data: {err}") from err

            await service_queue.enqueue(_execute())

    async def handle_display_gif(call: ServiceCall) -> None:
        """Handle display_gif service call."""
        url = call.data["url"]
        entity_ids = call.data.get("entity_id")

        # Download GIF
        try:
            gif_data = await download_image(hass, url)
        except Exception as err:
            raise ServiceValidationError(f"Failed to download GIF: {err}") from err

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        # Send to all target devices
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]

            try:
                await pixoo.display_gif_from_bytes(gif_data)
            except Exception as err:
                _LOGGER.error("Failed to display GIF on %s: %s", entry.data[CONF_HOST], err)
                raise HomeAssistantError(f"Failed to display GIF: {err}") from err

    async def handle_display_text(call: ServiceCall) -> None:
        """Handle display_text service call."""
        text = call.data["text"]
        color = call.data.get("color", "#FFFFFF")
        x = call.data.get("x", 0)
        y = call.data.get("y", 0)
        font = call.data.get("font", 2)
        speed = call.data.get("speed", 0)
        text_id = call.data.get("text_id", 1)
        scroll_direction = call.data.get("scroll_direction", "left")
        entity_ids = call.data.get("entity_id")

        # Parse color: accept both hex string "#RRGGBB" or RGB list [R, G, B]
        if isinstance(color, list) and len(color) == 3:
            # RGB list from color_rgb selector: [255, 0, 0]
            r, g, b = int(color[0]), int(color[1]), int(color[2])
        elif isinstance(color, str):
            # Hex string: "#FF0000" or "FF0000"
            color_hex = color.lstrip("#")
            try:
                r = int(color_hex[0:2], 16)
                g = int(color_hex[2:4], 16)
                b = int(color_hex[4:6], 16)
            except (ValueError, IndexError) as err:
                raise ServiceValidationError(f"Invalid color hex format: {color}") from err
        else:
            raise ServiceValidationError(f"Invalid color format: {color}. Use hex string '#RRGGBB' or RGB list [R,G,B]")

        # Map scroll direction to enum
        direction_map = {
            "left": TextScrollDirection.LEFT,
            "right": TextScrollDirection.RIGHT,
        }
        direction = direction_map.get(scroll_direction, TextScrollDirection.LEFT)

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        # Send to all target devices
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            device_size = entry.data.get(CONF_DEVICE_SIZE, 64)

            try:
                # Use all configurable parameters for media player automation support
                await pixoo.send_text(
                    text=text,
                    xy=(x, y),
                    color=(r, g, b),
                    identifier=text_id,
                    font=font,
                    width=device_size,
                    movement_speed=speed,
                    direction=direction,
                )
            except Exception as err:
                _LOGGER.error("Failed to display text on %s: %s", entry.data[CONF_HOST], err)
                raise HomeAssistantError(f"Failed to display text: {err}") from err

    async def handle_clear_display(call: ServiceCall) -> None:
        """Handle clear_display service call."""
        entity_ids = call.data.get("entity_id")

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        # Clear all target devices
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]

            try:
                # Fixed: Use clear() method and push buffer
                pixoo.clear()
                await pixoo.push()
            except Exception as err:
                _LOGGER.error("Failed to clear display on %s: %s", entry.data[CONF_HOST], err)
                raise HomeAssistantError(f"Failed to clear display: {err}") from err

    async def handle_play_buzzer(call: ServiceCall) -> None:
        """Handle play_buzzer service call."""
        active_ms = call.data.get("active_ms", 500)
        off_ms = call.data.get("off_ms", 500)
        count = call.data.get("count", 1)
        entity_ids = call.data.get("entity_id")

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        # Play buzzer on all target devices
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]

            try:
                # Fixed: Correct parameter names and calculate total_time
                cycle_time = active_ms + off_ms
                total_time = cycle_time * count
                await pixoo.play_buzzer(
                    active_time=active_ms,
                    off_time=off_ms,
                    total_time=total_time
                )
            except Exception as err:
                _LOGGER.error("Failed to play buzzer on %s: %s", entry.data[CONF_HOST], err)
                raise HomeAssistantError(f"Failed to play buzzer: {err}") from err

    async def handle_list_animations(call: ServiceCall) -> None:
        """Handle list_animations service call."""
        entity_ids = call.data.get("entity_id")

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        # Fetch animations from all target devices
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            # Fixed: Correct coordinator reference
            gallery_coordinator = data["coordinators"]["gallery"]

            try:
                # Refresh gallery coordinator to fetch latest animations
                await gallery_coordinator.async_request_refresh()
                animations = gallery_coordinator.data
                _LOGGER.info(
                    "Animations for %s: clocks=%d, visualizers=%d",
                    entry.data[CONF_HOST],
                    len(animations.get("clocks", [])),
                    len(animations.get("visualizers", [])),
                )
            except Exception as err:
                _LOGGER.error("Failed to list animations on %s: %s", entry.data[CONF_HOST], err)
                raise HomeAssistantError(f"Failed to list animations: {err}") from err

    async def handle_play_animation(call: ServiceCall) -> None:
        """Handle play_animation service call."""
        pic_id = call.data["pic_id"]
        entity_ids = call.data.get("entity_id")

        # Get target devices
        entries = _resolve_entry_ids(hass, entity_ids)

        # Play animation on all target devices
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _play_animation():
                try:
                    await pixoo.play_animation(pic_id=pic_id)
                    _LOGGER.debug("Playing animation %d on %s", pic_id, entry.data[CONF_HOST])
                except Exception as err:
                    _LOGGER.error("Failed to play animation on %s: %s", entry.data[CONF_HOST], err)
                    raise HomeAssistantError(f"Failed to play animation: {err}") from err

            await service_queue.enqueue(_play_animation())

    async def handle_send_playlist(call: ServiceCall) -> None:
        """Handle send_playlist service call."""
        items_data = call.data["items"]
        entity_ids = call.data.get("entity_id")

        # Get target devices
        entries = _resolve_entry_ids(hass, entity_ids)

        # Parse playlist items
        from .pixooasync.models import PlaylistItem

        try:
            playlist_items = [PlaylistItem(**item) for item in items_data]
        except Exception as err:
            raise ServiceValidationError(f"Invalid playlist item format: {err}") from err

        # Send playlist to all target devices
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _send_playlist():
                try:
                    await pixoo.send_playlist(items=playlist_items)
                    _LOGGER.debug("Sent playlist with %d items to %s", len(playlist_items), entry.data[CONF_HOST])
                except Exception as err:
                    _LOGGER.error("Failed to send playlist to %s: %s", entry.data[CONF_HOST], err)
                    raise HomeAssistantError(f"Failed to send playlist: {err}") from err

            await service_queue.enqueue(_send_playlist())

    async def handle_set_white_balance(call: ServiceCall) -> None:
        """Handle set_white_balance service call."""
        red = call.data["red"]
        green = call.data["green"]
        blue = call.data["blue"]
        entity_ids = call.data.get("entity_id")

        # Get target devices
        entries = _resolve_entry_ids(hass, entity_ids)

        # Set white balance on all target devices
        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _set_white_balance():
                try:
                    success = await pixoo.set_white_balance(red=red, green=green, blue=blue)
                    if success:
                        _LOGGER.debug("Set white balance to RGB(%d, %d, %d) on %s", red, green, blue, entry.data[CONF_HOST])
                    else:
                        _LOGGER.warning("White balance not supported by firmware on %s", entry.data[CONF_HOST])
                except Exception as err:
                    _LOGGER.error("Failed to set white balance on %s: %s", entry.data[CONF_HOST], err)
                    raise HomeAssistantError(f"Failed to set white balance: {err}") from err

            await service_queue.enqueue(_set_white_balance())

    async def handle_set_timer(call: ServiceCall) -> None:
        """Handle set_timer service call."""
        entity_ids = call.data.get("entity_id")
        duration = call.data.get("duration")  # time string HH:MM:SS or MM:SS
        
        if not duration:
            raise ServiceValidationError("Duration is required")

        # Parse duration string (can be HH:MM:SS or MM:SS)
        parts = str(duration).split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            total_minutes = hours * 60 + minutes
        elif len(parts) == 2:
            total_minutes, seconds = map(int, parts)
        else:
            raise ServiceValidationError("Duration must be in HH:MM:SS or MM:SS format")

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]

            try:
                # API call is correct - no changes needed
                await pixoo.set_timer(minutes=total_minutes, seconds=seconds, enabled=True)
                _LOGGER.info(
                    "Timer set on %s: %02d:%02d",
                    entry.data[CONF_HOST],
                    total_minutes,
                    seconds,
                )
            except Exception as err:
                _LOGGER.error("Failed to set timer on %s: %s", entry.data[CONF_HOST], err)
                raise HomeAssistantError(f"Failed to set timer: {err}") from err

    async def handle_set_alarm(call: ServiceCall) -> None:
        """Handle set_alarm service call."""
        entity_ids = call.data.get("entity_id")
        time = call.data.get("time")  # time string HH:MM
        enabled = call.data.get("enabled", True)
        
        if not time:
            raise ServiceValidationError("Time is required")

        # Parse time string HH:MM
        parts = str(time).split(":")
        if len(parts) != 2:
            raise ServiceValidationError("Time must be in HH:MM format")
        
        hour, minute = map(int, parts)
        
        if not (0 <= hour <= 23):
            raise ServiceValidationError("Hour must be between 0 and 23")
        if not (0 <= minute <= 59):
            raise ServiceValidationError("Minute must be between 0 and 59")

        # Get target devices (fixed entity ID resolution)
        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]

            try:
                # API call is correct - no changes needed
                await pixoo.set_alarm(hour=hour, minute=minute, enabled=enabled)
                _LOGGER.info(
                    "Alarm set on %s: %02d:%02d (enabled=%s)",
                    entry.data[CONF_HOST],
                    hour,
                    minute,
                    enabled,
                )
            except Exception as err:
                _LOGGER.error("Failed to set alarm on %s: %s", entry.data[CONF_HOST], err)
                raise HomeAssistantError(f"Failed to set alarm: {err}") from err

    async def handle_draw_pixel(call: ServiceCall) -> None:
        """Handle draw_pixel service call."""
        x = call.data["x"]
        y = call.data["y"]
        rgb = call.data["rgb"]
        entity_ids = call.data.get("entity_id")

        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _execute():
                try:
                    pixoo.draw_pixel((x, y), tuple(rgb))
                    _LOGGER.debug("Drew pixel at (%d, %d) with RGB%s", x, y, tuple(rgb))
                except Exception as err:
                    _LOGGER.error("Failed to draw pixel: %s", err)
                    raise HomeAssistantError(f"Failed to draw pixel: {err}") from err

            await service_queue.add(_execute())

    async def handle_draw_line(call: ServiceCall) -> None:
        """Handle draw_line service call."""
        start_x = call.data["start_x"]
        start_y = call.data["start_y"]
        end_x = call.data["end_x"]
        end_y = call.data["end_y"]
        rgb = call.data["rgb"]
        entity_ids = call.data.get("entity_id")

        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _execute():
                try:
                    pixoo.draw_line((start_x, start_y), (end_x, end_y), tuple(rgb))
                    _LOGGER.debug("Drew line from (%d, %d) to (%d, %d)", start_x, start_y, end_x, end_y)
                except Exception as err:
                    _LOGGER.error("Failed to draw line: %s", err)
                    raise HomeAssistantError(f"Failed to draw line: {err}") from err

            await service_queue.add(_execute())

    async def handle_draw_rectangle(call: ServiceCall) -> None:
        """Handle draw_rectangle service call."""
        top_left_x = call.data["top_left_x"]
        top_left_y = call.data["top_left_y"]
        bottom_right_x = call.data["bottom_right_x"]
        bottom_right_y = call.data["bottom_right_y"]
        rgb = call.data["rgb"]
        fill = call.data.get("fill", False)
        entity_ids = call.data.get("entity_id")

        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _execute():
                try:
                    if fill:
                        pixoo.draw_filled_rectangle(
                            (top_left_x, top_left_y),
                            (bottom_right_x, bottom_right_y),
                            tuple(rgb)
                        )
                        _LOGGER.debug("Drew filled rectangle from (%d, %d) to (%d, %d)", 
                                    top_left_x, top_left_y, bottom_right_x, bottom_right_y)
                    else:
                        # Draw outline (4 lines)
                        pixoo.draw_line((top_left_x, top_left_y), (bottom_right_x, top_left_y), tuple(rgb))  # Top
                        pixoo.draw_line((bottom_right_x, top_left_y), (bottom_right_x, bottom_right_y), tuple(rgb))  # Right
                        pixoo.draw_line((bottom_right_x, bottom_right_y), (top_left_x, bottom_right_y), tuple(rgb))  # Bottom
                        pixoo.draw_line((top_left_x, bottom_right_y), (top_left_x, top_left_y), tuple(rgb))  # Left
                        _LOGGER.debug("Drew rectangle outline from (%d, %d) to (%d, %d)", 
                                    top_left_x, top_left_y, bottom_right_x, bottom_right_y)
                except Exception as err:
                    _LOGGER.error("Failed to draw rectangle: %s", err)
                    raise HomeAssistantError(f"Failed to draw rectangle: {err}") from err

            await service_queue.add(_execute())

    async def handle_draw_text_at_position(call: ServiceCall) -> None:
        """Handle draw_text_at_position service call."""
        text = call.data["text"]
        x = call.data["x"]
        y = call.data["y"]
        rgb = call.data["rgb"]
        entity_ids = call.data.get("entity_id")

        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _execute():
                try:
                    pixoo.draw_text(text, (x, y), tuple(rgb))
                    _LOGGER.debug("Drew text '%s' at (%d, %d)", text, x, y)
                except Exception as err:
                    _LOGGER.error("Failed to draw text: %s", err)
                    raise HomeAssistantError(f"Failed to draw text: {err}") from err

            await service_queue.add(_execute())

    async def handle_fill_screen(call: ServiceCall) -> None:
        """Handle fill_screen service call."""
        rgb = call.data["rgb"]
        entity_ids = call.data.get("entity_id")

        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _execute():
                try:
                    pixoo.fill(tuple(rgb))
                    _LOGGER.debug("Filled screen with RGB%s", tuple(rgb))
                except Exception as err:
                    _LOGGER.error("Failed to fill screen: %s", err)
                    raise HomeAssistantError(f"Failed to fill screen: {err}") from err

            await service_queue.add(_execute())

    async def handle_clear_buffer(call: ServiceCall) -> None:
        """Handle clear_buffer service call."""
        rgb = call.data.get("rgb", [0, 0, 0])
        entity_ids = call.data.get("entity_id")

        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _execute():
                try:
                    pixoo.clear(tuple(rgb))
                    _LOGGER.debug("Cleared buffer to RGB%s", tuple(rgb))
                except Exception as err:
                    _LOGGER.error("Failed to clear buffer: %s", err)
                    raise HomeAssistantError(f"Failed to clear buffer: {err}") from err

            await service_queue.add(_execute())

    async def handle_push_buffer(call: ServiceCall) -> None:
        """Handle push_buffer service call."""
        entity_ids = call.data.get("entity_id")

        entries = _resolve_entry_ids(hass, entity_ids)

        for entry in entries:
            data = hass.data[DOMAIN][entry.entry_id]
            pixoo: PixooAsync = data["pixoo"]
            service_queue: ServiceQueue = data["service_queue"]

            async def _execute():
                try:
                    await pixoo.push()
                    _LOGGER.debug("Pushed buffer to device")
                except Exception as err:
                    _LOGGER.error("Failed to push buffer: %s", err)
                    raise HomeAssistantError(f"Failed to push buffer: {err}") from err

            await service_queue.add(_execute())

    # Register services (only once)
    if not hass.services.has_service(DOMAIN, SERVICE_DISPLAY_IMAGE):
        hass.services.async_register(DOMAIN, SERVICE_DISPLAY_IMAGE, handle_display_image)
    if not hass.services.has_service(DOMAIN, SERVICE_DISPLAY_IMAGE_DATA):
        hass.services.async_register(DOMAIN, SERVICE_DISPLAY_IMAGE_DATA, handle_display_image_data)
    if not hass.services.has_service(DOMAIN, SERVICE_DISPLAY_GIF):
        hass.services.async_register(DOMAIN, SERVICE_DISPLAY_GIF, handle_display_gif)
    if not hass.services.has_service(DOMAIN, SERVICE_DISPLAY_TEXT):
        hass.services.async_register(DOMAIN, SERVICE_DISPLAY_TEXT, handle_display_text)
    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_DISPLAY):
        hass.services.async_register(DOMAIN, SERVICE_CLEAR_DISPLAY, handle_clear_display)
    if not hass.services.has_service(DOMAIN, SERVICE_PLAY_BUZZER):
        hass.services.async_register(DOMAIN, SERVICE_PLAY_BUZZER, handle_play_buzzer)
    if not hass.services.has_service(DOMAIN, SERVICE_LIST_ANIMATIONS):
        hass.services.async_register(DOMAIN, SERVICE_LIST_ANIMATIONS, handle_list_animations)
    if not hass.services.has_service(DOMAIN, SERVICE_PLAY_ANIMATION):
        hass.services.async_register(DOMAIN, SERVICE_PLAY_ANIMATION, handle_play_animation)
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_PLAYLIST):
        hass.services.async_register(DOMAIN, SERVICE_SEND_PLAYLIST, handle_send_playlist)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_TIMER):
        hass.services.async_register(DOMAIN, SERVICE_SET_TIMER, handle_set_timer)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_ALARM):
        hass.services.async_register(DOMAIN, SERVICE_SET_ALARM, handle_set_alarm)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_WHITE_BALANCE):
        hass.services.async_register(DOMAIN, SERVICE_SET_WHITE_BALANCE, handle_set_white_balance)
    
    # Drawing services
    if not hass.services.has_service(DOMAIN, SERVICE_DRAW_PIXEL):
        hass.services.async_register(DOMAIN, SERVICE_DRAW_PIXEL, handle_draw_pixel)
    if not hass.services.has_service(DOMAIN, SERVICE_DRAW_LINE):
        hass.services.async_register(DOMAIN, SERVICE_DRAW_LINE, handle_draw_line)
    if not hass.services.has_service(DOMAIN, SERVICE_DRAW_RECTANGLE):
        hass.services.async_register(DOMAIN, SERVICE_DRAW_RECTANGLE, handle_draw_rectangle)
    if not hass.services.has_service(DOMAIN, SERVICE_DRAW_TEXT_AT_POSITION):
        hass.services.async_register(DOMAIN, SERVICE_DRAW_TEXT_AT_POSITION, handle_draw_text_at_position)
    if not hass.services.has_service(DOMAIN, SERVICE_FILL_SCREEN):
        hass.services.async_register(DOMAIN, SERVICE_FILL_SCREEN, handle_fill_screen)
    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_BUFFER):
        hass.services.async_register(DOMAIN, SERVICE_CLEAR_BUFFER, handle_clear_buffer)
    if not hass.services.has_service(DOMAIN, SERVICE_PUSH_BUFFER):
        hass.services.async_register(DOMAIN, SERVICE_PUSH_BUFFER, handle_push_buffer)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up
        data = hass.data[DOMAIN].pop(entry.entry_id)
        pixoo: PixooAsync = data["pixoo"]
        await pixoo.close()

    return unload_ok
