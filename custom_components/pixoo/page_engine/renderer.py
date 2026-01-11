"""Renderer entry points for Pixoo Page Engine.

Phase 2 provides core helpers used by all user stories:
- component bounds checks (skip+log semantics lives in US1 render loop)
- safe image source resolution (URL/path/base64) with allowlisting
"""

from __future__ import annotations

import base64
from io import BytesIO
import logging
from pathlib import Path
from typing import Any

from PIL import Image

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

import aiohttp

from ..utils import download_image
from . import PageEngineValidationError
from .colors import render_color, compute_threshold_color
from .models import (
    ArcComponent,
    ArrowComponent,
    ChannelPage,
    CircleComponent,
    ComponentsPage,
    GraphComponent,
    IconComponent,
    ImageComponent,
    ImageSource,
    LineComponent,
    PageModel,
    ProgressBarComponent,
    RectangleComponent,
    TemplatePage,
    TextComponent,
)
from .storage import load_builtin_template
from .templating import async_render_complex
from .display_buffer import DisplayBuffer, PillowDisplayBuffer


_LOGGER = logging.getLogger(__name__)


async def _render_int(
    hass: HomeAssistant,
    value: int | str,
    variables: dict[str, Any],
    field_name: str = "value",
) -> int:
    """Render a value that may be a template string to an integer.
    
    Args:
        hass: Home Assistant instance
        value: Integer or template string
        variables: Template variables
        field_name: Name of the field (for error messages)
        
    Returns:
        Integer value
        
    Raises:
        ValueError: If the value cannot be converted to an integer
    """
    if isinstance(value, int):
        return value
    
    if isinstance(value, str):
        # Check if it's a template
        if "{{" in value or "{%" in value:
            from homeassistant.helpers.template import Template
            rendered = Template(value, hass).async_render(variables, parse_result=False)
            try:
                return int(float(str(rendered)))
            except (ValueError, TypeError) as err:
                raise ValueError(f"Template for {field_name} did not render to a number: {rendered}") from err
        else:
            # Direct string, try to parse as int
            try:
                return int(float(value))
            except (ValueError, TypeError) as err:
                raise ValueError(f"{field_name} is not a valid integer: {value}") from err
    
    raise ValueError(f"{field_name} must be an integer or template string, got {type(value)}")

# Icon cache: (icon_name, size, color_hex) -> PIL Image
_ICON_CACHE: dict[tuple[str, int, str], Image.Image] = {}

# MDI SVG cache: icon_name -> svg_content
_MDI_SVG_CACHE: dict[str, str] = {}

# MDI SVG URL template (jsdelivr CDN)
_MDI_SVG_URL_TEMPLATE = "https://cdn.jsdelivr.net/npm/@mdi/svg@latest/svg/{icon_name}.svg"


async def _fetch_mdi_svg(hass: HomeAssistant, icon_name: str) -> str | None:
    """Fetch MDI SVG content from jsdelivr CDN."""
    if icon_name in _MDI_SVG_CACHE:
        return _MDI_SVG_CACHE[icon_name]

    url = _MDI_SVG_URL_TEMPLATE.format(icon_name=icon_name)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    svg_content = await resp.text()
                    _MDI_SVG_CACHE[icon_name] = svg_content
                    return svg_content
                else:
                    _LOGGER.warning("Failed to fetch MDI icon %s: HTTP %d", icon_name, resp.status)
                    return None
    except Exception as err:
        _LOGGER.warning("Failed to fetch MDI icon %s: %s", icon_name, err)
        return None


async def _fetch_and_render_mdi_icon(
    hass: HomeAssistant,
    icon_name: str,
    size: int,
    color: tuple[int, int, int],
) -> Image.Image:
    """Render MDI icon by fetching SVG and rasterizing with svg.path + Pillow.
    
    Uses 4x supersampling for anti-aliasing: render at 4x size, then downscale
    with LANCZOS filter for smooth edges.
    """
    import re
    from PIL import ImageDraw
    
    # Import svg.path - pure Python library, no native dependencies
    try:
        from svg.path import parse_path
    except ImportError:
        _LOGGER.error("svg.path not installed - cannot render icons")
        return _create_placeholder_icon(size, color)

    # Normalize icon name (strip mdi: prefix, use hyphens)
    name = icon_name.removeprefix("mdi:").replace("_", "-")

    # Check cache
    color_hex = "{:02x}{:02x}{:02x}".format(*color)
    cache_key = (name, size, color_hex)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key].copy()

    # Fetch SVG content
    svg_content = await _fetch_mdi_svg(hass, name)
    if svg_content is None:
        _LOGGER.warning("Icon %s not found, using placeholder", icon_name)
        return _create_placeholder_icon(size, color)

    def _render_svg() -> Image.Image:
        """Render SVG path to PIL Image with anti-aliasing via supersampling."""
        # Extract path data from SVG (format: <path d="...">)
        match = re.search(r'<path[^>]*\sd="([^"]+)"', svg_content)
        if not match:
            _LOGGER.warning("No path found in SVG for %s", icon_name)
            return _create_placeholder_icon(size, color)

        path_data = match.group(1)

        try:
            path = parse_path(path_data)
        except Exception as err:
            _LOGGER.warning("Failed to parse SVG path for %s: %s", icon_name, err)
            return _create_placeholder_icon(size, color)

        # Supersampling: render at 4x size for anti-aliasing
        supersample_factor = 4
        render_size = size * supersample_factor
        
        # MDI icons use viewBox="0 0 24 24"
        scale = render_size / 24.0

        # Create image with transparent background for composition
        # Use RGBA for proper alpha blending during downscale
        img = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Split path into subpaths at Move commands
        # MDI icons use subpaths for holes (e.g., battery icon has outer rect + inner cutouts)
        from svg.path import Move, Close
        
        subpaths = []
        current_subpath = []
        
        for segment in path:
            if isinstance(segment, Move):
                if current_subpath:
                    subpaths.append(current_subpath)
                current_subpath = [segment]
            else:
                current_subpath.append(segment)
        
        if current_subpath:
            subpaths.append(current_subpath)

        # Render each subpath as a separate polygon
        # More samples = smoother curves but slower rendering
        samples_per_segment = max(20, render_size // 2)
        
        for subpath in subpaths:
            points = []
            for segment in subpath:
                if isinstance(segment, (Move, Close)):
                    # Move/Close contribute start/end points only
                    if hasattr(segment, 'start'):
                        x = segment.start.real * scale
                        y = segment.start.imag * scale
                        points.append((x, y))
                    continue
                    
                for i in range(samples_per_segment):
                    t = i / samples_per_segment
                    try:
                        point = segment.point(t)
                        x = point.real * scale
                        y = point.imag * scale
                        points.append((x, y))
                    except (ValueError, ZeroDivisionError):
                        pass

            # Draw filled polygon
            if len(points) > 2:
                # Use XOR to handle holes (inner subpaths subtract from outer)
                from PIL import ImageDraw as PILImageDraw, ImageChops
                mask = Image.new("L", (render_size, render_size), 0)
                mask_draw = PILImageDraw.Draw(mask)
                mask_draw.polygon(points, fill=255)
                
                # XOR with existing alpha
                alpha = img.split()[3]
                new_alpha = ImageChops.logical_xor(alpha.convert("1"), mask.convert("1"))
                
                # Apply color where mask is set
                color_layer = Image.new("RGBA", (render_size, render_size), (*color, 255))
                img = Image.composite(color_layer, img, new_alpha.convert("L"))

        # Downscale with LANCZOS for anti-aliasing
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Return RGBA image - alpha blending happens in draw_image()
        return img

    result = await hass.async_add_executor_job(_render_svg)

    # Cache result
    _ICON_CACHE[cache_key] = result.copy()

    return result


def _create_placeholder_icon(size: int, color: tuple[int, int, int]) -> Image.Image:
    """Create a simple placeholder icon (question mark pattern) with alpha."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # Draw a simple "?" pattern
    center = size // 2
    for i in range(size // 4, size * 3 // 4):
        img.putpixel((center, i), (*color, 255))
    for i in range(size // 4, center):
        img.putpixel((i, size // 4), (*color, 255))
    return img


ALLOWLIST_MODE_STRICT = "strict"
ALLOWLIST_MODE_PERMISSIVE = "permissive"


def component_in_bounds(component: object, *, device_size: int) -> bool:
    """Return True if a component is within the device bounds.

    Note: For text and image components we only validate the anchor point (x, y).
    For rectangles, progress bars, graphs, and icons we validate the full width/height.
    
    If any dimension is a template string (not yet rendered), returns True to defer
    validation to render time.
    """

    def _is_template(val: Any) -> bool:
        """Check if a value is a template string."""
        return isinstance(val, str) and ("{{" in val or "{%" in val)

    if isinstance(component, (RectangleComponent, ProgressBarComponent, GraphComponent)):
        # Skip validation if any value is a template
        if _is_template(component.x) or _is_template(component.y):
            return True
        if _is_template(component.width) or _is_template(component.height):
            return True
        
        # Convert to int if string
        try:
            x = int(component.x) if isinstance(component.x, str) else component.x
            y = int(component.y) if isinstance(component.y, str) else component.y
            w = int(component.width) if isinstance(component.width, str) else component.width
            h = int(component.height) if isinstance(component.height, str) else component.height
        except (ValueError, TypeError):
            return True  # Defer to render time
        
        if w <= 0 or h <= 0:
            return False
        if x < 0 or y < 0:
            return False
        if x >= device_size or y >= device_size:
            return False
        if x + w > device_size:
            return False
        if y + h > device_size:
            return False
        return True

    if isinstance(component, IconComponent):
        # Skip validation if any value is a template
        if _is_template(component.x) or _is_template(component.y):
            return True
        
        try:
            x = int(component.x) if isinstance(component.x, str) else component.x
            y = int(component.y) if isinstance(component.y, str) else component.y
        except (ValueError, TypeError):
            return True  # Defer to render time
            
        if x < 0 or y < 0:
            return False
        if x >= device_size or y >= device_size:
            return False
        if x + component.size > device_size:
            return False
        if y + component.size > device_size:
            return False
        return True

    if isinstance(component, (TextComponent, ImageComponent)):
        # Skip validation if any value is a template
        if _is_template(component.x) or _is_template(component.y):
            return True
        
        try:
            x = int(component.x) if isinstance(component.x, str) else component.x
            y = int(component.y) if isinstance(component.y, str) else component.y
        except (ValueError, TypeError):
            return True  # Defer to render time
            
        return 0 <= x < device_size and 0 <= y < device_size

    if isinstance(component, LineComponent):
        # Check if line endpoints are within bounds
        if _is_template(component.start) or _is_template(component.end):
            return True
        
        try:
            start_x = int(component.start[0]) if isinstance(component.start[0], str) else component.start[0]
            start_y = int(component.start[1]) if isinstance(component.start[1], str) else component.start[1]
            end_x = int(component.end[0]) if isinstance(component.end[0], str) else component.end[0]
            end_y = int(component.end[1]) if isinstance(component.end[1], str) else component.end[1]
        except (ValueError, TypeError, IndexError):
            return True  # Defer to render time
        
        # Allow lines that partially intersect the display
        # (at least one endpoint within bounds, or line crosses display)
        in_bounds_start = 0 <= start_x < device_size and 0 <= start_y < device_size
        in_bounds_end = 0 <= end_x < device_size and 0 <= end_y < device_size
        return in_bounds_start or in_bounds_end

    if isinstance(component, CircleComponent):
        # Check if circle is within or intersecting bounds
        if _is_template(component.center) or _is_template(component.radius):
            return True
        
        try:
            center_x = int(component.center[0]) if isinstance(component.center[0], str) else component.center[0]
            center_y = int(component.center[1]) if isinstance(component.center[1], str) else component.center[1]
            radius = int(component.radius) if isinstance(component.radius, str) else component.radius
        except (ValueError, TypeError, IndexError):
            return True  # Defer to render time
        
        # Circle is visible if any part intersects with display bounds
        # Simple check: center +/- radius overlaps with [0, device_size)
        left = center_x - radius
        right = center_x + radius
        top = center_y - radius
        bottom = center_y + radius
        
        # Circle is visible if it overlaps with [0, device_size) x [0, device_size)
        return right >= 0 and left < device_size and bottom >= 0 and top < device_size

    if isinstance(component, ArcComponent):
        # Check if arc is within or intersecting bounds (same as circle)
        if _is_template(component.center) or _is_template(component.radius):
            return True
        
        try:
            center_x = int(component.center[0]) if isinstance(component.center[0], str) else component.center[0]
            center_y = int(component.center[1]) if isinstance(component.center[1], str) else component.center[1]
            radius = int(component.radius) if isinstance(component.radius, str) else component.radius
        except (ValueError, TypeError, IndexError):
            return True  # Defer to render time
        
        # Arc is visible if any part intersects with display bounds
        left = center_x - radius
        right = center_x + radius
        top = center_y - radius
        bottom = center_y + radius
        return right >= 0 and left < device_size and bottom >= 0 and top < device_size

    if isinstance(component, ArrowComponent):
        # Check if arrow is within or intersecting bounds
        if _is_template(component.center) or _is_template(component.length):
            return True
        
        try:
            center_x = int(component.center[0]) if isinstance(component.center[0], str) else component.center[0]
            center_y = int(component.center[1]) if isinstance(component.center[1], str) else component.center[1]
            length = int(component.length) if isinstance(component.length, str) else component.length
        except (ValueError, TypeError, IndexError):
            return True  # Defer to render time
        
        # Arrow is visible if center is in bounds or arrow extends into bounds
        # Simple approximation: check if center +/- length overlaps display
        left = center_x - length
        right = center_x + length
        top = center_y - length
        bottom = center_y + length
        return right >= 0 and left < device_size and bottom >= 0 and top < device_size

    # Unknown component type: be conservative.
    return False


async def async_resolve_image_source(
    hass: HomeAssistant,
    source: ImageSource,
    *,
    device_size: int,
    allowlist_mode: str = ALLOWLIST_MODE_STRICT,
) -> Image.Image:
    """Resolve an ImageSource into a Pillow Image, resized to the device size.

    Security:
    - strict mode enforces HA allowlisting for URL and path.
    - permissive mode disables allowlisting checks (timeouts/size limits still apply for URLs).
    """

    if source.kind == "none":
        raise ServiceValidationError("image.source must specify exactly one of url/path/base64")

    target_size = (device_size, device_size)

    if source.url is not None:
        url = source.url
        
        # Handle empty/None URL - return transparent image instead of error
        # This supports templates like: {{ cover_url if has_cover else '' }}
        if not url or url == "None":
            _LOGGER.debug("Page Engine: image URL is empty, returning transparent image")
            return Image.new("RGBA", target_size, (0, 0, 0, 0))

        # Support file:// URLs as local paths.
        if url.startswith("file://"):
            return await async_resolve_image_source(
                hass,
                ImageSource(path=url.removeprefix("file://")),
                device_size=device_size,
                allowlist_mode=allowlist_mode,
            )

        # Support relative HA API URLs (e.g., /api/media_player_proxy/...)
        # These are internal HA endpoints and should be treated as trusted
        if url.startswith("/api/"):
            # Get the internal URL from HA config
            from homeassistant.helpers.network import get_url
            try:
                base_url = get_url(hass, prefer_external=False, allow_internal=True)
                url = f"{base_url.rstrip('/')}{url}"
                _LOGGER.debug("Page Engine: resolved relative API URL to: %s", url)
            except Exception as err:
                _LOGGER.warning("Page Engine: could not resolve internal URL: %s", err)
                # Fallback: try localhost
                url = f"http://127.0.0.1:8123{url}"
            # API URLs are internal, skip allowlist check
            allowlist_mode = ALLOWLIST_MODE_PERMISSIVE

        if allowlist_mode == ALLOWLIST_MODE_STRICT and not hass.config.is_allowed_external_url(url):
            raise ServiceValidationError(f"URL not allowlisted: {url}")

        image_bytes = await download_image(hass, url, target_size=target_size)
        return Image.open(BytesIO(image_bytes))

    if source.path is not None:
        path = source.path

        if allowlist_mode == ALLOWLIST_MODE_STRICT and not hass.config.is_allowed_path(path):
            raise ServiceValidationError(f"Path not allowlisted: {path}")

        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            raise ServiceValidationError(f"Image path does not exist: {path}")

        def _load_and_process() -> bytes:
            try:
                raw = file_path.read_bytes()
                img = Image.open(BytesIO(raw))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                out = BytesIO()
                img.save(out, format="PNG")
                return out.getvalue()
            except Exception as err:  # pragma: no cover
                raise ServiceValidationError(f"Failed to load/process image from path: {err}") from err

        processed = await hass.async_add_executor_job(_load_and_process)
        return Image.open(BytesIO(processed))

    if source.base64 is not None:
        try:
            raw = base64.b64decode(source.base64)
        except Exception as err:
            raise ServiceValidationError(f"Failed to decode base64 image: {err}") from err

        def _decode_and_process() -> bytes:
            try:
                img = Image.open(BytesIO(raw))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                out = BytesIO()
                img.save(out, format="PNG")
                return out.getvalue()
            except Exception as err:  # pragma: no cover
                raise ServiceValidationError(f"Failed to decode/process base64 image: {err}") from err

        processed = await hass.async_add_executor_job(_decode_and_process)
        return Image.open(BytesIO(processed))

    raise ServiceValidationError("image.source must specify exactly one of url/path/base64")


async def render_page(
    hass: HomeAssistant,
    pixoo: Any,
    page: Any,
    *,
    device_size: int,
    variables: dict[str, Any] | None = None,
    allowlist_mode: str = ALLOWLIST_MODE_STRICT,
    entry_id: str | None = None,
) -> None:
    """Render a page onto a device buffer and push.

    Placeholder implementation.
    """
    # Merge per-page default variables into the rendering context. Service-level
    # variables take precedence.
    vars_: dict[str, Any] = {}
    if isinstance(page, dict) and isinstance(page.get("variables"), dict):
        vars_.update(page["variables"])
    if variables:
        vars_.update(variables)

    # 1) Template rendering (best effort happens later, per component)
    rendered_payload = await async_render_complex(hass, page, variables=vars_)

    # 2) Validate into a discriminated page model
    page = PageModel.model_validate(rendered_payload)

    if isinstance(page, TemplatePage):
        # Load the built-in template payload (a full components page dict).
        template_payload = await load_builtin_template(hass, page.template_name)

        # Merge variables in a predictable order (later wins):
        # 1) template file defaults (`variables:`)
        # 2) template page vars (`template_vars`)
        # 3) service call vars (render_page(..., variables=...))
        template_vars: dict[str, Any] = {}
        if isinstance(template_payload.get("variables"), dict):
            template_vars.update(template_payload["variables"])
        if isinstance(page.template_vars, dict):
            template_vars.update(page.template_vars)
        template_vars.update(vars_)

        # Allow TemplatePage to override duration in the expanded payload
        # (useful for rotation config; renderer itself doesn't depend on it).
        if page.duration is not None:
            template_payload = dict(template_payload)
            template_payload["duration"] = page.duration

        rendered_payload = await async_render_complex(
            hass, template_payload, variables=template_vars
        )
        page = PageModel.model_validate(rendered_payload)

        if isinstance(page, TemplatePage):
            raise PageEngineValidationError("Nested template pages are not supported")

        vars_ = template_vars

    # Handle ChannelPage: switch to native Pixoo channel (no buffer rendering)
    if isinstance(page, ChannelPage):
        channel_map = {
            "clock": 0,      # Channel.FACES
            "cloud": 1,      # Channel.CLOUD
            "visualizer": 2, # Channel.VISUALIZER
            "custom": 3,     # Channel.CUSTOM
        }
        channel_id = channel_map.get(page.channel_name, 0)
        await pixoo.set_channel(channel_id)

        # Optional: set specific clock/visualizer/custom page ID
        if page.channel_name == "clock" and page.clock_id is not None:
            await pixoo.set_clock(page.clock_id)
        elif page.channel_name == "visualizer" and page.visualizer_id is not None:
            await pixoo.set_visualizer(page.visualizer_id)
        elif page.channel_name == "custom" and page.custom_page_id is not None:
            await pixoo.set_custom_page(page.custom_page_id)

        _LOGGER.debug(
            "Page Engine: switched to channel %s (entry_id=%s)",
            page.channel_name,
            entry_id,
        )
        return  # No buffer push needed for channel switch

    if not isinstance(page, ComponentsPage):
        raise PageEngineValidationError(f"Unsupported page type: {type(page)!r}")

    # 3) Apply background/clear buffer first
    rendered_any = False
    component_errors: list[Exception] = []

    try:
        if page.background is not None:
            bg = render_color(hass, page.background, variables=vars_)
            pixoo.fill(bg)
            rendered_any = True
        else:
            pixoo.clear()
    except Exception as err:
        component_errors.append(err)
        _LOGGER.exception(
            "Page Engine: failed to apply background (entry_id=%s): %s",
            entry_id,
            err,
        )
        pixoo.clear()

    # 4) Render components in z-order (stable)
    ordered = sorted(
        ((c.z if c.z is not None else idx, idx, c) for idx, c in enumerate(page.components)),
        key=lambda t: (t[0], t[1]),
    )

    for _z, idx, component in ordered:
        # Check component-level enabled condition
        if component.enabled is not None:
            enabled = component.enabled
            if isinstance(enabled, str):
                # Template: render and evaluate as boolean
                from homeassistant.helpers.template import Template
                try:
                    rendered = Template(enabled, hass).async_render(vars_, parse_result=False)
                    # Parse as boolean (handle "true"/"false"/truthy values)
                    if isinstance(rendered, bool):
                        enabled = rendered
                    elif isinstance(rendered, str):
                        enabled = rendered.lower() not in ("false", "0", "no", "off", "none", "")
                    else:
                        enabled = bool(rendered)
                except Exception as err:
                    _LOGGER.warning(
                        "Page Engine: component %d enabled template failed: %s - skipping",
                        idx, err
                    )
                    enabled = False
            if not enabled:
                _LOGGER.debug(
                    "Page Engine: component %d (%s) disabled by enabled condition - skipping",
                    idx, getattr(component, "type", type(component).__name__)
                )
                continue

        if not component_in_bounds(component, device_size=device_size):
            _LOGGER.warning(
                "Page Engine: component %d (%s) out of bounds for %dx%d (entry_id=%s) - skipping",
                idx,
                getattr(component, "type", type(component).__name__),
                device_size,
                device_size,
                entry_id,
            )
            continue

        try:
            if isinstance(component, TextComponent):
                rgb = render_color(hass, component.color or "#FFFFFF", variables=vars_)
                text = component.text

                # Render template values for coordinates
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")

                # Check if scrolling text is enabled
                if component.scroll:
                    # Use scrolling text API
                    scroll_dir = (
                        1 if component.scroll_direction == "right" else 0  # 0=LEFT, 1=RIGHT
                    )
                    text_width = component.text_width or device_size
                    
                    # send_text uses identifier 0-19, we use component index mod 20
                    text_id = idx % 20
                    
                    await pixoo.send_text(
                        text=text,
                        xy=(comp_x, comp_y),
                        color=rgb,
                        identifier=text_id,
                        font=2,  # Default font
                        width=text_width,
                        movement_speed=component.scroll_speed,
                        direction=scroll_dir,
                    )
                else:
                    # Static text
                    x = comp_x
                    if component.align in ("center", "right"):
                        # Pixoo font: 3px wide + 1px spacing -> total width = 4*n - 1
                        text_width = max(0, 4 * len(text) - 1)
                        if component.align == "center":
                            x = x - (text_width // 2)
                        else:  # right
                            x = x - text_width + 1

                    pixoo.draw_text(text, (x, comp_y), rgb)
                rendered_any = True
                continue

            if isinstance(component, RectangleComponent):
                # Render template values for coordinates and dimensions
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")
                comp_width = await _render_int(hass, component.width, vars_, "width")
                comp_height = await _render_int(hass, component.height, vars_, "height")
                
                # Validate bounds after rendering
                if comp_width <= 0 or comp_height <= 0:
                    _LOGGER.warning(
                        "Page Engine: rectangle %d has invalid dimensions %dx%d - skipping",
                        idx, comp_width, comp_height
                    )
                    continue
                
                rgb = render_color(hass, component.color or "#FFFFFF", variables=vars_)
                top_left = (comp_x, comp_y)
                bottom_right = (
                    comp_x + comp_width - 1,
                    comp_y + comp_height - 1,
                )

                if component.filled:
                    pixoo.draw_filled_rectangle(top_left, bottom_right, rgb)
                else:
                    # Outline: 4 lines
                    pixoo.draw_line((top_left[0], top_left[1]), (bottom_right[0], top_left[1]), rgb)
                    pixoo.draw_line((bottom_right[0], top_left[1]), (bottom_right[0], bottom_right[1]), rgb)
                    pixoo.draw_line((bottom_right[0], bottom_right[1]), (top_left[0], bottom_right[1]), rgb)
                    pixoo.draw_line((top_left[0], bottom_right[1]), (top_left[0], top_left[1]), rgb)

                rendered_any = True
                continue

            if isinstance(component, ImageComponent):
                # Render template values for coordinates
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")
                
                # Render template in image source URL/path if present
                source = component.source
                if source.url is not None and ("{{" in source.url or "{%" in source.url):
                    from homeassistant.helpers.template import Template
                    rendered_url = Template(source.url, hass).async_render(vars_, parse_result=False)
                    rendered_url_str = str(rendered_url).strip() if rendered_url else ""
                    # Skip if URL rendered to empty/None
                    if not rendered_url_str or rendered_url_str in ("None", ""):
                        _LOGGER.debug("Page Engine: image URL template rendered to empty - skipping")
                        continue
                    # Create a new ImageSource with the rendered URL
                    from .models import ImageSource
                    source = ImageSource(url=rendered_url_str)
                elif source.path is not None and ("{{" in source.path or "{%" in source.path):
                    from homeassistant.helpers.template import Template
                    rendered_path = Template(source.path, hass).async_render(vars_, parse_result=False)
                    rendered_path_str = str(rendered_path).strip() if rendered_path else ""
                    if not rendered_path_str or rendered_path_str in ("None", ""):
                        _LOGGER.debug("Page Engine: image path template rendered to empty - skipping")
                        continue
                    from .models import ImageSource
                    source = ImageSource(path=rendered_path_str)
                # Also check if the source URL/path is empty without being a template
                elif source.url is not None and (not source.url.strip() or source.url.strip() == "None"):
                    _LOGGER.debug("Page Engine: image URL is empty - skipping")
                    continue
                elif source.path is not None and (not source.path.strip() or source.path.strip() == "None"):
                    _LOGGER.debug("Page Engine: image path is empty - skipping")
                    continue
                
                image = await async_resolve_image_source(
                    hass,
                    source,
                    device_size=device_size,
                    allowlist_mode=allowlist_mode,
                )
                pixoo.draw_image(image, xy=(comp_x, comp_y))
                rendered_any = True
                continue

            if isinstance(component, ProgressBarComponent):
                # Render template values for coordinates and dimensions
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")
                comp_width = await _render_int(hass, component.width, vars_, "width")
                comp_height = await _render_int(hass, component.height, vars_, "height")
                
                # Validate bounds after rendering
                if comp_width <= 0 or comp_height <= 0:
                    _LOGGER.warning(
                        "Page Engine: progress_bar %d has invalid dimensions %dx%d - skipping",
                        idx, comp_width, comp_height
                    )
                    continue
                
                # Resolve progress value (entity_id, template, or direct float)
                progress_val = component.progress
                if isinstance(progress_val, str):
                    # Check if it's an entity_id (contains dot but no template braces)
                    if "." in progress_val and "{{" not in progress_val and "{%" not in progress_val:
                        state = hass.states.get(progress_val)
                        if state is not None:
                            try:
                                progress_val = float(state.state)
                            except (ValueError, TypeError):
                                progress_val = 0.0
                        else:
                            progress_val = 0.0
                    else:
                        # Template
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(progress_val), hass).async_render(vars_, parse_result=False)
                        try:
                            progress_val = float(rendered)
                        except (ValueError, TypeError):
                            progress_val = 0.0

                # Normalize to 0-1 range
                range_size = component.max_value - component.min_value
                if range_size > 0:
                    normalized = (float(progress_val) - component.min_value) / range_size
                else:
                    normalized = 0.0
                normalized = max(0.0, min(1.0, normalized))

                # Determine bar color (threshold or static)
                if component.color_thresholds:
                    bar_rgb = compute_threshold_color(
                        hass, float(progress_val), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(0, 255, 0), variables=vars_
                    )
                else:
                    bar_rgb = render_color(hass, component.bar_color or "#00FF00", variables=vars_)

                bg_rgb = render_color(hass, component.background_color or "#333333", variables=vars_)

                # Draw background
                pixoo.draw_filled_rectangle(
                    (comp_x, comp_y),
                    (comp_x + comp_width - 1, comp_y + comp_height - 1),
                    bg_rgb
                )

                # Draw progress fill
                if component.orientation == "horizontal":
                    fill_width = int(normalized * comp_width)
                    if fill_width > 0:
                        pixoo.draw_filled_rectangle(
                            (comp_x, comp_y),
                            (comp_x + fill_width - 1, comp_y + comp_height - 1),
                            bar_rgb
                        )
                else:  # vertical
                    fill_height = int(normalized * comp_height)
                    if fill_height > 0:
                        y_start = comp_y + comp_height - fill_height
                        pixoo.draw_filled_rectangle(
                            (comp_x, y_start),
                            (comp_x + comp_width - 1, comp_y + comp_height - 1),
                            bar_rgb
                        )

                # Draw border if requested
                if component.show_border and component.border_color:
                    border_rgb = render_color(hass, component.border_color, variables=vars_)
                    tl = (comp_x, comp_y)
                    br = (comp_x + comp_width - 1, comp_y + comp_height - 1)
                    pixoo.draw_line((tl[0], tl[1]), (br[0], tl[1]), border_rgb)
                    pixoo.draw_line((br[0], tl[1]), (br[0], br[1]), border_rgb)
                    pixoo.draw_line((br[0], br[1]), (tl[0], br[1]), border_rgb)
                    pixoo.draw_line((tl[0], br[1]), (tl[0], tl[1]), border_rgb)

                rendered_any = True
                continue

            if isinstance(component, GraphComponent):
                # Render template values for coordinates and dimensions
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")
                comp_width = await _render_int(hass, component.width, vars_, "width")
                comp_height = await _render_int(hass, component.height, vars_, "height")
                
                # Validate bounds after rendering
                if comp_width <= 0 or comp_height <= 0:
                    _LOGGER.warning(
                        "Page Engine: graph %d has invalid dimensions %dx%d - skipping",
                        idx, comp_width, comp_height
                    )
                    continue
                
                # Fetch entity history
                from datetime import datetime, timedelta

                end_time = datetime.now()
                start_time = end_time - timedelta(hours=component.hours)

                # Get history from recorder
                states = []
                try:
                    from homeassistant.components.recorder import get_instance
                    from homeassistant.components.recorder.history import state_changes_during_period

                    history = await get_instance(hass).async_add_executor_job(
                        state_changes_during_period,
                        hass,
                        start_time,
                        end_time,
                        component.entity_id,
                    )
                    states = history.get(component.entity_id, [])
                except Exception as err:
                    _LOGGER.warning("Graph: failed to fetch history for %s: %s", component.entity_id, err)

                # Parse numeric values
                values = []
                for state in states:
                    try:
                        values.append(float(state.state))
                    except (ValueError, TypeError):
                        continue

                # Draw background
                bg_rgb = render_color(hass, component.background_color or "#111111", variables=vars_)
                pixoo.draw_filled_rectangle(
                    (comp_x, comp_y),
                    (comp_x + comp_width - 1, comp_y + comp_height - 1),
                    bg_rgb
                )

                if not values:
                    # No data: just show background
                    rendered_any = True
                    continue

                # Auto-calculate points from width if not specified
                num_points = component.points if component.points else comp_width

                # Aggregate values into bins
                bin_size = max(1, len(values) // num_points)
                aggregated = []
                for i in range(0, len(values), bin_size):
                    bin_values = values[i:i + bin_size]
                    if component.aggregate_func == "avg":
                        aggregated.append(sum(bin_values) / len(bin_values))
                    elif component.aggregate_func == "min":
                        aggregated.append(min(bin_values))
                    elif component.aggregate_func == "max":
                        aggregated.append(max(bin_values))
                    else:  # last
                        aggregated.append(bin_values[-1])

                # Limit to num_points
                aggregated = aggregated[-num_points:]

                if not aggregated:
                    rendered_any = True
                    continue

                # Calculate Y bounds
                y_min = component.min_value if component.min_value is not None else min(aggregated)
                y_max = component.max_value if component.max_value is not None else max(aggregated)
                y_range = y_max - y_min if y_max > y_min else 1

                default_color = render_color(hass, component.line_color or "#3498db", variables=vars_)

                # Calculate pixel positions
                points_px = []
                x_step = (comp_width - 1) / max(1, len(aggregated) - 1) if len(aggregated) > 1 else 0
                for i, val in enumerate(aggregated):
                    px_x = comp_x + int(i * x_step) if x_step else comp_x + i
                    normalized_y = (val - y_min) / y_range
                    px_y = comp_y + comp_height - 1 - int(normalized_y * (comp_height - 1))
                    points_px.append((px_x, px_y, val))

                if component.style == "bar":
                    bar_width = max(1, comp_width // len(aggregated) - 1)
                    for px_x, px_y, val in points_px:
                        # Determine color
                        if component.color_thresholds:
                            bar_rgb = compute_threshold_color(
                                hass, val, component.color_thresholds,
                                component.color_thresholds_transition,
                                default_color=default_color, variables=vars_
                            )
                        else:
                            bar_rgb = default_color
                        # Draw bar from bottom to value
                        bottom_y = comp_y + comp_height - 1
                        if px_y < bottom_y:
                            pixoo.draw_filled_rectangle(
                                (px_x, px_y),
                                (min(px_x + bar_width - 1, comp_x + comp_width - 1), bottom_y),
                                bar_rgb
                            )

                else:  # line or area
                    # Draw fill if area style or show_fill
                    if component.style == "area" or component.show_fill:
                        fill_rgb = render_color(hass, component.fill_color or "#1a5276", variables=vars_)
                        bottom_y = comp_y + comp_height - 1
                        for px_x, px_y, _ in points_px:
                            if px_y < bottom_y:
                                pixoo.draw_line((px_x, px_y), (px_x, bottom_y), fill_rgb)

                    # Draw line segments with threshold coloring
                    for i in range(len(points_px) - 1):
                        x1, y1, v1 = points_px[i]
                        x2, y2, v2 = points_px[i + 1]
                        avg_val = (v1 + v2) / 2

                        if component.color_thresholds:
                            line_rgb = compute_threshold_color(
                                hass, avg_val, component.color_thresholds,
                                component.color_thresholds_transition,
                                default_color=default_color, variables=vars_
                            )
                        else:
                            line_rgb = default_color

                        pixoo.draw_line((x1, y1), (x2, y2), line_rgb)

                rendered_any = True
                continue

            if isinstance(component, IconComponent):
                # Render template values for coordinates
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")
                
                # Resolve value for threshold coloring
                icon_value = component.value
                if isinstance(icon_value, str):
                    # Check if entity_id or template
                    if "." in icon_value and "{{" not in icon_value and "{%" not in icon_value:
                        state = hass.states.get(icon_value)
                        if state is not None:
                            try:
                                icon_value = float(state.state)
                            except (ValueError, TypeError):
                                icon_value = 0.0
                        else:
                            icon_value = 0.0
                    else:
                        # Template
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(icon_value), hass).async_render(vars_, parse_result=False)
                        try:
                            icon_value = float(rendered)
                        except (ValueError, TypeError):
                            icon_value = 0.0

                # Determine icon color (threshold or static)
                if component.color_thresholds and icon_value is not None:
                    icon_rgb = compute_threshold_color(
                        hass, float(icon_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    icon_rgb = render_color(hass, component.color or "#FFFFFF", variables=vars_)

                # Fetch and render icon
                icon_img = await _fetch_and_render_mdi_icon(
                    hass, component.icon, component.size, icon_rgb
                )

                # Draw icon onto buffer
                pixoo.draw_image(icon_img, xy=(comp_x, comp_y))
                rendered_any = True
                continue

            if isinstance(component, LineComponent):
                # Render line coordinates
                start_x = await _render_int(hass, component.start[0], vars_, "start[0]")
                start_y = await _render_int(hass, component.start[1], vars_, "start[1]")
                end_x = await _render_int(hass, component.end[0], vars_, "end[0]")
                end_y = await _render_int(hass, component.end[1], vars_, "end[1]")
                
                # Resolve value for threshold coloring
                line_value = component.value
                if isinstance(line_value, str):
                    if "." in line_value and "{{" not in line_value and "{%" not in line_value:
                        state = hass.states.get(line_value)
                        if state is not None:
                            try:
                                line_value = float(state.state)
                            except (ValueError, TypeError):
                                line_value = 0.0
                        else:
                            line_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(line_value), hass).async_render(vars_, parse_result=False)
                        try:
                            line_value = float(rendered)
                        except (ValueError, TypeError):
                            line_value = 0.0

                # Determine line color (threshold or static)
                if component.color_thresholds and line_value is not None:
                    line_rgb = compute_threshold_color(
                        hass, float(line_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    line_rgb = render_color(hass, component.color, variables=vars_)

                # Draw line with thickness
                if component.thickness == 1:
                    pixoo.draw_line((start_x, start_y), (end_x, end_y), line_rgb)
                else:
                    # For thickness > 1, draw multiple parallel lines
                    import math
                    dx = end_x - start_x
                    dy = end_y - start_y
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        # Perpendicular offset
                        px = -dy / length
                        py = dx / length
                        # Draw multiple lines offset perpendicular to main line
                        for offset in range(-(component.thickness // 2), (component.thickness + 1) // 2):
                            offset_x = int(px * offset)
                            offset_y = int(py * offset)
                            pixoo.draw_line(
                                (start_x + offset_x, start_y + offset_y),
                                (end_x + offset_x, end_y + offset_y),
                                line_rgb
                            )
                
                rendered_any = True
                continue

            if isinstance(component, CircleComponent):
                # Render circle parameters
                center_x = await _render_int(hass, component.center[0], vars_, "center[0]")
                center_y = await _render_int(hass, component.center[1], vars_, "center[1]")
                radius = await _render_int(hass, component.radius, vars_, "radius")
                
                # Resolve value for threshold coloring
                circle_value = component.value
                if isinstance(circle_value, str):
                    if "." in circle_value and "{{" not in circle_value and "{%" not in circle_value:
                        state = hass.states.get(circle_value)
                        if state is not None:
                            try:
                                circle_value = float(state.state)
                            except (ValueError, TypeError):
                                circle_value = 0.0
                        else:
                            circle_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(circle_value), hass).async_render(vars_, parse_result=False)
                        try:
                            circle_value = float(rendered)
                        except (ValueError, TypeError):
                            circle_value = 0.0

                # Determine circle color (threshold or static)
                if component.color_thresholds and circle_value is not None:
                    circle_rgb = compute_threshold_color(
                        hass, float(circle_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    circle_rgb = render_color(hass, component.color, variables=vars_)

                # Calculate bounding box
                x0 = center_x - radius
                y0 = center_y - radius
                x1 = center_x + radius
                y1 = center_y + radius
                
                # Draw circle/ellipse
                if component.filled:
                    # Filled circle using Pillow's ellipse
                    # We need to use the buffer's internal image for this
                    from PIL import ImageDraw
                    # Get the underlying image from buffer
                    if hasattr(pixoo, '_image'):
                        draw = ImageDraw.Draw(pixoo._image)
                        draw.ellipse([x0, y0, x1, y1], fill=circle_rgb)
                    else:
                        # Fallback: draw filled circle pixel by pixel
                        import math
                        for x in range(max(0, x0), min(device_size, x1 + 1)):
                            for y in range(max(0, y0), min(device_size, y1 + 1)):
                                dx = x - center_x
                                dy = y - center_y
                                if dx*dx + dy*dy <= radius*radius:
                                    pixoo.draw_pixel((x, y), circle_rgb)
                else:
                    # Outline only using Pillow's ellipse
                    if hasattr(pixoo, '_image'):
                        from PIL import ImageDraw
                        draw = ImageDraw.Draw(pixoo._image)
                        draw.ellipse([x0, y0, x1, y1], outline=circle_rgb, width=component.thickness)
                    else:
                        # Fallback: draw circle outline using Bresenham's algorithm
                        import math
                        for angle in range(0, 360, 2):
                            rad = math.radians(angle)
                            x = int(center_x + radius * math.cos(rad))
                            y = int(center_y + radius * math.sin(rad))
                            if 0 <= x < device_size and 0 <= y < device_size:
                                pixoo.draw_pixel((x, y), circle_rgb)
                
                rendered_any = True
                continue

            if isinstance(component, ArcComponent):
                # Render arc parameters
                center_x = await _render_int(hass, component.center[0], vars_, "center[0]")
                center_y = await _render_int(hass, component.center[1], vars_, "center[1]")
                radius = await _render_int(hass, component.radius, vars_, "radius")
                
                # Render angles (support templates)
                start_angle = component.start_angle
                if isinstance(start_angle, str):
                    from homeassistant.helpers.template import Template
                    rendered = Template(str(start_angle), hass).async_render(vars_, parse_result=False)
                    try:
                        start_angle = float(rendered)
                    except (ValueError, TypeError):
                        start_angle = 0.0
                else:
                    start_angle = float(start_angle)
                
                end_angle = component.end_angle
                if isinstance(end_angle, str):
                    from homeassistant.helpers.template import Template
                    rendered = Template(str(end_angle), hass).async_render(vars_, parse_result=False)
                    try:
                        end_angle = float(rendered)
                    except (ValueError, TypeError):
                        end_angle = 90.0
                else:
                    end_angle = float(end_angle)
                
                # Resolve value for threshold coloring
                arc_value = component.value
                if isinstance(arc_value, str):
                    if "." in arc_value and "{{" not in arc_value and "{%" not in arc_value:
                        state = hass.states.get(arc_value)
                        if state is not None:
                            try:
                                arc_value = float(state.state)
                            except (ValueError, TypeError):
                                arc_value = 0.0
                        else:
                            arc_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(arc_value), hass).async_render(vars_, parse_result=False)
                        try:
                            arc_value = float(rendered)
                        except (ValueError, TypeError):
                            arc_value = 0.0

                # Determine arc color (threshold or static)
                if component.color_thresholds and arc_value is not None:
                    arc_rgb = compute_threshold_color(
                        hass, float(arc_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    arc_rgb = render_color(hass, component.color, variables=vars_)

                # Convert angles from "0=top, clockwise" to Pillow's "0=right, counter-clockwise"
                # Pillow uses: 0° = 3 o'clock, counter-clockwise
                # We use: 0° = 12 o'clock, clockwise
                # Conversion: pillow_angle = 90 - our_angle
                pillow_start = 90 - start_angle
                pillow_end = 90 - end_angle
                
                # Ensure start < end for Pillow (swap if needed)
                if pillow_start > pillow_end:
                    pillow_start, pillow_end = pillow_end, pillow_start

                # Calculate bounding box
                x0 = center_x - radius
                y0 = center_y - radius
                x1 = center_x + radius
                y1 = center_y + radius
                
                # Draw arc
                if hasattr(pixoo, '_image'):
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(pixoo._image)
                    if component.filled:
                        # Filled pie slice
                        draw.pieslice([x0, y0, x1, y1], start=pillow_start, end=pillow_end, fill=arc_rgb)
                    else:
                        # Arc outline
                        draw.arc([x0, y0, x1, y1], start=pillow_start, end=pillow_end, fill=arc_rgb, width=component.thickness)
                else:
                    # Fallback: draw arc pixel by pixel
                    import math
                    for angle in range(int(start_angle), int(end_angle) + 1, 2):
                        rad = math.radians(angle)
                        x = int(center_x + radius * math.sin(rad))
                        y = int(center_y - radius * math.cos(rad))
                        if 0 <= x < device_size and 0 <= y < device_size:
                            pixoo.draw_pixel((x, y), arc_rgb)
                
                rendered_any = True
                continue

            if isinstance(component, ArrowComponent):
                # Render arrow parameters
                center_x = await _render_int(hass, component.center[0], vars_, "center[0]")
                center_y = await _render_int(hass, component.center[1], vars_, "center[1]")
                length = await _render_int(hass, component.length, vars_, "length")
                
                # Render angle (support templates)
                angle = component.angle
                if isinstance(angle, str):
                    from homeassistant.helpers.template import Template
                    rendered = Template(str(angle), hass).async_render(vars_, parse_result=False)
                    try:
                        angle = float(rendered)
                    except (ValueError, TypeError):
                        angle = 0.0
                else:
                    angle = float(angle)
                
                # Resolve value for threshold coloring
                arrow_value = component.value
                if isinstance(arrow_value, str):
                    if "." in arrow_value and "{{" not in arrow_value and "{%" not in arrow_value:
                        state = hass.states.get(arrow_value)
                        if state is not None:
                            try:
                                arrow_value = float(state.state)
                            except (ValueError, TypeError):
                                arrow_value = 0.0
                        else:
                            arrow_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(arrow_value), hass).async_render(vars_, parse_result=False)
                        try:
                            arrow_value = float(rendered)
                        except (ValueError, TypeError):
                            arrow_value = 0.0

                # Determine arrow color (threshold or static)
                if component.color_thresholds and arrow_value is not None:
                    arrow_rgb = compute_threshold_color(
                        hass, float(arrow_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    arrow_rgb = render_color(hass, component.color, variables=vars_)

                # Calculate arrow endpoint (angle: 0=up, clockwise)
                import math
                rad = math.radians(angle)
                end_x = int(center_x + length * math.sin(rad))
                end_y = int(center_y - length * math.cos(rad))
                
                # Draw arrow line with thickness
                if component.thickness == 1:
                    pixoo.draw_line((center_x, center_y), (end_x, end_y), arrow_rgb)
                else:
                    # For thickness > 1, draw multiple parallel lines
                    dx = end_x - center_x
                    dy = end_y - center_y
                    line_length = math.sqrt(dx*dx + dy*dy)
                    if line_length > 0:
                        px = -dy / line_length
                        py = dx / line_length
                        for offset in range(-(component.thickness // 2), (component.thickness + 1) // 2):
                            offset_x = int(px * offset)
                            offset_y = int(py * offset)
                            pixoo.draw_line(
                                (center_x + offset_x, center_y + offset_y),
                                (end_x + offset_x, end_y + offset_y),
                                arrow_rgb
                            )
                
                # Draw arrow head (triangle)
                head_size = component.head_size
                # Calculate two points for arrow head triangle
                head_angle1 = angle + 150  # 30° left
                head_angle2 = angle - 150  # 30° right
                rad1 = math.radians(head_angle1)
                rad2 = math.radians(head_angle2)
                
                head1_x = int(end_x + head_size * math.sin(rad1))
                head1_y = int(end_y - head_size * math.cos(rad1))
                head2_x = int(end_x + head_size * math.sin(rad2))
                head2_y = int(end_y - head_size * math.cos(rad2))
                
                # Draw triangle (3 lines)
                pixoo.draw_line((end_x, end_y), (head1_x, head1_y), arrow_rgb)
                pixoo.draw_line((end_x, end_y), (head2_x, head2_y), arrow_rgb)
                pixoo.draw_line((head1_x, head1_y), (head2_x, head2_y), arrow_rgb)
                
                # Fill triangle if thickness > 1
                if component.thickness > 1 and hasattr(pixoo, '_image'):
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(pixoo._image)
                    draw.polygon([(end_x, end_y), (head1_x, head1_y), (head2_x, head2_y)], fill=arrow_rgb)
                
                rendered_any = True
                continue

            raise PageEngineValidationError(
                f"Unsupported component type: {getattr(component, 'type', type(component).__name__)}"
            )

        except Exception as err:
            component_errors.append(err)
            _LOGGER.exception(
                "Page Engine: component %d (%s) failed (entry_id=%s): %s",
                idx,
                getattr(component, "type", type(component).__name__),
                entry_id,
                err,
            )
            continue

    if not rendered_any:
        if component_errors:
            raise PageEngineValidationError(
                f"No components/background rendered; last error: {component_errors[-1]}"
            )
        raise PageEngineValidationError("No components rendered (all were out of bounds?)")

    # 5) Push buffer to device
    try:
        await pixoo.push()
    except Exception as err:
        _LOGGER.error(
            "Page Engine: push failed (entry_id=%s): %s",
            entry_id,
            err,
        )
        raise

async def render_page_to_buffer(
    hass: HomeAssistant,
    buffer: DisplayBuffer,
    page: Any,
    *,
    device_size: int,
    variables: dict[str, Any] | None = None,
    allowlist_mode: str = ALLOWLIST_MODE_STRICT,
    entry_id: str | None = None,
) -> None:
    """Render a page onto a DisplayBuffer (without pushing to device).
    
    This function is used for preview/simulator rendering. It works the same
    as render_page() but uses the DisplayBuffer interface instead of a Pixoo
    device, and does NOT push the result.
    
    For ChannelPage types, this renders a placeholder since native Pixoo
    channels cannot be simulated.
    
    Args:
        hass: Home Assistant instance
        buffer: DisplayBuffer to render onto (e.g., PillowDisplayBuffer)
        page: Page definition (dict or Pydantic model)
        device_size: Display size in pixels
        variables: Template variables
        allowlist_mode: URL/path allowlist mode
        entry_id: Config entry ID for logging
    """
    # Merge per-page default variables into the rendering context
    vars_: dict[str, Any] = {}
    if isinstance(page, dict) and isinstance(page.get("variables"), dict):
        vars_.update(page["variables"])
    if variables:
        vars_.update(variables)

    # Template rendering
    rendered_payload = await async_render_complex(hass, page, variables=vars_)

    # Validate into a discriminated page model
    page = PageModel.model_validate(rendered_payload)

    if isinstance(page, TemplatePage):
        template_payload = await load_builtin_template(hass, page.template_name)
        template_vars: dict[str, Any] = {}
        if isinstance(template_payload.get("variables"), dict):
            template_vars.update(template_payload["variables"])
        if isinstance(page.template_vars, dict):
            template_vars.update(page.template_vars)
        template_vars.update(vars_)

        if page.duration is not None:
            template_payload = dict(template_payload)
            template_payload["duration"] = page.duration

        rendered_payload = await async_render_complex(
            hass, template_payload, variables=template_vars
        )
        page = PageModel.model_validate(rendered_payload)

        if isinstance(page, TemplatePage):
            raise PageEngineValidationError("Nested template pages are not supported")

        vars_ = template_vars

    # Handle ChannelPage: render a placeholder (cannot simulate native channels)
    if isinstance(page, ChannelPage):
        buffer.clear()
        # Draw a simple placeholder indicating channel mode
        text = f"[{page.channel_name}]"
        buffer.draw_text(text, (4, 28), (100, 100, 100))
        _LOGGER.debug(
            "Page Engine preview: ChannelPage '%s' rendered as placeholder (entry_id=%s)",
            page.channel_name,
            entry_id,
        )
        return

    if not isinstance(page, ComponentsPage):
        raise PageEngineValidationError(f"Unsupported page type: {type(page)!r}")

    # Apply background/clear buffer
    rendered_any = False
    component_errors: list[Exception] = []

    try:
        if page.background is not None:
            bg = render_color(hass, page.background, variables=vars_)
            buffer.fill(bg)
            rendered_any = True
        else:
            buffer.clear()
    except Exception as err:
        component_errors.append(err)
        _LOGGER.exception(
            "Page Engine preview: failed to apply background (entry_id=%s): %s",
            entry_id,
            err,
        )
        buffer.clear()

    # Render components in z-order
    ordered = sorted(
        ((c.z if c.z is not None else idx, idx, c) for idx, c in enumerate(page.components)),
        key=lambda t: (t[0], t[1]),
    )

    for _z, idx, component in ordered:
        # Check component-level enabled condition
        if component.enabled is not None:
            enabled = component.enabled
            if isinstance(enabled, str):
                from homeassistant.helpers.template import Template
                try:
                    rendered = Template(enabled, hass).async_render(vars_, parse_result=False)
                    if isinstance(rendered, bool):
                        enabled = rendered
                    elif isinstance(rendered, str):
                        enabled = rendered.lower() not in ("false", "0", "no", "off", "none", "")
                    else:
                        enabled = bool(rendered)
                except Exception as err:
                    _LOGGER.warning(
                        "Page Engine preview: component %d enabled template failed: %s - skipping",
                        idx, err
                    )
                    enabled = False
            if not enabled:
                continue

        if not component_in_bounds(component, device_size=device_size):
            _LOGGER.debug(
                "Page Engine preview: component %d out of bounds - skipping",
                idx,
            )
            continue

        try:
            if isinstance(component, TextComponent):
                rgb = render_color(hass, component.color or "#FFFFFF", variables=vars_)
                text = component.text
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")

                if component.scroll:
                    # Scrolling text: render as static for preview
                    await buffer.send_text(
                        text=text,
                        xy=(comp_x, comp_y),
                        color=rgb,
                        identifier=idx % 20,
                        font=2,
                        width=component.text_width or device_size,
                        movement_speed=component.scroll_speed,
                        direction=1 if component.scroll_direction == "right" else 0,
                    )
                else:
                    x = comp_x
                    if component.align in ("center", "right"):
                        text_width = max(0, 4 * len(text) - 1)
                        if component.align == "center":
                            x = x - (text_width // 2)
                        else:
                            x = x - text_width + 1
                    buffer.draw_text(text, (x, comp_y), rgb)
                rendered_any = True
                continue

            if isinstance(component, RectangleComponent):
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")
                comp_width = await _render_int(hass, component.width, vars_, "width")
                comp_height = await _render_int(hass, component.height, vars_, "height")

                if comp_width <= 0 or comp_height <= 0:
                    continue

                rgb = render_color(hass, component.color or "#FFFFFF", variables=vars_)
                top_left = (comp_x, comp_y)
                bottom_right = (comp_x + comp_width - 1, comp_y + comp_height - 1)

                if component.filled:
                    buffer.draw_filled_rectangle(top_left, bottom_right, rgb)
                else:
                    buffer.draw_line((top_left[0], top_left[1]), (bottom_right[0], top_left[1]), rgb)
                    buffer.draw_line((bottom_right[0], top_left[1]), (bottom_right[0], bottom_right[1]), rgb)
                    buffer.draw_line((bottom_right[0], bottom_right[1]), (top_left[0], bottom_right[1]), rgb)
                    buffer.draw_line((top_left[0], bottom_right[1]), (top_left[0], top_left[1]), rgb)
                rendered_any = True
                continue

            if isinstance(component, ImageComponent):
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")

                source = component.source
                if source.url is not None and ("{{" in source.url or "{%" in source.url):
                    from homeassistant.helpers.template import Template
                    rendered_url = Template(source.url, hass).async_render(vars_, parse_result=False)
                    source = ImageSource(url=str(rendered_url))
                elif source.path is not None and ("{{" in source.path or "{%" in source.path):
                    from homeassistant.helpers.template import Template
                    rendered_path = Template(source.path, hass).async_render(vars_, parse_result=False)
                    source = ImageSource(path=str(rendered_path))

                img = await async_resolve_image_source(
                    hass, source, device_size=device_size, allowlist_mode=allowlist_mode
                )
                buffer.draw_image(img, xy=(comp_x, comp_y))
                rendered_any = True
                continue

            if isinstance(component, ProgressBarComponent):
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")
                comp_width = await _render_int(hass, component.width, vars_, "width")
                comp_height = await _render_int(hass, component.height, vars_, "height")

                progress_val = component.progress
                if isinstance(progress_val, str):
                    if "." in progress_val and "{{" not in progress_val:
                        state = hass.states.get(progress_val)
                        if state is not None:
                            try:
                                progress_val = float(state.state)
                            except (ValueError, TypeError):
                                progress_val = 0.0
                        else:
                            progress_val = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(progress_val), hass).async_render(vars_, parse_result=False)
                        try:
                            progress_val = float(rendered)
                        except (ValueError, TypeError):
                            progress_val = 0.0

                progress_val = float(progress_val)
                min_val = float(component.min_value)
                max_val = float(component.max_value)
                if max_val <= min_val:
                    max_val = min_val + 100
                pct = max(0.0, min(100.0, (progress_val - min_val) / (max_val - min_val) * 100))

                bg_rgb = render_color(hass, component.background_color or "#333333", variables=vars_)
                buffer.draw_filled_rectangle(
                    (comp_x, comp_y),
                    (comp_x + comp_width - 1, comp_y + comp_height - 1),
                    bg_rgb
                )

                if component.color_thresholds:
                    bar_rgb = compute_threshold_color(
                        hass, progress_val, component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(0, 255, 0), variables=vars_
                    )
                else:
                    bar_rgb = render_color(hass, component.bar_color or "#00FF00", variables=vars_)

                if component.orientation == "horizontal":
                    fill_width = max(1, int((comp_width - 1) * pct / 100))
                    buffer.draw_filled_rectangle(
                        (comp_x, comp_y),
                        (comp_x + fill_width - 1, comp_y + comp_height - 1),
                        bar_rgb
                    )
                else:
                    fill_height = max(1, int((comp_height - 1) * pct / 100))
                    buffer.draw_filled_rectangle(
                        (comp_x, comp_y + comp_height - fill_height),
                        (comp_x + comp_width - 1, comp_y + comp_height - 1),
                        bar_rgb
                    )
                rendered_any = True
                continue

            if isinstance(component, IconComponent):
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")

                icon_value = component.value
                if isinstance(icon_value, str):
                    if "." in icon_value and "{{" not in icon_value:
                        state = hass.states.get(icon_value)
                        if state is not None:
                            try:
                                icon_value = float(state.state)
                            except (ValueError, TypeError):
                                icon_value = 0.0
                        else:
                            icon_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(icon_value), hass).async_render(vars_, parse_result=False)
                        try:
                            icon_value = float(rendered)
                        except (ValueError, TypeError):
                            icon_value = 0.0

                if component.color_thresholds and icon_value is not None:
                    icon_rgb = compute_threshold_color(
                        hass, float(icon_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    icon_rgb = render_color(hass, component.color or "#FFFFFF", variables=vars_)

                icon_img = await _fetch_and_render_mdi_icon(
                    hass, component.icon, component.size, icon_rgb
                )
                buffer.draw_image(icon_img, xy=(comp_x, comp_y))
                rendered_any = True
                continue

            if isinstance(component, LineComponent):
                start_x = await _render_int(hass, component.start[0], vars_, "start[0]")
                start_y = await _render_int(hass, component.start[1], vars_, "start[1]")
                end_x = await _render_int(hass, component.end[0], vars_, "end[0]")
                end_y = await _render_int(hass, component.end[1], vars_, "end[1]")
                
                line_value = component.value
                if isinstance(line_value, str):
                    if "." in line_value and "{{" not in line_value:
                        state = hass.states.get(line_value)
                        if state is not None:
                            try:
                                line_value = float(state.state)
                            except (ValueError, TypeError):
                                line_value = 0.0
                        else:
                            line_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(line_value), hass).async_render(vars_, parse_result=False)
                        try:
                            line_value = float(rendered)
                        except (ValueError, TypeError):
                            line_value = 0.0

                if component.color_thresholds and line_value is not None:
                    line_rgb = compute_threshold_color(
                        hass, float(line_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    line_rgb = render_color(hass, component.color, variables=vars_)

                if component.thickness == 1:
                    buffer.draw_line((start_x, start_y), (end_x, end_y), line_rgb)
                else:
                    import math
                    dx = end_x - start_x
                    dy = end_y - start_y
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        px = -dy / length
                        py = dx / length
                        for offset in range(-(component.thickness // 2), (component.thickness + 1) // 2):
                            offset_x = int(px * offset)
                            offset_y = int(py * offset)
                            buffer.draw_line(
                                (start_x + offset_x, start_y + offset_y),
                                (end_x + offset_x, end_y + offset_y),
                                line_rgb
                            )
                
                rendered_any = True
                continue

            if isinstance(component, CircleComponent):
                center_x = await _render_int(hass, component.center[0], vars_, "center[0]")
                center_y = await _render_int(hass, component.center[1], vars_, "center[1]")
                radius = await _render_int(hass, component.radius, vars_, "radius")
                
                circle_value = component.value
                if isinstance(circle_value, str):
                    if "." in circle_value and "{{" not in circle_value:
                        state = hass.states.get(circle_value)
                        if state is not None:
                            try:
                                circle_value = float(state.state)
                            except (ValueError, TypeError):
                                circle_value = 0.0
                        else:
                            circle_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(circle_value), hass).async_render(vars_, parse_result=False)
                        try:
                            circle_value = float(rendered)
                        except (ValueError, TypeError):
                            circle_value = 0.0

                if component.color_thresholds and circle_value is not None:
                    circle_rgb = compute_threshold_color(
                        hass, float(circle_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    circle_rgb = render_color(hass, component.color, variables=vars_)

                # Use buffer methods directly
                if hasattr(buffer, '_image'):
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(buffer._image)
                    x0 = center_x - radius
                    y0 = center_y - radius
                    x1 = center_x + radius
                    y1 = center_y + radius
                    if component.filled:
                        draw.ellipse([x0, y0, x1, y1], fill=circle_rgb)
                    else:
                        draw.ellipse([x0, y0, x1, y1], outline=circle_rgb, width=component.thickness)
                else:
                    # Fallback: pixel-by-pixel
                    import math
                    if component.filled:
                        for x in range(max(0, center_x - radius), min(device_size, center_x + radius + 1)):
                            for y in range(max(0, center_y - radius), min(device_size, center_y + radius + 1)):
                                dx = x - center_x
                                dy = y - center_y
                                if dx*dx + dy*dy <= radius*radius:
                                    buffer.draw_pixel((x, y), circle_rgb)
                    else:
                        for angle in range(0, 360, 2):
                            rad = math.radians(angle)
                            x = int(center_x + radius * math.cos(rad))
                            y = int(center_y + radius * math.sin(rad))
                            if 0 <= x < device_size and 0 <= y < device_size:
                                buffer.draw_pixel((x, y), circle_rgb)
                
                rendered_any = True
                continue

            if isinstance(component, ArcComponent):
                center_x = await _render_int(hass, component.center[0], vars_, "center[0]")
                center_y = await _render_int(hass, component.center[1], vars_, "center[1]")
                radius = await _render_int(hass, component.radius, vars_, "radius")
                
                start_angle = component.start_angle
                if isinstance(start_angle, str):
                    from homeassistant.helpers.template import Template
                    rendered = Template(str(start_angle), hass).async_render(vars_, parse_result=False)
                    try:
                        start_angle = float(rendered)
                    except (ValueError, TypeError):
                        start_angle = 0.0
                else:
                    start_angle = float(start_angle)
                
                end_angle = component.end_angle
                if isinstance(end_angle, str):
                    from homeassistant.helpers.template import Template
                    rendered = Template(str(end_angle), hass).async_render(vars_, parse_result=False)
                    try:
                        end_angle = float(rendered)
                    except (ValueError, TypeError):
                        end_angle = 90.0
                else:
                    end_angle = float(end_angle)
                
                arc_value = component.value
                if isinstance(arc_value, str):
                    if "." in arc_value and "{{" not in arc_value:
                        state = hass.states.get(arc_value)
                        if state is not None:
                            try:
                                arc_value = float(state.state)
                            except (ValueError, TypeError):
                                arc_value = 0.0
                        else:
                            arc_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(arc_value), hass).async_render(vars_, parse_result=False)
                        try:
                            arc_value = float(rendered)
                        except (ValueError, TypeError):
                            arc_value = 0.0

                if component.color_thresholds and arc_value is not None:
                    arc_rgb = compute_threshold_color(
                        hass, float(arc_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    arc_rgb = render_color(hass, component.color, variables=vars_)

                pillow_start = 90 - start_angle
                pillow_end = 90 - end_angle
                if pillow_start > pillow_end:
                    pillow_start, pillow_end = pillow_end, pillow_start

                if hasattr(buffer, '_image'):
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(buffer._image)
                    x0 = center_x - radius
                    y0 = center_y - radius
                    x1 = center_x + radius
                    y1 = center_y + radius
                    if component.filled:
                        draw.pieslice([x0, y0, x1, y1], start=pillow_start, end=pillow_end, fill=arc_rgb)
                    else:
                        draw.arc([x0, y0, x1, y1], start=pillow_start, end=pillow_end, fill=arc_rgb, width=component.thickness)
                else:
                    import math
                    for angle in range(int(start_angle), int(end_angle) + 1, 2):
                        rad = math.radians(angle)
                        x = int(center_x + radius * math.sin(rad))
                        y = int(center_y - radius * math.cos(rad))
                        if 0 <= x < device_size and 0 <= y < device_size:
                            buffer.draw_pixel((x, y), arc_rgb)
                
                rendered_any = True
                continue

            if isinstance(component, ArrowComponent):
                center_x = await _render_int(hass, component.center[0], vars_, "center[0]")
                center_y = await _render_int(hass, component.center[1], vars_, "center[1]")
                length = await _render_int(hass, component.length, vars_, "length")
                
                angle = component.angle
                if isinstance(angle, str):
                    from homeassistant.helpers.template import Template
                    rendered = Template(str(angle), hass).async_render(vars_, parse_result=False)
                    try:
                        angle = float(rendered)
                    except (ValueError, TypeError):
                        angle = 0.0
                else:
                    angle = float(angle)
                
                arrow_value = component.value
                if isinstance(arrow_value, str):
                    if "." in arrow_value and "{{" not in arrow_value:
                        state = hass.states.get(arrow_value)
                        if state is not None:
                            try:
                                arrow_value = float(state.state)
                            except (ValueError, TypeError):
                                arrow_value = 0.0
                        else:
                            arrow_value = 0.0
                    else:
                        from homeassistant.helpers.template import Template
                        rendered = Template(str(arrow_value), hass).async_render(vars_, parse_result=False)
                        try:
                            arrow_value = float(rendered)
                        except (ValueError, TypeError):
                            arrow_value = 0.0

                if component.color_thresholds and arrow_value is not None:
                    arrow_rgb = compute_threshold_color(
                        hass, float(arrow_value), component.color_thresholds,
                        component.color_thresholds_transition,
                        default_color=(255, 255, 255), variables=vars_
                    )
                else:
                    arrow_rgb = render_color(hass, component.color, variables=vars_)

                import math
                rad = math.radians(angle)
                end_x = int(center_x + length * math.sin(rad))
                end_y = int(center_y - length * math.cos(rad))
                
                if component.thickness == 1:
                    buffer.draw_line((center_x, center_y), (end_x, end_y), arrow_rgb)
                else:
                    dx = end_x - center_x
                    dy = end_y - center_y
                    line_length = math.sqrt(dx*dx + dy*dy)
                    if line_length > 0:
                        px = -dy / line_length
                        py = dx / line_length
                        for offset in range(-(component.thickness // 2), (component.thickness + 1) // 2):
                            offset_x = int(px * offset)
                            offset_y = int(py * offset)
                            buffer.draw_line(
                                (center_x + offset_x, center_y + offset_y),
                                (end_x + offset_x, end_y + offset_y),
                                arrow_rgb
                            )
                
                head_size = component.head_size
                head_angle1 = angle + 150
                head_angle2 = angle - 150
                rad1 = math.radians(head_angle1)
                rad2 = math.radians(head_angle2)
                
                head1_x = int(end_x + head_size * math.sin(rad1))
                head1_y = int(end_y - head_size * math.cos(rad1))
                head2_x = int(end_x + head_size * math.sin(rad2))
                head2_y = int(end_y - head_size * math.cos(rad2))
                
                buffer.draw_line((end_x, end_y), (head1_x, head1_y), arrow_rgb)
                buffer.draw_line((end_x, end_y), (head2_x, head2_y), arrow_rgb)
                buffer.draw_line((head1_x, head1_y), (head2_x, head2_y), arrow_rgb)
                
                if component.thickness > 1 and hasattr(buffer, '_image'):
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(buffer._image)
                    draw.polygon([(end_x, end_y), (head1_x, head1_y), (head2_x, head2_y)], fill=arrow_rgb)
                
                rendered_any = True
                continue

            if isinstance(component, GraphComponent):
                # For preview, render a placeholder for graph (history not available)
                comp_x = await _render_int(hass, component.x, vars_, "x")
                comp_y = await _render_int(hass, component.y, vars_, "y")
                comp_width = await _render_int(hass, component.width, vars_, "width")
                comp_height = await _render_int(hass, component.height, vars_, "height")

                # Draw a simple placeholder rectangle
                buffer.draw_filled_rectangle(
                    (comp_x, comp_y),
                    (comp_x + comp_width - 1, comp_y + comp_height - 1),
                    (40, 40, 50)
                )
                # Draw a simple line pattern to indicate graph
                mid_y = comp_y + comp_height // 2
                buffer.draw_line(
                    (comp_x, mid_y),
                    (comp_x + comp_width - 1, mid_y),
                    (80, 80, 100)
                )
                rendered_any = True
                continue

        except Exception as err:
            component_errors.append(err)
            _LOGGER.warning(
                "Page Engine preview: component %d failed: %s",
                idx, err,
            )
            continue

    if not rendered_any and not component_errors:
        _LOGGER.debug("Page Engine preview: no components rendered")