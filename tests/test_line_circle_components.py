"""Tests for LineComponent and CircleComponent rendering."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.pixoo.page_engine.models import (
    ComponentsPage,
    LineComponent,
    CircleComponent,
    ColorThreshold,
)
from custom_components.pixoo.page_engine.renderer import render_page_to_buffer
from custom_components.pixoo.page_engine.display_buffer import PillowDisplayBuffer


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    return hass


@pytest.mark.asyncio
async def test_line_component_simple(mock_hass):
    """Test simple line rendering."""
    page = ComponentsPage(
        page_type="components",
        background="#000000",
        components=[
            LineComponent(
                type="line",
                start=[10, 10],
                end=[50, 50],
                color="#FFFFFF",
                thickness=1,
            )
        ],
    )
    
    buffer = PillowDisplayBuffer(size=64)
    
    await render_page_to_buffer(
        hass=mock_hass,
        buffer=buffer,
        page=page.model_dump(),
        device_size=64,
        variables={},
        allowlist_mode="permissive",
        entry_id=None,
    )
    
    # Verify line was drawn (check a few pixels along the line)
    img = buffer.to_image()
    # Diagonal line should have white pixels along it
    pixel = img.getpixel((10, 10))
    assert pixel == (255, 255, 255), f"Expected white pixel at (10,10), got {pixel}"


@pytest.mark.asyncio
async def test_line_component_with_thickness(mock_hass):
    """Test line rendering with thickness > 1."""
    page = ComponentsPage(
        page_type="components",
        background="#000000",
        components=[
            LineComponent(
                type="line",
                start=[20, 32],
                end=[44, 32],
                color="#FF0000",
                thickness=3,
            )
        ],
    )
    
    buffer = PillowDisplayBuffer(size=64)
    
    await render_page_to_buffer(
        hass=mock_hass,
        buffer=buffer,
        page=page.model_dump(),
        device_size=64,
        variables={},
        allowlist_mode="permissive",
        entry_id=None,
    )
    
    img = buffer.to_image()
    # Check that pixels near the line are red
    pixel = img.getpixel((32, 32))
    assert pixel == (255, 0, 0), f"Expected red pixel at (32,32), got {pixel}"


@pytest.mark.asyncio
async def test_line_component_with_color_thresholds(mock_hass):
    """Test line with color thresholds based on entity value."""
    # Mock entity state
    mock_state = MagicMock()
    mock_state.state = "75"
    mock_hass.states.get.return_value = mock_state
    
    page = ComponentsPage(
        page_type="components",
        background="#000000",
        components=[
            LineComponent(
                type="line",
                start=[10, 10],
                end=[50, 10],
                color="#FFFFFF",
                thickness=1,
                value="sensor.test",
                color_thresholds=[
                    ColorThreshold(value=0, color="#FF0000"),
                    ColorThreshold(value=50, color="#FFFF00"),
                    ColorThreshold(value=100, color="#00FF00"),
                ],
            )
        ],
    )
    
    buffer = PillowDisplayBuffer(size=64)
    
    await render_page_to_buffer(
        hass=mock_hass,
        buffer=buffer,
        page=page.model_dump(),
        device_size=64,
        variables={},
        allowlist_mode="permissive",
        entry_id=None,
    )
    
    img = buffer.to_image()
    pixel = img.getpixel((30, 10))
    # Should be yellow-green (between 50 and 100)
    assert pixel[1] > 200, f"Expected greenish pixel for value 75, got {pixel}"


@pytest.mark.asyncio
async def test_circle_component_filled(mock_hass):
    """Test filled circle rendering."""
    page = ComponentsPage(
        page_type="components",
        background="#000000",
        components=[
            CircleComponent(
                type="circle",
                center=[32, 32],
                radius=10,
                color="#00FF00",
                filled=True,
            )
        ],
    )
    
    buffer = PillowDisplayBuffer(size=64)
    
    await render_page_to_buffer(
        hass=mock_hass,
        buffer=buffer,
        page=page.model_dump(),
        device_size=64,
        variables={},
        allowlist_mode="permissive",
        entry_id=None,
    )
    
    img = buffer.to_image()
    # Check center pixel is green
    pixel = img.getpixel((32, 32))
    assert pixel == (0, 255, 0), f"Expected green pixel at center, got {pixel}"
    
    # Check edge pixel is green
    pixel_edge = img.getpixel((32, 27))  # Should be inside circle
    assert pixel_edge == (0, 255, 0), f"Expected green pixel at edge, got {pixel_edge}"


@pytest.mark.asyncio
async def test_circle_component_outline(mock_hass):
    """Test circle outline rendering."""
    page = ComponentsPage(
        page_type="components",
        background="#000000",
        components=[
            CircleComponent(
                type="circle",
                center=[32, 32],
                radius=15,
                color="#0000FF",
                filled=False,
                thickness=2,
            )
        ],
    )
    
    buffer = PillowDisplayBuffer(size=64)
    
    await render_page_to_buffer(
        hass=mock_hass,
        buffer=buffer,
        page=page.model_dump(),
        device_size=64,
        variables={},
        allowlist_mode="permissive",
        entry_id=None,
    )
    
    img = buffer.to_image()
    # Center should be black (not filled)
    pixel_center = img.getpixel((32, 32))
    assert pixel_center == (0, 0, 0), f"Expected black center, got {pixel_center}"
    
    # Edge should have blue outline
    pixel_edge = img.getpixel((32, 17))  # Top of circle
    assert pixel_edge[2] > 200, f"Expected blue outline, got {pixel_edge}"


@pytest.mark.asyncio
async def test_circle_component_with_template_radius(hass):
    """Test circle with templated radius."""
    page = ComponentsPage(
        page_type="components",
        background="#000000",
        components=[
            CircleComponent(
                type="circle",
                center=[32, 32],
                radius="{{ radius_var }}",
                color="#FF00FF",
                filled=True,
            )
        ],
    )
    
    buffer = PillowDisplayBuffer(size=64)
    
    await render_page_to_buffer(
        hass=hass,
        buffer=buffer,
        page=page.model_dump(),
        device_size=64,
        variables={"radius_var": 8},
        allowlist_mode="permissive",
        entry_id=None,
    )
    
    img = buffer.to_image()
    pixel = img.getpixel((32, 32))
    assert pixel == (255, 0, 255), f"Expected magenta center, got {pixel}"


@pytest.mark.asyncio
async def test_circle_component_with_color_thresholds(mock_hass):
    """Test circle with color thresholds."""
    mock_state = MagicMock()
    mock_state.state = "30"
    mock_hass.states.get.return_value = mock_state
    
    page = ComponentsPage(
        page_type="components",
        background="#000000",
        components=[
            CircleComponent(
                type="circle",
                center=[32, 32],
                radius=12,
                color="#FFFFFF",
                filled=True,
                value="sensor.temperature",
                color_thresholds=[
                    ColorThreshold(value=0, color="#0000FF"),
                    ColorThreshold(value=20, color="#00FF00"),
                    ColorThreshold(value=30, color="#FF0000"),
                ],
            )
        ],
    )
    
    buffer = PillowDisplayBuffer(size=64)
    
    await render_page_to_buffer(
        hass=mock_hass,
        buffer=buffer,
        page=page.model_dump(),
        device_size=64,
        variables={},
        allowlist_mode="permissive",
        entry_id=None,
    )
    
    img = buffer.to_image()
    pixel = img.getpixel((32, 32))
    # Should be red (value 30)
    assert pixel[0] > 200, f"Expected reddish pixel for value 30, got {pixel}"


@pytest.mark.asyncio
async def test_line_and_circle_combined(mock_hass):
    """Test page with both line and circle components."""
    page = ComponentsPage(
        page_type="components",
        background="#000000",
        components=[
            LineComponent(
                type="line",
                start=[0, 32],
                end=[64, 32],
                color="#FFFFFF",
                thickness=1,
            ),
            CircleComponent(
                type="circle",
                center=[32, 32],
                radius=10,
                color="#FF0000",
                filled=True,
            ),
        ],
    )
    
    buffer = PillowDisplayBuffer(size=64)
    
    await render_page_to_buffer(
        hass=mock_hass,
        buffer=buffer,
        page=page.model_dump(),
        device_size=64,
        variables={},
        allowlist_mode="permissive",
        entry_id=None,
    )
    
    img = buffer.to_image()
    # Circle center should be red
    pixel_center = img.getpixel((32, 32))
    assert pixel_center == (255, 0, 0), f"Expected red center, got {pixel_center}"
    
    # Line far from circle should be white
    pixel_line = img.getpixel((10, 32))
    assert pixel_line == (255, 255, 255), f"Expected white line, got {pixel_line}"
