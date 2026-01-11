"""Models for Pixoo Page Engine.

These models are validated via Pydantic (v2) and primarily used by service
handlers to validate user-provided page definitions.
"""

from __future__ import annotations

from typing import Any, Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class BaseComponent(BaseModel):
    """Common component fields."""

    model_config = ConfigDict(extra="forbid")

    type: str
    x: int | str  # Supports templates like {{ x }}
    y: int | str  # Supports templates like {{ y }}
    z: int | str | None = None  # Supports templates like {{ z }}
    enabled: bool | str | None = None  # Template-based conditional visibility


class TextComponent(BaseComponent):
    type: Literal["text"] = "text"
    text: str
    color: Any | None = None
    align: Literal["left", "center", "right"] = "left"
    font: str | None = None
    # Scrolling text options
    scroll: bool = False  # Enable scrolling for long text
    scroll_speed: int = 50  # Scroll speed (0-100, higher = faster)
    scroll_direction: Literal["left", "right"] = "left"  # Scroll direction
    text_width: int | None = None  # Width in pixels for scrolling text (default: device_size)


class RectangleComponent(BaseComponent):
    type: Literal["rectangle"] = "rectangle"
    width: int | str  # Supports templates like {{ width }}
    height: int | str  # Supports templates like {{ height }}
    color: Any | None = None
    filled: bool = True


class ImageSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str | None = None
    path: str | None = None
    base64: str | None = None

    @property
    def kind(self) -> str:
        if self.url is not None:
            return "url"
        if self.path is not None:
            return "path"
        if self.base64 is not None:
            return "base64"
        return "none"


class ImageComponent(BaseComponent):
    type: Literal["image"] = "image"
    source: ImageSource
    resize_mode: Literal["fit", "fill", "none"] = "fit"


class ColorThreshold(BaseModel):
    """Color threshold for dynamic coloring based on value."""

    model_config = ConfigDict(extra="forbid")

    value: float
    color: Any  # Hex string, RGB list, or color name


class ProgressBarComponent(BaseComponent):
    """Progress bar component with threshold-based coloring."""

    type: Literal["progress_bar"] = "progress_bar"
    width: int | str  # Supports templates like {{ width }}
    height: int | str = 6  # Supports templates like {{ height }}
    # Progress value: float (0-100), entity_id, or template
    progress: float | str
    min_value: float = 0
    max_value: float = 100
    # Colors
    bar_color: Any | None = None  # Default: green
    background_color: Any | None = None  # Default: dark gray
    border_color: Any | None = None  # Default: none (no border)
    show_border: bool = False
    # Threshold-based dynamic coloring (like mini-graph-card)
    color_thresholds: list[ColorThreshold] | None = None
    color_thresholds_transition: Literal["smooth", "hard"] = "smooth"
    # Orientation
    orientation: Literal["horizontal", "vertical"] = "horizontal"


class GraphComponent(BaseComponent):
    """Graph component displaying entity history with threshold-based coloring."""

    type: Literal["graph"] = "graph"
    width: int | str  # Supports templates like {{ width }}
    height: int | str  # Supports templates like {{ height }}
    # Data source: entity_id (fetches history)
    entity_id: str
    hours: float = 24  # Hours of history to show
    points: int | None = None  # Auto-calculated from width if None
    aggregate_func: Literal["avg", "min", "max", "last"] = "avg"
    # Style
    style: Literal["line", "bar", "area"] = "line"
    line_color: Any | None = None  # Default: accent color
    fill_color: Any | None = None  # For area style
    background_color: Any | None = None
    show_fill: bool = False  # Fill under line
    # Threshold-based dynamic coloring
    color_thresholds: list[ColorThreshold] | None = None
    color_thresholds_transition: Literal["smooth", "hard"] = "smooth"
    # Y-axis bounds (auto if None)
    min_value: float | None = None
    max_value: float | None = None


class IconComponent(BaseComponent):
    """MDI icon component with dynamic color and size."""

    type: Literal["icon"] = "icon"
    icon: str  # MDI icon name, e.g., "mdi:battery" or just "battery"
    size: int = Field(default=16, ge=1, le=64, description="Icon size in pixels")
    color: Any | None = None  # Default: white
    # Threshold-based dynamic coloring
    color_thresholds: list[ColorThreshold] | None = None
    color_thresholds_transition: Literal["smooth", "hard"] = "smooth"
    # Value source for threshold coloring (entity_id or template)
    value: float | str | None = None


class LineComponent(BaseComponent):
    """Line component for dividers, decorations, and simple diagrams."""

    type: Literal["line"] = "line"
    x: int | str = 0  # Not used for lines, but required by BaseComponent
    y: int | str = 0  # Not used for lines, but required by BaseComponent
    start: tuple[int, int] | list[int]  # [x, y] start coordinates
    end: tuple[int, int] | list[int]  # [x, y] end coordinates
    color: Any = "#FFFFFF"  # Line color
    thickness: int = Field(default=1, ge=1, le=10, description="Line thickness in pixels")
    # Threshold-based dynamic coloring
    color_thresholds: list[ColorThreshold] | None = None
    color_thresholds_transition: Literal["smooth", "hard"] = "smooth"
    # Value source for threshold coloring (entity_id or template)
    value: float | str | None = None


class CircleComponent(BaseComponent):
    """Circle/ellipse component for gauges, indicators, and decorations."""

    type: Literal["circle"] = "circle"
    x: int | str = 0  # Not used for circles, but required by BaseComponent
    y: int | str = 0  # Not used for circles, but required by BaseComponent
    center: list[int | str]  # [x, y] center coordinates (supports templates)
    radius: int | str  # Radius (or [radius_x, radius_y] for ellipse - future)
    color: Any = "#FFFFFF"  # Circle color
    filled: bool = True  # Whether to fill or draw outline only
    thickness: int = Field(default=1, ge=1, le=10, description="Border thickness (when filled=false)")
    # Threshold-based dynamic coloring
    color_thresholds: list[ColorThreshold] | None = None
    color_thresholds_transition: Literal["smooth", "hard"] = "smooth"
    # Value source for threshold coloring (entity_id or template)
    value: float | str | None = None


class ArcComponent(BaseComponent):
    """Arc/pie slice component for progress rings, gauges, and circular indicators."""

    type: Literal["arc"] = "arc"
    x: int | str = 0  # Not used for arcs, but required by BaseComponent
    y: int | str = 0  # Not used for arcs, but required by BaseComponent
    center: list[int | str]  # [x, y] center coordinates (supports templates)
    radius: int | str  # Radius of the arc
    start_angle: float | str = 0  # Start angle in degrees (0 = top, clockwise)
    end_angle: float | str = 90  # End angle in degrees
    color: Any = "#FFFFFF"  # Arc color
    filled: bool = False  # Whether to draw pie slice (filled) or arc (outline)
    thickness: int = Field(default=2, ge=1, le=10, description="Arc thickness in pixels")
    # Threshold-based dynamic coloring
    color_thresholds: list[ColorThreshold] | None = None
    color_thresholds_transition: Literal["smooth", "hard"] = "smooth"
    # Value source for threshold coloring (entity_id or template)
    value: float | str | None = None


class ArrowComponent(BaseComponent):
    """Arrow component for compass, wind direction, navigation indicators."""

    type: Literal["arrow"] = "arrow"
    x: int | str = 0  # Not used for arrows, but required by BaseComponent
    y: int | str = 0  # Not used for arrows, but required by BaseComponent
    center: list[int | str]  # [x, y] center/base point of arrow (supports templates)
    length: int | str  # Length of arrow in pixels
    angle: float | str = 0  # Direction in degrees (0 = up/north, clockwise)
    color: Any = "#FFFFFF"  # Arrow color
    thickness: int = Field(default=2, ge=1, le=10, description="Arrow line thickness")
    head_size: int = Field(default=4, ge=2, le=10, description="Arrow head size in pixels")
    # Threshold-based dynamic coloring
    color_thresholds: list[ColorThreshold] | None = None
    color_thresholds_transition: Literal["smooth", "hard"] = "smooth"
    # Value source for threshold coloring (entity_id or template)
    value: float | str | None = None


ComponentModel = Annotated[
    Union[
        TextComponent,
        RectangleComponent,
        ImageComponent,
        ProgressBarComponent,
        GraphComponent,
        IconComponent,
        LineComponent,
        CircleComponent,
        ArcComponent,
        ArrowComponent,
    ],
    Field(discriminator="type"),
]


class BasePage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_type: str
    name: str | None = None  # Optional name for referencing the page
    duration: int | None = None
    enabled: bool | str | None = None
    variables: dict[str, Any] | None = None


class ComponentsPage(BasePage):
    page_type: Literal["components"] = "components"
    components: list[ComponentModel]
    background: Any | None = None


class TemplatePage(BasePage):
    page_type: Literal["template"] = "template"
    template_name: str
    template_vars: dict[str, Any] = Field(default_factory=dict)


class ChannelPage(BasePage):
    """Page type that switches to a native Pixoo channel instead of rendering components."""

    page_type: Literal["channel"] = "channel"
    channel_name: Literal["clock", "cloud", "visualizer", "custom"]
    # Optional: specific clock/visualizer/custom page ID
    clock_id: int | None = None
    visualizer_id: int | None = None
    custom_page_id: int | None = None


Page = Annotated[Union[ComponentsPage, TemplatePage, ChannelPage], Field(discriminator="page_type")]


_PAGE_ADAPTER: TypeAdapter[Page] = TypeAdapter(Page)


class PageModel:
    """Validation helper for page payloads.

    Using a helper keeps call sites nice (`PageModel.model_validate(...)`) while
    still returning the actual discriminated page instance.
    """

    @classmethod
    def model_validate(cls, obj: Any) -> Page:
        return _PAGE_ADAPTER.validate_python(obj)
