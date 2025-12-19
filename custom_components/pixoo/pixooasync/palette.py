"""Color palette for pixooasync."""

from typing import Final

# Type alias for RGB colors
RGBColor = tuple[int, int, int]

COLOR_BLACK: Final[RGBColor] = (0, 0, 0)
COLOR_WHITE: Final[RGBColor] = (255, 255, 255)


class Palette:
    """Common color palette for Pixoo displays."""

    BLACK: Final[RGBColor] = COLOR_BLACK
    WHITE: Final[RGBColor] = COLOR_WHITE
