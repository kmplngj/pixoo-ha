"""Tests for Arc and Arrow components."""

import pytest
from custom_components.pixoo.page_engine.models import ArcComponent, ArrowComponent


def test_arc_simple():
    """Test simple arc component."""
    arc = ArcComponent(
        center=[32, 32],
        radius=20,
        start_angle=0,
        end_angle=90,
        color="#00FF00",
    )
    assert arc.center == [32, 32]
    assert arc.radius == 20
    assert arc.start_angle == 0
    assert arc.end_angle == 90
    assert arc.color == "#00FF00"
    assert arc.filled is False  # Default
    assert arc.thickness == 2  # Default


def test_arc_filled():
    """Test filled arc (pie slice) component."""
    arc = ArcComponent(
        center=[32, 32],
        radius=15,
        start_angle=0,
        end_angle=180,
        color="#FF0000",
        filled=True,
    )
    assert arc.filled is True


def test_arc_template_angles():
    """Test arc with template angles."""
    arc = ArcComponent(
        center=[32, 32],
        radius=20,
        start_angle="{{ 0 }}",
        end_angle="{{ battery_level * 3.6 }}",  # 0-100% -> 0-360°
        color="#00FF00",
    )
    assert arc.start_angle == "{{ 0 }}"
    assert arc.end_angle == "{{ battery_level * 3.6 }}"


def test_arc_color_thresholds():
    """Test arc with color thresholds."""
    from custom_components.pixoo.page_engine.models import ColorThreshold
    
    arc = ArcComponent(
        center=[32, 32],
        radius=18,
        start_angle=0,
        end_angle=270,
        value="sensor.battery",
        color_thresholds=[
            ColorThreshold(value=20, color="#FF0000"),
            ColorThreshold(value=50, color="#FFAA00"),
            ColorThreshold(value=100, color="#00FF00"),
        ],
    )
    assert len(arc.color_thresholds) == 3
    assert arc.value == "sensor.battery"


def test_arrow_simple():
    """Test simple arrow component."""
    arrow = ArrowComponent(
        x=0,
        y=0,
        center=[32, 32],
        length=20,
        angle=0,  # North
        color="#FFFFFF",
    )
    assert arrow.center == [32, 32]
    assert arrow.length == 20
    assert arrow.angle == 0
    assert arrow.color == "#FFFFFF"
    assert arrow.thickness == 2  # Default
    assert arrow.head_size == 4  # Default


def test_arrow_cardinal_directions():
    """Test arrow pointing in all cardinal directions."""
    # North (0°)
    north = ArrowComponent(x=0, y=0, center=[32, 32], length=15, angle=0)
    assert north.angle == 0
    
    # East (90°)
    east = ArrowComponent(x=0, y=0, center=[32, 32], length=15, angle=90)
    assert east.angle == 90
    
    # South (180°)
    south = ArrowComponent(x=0, y=0, center=[32, 32], length=15, angle=180)
    assert south.angle == 180
    
    # West (270°)
    west = ArrowComponent(x=0, y=0, center=[32, 32], length=15, angle=270)
    assert west.angle == 270


def test_arrow_template_angle():
    """Test arrow with template angle (wind direction)."""
    arrow = ArrowComponent(
        x=0,
        y=0,
        center=[32, 32],
        length=20,
        angle="{{ state_attr('weather.home', 'wind_bearing') }}",
        color="#00AAFF",
    )
    assert arrow.angle == "{{ state_attr('weather.home', 'wind_bearing') }}"


def test_arrow_color_thresholds():
    """Test arrow with color thresholds (wind speed)."""
    from custom_components.pixoo.page_engine.models import ColorThreshold
    
    arrow = ArrowComponent(
        x=0,
        y=0,
        center=[32, 32],
        length=18,
        angle=45,
        value="sensor.wind_speed",
        color_thresholds=[
            ColorThreshold(value=10, color="#00FF00"),
            ColorThreshold(value=20, color="#FFAA00"),
            ColorThreshold(value=30, color="#FF0000"),
        ],
    )
    assert len(arrow.color_thresholds) == 3
    assert arrow.value == "sensor.wind_speed"


def test_arc_arrow_combined():
    """Test combining arc and arrow in a gauge."""
    # Arc for background/range indicator
    arc = ArcComponent(
        x=0,
        y=0,
        center=[32, 32],
        radius=22,
        start_angle=180,
        end_angle=360,
        color="#333333",
        thickness=3,
    )
    
    # Arrow for current value pointer
    arrow = ArrowComponent(
        x=0,
        y=0,
        center=[32, 32],
        length=20,
        angle="{{ 180 + (value / 100 * 180) }}",  # Map 0-100 to 180-360°
        color="#FF0000",
        thickness=2,
    )
    
    assert arc.center == arrow.center
    assert arc.radius > arrow.length
