"""Tests for Pixoo Page Engine rotation (US2)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from custom_components.pixoo.const import CONF_DEVICE_SIZE, DOMAIN


class _DummyQueue:
	async def enqueue(self, coro: Awaitable[Any]) -> Any:
		return await coro


def _rotation_options(*, enabled: bool, default_duration: int, pages: list[dict[str, Any]]) -> dict[str, Any]:
	return {
		"page_engine_rotation": {
			"enabled": enabled,
			"default_duration": default_duration,
			"pages": pages,
		}
	}


def _page(*, text: str, enabled: bool | str | None = None, duration: int | None = None) -> dict[str, Any]:
	page: dict[str, Any] = {
		"page_type": "components",
		"components": [{"type": "text", "x": 0, "y": 0, "text": text}],
	}
	if enabled is not None:
		page["enabled"] = enabled
	if duration is not None:
		page["duration"] = duration
	return page


@pytest.fixture
def _schedule_spy():
	"""Patch helper: capture scheduled callbacks and delays."""
	scheduled: list[tuple[float, Callable[[datetime], None]]] = []

	def _fake_async_call_later(
		hass: HomeAssistant,
		delay: float,
		action: Callable[[datetime], None],
		*args: Any,
		**kwargs: Any,
	) -> Callable[[], None]:
		scheduled.append((delay, action))

		def _cancel() -> None:
			return

		return _cancel

	return scheduled, _fake_async_call_later


async def test_rotation_skips_disabled_pages_and_renders_next_active(
	hass: HomeAssistant,
	monkeypatch,
	_schedule_spy,
) -> None:
	from custom_components.pixoo.page_engine.rotation import RotationController

	scheduled, fake_call_later = _schedule_spy
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.async_call_later",
		fake_call_later,
	)

	render_page = AsyncMock()
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.render_page_engine_page",
		render_page,
	)

	entry = MockConfigEntry(
		domain=DOMAIN,
		data={"host": "192.0.2.1", CONF_DEVICE_SIZE: 64},
		options=_rotation_options(
			enabled=True,
			default_duration=15,
			pages=[
				_page(text="A", enabled=False),
				_page(text="B", enabled=True, duration=5),
			],
		),
	)

	controller = RotationController(
		hass=hass,
		entry=entry,
		pixoo=AsyncMock(),
		service_queue=_DummyQueue(),
		device_size=64,
	)

	await controller.async_start()
	await controller.async_run_once()

	assert render_page.await_count == 1
	call = render_page.await_args
	assert call is not None
	args, _kwargs = call
	called_page = args[2]
	assert called_page["components"][0]["text"] == "B"

	# next schedule uses page.duration (5s)
	assert scheduled
	assert scheduled[-1][0] == 5

	await controller.async_stop()


async def test_rotation_uses_default_duration_when_page_has_none(
	hass: HomeAssistant,
	monkeypatch,
	_schedule_spy,
) -> None:
	from custom_components.pixoo.page_engine.rotation import RotationController

	scheduled, fake_call_later = _schedule_spy
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.async_call_later",
		fake_call_later,
	)

	render_page = AsyncMock()
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.render_page_engine_page",
		render_page,
	)

	entry = MockConfigEntry(
		domain=DOMAIN,
		data={"host": "192.0.2.1", CONF_DEVICE_SIZE: 64},
		options=_rotation_options(
			enabled=True,
			default_duration=11,
			pages=[_page(text="A", enabled=True)],
		),
	)

	controller = RotationController(
		hass=hass,
		entry=entry,
		pixoo=AsyncMock(),
		service_queue=_DummyQueue(),
		device_size=64,
	)

	await controller.async_start()
	await controller.async_run_once()

	assert render_page.await_count == 1
	assert scheduled
	assert scheduled[-1][0] == 11

	await controller.async_stop()


async def test_rotation_all_disabled_does_not_render_and_reschedules(
	hass: HomeAssistant,
	monkeypatch,
	_schedule_spy,
) -> None:
	from custom_components.pixoo.page_engine.rotation import RotationController

	scheduled, fake_call_later = _schedule_spy
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.async_call_later",
		fake_call_later,
	)

	render_page = AsyncMock()
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.render_page_engine_page",
		render_page,
	)

	entry = MockConfigEntry(
		domain=DOMAIN,
		data={"host": "192.0.2.1", CONF_DEVICE_SIZE: 64},
		options=_rotation_options(
			enabled=True,
			default_duration=7,
			pages=[
				_page(text="A", enabled=False),
				_page(text="B", enabled="{{ false }}"),
			],
		),
	)

	controller = RotationController(
		hass=hass,
		entry=entry,
		pixoo=AsyncMock(),
		service_queue=_DummyQueue(),
		device_size=64,
	)

	await controller.async_start()
	await controller.async_run_once()

	assert render_page.await_count == 0
	assert scheduled
	assert scheduled[-1][0] == 7

	await controller.async_stop()


async def test_show_message_last_wins_replaces_and_resets_timer(
	hass: HomeAssistant,
	monkeypatch,
) -> None:
	"""US3: A new message replaces the previous one and resets the expiry timer."""
	from custom_components.pixoo.page_engine.rotation import RotationController

	scheduled: list[float] = []
	cancel_calls: list[None] = []

	def _fake_async_call_later(
		_hass: HomeAssistant,
		delay: float,
		action: Callable[[datetime], None],
		*args: Any,
		**kwargs: Any,
	) -> Callable[[], None]:
		scheduled.append(delay)

		def _cancel() -> None:
			cancel_calls.append(None)

		return _cancel

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.async_call_later",
		_fake_async_call_later,
	)

	render_page = AsyncMock()
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.render_page_engine_page",
		render_page,
	)

	entry = MockConfigEntry(
		domain=DOMAIN,
		data={"host": "192.0.2.1", CONF_DEVICE_SIZE: 64},
		options=_rotation_options(
			enabled=True,
			default_duration=15,
			pages=[_page(text="A")],
		),
	)

	controller = RotationController(
		hass=hass,
		entry=entry,
		pixoo=AsyncMock(),
		service_queue=_DummyQueue(),
		device_size=64,
	)

	await controller.async_start()

	await controller.async_show_message(
		_page(text="MSG1"),
		duration=10,
		variables={},
		allowlist_mode="strict",
	)
	await controller.async_show_message(
		_page(text="MSG2"),
		duration=10,
		variables={},
		allowlist_mode="strict",
	)

	assert render_page.await_count == 2
	assert render_page.await_args_list[-1].args[2]["components"][0]["text"] == "MSG2"

	# Expect two expiry schedules (10s each) and one cancellation (MSG1 timer cancelled)
	assert scheduled.count(10) == 2
	assert len(cancel_calls) >= 1

	await controller.async_stop()
