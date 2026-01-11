"""Color parsing/rendering helpers for Pixoo Page Engine."""

from __future__ import annotations

import json
from typing import Any

from PIL import ImageColor

from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template


def _clamp_byte(v: int) -> int:
    return max(0, min(255, int(v)))


def parse_color(value: Any) -> tuple[int, int, int]:
    """Parse a color input into an (r, g, b) tuple.

    Placeholder implementation.
    """

    if isinstance(value, (list, tuple)):
        if len(value) != 3:
            raise ValueError("RGB list/tuple must have exactly 3 items")
        r, g, b = value
        return (_clamp_byte(r), _clamp_byte(g), _clamp_byte(b))

    if isinstance(value, str):
        v = value.strip()
        rgb = ImageColor.getrgb(v)
        r, g, b = rgb[0], rgb[1], rgb[2]
        return (_clamp_byte(r), _clamp_byte(g), _clamp_byte(b))

    raise ValueError(f"Unsupported color type: {type(value)!r}")


def _maybe_parse_json_rgb(s: str) -> tuple[int, int, int] | None:
    s_stripped = s.strip()
    if not (s_stripped.startswith("[") and s_stripped.endswith("]")):
        return None
    try:
        parsed = json.loads(s_stripped)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, list) and len(parsed) == 3:
        return parse_color(parsed)
    return None


def render_color(
    hass: HomeAssistant,
    value: Any,
    *,
    variables: dict[str, Any] | None = None,
) -> tuple[int, int, int]:
    """Render templates (if any) and parse as color.

    Supports:
    - RGB list/tuple: [255, 0, 0]
    - Strings: "#RRGGBB", "red" (Pillow ImageColor)
    - Template strings: "{{ '#FF0000' }}" (strict=True)
      Templates may return a string (hex/name) or a JSON list like "[255,0,0]".
    """

    vars_ = variables or {}

    if isinstance(value, str) and ("{{" in value or "{%" in value):
        rendered = Template(value, hass).async_render(vars_, parse_result=False, strict=True)
        if isinstance(rendered, str):
            if rgb := _maybe_parse_json_rgb(rendered):
                return rgb
        return parse_color(rendered)

    return parse_color(value)


def interpolate_color(
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
    factor: float,
) -> tuple[int, int, int]:
    """Interpolate between two colors. factor=0 returns color1, factor=1 returns color2."""
    factor = max(0.0, min(1.0, factor))
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    return (_clamp_byte(r), _clamp_byte(g), _clamp_byte(b))


def compute_threshold_color(
    hass: HomeAssistant,
    value: float,
    thresholds: list,
    transition: str = "smooth",
    default_color: tuple[int, int, int] = (0, 255, 0),
    variables: dict[str, Any] | None = None,
) -> tuple[int, int, int]:
    """Compute color based on value and thresholds (like mini-graph-card).

    Thresholds are sorted descending by value. For smooth transition, colors
    are interpolated between adjacent thresholds.
    """
    if not thresholds:
        return default_color

    # Sort thresholds descending by value
    sorted_thresholds = sorted(thresholds, key=lambda t: t.value, reverse=True)

    # Find applicable threshold
    for i, threshold in enumerate(sorted_thresholds):
        if value >= threshold.value:
            color = render_color(hass, threshold.color, variables=variables)

            if transition == "smooth" and i > 0:
                # Interpolate with previous (higher) threshold
                prev = sorted_thresholds[i - 1]
                prev_color = render_color(hass, prev.color, variables=variables)
                # Calculate interpolation factor
                range_size = prev.value - threshold.value
                if range_size > 0:
                    factor = (value - threshold.value) / range_size
                    return interpolate_color(color, prev_color, factor)

            return color

    # Value below all thresholds: use last (lowest) threshold color
    return render_color(hass, sorted_thresholds[-1].color, variables=variables)
