"""Type definitions and enums for pixoo-ng."""

from enum import IntEnum


class Channel(IntEnum):
    """Display channels available on Pixoo devices."""

    FACES = 0
    CLOUD = 1
    VISUALIZER = 2
    CUSTOM = 3


class ImageResampleMode(IntEnum):
    """Image resampling modes for PIL."""

    PIXEL_ART = 0  # Nearest neighbor
    SMOOTH = 1  # Bilinear/Lanczos


class TextScrollDirection(IntEnum):
    """Text scroll direction options."""

    LEFT = 0
    RIGHT = 1


class PlaylistItemType(IntEnum):
    """Types of items that can be added to a playlist."""

    IMAGE = 0
    TEXT = 1
    CLOCK = 2
    WEATHER = 3
    ANIMATION = 4
    VISUALIZER = 5
    CUSTOM = 6


class WeatherType(IntEnum):
    """Weather condition types for display."""

    CLEAR_DAY = 1
    CLEAR_NIGHT = 2
    CLOUDY = 3
    RAIN = 5
    SNOW = 8
    FOG = 9
    THUNDERSTORM = 11


class TemperatureMode(IntEnum):
    """Temperature unit display modes."""

    CELSIUS = 0
    FAHRENHEIT = 1


class Rotation(IntEnum):
    """Screen rotation angles."""

    NORMAL = 0
    ROTATE_90 = 1
    ROTATE_180 = 2
    ROTATE_270 = 3
