"""Media player platform for Pixoo integration."""
from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    MediaClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PixooSystemCoordinator
from .utils import download_image

_LOGGER = logging.getLogger(__name__)


@dataclass
class PixooPlaylistItem:
    """Playlist item model."""

    url: str
    duration: int = 10  # seconds per image


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixoo media player entity."""
    from homeassistant.helpers import entity_platform
    import voluptuous as vol
    from homeassistant.helpers import config_validation as cv
    
    coordinators = hass.data[DOMAIN][entry.entry_id]["coordinators"]
    pixoo = hass.data[DOMAIN][entry.entry_id]["pixoo"]
    
    system_coordinator: PixooSystemCoordinator = coordinators["system"]
    
    entities: list[MediaPlayerEntity] = [
        PixooMediaPlayer(hass, system_coordinator, pixoo, entry),
    ]
    
    async_add_entities(entities)
    
    # Register entity services
    platform = entity_platform.async_get_current_platform()
    
    platform.async_register_entity_service(
        "load_image",
        {
            vol.Required("url"): cv.string,
            vol.Optional("duration", default=0): cv.positive_int,
        },
        "async_load_image",
    )
    
    platform.async_register_entity_service(
        "load_folder",
        {
            vol.Required("path"): cv.string,
            vol.Optional("duration", default=10): cv.positive_int,
            vol.Optional("shuffle", default=False): cv.boolean,
        },
        "async_load_folder",
    )
    
    platform.async_register_entity_service(
        "load_playlist",
        {
            vol.Required("items"): vol.All(cv.ensure_list, [dict]),
            vol.Optional("shuffle", default=False): cv.boolean,
        },
        "async_load_playlist",
    )


class PixooMediaPlayer(MediaPlayerEntity):
    """Media player entity for image gallery/slideshow."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.BROWSE_MEDIA
    )
    _attr_media_content_type = MediaType.IMAGE
    _attr_media_class = MediaClass.IMAGE

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: PixooSystemCoordinator,
        pixoo: Any,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the media player."""
        self.hass = hass
        self.coordinator = coordinator
        self.pixoo = pixoo
        self._entry = entry
        
        self._attr_unique_id = f"{entry.unique_id}_gallery"
        self._attr_name = "Gallery"
        # Don't create device_info - will be inherited from coordinator
        
        # Playlist state
        self._playlist: list[PixooPlaylistItem] = []
        self._position: int = 0
        self._state: MediaPlayerState = MediaPlayerState.IDLE
        self._shuffle: bool = False
        self._repeat: bool = False
        self._shuffle_order: list[int] | None = None
        self._timer_handle: asyncio.TimerHandle | None = None
        self._media_image_url: str | None = None

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        if not self._playlist:
            return MediaPlayerState.IDLE
        return self._state

    @property
    def media_content_id(self) -> str | None:
        """Return the content ID of current playing media."""
        if not self._playlist:
            return None
        if len(self._playlist) == 1:
            return self._playlist[0].url
        # Return playlist as JSON for multi-item playlists
        return json.dumps([{"url": item.url, "duration": item.duration} for item in self._playlist])

    @property
    def media_image_url(self) -> str | None:
        """Return the image URL of current playing media."""
        return self._media_image_url

    @property
    def media_position(self) -> int:
        """Return position in playlist (0-based)."""
        return self._position

    @property
    def media_duration(self) -> int:
        """Return duration of current item in seconds."""
        if not self._playlist or self._position >= len(self._playlist):
            return 10
        return self._playlist[self._position].duration

    @property
    def shuffle(self) -> bool:
        """Return shuffle state."""
        return self._shuffle

    @property
    def repeat(self) -> bool:
        """Return repeat state (True = repeat all)."""
        return self._repeat

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media (image or playlist)."""
        _LOGGER.debug(
            "Playing media: type=%s, id=%s", media_type, media_id
        )
        
        if media_type == MediaType.PLAYLIST:
            # Load playlist from JSON
            try:
                playlist_data = json.loads(media_id)
                self._load_playlist(playlist_data)
                await self._display_current_image()
                self._schedule_next()
            except (json.JSONDecodeError, ValueError) as err:
                _LOGGER.error("Invalid playlist JSON: %s", err)
                return
        else:
            # Single image
            self._load_single_image(media_id)
            await self._display_current_image()

    async def async_media_play(self) -> None:
        """Resume slideshow."""
        if not self._playlist:
            _LOGGER.warning("No playlist loaded")
            return
        
        self._state = MediaPlayerState.PLAYING
        self._schedule_next()
        self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        """Pause slideshow."""
        self._state = MediaPlayerState.PAUSED
        self._cancel_timer()
        self.async_write_ha_state()

    async def async_media_stop(self) -> None:
        """Stop slideshow and clear display."""
        self._state = MediaPlayerState.IDLE
        self._cancel_timer()
        self._playlist = []
        self._position = 0
        self._media_image_url = None
        await self.pixoo.clear_display()
        self.async_write_ha_state()

    async def async_media_next_track(self) -> None:
        """Display next image in playlist."""
        if not self._playlist:
            return
        
        if self._shuffle and self._shuffle_order:
            current_shuffle_idx = self._shuffle_order.index(self._position)
            next_shuffle_idx = (current_shuffle_idx + 1) % len(self._shuffle_order)
            self._position = self._shuffle_order[next_shuffle_idx]
        else:
            self._position = (self._position + 1) % len(self._playlist)
        
        await self._display_current_image()
        
        if self._state == MediaPlayerState.PLAYING:
            self._schedule_next()

    async def async_media_previous_track(self) -> None:
        """Display previous image in playlist."""
        if not self._playlist:
            return
        
        if self._shuffle and self._shuffle_order:
            current_shuffle_idx = self._shuffle_order.index(self._position)
            prev_shuffle_idx = (current_shuffle_idx - 1) % len(self._shuffle_order)
            self._position = self._shuffle_order[prev_shuffle_idx]
        else:
            self._position = (self._position - 1) % len(self._playlist)
        
        await self._display_current_image()
        
        if self._state == MediaPlayerState.PLAYING:
            self._schedule_next()

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Enable/disable shuffle mode."""
        self._shuffle = shuffle
        
        if shuffle and self._playlist:
            if not self._shuffle_order:
                self._shuffle_order = list(range(len(self._playlist)))
                random.shuffle(self._shuffle_order)
        else:
            self._shuffle_order = None
        
        self.async_write_ha_state()

    async def async_set_repeat(self, repeat: str) -> None:
        """Enable/disable repeat mode."""
        # repeat can be "off", "all", "one"
        # We support "off" (False) and "all" (True)
        self._repeat = repeat != "off"
        self.async_write_ha_state()

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the browse media feature."""
        _LOGGER.debug(
            "Browse media called with type=%s, id=%s", media_content_type, media_content_id
        )
        
        # Root level - show categories
        if media_content_id is None:
            return BrowseMedia(
                media_class=MediaClass.DIRECTORY,
                media_content_id="root",
                media_content_type="root",
                title="Pixoo Gallery",
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMedia(
                        media_class=MediaClass.IMAGE,
                        media_content_id="local_media",
                        media_content_type=MediaType.IMAGE,
                        title="Local Media",
                        can_play=False,
                        can_expand=True,
                    ),
                ],
            )
        
        # If media source integration exists, delegate to it
        if media_content_id.startswith("media-source://"):
            try:
                from homeassistant.components.media_source import async_browse_media as browse_media_source
                return await browse_media_source(self.hass, media_content_id)
            except ImportError:
                _LOGGER.warning("Media source integration not available")
        
        # Default empty response
        return BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id=media_content_id or "root",
            media_content_type="directory",
            title="Browse",
            can_play=False,
            can_expand=False,
            children=[],
        )

    async def async_load_image(self, url: str, duration: int = 0) -> None:
        """Load a single image (custom service method)."""
        _LOGGER.debug("Loading single image: %s (duration=%ds)", url, duration)
        self._load_single_image(url, duration)
        await self._display_current_image()
        
        if duration > 0:
            self._state = MediaPlayerState.PLAYING
            self._schedule_next()
        else:
            self._state = MediaPlayerState.IDLE
        
        self.async_write_ha_state()

    async def async_load_folder(
        self, path: str, duration: int = 10, shuffle: bool = False
    ) -> None:
        """Load all images from a folder as a playlist (custom service method)."""
        _LOGGER.debug(
            "Loading folder: %s (duration=%ds, shuffle=%s)", path, duration, shuffle
        )
        
        # Try to use media source to browse folder
        try:
            from homeassistant.components.media_source import async_browse_media as browse_media_source
            
            # Browse the media source path
            browse_result = await browse_media_source(self.hass, path)
            
            # Extract image URLs from children
            playlist_items = []
            if browse_result.children:
                for child in browse_result.children:
                    # Only add images
                    if child.media_content_type in (MediaType.IMAGE, "image"):
                        playlist_items.append({
                            "url": child.media_content_id,
                            "duration": duration,
                        })
            
            if not playlist_items:
                _LOGGER.warning("No images found in folder: %s", path)
                return
            
            _LOGGER.info("Loaded %d images from folder", len(playlist_items))
            self._load_playlist(playlist_items)
            
            if shuffle:
                self._shuffle = True
                self._shuffle_order = list(range(len(self._playlist)))
                random.shuffle(self._shuffle_order)
            
            await self._display_current_image()
            self._schedule_next()
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Failed to load folder %s: %s", path, err)
            raise

    async def async_load_playlist(
        self, items: list[dict], shuffle: bool = False
    ) -> None:
        """Load a custom playlist of images (custom service method)."""
        _LOGGER.debug("Loading playlist with %d items (shuffle=%s)", len(items), shuffle)
        
        self._load_playlist(items)
        
        if shuffle:
            self._shuffle = True
            self._shuffle_order = list(range(len(self._playlist)))
            random.shuffle(self._shuffle_order)
        
        await self._display_current_image()
        self._schedule_next()
        self.async_write_ha_state()

    # Private methods

    async def _display_current_image(self) -> None:
        """Display the current playlist image."""
        if not self._playlist or self._position >= len(self._playlist):
            return
        
        item = self._playlist[self._position]
        url = item.url
        
        # Handle media-source:// URLs
        if url.startswith("media-source://"):
            try:
                # Resolve media source to actual URL
                from homeassistant.components import media_source
                resolved = await media_source.async_resolve_media(self.hass, url, None)
                url = resolved.url
            except Exception as err:
                _LOGGER.error("Failed to resolve media source URL %s: %s", url, err)
                return
        
        # Download and display image
        try:
            image_data = await download_image(self.hass, url)
            await self.pixoo.display_image_from_bytes(image_data)
            self._media_image_url = url
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to display image %s: %s", url, err)

    def _schedule_next(self) -> None:
        """Schedule automatic advance to next image."""
        self._cancel_timer()
        
        if not self._playlist or self._position >= len(self._playlist):
            return
        
        item = self._playlist[self._position]
        
        # Only schedule if duration > 0 (single images have duration=0)
        if item.duration > 0:
            self._timer_handle = self.hass.loop.call_later(
                item.duration,
                lambda: self.hass.async_create_task(self._auto_advance()),
            )

    async def _auto_advance(self) -> None:
        """Automatically advance to next image."""
        if self._state != MediaPlayerState.PLAYING:
            return
        
        # Check if at end of playlist
        if self._shuffle and self._shuffle_order:
            current_shuffle_idx = self._shuffle_order.index(self._position)
            is_last = current_shuffle_idx == len(self._shuffle_order) - 1
        else:
            is_last = self._position == len(self._playlist) - 1
        
        if is_last and not self._repeat:
            # End of playlist without repeat
            self._state = MediaPlayerState.IDLE
            self.async_write_ha_state()
            return
        
        # Advance to next track
        await self.async_media_next_track()

    def _cancel_timer(self) -> None:
        """Cancel the auto-advance timer."""
        if self._timer_handle:
            self._timer_handle.cancel()
            self._timer_handle = None

    def _load_playlist(self, items: list[dict]) -> None:
        """Load playlist from JSON data."""
        self._playlist = [PixooPlaylistItem(**item) for item in items]
        self._position = 0
        self._state = MediaPlayerState.PLAYING
        self._media_image_url = None
        
        if self._shuffle:
            self._shuffle_order = list(range(len(self._playlist)))
            random.shuffle(self._shuffle_order)

    def _load_single_image(self, url: str, duration: int = 0) -> None:
        """Load single image as 1-item playlist."""
        self._playlist = [PixooPlaylistItem(url=url, duration=duration)]
        self._position = 0
        self._state = MediaPlayerState.IDLE if duration == 0 else MediaPlayerState.PLAYING
        self._media_image_url = None
