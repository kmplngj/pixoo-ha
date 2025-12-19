"""Simulator for testing Pixoo displays without hardware."""

import tkinter
from typing import TYPE_CHECKING, Protocol

from PIL import Image, ImageDraw, ImageTk

from .models import SimulatorConfig
from .palette import Palette

if TYPE_CHECKING:
    class PixooProtocol(Protocol):
        """Protocol for Pixoo-like objects."""
        size: int


class Simulator:
    """GUI simulator for Pixoo display.
    
    Can run in headless mode (no GUI) for testing environments without display.
    """

    def __init__(self, pixoo: "PixooProtocol", config: SimulatorConfig) -> None:
        """Initialize the simulator.

        Args:
            pixoo: Parent Pixoo instance
            config: Simulator configuration
        """
        self._config = config
        self._screen_size = (pixoo.size, pixoo.size)
        scale = self._config.scale
        self._image_size = (pixoo.size * scale, pixoo.size * scale)

        # Initialize GUI components only if not headless
        if not self._config.headless:
            # Setup tkinter window
            self._root = tkinter.Tk()
            self._root.title("Pixoo Simulator")
            self._root.geometry(f"{self._image_size[0]}x{self._image_size[1]}")
            self._root.attributes("-topmost", True)

            self._canvas = tkinter.Canvas(self._root, height=self._image_size[1], width=self._image_size[0])
            self._canvas.pack()

            # Create loading screen
            image = Image.new("RGB", self._screen_size, color="red")
            draw = ImageDraw.Draw(image)
            x, y = 12, 14
            draw.text((x, y), "waiting", fill=Palette.WHITE)
            draw.text((x + 11, y + 12), "for", fill=Palette.WHITE)
            draw.text((x + 2, y + 24), "buffer", fill=Palette.WHITE)

            # Scale and display
            prepared_image = self._prepare_image(image)
            self._image_container = self._canvas.create_image(
                self._image_size[0] / 2,
                self._image_size[1] / 2,
                image=prepared_image,
            )
            self._root.update()
        else:
            # Headless mode - no GUI components
            self._root = None
            self._canvas = None
            self._image_container = None

    def display(self, buffer: list[int], counter: int) -> None:
        """Display a buffer on the simulator.

        Args:
            buffer: RGB buffer to display
            counter: Frame counter (currently unused)
        """
        # In headless mode, just validate buffer but don't display
        if self._config.headless:
            return

        # Convert buffer to image
        image = Image.frombytes("RGB", self._screen_size, bytes(buffer), "raw")

        # Scale and update
        prepared_image = self._prepare_image(image)
        if self._canvas and self._image_container and self._root:
            self._canvas.itemconfig(self._image_container, image=prepared_image)
            self._root.update()

    def _prepare_image(self, image: Image.Image) -> ImageTk.PhotoImage:
        """Prepare an image for display in tkinter.

        Args:
            image: PIL Image to prepare

        Returns:
            PhotoImage ready for tkinter
        """
        scaled = image.resize(self._image_size, Image.Resampling.NEAREST)
        return ImageTk.PhotoImage(scaled)
