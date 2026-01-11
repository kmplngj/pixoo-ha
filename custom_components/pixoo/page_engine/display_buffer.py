"""Display buffer abstraction for device-agnostic rendering.

This module provides an abstract DisplayBuffer interface and implementations
for rendering pages without a physical device (simulator/preview).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO
import logging
from typing import Any, TYPE_CHECKING

from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from ..pixooasync import PixooAsync
    from ..pixooasync.enums import TextScrollDirection

_LOGGER = logging.getLogger(__name__)


class DisplayBuffer(ABC):
    """Abstract display buffer – device-agnostic rendering target.
    
    This interface matches the subset of PixooAsync methods used by the renderer,
    allowing the same rendering code to work with physical devices or simulators.
    """

    @property
    @abstractmethod
    def size(self) -> int:
        """Return the display size (width = height for square displays)."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear the buffer to black."""
        ...

    @abstractmethod
    def fill(self, color: tuple[int, int, int]) -> None:
        """Fill the buffer with a solid color."""
        ...

    @abstractmethod
    def draw_pixel(self, xy: tuple[int, int], color: tuple[int, int, int]) -> None:
        """Draw a single pixel."""
        ...

    @abstractmethod
    def draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        """Draw a line between two points."""
        ...

    @abstractmethod
    def draw_filled_rectangle(
        self,
        top_left: tuple[int, int],
        bottom_right: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled rectangle."""
        ...

    @abstractmethod
    def draw_text(
        self,
        text: str,
        xy: tuple[int, int],
        color: tuple[int, int, int],
        font: Any = None,
    ) -> None:
        """Draw static text at position."""
        ...

    @abstractmethod
    def draw_image(self, image: Image.Image, xy: tuple[int, int]) -> None:
        """Draw a PIL Image at position."""
        ...

    @abstractmethod
    async def push(self) -> None:
        """Send buffer content to display (no-op for simulator)."""
        ...

    @abstractmethod
    async def send_text(
        self,
        text: str,
        xy: tuple[int, int],
        color: tuple[int, int, int],
        identifier: int = 0,
        font: int = 2,
        width: int = 64,
        movement_speed: int = 50,
        direction: int = 0,
    ) -> None:
        """Send scrolling text (rendered as static for simulator)."""
        ...

    def to_image(self) -> Image.Image:
        """Export buffer as PIL Image."""
        raise NotImplementedError("Subclass must implement to_image()")

    def to_png_bytes(self) -> bytes:
        """Export buffer as PNG bytes."""
        img = self.to_image()
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()


class PillowDisplayBuffer(DisplayBuffer):
    """Pure Pillow implementation for testing and preview.
    
    This buffer renders to an in-memory PIL Image, enabling:
    - Preview rendering without a physical device
    - Unit testing without mocking device calls
    - Dashboard camera entities showing simulated output
    """

    def __init__(self, size: int = 64) -> None:
        """Initialize the Pillow buffer.
        
        Args:
            size: Display size in pixels (width = height).
        """
        self._size = size
        self._image = Image.new("RGB", (size, size), (0, 0, 0))
        self._draw = ImageDraw.Draw(self._image)

    @property
    def size(self) -> int:
        """Return the display size."""
        return self._size

    def clear(self) -> None:
        """Clear the buffer to black."""
        self._image = Image.new("RGB", (self._size, self._size), (0, 0, 0))
        self._draw = ImageDraw.Draw(self._image)

    def fill(self, color: tuple[int, int, int]) -> None:
        """Fill the buffer with a solid color."""
        self._image = Image.new("RGB", (self._size, self._size), color)
        self._draw = ImageDraw.Draw(self._image)

    def draw_pixel(self, xy: tuple[int, int], color: tuple[int, int, int]) -> None:
        """Draw a single pixel."""
        if 0 <= xy[0] < self._size and 0 <= xy[1] < self._size:
            self._image.putpixel(xy, color)

    def draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        """Draw a line between two points."""
        self._draw.line([start, end], fill=color)

    def draw_filled_rectangle(
        self,
        top_left: tuple[int, int],
        bottom_right: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled rectangle."""
        self._draw.rectangle([top_left, bottom_right], fill=color)

    def draw_text(
        self,
        text: str,
        xy: tuple[int, int],
        color: tuple[int, int, int],
        font: Any = None,
    ) -> None:
        """Draw static text at position.
        
        Uses Pillow's default bitmap font for pixel-accurate rendering.
        """
        # Use default bitmap font (similar size to Pixoo's built-in font)
        self._draw.text(xy, text, fill=color, font=font)

    def draw_image(self, image: Image.Image, xy: tuple[int, int]) -> None:
        """Draw a PIL Image at position with alpha blending."""
        if image.mode == "RGBA":
            # Composite with alpha
            self._image.paste(image, xy, mask=image.split()[3])
        else:
            self._image.paste(image, xy)

    async def push(self) -> None:
        """No-op for simulator - buffer is already "pushed"."""
        pass

    async def send_text(
        self,
        text: str,
        xy: tuple[int, int],
        color: tuple[int, int, int],
        identifier: int = 0,
        font: int = 2,
        width: int = 64,
        movement_speed: int = 50,
        direction: int = 0,
    ) -> None:
        """Render scrolling text as static (simulation doesn't scroll)."""
        # For preview, just render the text statically
        self.draw_text(text, xy, color)

    def to_image(self) -> Image.Image:
        """Export buffer as PIL Image (copy)."""
        return self._image.copy()


class PixooDisplayBuffer(DisplayBuffer):
    """Wrapper around PixooAsync that implements DisplayBuffer interface.
    
    This allows using a real Pixoo device with the same interface as PillowDisplayBuffer.
    """

    def __init__(self, pixoo: "PixooAsync") -> None:
        """Initialize with a PixooAsync client.
        
        Args:
            pixoo: PixooAsync client instance.
        """
        self._pixoo = pixoo

    @property
    def size(self) -> int:
        """Return the device display size."""
        return self._pixoo.size

    def clear(self) -> None:
        """Clear the device buffer."""
        self._pixoo.clear()

    def fill(self, color: tuple[int, int, int]) -> None:
        """Fill the device buffer with a solid color."""
        self._pixoo.fill(color)

    def draw_pixel(self, xy: tuple[int, int], color: tuple[int, int, int]) -> None:
        """Draw a single pixel on the device buffer."""
        self._pixoo.draw_pixel(xy, color)

    def draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        """Draw a line on the device buffer."""
        self._pixoo.draw_line(start, end, color)

    def draw_filled_rectangle(
        self,
        top_left: tuple[int, int],
        bottom_right: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled rectangle on the device buffer."""
        self._pixoo.draw_filled_rectangle(top_left, bottom_right, color)

    def draw_text(
        self,
        text: str,
        xy: tuple[int, int],
        color: tuple[int, int, int],
        font: Any = None,
    ) -> None:
        """Draw static text on the device buffer."""
        self._pixoo.draw_text(text, xy, color)

    def draw_image(self, image: Image.Image, xy: tuple[int, int]) -> None:
        """Draw a PIL Image on the device buffer."""
        self._pixoo.draw_image(image, xy)

    async def push(self) -> None:
        """Push the buffer to the physical device."""
        await self._pixoo.push()

    async def send_text(
        self,
        text: str,
        xy: tuple[int, int],
        color: tuple[int, int, int],
        identifier: int = 0,
        font: int = 2,
        width: int = 64,
        movement_speed: int = 50,
        direction: "TextScrollDirection | int" = 0,
    ) -> None:
        """Send scrolling text to the device."""
        from ..pixooasync.enums import TextScrollDirection
        
        # Convert int to TextScrollDirection if needed
        if isinstance(direction, int):
            direction = TextScrollDirection(direction)
        
        await self._pixoo.send_text(
            text=text,
            xy=xy,
            color=color,
            identifier=identifier,
            font=font,
            width=width,
            movement_speed=movement_speed,
            direction=direction,
        )

    def to_image(self) -> Image.Image:
        """Export current buffer as PIL Image.
        
        Note: This creates a copy of the internal buffer, not the device screen.
        """
        # PixooAsync doesn't expose buffer directly, so we can't implement this
        # without maintaining our own shadow buffer
        raise NotImplementedError(
            "PixooDisplayBuffer.to_image() not supported - use PillowDisplayBuffer for preview"
        )
