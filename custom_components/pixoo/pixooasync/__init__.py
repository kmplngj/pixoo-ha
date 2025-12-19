"""
pixooasync: Modern async library to communicate with Divoom Pixoo devices.

This package provides a simple and modern async interface to control Divoom Pixoo
LED displays (16x16, 32x32, and 64x64) via Wi-Fi.
"""

from .client import Pixoo, PixooAsync
from .discovery import (
    create_pixoo_from_discovery,
    create_pixoo_from_discovery_async,
    discover_devices,
    discover_devices_async,
)
from .enums import (
    Channel,
    ImageResampleMode,
    PlaylistItemType,
    Rotation,
    TemperatureMode,
    TextScrollDirection,
    WeatherType,
)
from .models import (
    AlarmConfig,
    AnimationList,
    BuzzerConfig,
    DiscoveredDevice,
    Location,
    NoiseMeterConfig,
    PixooConfig,
    PlaylistItem,
    ScoreboardConfig,
    SimulatorConfig,
    StopwatchConfig,
    TimerConfig,
    TimeInfo,
    WeatherInfo,
    WhiteBalance,
)
from .palette import COLOR_BLACK, COLOR_WHITE, Palette

__version__ = "1.0.0"
__all__ = [
    "Pixoo",
    "PixooAsync",
    "Channel",
    "ImageResampleMode",
    "TextScrollDirection",
    "PlaylistItemType",
    "TemperatureMode",
    "WeatherType",
    "Rotation",
    "PixooConfig",
    "SimulatorConfig",
    "DiscoveredDevice",
    "PlaylistItem",
    "AnimationList",
    "Location",
    "WeatherInfo",
    "TimeInfo",
    "WhiteBalance",
    "TimerConfig",
    "AlarmConfig",
    "BuzzerConfig",
    "StopwatchConfig",
    "ScoreboardConfig",
    "NoiseMeterConfig",
    "Palette",
    "COLOR_BLACK",
    "COLOR_WHITE",
    "discover_devices",
    "discover_devices_async",
    "create_pixoo_from_discovery",
    "create_pixoo_from_discovery_async",
]
