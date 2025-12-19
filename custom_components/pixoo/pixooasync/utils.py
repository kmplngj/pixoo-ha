"""Utility functions for pixooasync."""

from .palette import RGBColor


def clamp(value: int | float, minimum: int | float = 0, maximum: int | float = 255) -> int | float:
    """Clamp a value between minimum and maximum.

    Args:
        value: Value to clamp
        minimum: Minimum allowed value
        maximum: Maximum allowed value

    Returns:
        Clamped value
    """
    if value > maximum:
        return maximum
    if value < minimum:
        return minimum
    return value


def clamp_color(rgb: RGBColor) -> RGBColor:
    """Clamp RGB color values to valid range (0-255).

    Args:
        rgb: RGB color tuple

    Returns:
        Clamped RGB color tuple
    """
    return (
        int(clamp(rgb[0])),
        int(clamp(rgb[1])),
        int(clamp(rgb[2])),
    )


def lerp(start: float, end: float, interpolant: float) -> float:
    """Linear interpolation between two values.

    Args:
        start: Start value
        end: End value
        interpolant: Interpolation factor (0.0-1.0)

    Returns:
        Interpolated value
    """
    return start + interpolant * (end - start)


def lerp_location(
    xy1: tuple[float, float], xy2: tuple[float, float], interpolant: float
) -> tuple[float, float]:
    """Linear interpolation between two 2D points.

    Args:
        xy1: Start point (x, y)
        xy2: End point (x, y)
        interpolant: Interpolation factor (0.0-1.0)

    Returns:
        Interpolated point
    """
    return lerp(xy1[0], xy2[0], interpolant), lerp(xy1[1], xy2[1], interpolant)


def minimum_amount_of_steps(xy1: tuple[float, float], xy2: tuple[float, float]) -> int:
    """Calculate minimum steps needed to draw a line between two points.

    Args:
        xy1: Start point
        xy2: End point

    Returns:
        Number of steps needed
    """
    return int(max(abs(xy1[0] - xy2[0]), abs(xy1[1] - xy2[1])))


def rgb_to_hex_color(rgb: RGBColor) -> str:
    """Convert RGB color to hex string format.

    Args:
        rgb: RGB color tuple

    Returns:
        Hex color string (e.g., "#FF00AA")
    """
    return f"#{rgb[0]:0>2X}{rgb[1]:0>2X}{rgb[2]:0>2X}"


def round_location(xy: tuple[float, float]) -> tuple[int, int]:
    """Round a floating point location to integers.

    Args:
        xy: Floating point coordinates

    Returns:
        Integer coordinates
    """
    return round(xy[0]), round(xy[1])
