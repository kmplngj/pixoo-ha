"""Tests for Pixoo Page Engine services (US1)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.config_entries import ConfigEntryState

from custom_components.pixoo.const import CONF_DEVICE_SIZE, DOMAIN
from custom_components.pixoo.pixooasync.enums import Rotation
from custom_components.pixoo.pixooasync.models import SystemConfig


async def test_render_page_missing_page_raises(hass: HomeAssistant, setup_integration) -> None:
	with pytest.raises(ServiceValidationError):
		await hass.services.async_call(
			DOMAIN,
			"render_page",
			{},
			blocking=True,
		)


async def test_render_page_renders_text_on_single_device(
	hass: HomeAssistant,
	setup_integration,
	mock_pixoo,
) -> None:
	# Ensure clean call history
	mock_pixoo.clear.reset_mock()
	mock_pixoo.draw_text.reset_mock()
	mock_pixoo.push.reset_mock()

	await hass.services.async_call(
		DOMAIN,
		"render_page",
		{
			"page": {
				"page_type": "components",
				"components": [
					{"type": "text", "x": 0, "y": 0, "text": "HI"},
				],
			},
		},
		blocking=True,
	)

	mock_pixoo.clear.assert_called_once()
	mock_pixoo.draw_text.assert_called_once()
	mock_pixoo.push.assert_awaited_once()


async def test_render_page_invalid_target_raises(
	hass: HomeAssistant,
	setup_integration,
) -> None:
	with pytest.raises(ServiceValidationError):
		await hass.services.async_call(
			DOMAIN,
			"render_page",
			{
				"entity_id": ["light.does_not_exist"],
				"page": {
					"page_type": "components",
					"components": [{"type": "text", "x": 0, "y": 0, "text": "HI"}],
				},
			},
			blocking=True,
		)


def _make_pixoo_mock() -> AsyncMock:
	mock_pixoo = AsyncMock()
	# Setup methods that are awaited during setup/teardown
	mock_pixoo.initialize = AsyncMock()
	mock_pixoo.close = AsyncMock()
	mock_pixoo.get_all_channel_config = AsyncMock()
	# Coordinators
	mock_pixoo.get_system_config = AsyncMock(
		return_value=SystemConfig(
			brightness=80,
			rotation=Rotation.NORMAL,
			mirror_mode=False,
			white_balance_r=255,
			white_balance_g=255,
			white_balance_b=255,
			time_zone="UTC",
			hour_mode=24,
			temperature_mode=0,
			screen_power=True,
		)
	)
	mock_pixoo.get_current_channel = AsyncMock(return_value=0)
	mock_pixoo.get_time_info = AsyncMock(return_value=None)
	mock_pixoo.get_weather_info = AsyncMock(return_value=None)
	mock_pixoo.get_animation_list = AsyncMock(return_value=[])
	# Buffer workflow
	mock_pixoo.clear = Mock()
	mock_pixoo.fill = Mock()
	mock_pixoo.draw_text = Mock()
	mock_pixoo.draw_line = Mock()
	mock_pixoo.draw_filled_rectangle = Mock()
	mock_pixoo.draw_image = Mock()
	mock_pixoo.push = AsyncMock()
	return mock_pixoo


async def test_render_page_multi_device_best_effort(hass: HomeAssistant) -> None:
	entry_a = MockConfigEntry(
		domain=DOMAIN,
		data={CONF_HOST: "192.168.1.10", CONF_NAME: "Pixoo A", CONF_DEVICE_SIZE: 64},
		entry_id="entry_a",
		unique_id="AA",
		title="Pixoo A",
	)
	entry_b = MockConfigEntry(
		domain=DOMAIN,
		data={CONF_HOST: "192.168.1.11", CONF_NAME: "Pixoo B", CONF_DEVICE_SIZE: 64},
		entry_id="entry_b",
		unique_id="BB",
		title="Pixoo B",
	)

	pixoo_a = _make_pixoo_mock()
	pixoo_b = _make_pixoo_mock()
	# A fails on push, B succeeds
	pixoo_a.push = AsyncMock(side_effect=Exception("offline"))

	entry_a.add_to_hass(hass)
	entry_b.add_to_hass(hass)

	with patch("custom_components.pixoo.PixooAsync", side_effect=[pixoo_a, pixoo_b]):
		assert await hass.config_entries.async_setup(entry_a.entry_id)
		await hass.async_block_till_done()

		# Depending on HA internals, adding multiple entries can result in both being
		# loaded as a side-effect when the integration is initialized. Avoid double setup.
		entry_b_entry = hass.config_entries.async_get_entry(entry_b.entry_id)
		assert entry_b_entry is not None
		if entry_b_entry.state == ConfigEntryState.NOT_LOADED:
			assert await hass.config_entries.async_setup(entry_b.entry_id)
			await hass.async_block_till_done()

	# Should succeed overall because B works.
	await hass.services.async_call(
		DOMAIN,
		"render_page",
		{
			"page": {
				"page_type": "components",
				"components": [{"type": "text", "x": 0, "y": 0, "text": "HI"}],
			},
		},
		blocking=True,
	)

	assert pixoo_a.push.await_count == 1
	assert pixoo_b.push.await_count == 1

	# Now both fail => service should raise.
	pixoo_b.push = AsyncMock(side_effect=Exception("offline_b"))

	with pytest.raises(HomeAssistantError):
		await hass.services.async_call(
			DOMAIN,
			"render_page",
			{
				"page": {
					"page_type": "components",
					"components": [{"type": "text", "x": 0, "y": 0, "text": "HI"}],
				},
			},
			blocking=True,
		)


async def test_rotation_starts_from_entry_options_and_schedules_renders(
	hass: HomeAssistant,
	monkeypatch,
) -> None:
	"""US2: Rotation should start when enabled in entry options and render pages."""
	entry = MockConfigEntry(
		domain=DOMAIN,
		data={CONF_HOST: "192.168.1.10", CONF_NAME: "Pixoo A", CONF_DEVICE_SIZE: 64},
		options={
			"page_engine_rotation": {
				"enabled": True,
				"default_duration": 15,
				"pages": [
					{
						"page_type": "components",
						"duration": 3,
						"components": [{"type": "text", "x": 0, "y": 0, "text": "A"}],
					},
					{
						"page_type": "components",
						"duration": 4,
						"components": [{"type": "text", "x": 0, "y": 0, "text": "B"}],
					},
				],
			}
		},
		entry_id="entry_rot",
		unique_id="ROT",
		title="Pixoo Rot",
	)

	pixoo = _make_pixoo_mock()

	# Capture scheduled callbacks from rotation controller.
	scheduled: list[tuple[float, Callable[[datetime], None]]] = []

	def _fake_async_call_later(_hass: HomeAssistant, delay: float, action, *args, **kwargs):
		scheduled.append((delay, action))
		return lambda: None

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.async_call_later",
		_fake_async_call_later,
	)

	render_page = AsyncMock()
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.render_page_engine_page",
		render_page,
	)

	entry.add_to_hass(hass)
	with patch("custom_components.pixoo.PixooAsync", return_value=pixoo):
		assert await hass.config_entries.async_setup(entry.entry_id)
		await hass.async_block_till_done()

	# Rotation should have scheduled an immediate run (delay 0)
	assert scheduled
	assert scheduled[0][0] == 0

	# Trigger the scheduled callback manually.
	delay0, action0 = scheduled.pop(0)
	action0(datetime.now(timezone.utc))
	await hass.async_block_till_done()

	assert render_page.await_count == 1
	# Next schedule should respect per-page duration (3s for first page)
	assert scheduled
	assert scheduled[-1][0] == 3


async def test_show_message_pauses_and_resumes_rotation_when_previously_running(
	hass: HomeAssistant,
	monkeypatch,
) -> None:
	"""US3: show_message should pause rotation and resume it after expiry."""
	entry = MockConfigEntry(
		domain=DOMAIN,
		data={CONF_HOST: "192.168.1.10", CONF_NAME: "Pixoo A", CONF_DEVICE_SIZE: 64},
		options={
			"page_engine_rotation": {
				"enabled": True,
				"default_duration": 15,
				"pages": [
					{
						"page_type": "components",
						"duration": 3,
						"components": [{"type": "text", "x": 0, "y": 0, "text": "A"}],
					},
					{
						"page_type": "components",
						"duration": 4,
						"components": [{"type": "text", "x": 0, "y": 0, "text": "B"}],
					},
				],
			}
		},
		entry_id="entry_msg",
		unique_id="MSG",
		title="Pixoo Msg",
	)

	pixoo = _make_pixoo_mock()

	# Capture scheduled callbacks (rotation + message expiry) from rotation controller.
	scheduled: list[tuple[float, Callable[[datetime], None]]] = []

	def _fake_async_call_later(_hass: HomeAssistant, delay: float, action, *args, **kwargs):
		scheduled.append((delay, action))
		return lambda: None

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.async_call_later",
		_fake_async_call_later,
	)

	render_page = AsyncMock()
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.render_page_engine_page",
		render_page,
	)

	entry.add_to_hass(hass)
	with patch("custom_components.pixoo.PixooAsync", return_value=pixoo):
		assert await hass.config_entries.async_setup(entry.entry_id)
		await hass.async_block_till_done()

	# Initial rotation schedule (delay 0)
	assert scheduled
	assert scheduled[0][0] == 0

	# Run first rotation tick.
	_d0, action0 = scheduled.pop(0)
	action0(datetime.now(timezone.utc))
	await hass.async_block_till_done()
	assert render_page.await_count == 1

	# Call show_message (should render immediately and schedule expiry)
	await hass.services.async_call(
		DOMAIN,
		"show_message",
		{
			"page": {
				"page_type": "components",
				"components": [{"type": "text", "x": 0, "y": 0, "text": "MSG"}],
			},
			"duration": 10,
		},
		blocking=True,
	)

	assert render_page.await_count == 2
	assert any(delay == 10 for delay, _ in scheduled)

	# Trigger expiry callback (delay 10). Expect rotation to resume by scheduling delay 0.
	_exp_idx = next(i for i, (d, _) in enumerate(scheduled) if d == 10)
	_d_exp, exp_action = scheduled.pop(_exp_idx)
	exp_action(datetime.now(timezone.utc))
	await hass.async_block_till_done()

	assert any(d == 0 for d, _ in scheduled)

	# Trigger the resume tick.
	_resume_idx = next(i for i, (d, _) in enumerate(scheduled) if d == 0)
	_d_res, res_action = scheduled.pop(_resume_idx)
	res_action(datetime.now(timezone.utc))
	await hass.async_block_till_done()

	assert render_page.await_count >= 3


async def test_show_message_does_not_resume_when_rotation_was_not_running(
	hass: HomeAssistant,
	monkeypatch,
) -> None:
	"""US3: if rotation was not active, expiry must not schedule rotation."""
	entry = MockConfigEntry(
		domain=DOMAIN,
		data={CONF_HOST: "192.168.1.10", CONF_NAME: "Pixoo A", CONF_DEVICE_SIZE: 64},
		options={
			"page_engine_rotation": {
				"enabled": False,
				"default_duration": 15,
				"pages": [],
			}
		},
		entry_id="entry_msg2",
		unique_id="MSG2",
		title="Pixoo Msg2",
	)

	pixoo = _make_pixoo_mock()
	scheduled: list[tuple[float, Callable[[datetime], None]]] = []

	def _fake_async_call_later(_hass: HomeAssistant, delay: float, action, *args, **kwargs):
		scheduled.append((delay, action))
		return lambda: None

	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.async_call_later",
		_fake_async_call_later,
	)

	render_page = AsyncMock()
	monkeypatch.setattr(
		"custom_components.pixoo.page_engine.rotation.render_page_engine_page",
		render_page,
	)

	entry.add_to_hass(hass)
	with patch("custom_components.pixoo.PixooAsync", return_value=pixoo):
		assert await hass.config_entries.async_setup(entry.entry_id)
		await hass.async_block_till_done()

	# Rotation disabled => no initial schedule at 0
	assert not scheduled

	await hass.services.async_call(
		DOMAIN,
		"show_message",
		{
			"page": {
				"page_type": "components",
				"components": [{"type": "text", "x": 0, "y": 0, "text": "MSG"}],
			},
			"duration": 2,
		},
		blocking=True,
	)

	assert render_page.await_count == 1
	assert any(delay == 2 for delay, _ in scheduled)

	# Trigger expiry callback. It must NOT schedule rotation (delay 0).
	_exp_idx = next(i for i, (d, _) in enumerate(scheduled) if d == 2)
	_d_exp, exp_action = scheduled.pop(_exp_idx)
	exp_action(datetime.now(timezone.utc))
	await hass.async_block_till_done()

	assert not any(d == 0 for d, _ in scheduled)
