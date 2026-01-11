"""Tests for Pixoo Page Engine display buffer and preview."""

from __future__ import annotations

import pytest

from custom_components.pixoo.page_engine.display_buffer import (
    DisplayBuffer,
    PillowDisplayBuffer,
)


class TestPillowDisplayBuffer:
    """Tests for PillowDisplayBuffer."""

    def test_create_buffer(self):
        """Test creating a buffer with default size."""
        buffer = PillowDisplayBuffer(size=64)
        assert buffer.size == 64

    def test_create_buffer_custom_size(self):
        """Test creating a buffer with custom size."""
        buffer = PillowDisplayBuffer(size=32)
        assert buffer.size == 32

    def test_clear_buffer(self):
        """Test clearing the buffer."""
        buffer = PillowDisplayBuffer(size=64)
        buffer.fill((255, 0, 0))  # Fill with red
        buffer.clear()  # Clear to black
        
        img = buffer.to_image()
        # Check center pixel is black
        assert img.getpixel((32, 32)) == (0, 0, 0)

    def test_fill_buffer(self):
        """Test filling the buffer with a color."""
        buffer = PillowDisplayBuffer(size=64)
        buffer.fill((0, 255, 0))  # Fill with green
        
        img = buffer.to_image()
        # Check center pixel is green
        assert img.getpixel((32, 32)) == (0, 255, 0)

    def test_draw_pixel(self):
        """Test drawing a single pixel."""
        buffer = PillowDisplayBuffer(size=64)
        buffer.draw_pixel((10, 10), (255, 0, 0))
        
        img = buffer.to_image()
        assert img.getpixel((10, 10)) == (255, 0, 0)

    def test_draw_line(self):
        """Test drawing a line."""
        buffer = PillowDisplayBuffer(size=64)
        buffer.draw_line((0, 0), (63, 63), (255, 255, 255))
        
        img = buffer.to_image()
        # Diagonal line should have white pixels
        assert img.getpixel((0, 0)) == (255, 255, 255)
        assert img.getpixel((32, 32)) == (255, 255, 255)
        assert img.getpixel((63, 63)) == (255, 255, 255)

    def test_draw_filled_rectangle(self):
        """Test drawing a filled rectangle."""
        buffer = PillowDisplayBuffer(size=64)
        buffer.draw_filled_rectangle((10, 10), (20, 20), (0, 0, 255))
        
        img = buffer.to_image()
        # Inside rectangle should be blue
        assert img.getpixel((15, 15)) == (0, 0, 255)
        # Outside rectangle should be black
        assert img.getpixel((5, 5)) == (0, 0, 0)

    def test_draw_text(self):
        """Test drawing text."""
        buffer = PillowDisplayBuffer(size=64)
        buffer.draw_text("Hi", (10, 10), (255, 255, 255))
        
        # Text was drawn - check image is not all black
        img = buffer.to_image()
        has_white = any(
            img.getpixel((x, y)) != (0, 0, 0)
            for x in range(64) for y in range(64)
        )
        assert has_white

    def test_to_png_bytes(self):
        """Test exporting buffer as PNG bytes."""
        buffer = PillowDisplayBuffer(size=64)
        buffer.fill((128, 128, 128))
        
        png_bytes = buffer.to_png_bytes()
        
        # PNG magic bytes
        assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        assert len(png_bytes) > 100  # Some reasonable size

    def test_to_image_returns_copy(self):
        """Test that to_image returns a copy."""
        buffer = PillowDisplayBuffer(size=64)
        buffer.fill((255, 0, 0))
        
        img1 = buffer.to_image()
        buffer.fill((0, 255, 0))
        img2 = buffer.to_image()
        
        # img1 should still be red
        assert img1.getpixel((32, 32)) == (255, 0, 0)
        # img2 should be green
        assert img2.getpixel((32, 32)) == (0, 255, 0)

    @pytest.mark.asyncio
    async def test_push_is_noop(self):
        """Test that push does nothing for simulator."""
        buffer = PillowDisplayBuffer(size=64)
        # Should not raise
        await buffer.push()

    @pytest.mark.asyncio
    async def test_send_text_renders_static(self):
        """Test that send_text renders text statically."""
        buffer = PillowDisplayBuffer(size=64)
        await buffer.send_text(
            text="Test",
            xy=(10, 10),
            color=(255, 255, 255),
        )
        
        # Text was drawn - check image is not all black
        img = buffer.to_image()
        has_white = any(
            img.getpixel((x, y)) != (0, 0, 0)
            for x in range(64) for y in range(64)
        )
        assert has_white

    def test_draw_image_rgb(self):
        """Test drawing an RGB image."""
        from PIL import Image
        
        buffer = PillowDisplayBuffer(size=64)
        
        # Create a small red image
        red_img = Image.new("RGB", (10, 10), (255, 0, 0))
        buffer.draw_image(red_img, (20, 20))
        
        img = buffer.to_image()
        # Check the drawn image area
        assert img.getpixel((25, 25)) == (255, 0, 0)
        # Outside should be black
        assert img.getpixel((5, 5)) == (0, 0, 0)

    def test_draw_image_rgba_with_alpha(self):
        """Test drawing an RGBA image with transparency."""
        from PIL import Image
        
        buffer = PillowDisplayBuffer(size=64)
        buffer.fill((0, 0, 255))  # Blue background
        
        # Create a semi-transparent red image
        red_img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
        buffer.draw_image(red_img, (20, 20))
        
        img = buffer.to_image()
        # The result should be a blend of red and blue
        pixel = img.getpixel((25, 25))
        # Should have some red component
        assert pixel[0] > 0
