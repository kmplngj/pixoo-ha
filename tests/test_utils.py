"""Tests for Pixoo utility functions."""

import pytest

from custom_components.pixoo.utils import detect_device_size


def test_detect_device_size_pixoo_16():
    """Test device size detection for Pixoo-16."""
    assert detect_device_size("Pixoo-16") == 16
    assert detect_device_size("pixoo-16") == 16
    assert detect_device_size("Pixoo16") == 16


def test_detect_device_size_pixoo_32():
    """Test device size detection for Pixoo-32."""
    assert detect_device_size("Pixoo-32") == 32
    assert detect_device_size("Pixoo Max") == 32
    assert detect_device_size("pixoo max") == 32


def test_detect_device_size_pixoo_64():
    """Test device size detection for Pixoo-64."""
    assert detect_device_size("Pixoo-64") == 64
    assert detect_device_size("pixoo-64") == 64
    assert detect_device_size("Pixoo64") == 64


def test_detect_device_size_unknown():
    """Test device size detection for unknown models defaults to 64."""
    assert detect_device_size("Unknown Device") == 64
    assert detect_device_size("Pixoo") == 64
    assert detect_device_size("") == 64
