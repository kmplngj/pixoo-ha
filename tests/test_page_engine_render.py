"""Tests for Pixoo Page Engine templating/render helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.exceptions import TemplateError
from homeassistant.exceptions import ServiceValidationError


async def test_render_complex_renders_templates(hass) -> None:
	from custom_components.pixoo.page_engine.templating import async_render_complex

	data = {
		"text": "{{ 'hi' }}",
		"nested": {"n": "{{ 1 + 1 }}"},
		"plain": "ok",
	}

	rendered = await async_render_complex(hass, data, variables={})

	assert rendered["text"] == "hi"
	assert rendered["nested"]["n"] == "2"
	assert rendered["plain"] == "ok"


async def test_render_complex_propagates_template_error(hass) -> None:
	from custom_components.pixoo.page_engine.templating import async_render_complex

	with pytest.raises(TemplateError):
		await async_render_complex(hass, {"x": "{{ states('sensor.does_not_exist').nope }}"}, variables={})


async def test_render_color_from_template(hass) -> None:
	from custom_components.pixoo.page_engine.colors import render_color

	assert render_color(hass, "{{ '#00FF00' }}", variables={}) == (0, 255, 0)


async def test_render_color_template_error_is_strict(hass) -> None:
	from custom_components.pixoo.page_engine.colors import render_color

	with pytest.raises(TemplateError):
		render_color(hass, "{{ states('sensor.does_not_exist').nope }}", variables={})


def test_component_in_bounds_rectangle() -> None:
	from custom_components.pixoo.page_engine.models import PageModel
	from custom_components.pixoo.page_engine.models import ComponentsPage
	from custom_components.pixoo.page_engine.renderer import component_in_bounds

	page = PageModel.model_validate(
		{
			"page_type": "components",
			"components": [
				{"type": "rectangle", "x": 62, "y": 0, "width": 2, "height": 1},
			],
		}
	)

	assert isinstance(page, ComponentsPage)
	assert component_in_bounds(page.components[0], device_size=64) is True

	page_oob = PageModel.model_validate(
		{
			"page_type": "components",
			"components": [
				{"type": "rectangle", "x": 63, "y": 0, "width": 2, "height": 1},
			],
		}
	)
	assert isinstance(page_oob, ComponentsPage)
	assert component_in_bounds(page_oob.components[0], device_size=64) is False


async def test_image_source_allowlist_strict_blocks(hass) -> None:
	from custom_components.pixoo.page_engine.models import ImageSource
	from custom_components.pixoo.page_engine.renderer import (
		ALLOWLIST_MODE_STRICT,
		async_resolve_image_source,
	)

	hass.config.is_allowed_external_url = lambda _url: False  # type: ignore[method-assign]

	with pytest.raises(ServiceValidationError):
		await async_resolve_image_source(
			hass,
			ImageSource(url="https://example.com/x.png"),
			device_size=64,
			allowlist_mode=ALLOWLIST_MODE_STRICT,
		)


async def test_image_source_allowlist_permissive_allows(monkeypatch, hass) -> None:
	from custom_components.pixoo.page_engine.models import ImageSource
	from custom_components.pixoo.page_engine.renderer import (
		ALLOWLIST_MODE_PERMISSIVE,
		async_resolve_image_source,
	)

	# Even if not allowlisted, permissive should proceed.
	hass.config.is_allowed_external_url = lambda _url: False  # type: ignore[method-assign]

	# Minimal valid 1x1 PNG
	png_1x1 = (
		b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
		b"\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
	)

	async def _fake_download_image(_hass, _url, target_size=(64, 64)) -> bytes:  # noqa: ARG001
		return png_1x1

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.renderer.download_image",
		_fake_download_image,
	)

	img = await async_resolve_image_source(
		hass,
		ImageSource(url="https://example.com/x.png"),
		device_size=64,
		allowlist_mode=ALLOWLIST_MODE_PERMISSIVE,
	)
	assert img.size == (1, 1)


async def test_render_page_text_draws_and_pushes(hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{"type": "text", "x": 1, "y": 2, "text": "HI"},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	pixoo.clear.assert_called_once()
	pixoo.draw_text.assert_called_once_with("HI", (1, 2), (255, 255, 255))
	pixoo.push.assert_awaited_once()


async def test_render_page_rectangle_draws_filled_rectangle(hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{"type": "rectangle", "x": 10, "y": 5, "width": 2, "height": 3, "filled": True},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	# bottom_right is inclusive
	pixoo.draw_filled_rectangle.assert_called_once_with((10, 5), (11, 7), (255, 255, 255))
	pixoo.push.assert_awaited_once()


async def test_render_page_image_draws_image(monkeypatch, hass) -> None:
	from PIL import Image
	from custom_components.pixoo.page_engine.renderer import render_page

	dummy = Image.new("RGB", (1, 1), (1, 2, 3))

	async def _fake_resolve(*_args, **_kwargs):
		return dummy

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.renderer.async_resolve_image_source",
		_fake_resolve,
	)

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{"type": "image", "x": 3, "y": 4, "source": {"url": "https://example.com/x.png"}},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	assert pixoo.draw_image.call_count == 1
	args, kwargs = pixoo.draw_image.call_args
	assert args[0] is dummy
	assert kwargs["xy"] == (3, 4)
	pixoo.push.assert_awaited_once()


async def test_render_page_component_failure_is_best_effort(caplog, hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			# Invalid color type -> render_color raises ValueError
			{"type": "rectangle", "x": 0, "y": 0, "width": 2, "height": 2, "color": {"bad": 1}},
			{"type": "text", "x": 1, "y": 2, "text": "OK"},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	assert pixoo.draw_text.call_count == 1
	assert "component 0" in caplog.text
	pixoo.push.assert_awaited_once()


async def test_render_page_out_of_bounds_skips_and_continues(caplog, hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{"type": "rectangle", "x": 63, "y": 0, "width": 2, "height": 1},
			{"type": "text", "x": 0, "y": 0, "text": "OK"},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	assert "out of bounds" in caplog.text
	assert pixoo.draw_text.call_count == 1
	pixoo.push.assert_awaited_once()


async def test_render_page_errors_if_nothing_rendered(hass) -> None:
	from custom_components.pixoo.page_engine import PageEngineValidationError
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{"type": "rectangle", "x": 63, "y": 0, "width": 2, "height": 1},
		],
	}

	with pytest.raises(PageEngineValidationError):
		await render_page(hass, pixoo, page, device_size=64, variables={})


async def test_template_page_missing_template_raises(hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "template",
		"template_name": "does_not_exist",
		"template_vars": {},
	}

	with pytest.raises(ServiceValidationError):
		await render_page(hass, pixoo, page, device_size=64, variables={})


async def test_template_progress_bar_renders_expected_shapes(hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "template",
		"template_name": "progress_bar",
		"template_vars": {"title": "Load", "progress": 0.5, "bar_color": "#FF0000"},
	}

	# Service variables should win over template_vars
	await render_page(hass, pixoo, page, device_size=64, variables={"bar_color": "#00FF00"})

	# We expect at least one filled rectangle call for the bar itself.
	# progress=0.5 -> width=30 (of 60)
	assert pixoo.draw_filled_rectangle.call_count >= 1
	bar_calls = [c for c in pixoo.draw_filled_rectangle.call_args_list if c.args and c.args[0] == (2, 29)]
	assert len(bar_calls) == 1
	args = bar_calls[0].args
	assert args[1] == (2 + 30 - 1, 29 + 6 - 1)
	assert args[2] == (0, 255, 0)
	pixoo.push.assert_awaited_once()


async def test_template_now_playing_renders_image_and_text(monkeypatch, hass) -> None:
	from PIL import Image
	from custom_components.pixoo.page_engine.renderer import render_page

	dummy = Image.new("RGB", (1, 1), (1, 2, 3))

	async def _fake_resolve(*_args, **_kwargs):
		return dummy

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.renderer.async_resolve_image_source",
		_fake_resolve,
	)

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "template",
		"template_name": "now_playing",
		"template_vars": {
			"title": "Song",
			"artist": "Artist",
			"cover_url": "https://example.com/cover.png",
		},
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	# Image drawn
	assert pixoo.draw_image.call_count == 1
	img_args, img_kwargs = pixoo.draw_image.call_args
	assert img_args[0] is dummy
	assert img_kwargs["xy"] == (0, 0)

	# Text drawn (title + artist)
	all_text = " ".join(str(c.args[0]) for c in pixoo.draw_text.call_args_list)
	assert "Song" in all_text
	assert "Artist" in all_text
	pixoo.push.assert_awaited_once()


async def test_render_progress_bar_basic(hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{
				"type": "progress_bar",
				"x": 2,
				"y": 28,
				"width": 60,
				"height": 6,
				"progress": 50.0,
				"bar_color": "#00FF00",
				"background_color": "#333333",
			},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	# Should draw background + fill (2 rectangles)
	assert pixoo.draw_filled_rectangle.call_count == 2
	pixoo.push.assert_awaited_once()


async def test_render_progress_bar_with_thresholds(hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{
				"type": "progress_bar",
				"x": 0,
				"y": 0,
				"width": 64,
				"height": 8,
				"progress": 25.0,  # Below 50 threshold -> should use lower threshold color
				"color_thresholds": [
					{"value": 80, "color": "#00FF00"},
					{"value": 50, "color": "#FFFF00"},
					{"value": 20, "color": "#FF0000"},
				],
				"color_thresholds_transition": "hard",
			},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	# Background + fill
	assert pixoo.draw_filled_rectangle.call_count == 2
	pixoo.push.assert_awaited_once()


async def test_render_progress_bar_vertical(hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{
				"type": "progress_bar",
				"x": 56,
				"y": 0,
				"width": 8,
				"height": 64,
				"progress": 75.0,
				"orientation": "vertical",
			},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	assert pixoo.draw_filled_rectangle.call_count == 2
	pixoo.push.assert_awaited_once()


async def test_render_progress_bar_with_border(hass) -> None:
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{
				"type": "progress_bar",
				"x": 0,
				"y": 0,
				"width": 64,
				"height": 8,
				"progress": 50.0,
				"show_border": True,
				"border_color": "#FFFFFF",
			},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	# 2 rectangles + 4 lines for border
	assert pixoo.draw_filled_rectangle.call_count == 2
	assert pixoo.draw_line.call_count == 4
	pixoo.push.assert_awaited_once()


async def test_render_icon_component(monkeypatch, hass) -> None:
	"""Test IconComponent rendering with mocked icon fetch."""
	from PIL import Image
	from custom_components.pixoo.page_engine.renderer import render_page

	dummy_icon = Image.new("RGB", (16, 16), (0, 255, 0))

	async def _fake_fetch_icon(hass, icon_name, size, color):
		return dummy_icon

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.renderer._fetch_and_render_mdi_icon",
		_fake_fetch_icon,
	)

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{
				"type": "icon",
				"x": 24,
				"y": 24,
				"icon": "mdi:battery",
				"size": 16,
				"color": "#00FF00",
			},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	assert pixoo.draw_image.call_count == 1
	args, kwargs = pixoo.draw_image.call_args
	assert args[0] is dummy_icon
	assert kwargs["xy"] == (24, 24)
	pixoo.push.assert_awaited_once()


async def test_render_icon_with_thresholds(monkeypatch, hass) -> None:
	"""Test IconComponent with color thresholds based on entity value."""
	from PIL import Image
	from custom_components.pixoo.page_engine.renderer import render_page
	from homeassistant.core import State

	# Set up a mock sensor state
	hass.states.async_set("sensor.battery_soc", "75")

	captured_color = None

	async def _fake_fetch_icon(hass, icon_name, size, color):
		nonlocal captured_color
		captured_color = color
		return Image.new("RGB", (size, size), color)

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.renderer._fetch_and_render_mdi_icon",
		_fake_fetch_icon,
	)

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"components": [
			{
				"type": "icon",
				"x": 0,
				"y": 0,
				"icon": "battery",
				"size": 32,
				"value": "sensor.battery_soc",
				"color_thresholds": [
					{"value": 80, "color": "#00FF00"},  # green
					{"value": 50, "color": "#FFFF00"},  # yellow
					{"value": 20, "color": "#FF0000"},  # red
				],
				"color_thresholds_transition": "hard",
			},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	# Value 75 is between 50 and 80, with hard transition should be yellow
	assert captured_color == (255, 255, 0)
	pixoo.push.assert_awaited_once()


async def test_render_component_enabled_condition(monkeypatch, hass) -> None:
	"""Test component-level enabled condition skips disabled components."""
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	# Set up state for template
	hass.states.async_set("binary_sensor.show_text", "off")

	page = {
		"page_type": "components",
		"background": "#000000",
		"components": [
			{
				"type": "text",
				"x": 0,
				"y": 0,
				"text": "Hidden",
				"enabled": "{{ is_state('binary_sensor.show_text', 'on') }}",
			},
			{
				"type": "text",
				"x": 0,
				"y": 10,
				"text": "Visible",
				# No enabled condition = always rendered
			},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	# Only the second text should be rendered
	assert pixoo.draw_text.call_count == 1
	assert pixoo.draw_text.call_args.args[0] == "Visible"
	pixoo.push.assert_awaited_once()


async def test_render_component_enabled_false(hass) -> None:
	"""Test component with enabled=False is skipped."""
	from custom_components.pixoo.page_engine.renderer import render_page

	pixoo = SimpleNamespace(
		clear=Mock(),
		fill=Mock(),
		draw_text=Mock(),
		draw_line=Mock(),
		draw_filled_rectangle=Mock(),
		draw_image=Mock(),
		push=AsyncMock(),
	)

	page = {
		"page_type": "components",
		"background": "#000000",
		"components": [
			{
				"type": "text",
				"x": 0,
				"y": 0,
				"text": "Disabled",
				"enabled": False,
			},
			{
				"type": "text",
				"x": 0,
				"y": 10,
				"text": "Enabled",
				"enabled": True,
			},
		],
	}

	await render_page(hass, pixoo, page, device_size=64, variables={})

	# Only enabled text rendered
	assert pixoo.draw_text.call_count == 1
	assert pixoo.draw_text.call_args.args[0] == "Enabled"
	pixoo.push.assert_awaited_once()