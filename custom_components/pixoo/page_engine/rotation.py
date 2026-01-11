"""Rotation controller for Pixoo Page Engine.

US2 implements an entry-bound scheduler that cycles through a list of pages.
The controller is intentionally service/renderer-driven: it calls the existing
Page Engine renderer and relies on the integration's per-device ServiceQueue.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .renderer import ALLOWLIST_MODE_STRICT, render_page as render_page_engine_page
from .templating import async_render_complex
from .storage import load_pages_from_yaml


_LOGGER = logging.getLogger(__name__)


_ROTATION_OPTIONS_KEY = "page_engine_rotation"


# Avoid back-to-back immediate rescheduling loops (0s) that can spam logs/devices.
_MIN_RERENDER_DELAY_S = 0.1

# Defensive minimums for user-provided durations.
_MIN_DURATION_S = 1


@dataclass(frozen=True)
class RotationConfig:
    enabled: bool
    default_duration: int
    pages: list[dict[str, Any]]
    pages_yaml_path: str | None = None
    allowlist_mode: str = ALLOWLIST_MODE_STRICT
    variables: dict[str, Any] | None = None

    @classmethod
    def from_entry(cls, entry: ConfigEntry) -> "RotationConfig":
        raw = entry.options.get(_ROTATION_OPTIONS_KEY, {})
        if not isinstance(raw, dict):
            raw = {}

        enabled = bool(raw.get("enabled", False))

        try:
            default_duration = int(raw.get("default_duration", 15))
        except (TypeError, ValueError):
            default_duration = 15
        if default_duration < _MIN_DURATION_S:
            default_duration = _MIN_DURATION_S

        pages_raw = raw.get("pages", [])
        if not isinstance(pages_raw, list):
            pages_raw = []

        pages: list[dict[str, Any]] = []
        for item in pages_raw:
            if isinstance(item, dict) and "page" in item and isinstance(item["page"], dict):
                pages.append(item["page"])
            elif isinstance(item, dict):
                pages.append(item)

        pages_yaml_path = raw.get("pages_yaml_path")
        if pages_yaml_path is not None and not isinstance(pages_yaml_path, str):
            pages_yaml_path = None
        if isinstance(pages_yaml_path, str) and not pages_yaml_path.strip():
            pages_yaml_path = None

        allowlist_mode = raw.get("allowlist_mode", ALLOWLIST_MODE_STRICT)
        if allowlist_mode not in ("strict", "permissive"):
            allowlist_mode = ALLOWLIST_MODE_STRICT

        variables = raw.get("variables")
        if variables is not None and not isinstance(variables, dict):
            variables = None

        return cls(
            enabled=enabled,
            default_duration=default_duration,
            pages=pages,
            pages_yaml_path=pages_yaml_path,
            allowlist_mode=allowlist_mode,
            variables=variables,
        )


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("true", "1", "yes", "on"):
            return True
        if s in ("false", "0", "no", "off", ""):
            return False
    # Unknown: treat as False (defensive)
    return False


class RotationController:
    """Entry-bound rotation scheduler.

    This controller is intentionally conservative:
    - If rotation is disabled or misconfigured, it does nothing.
    - If all pages are disabled, it reschedules checks without forcing display changes.
    - Render failures are logged; rotation continues.
    """

    def __init__(
        self,
        *,
        hass: HomeAssistant,
        entry: ConfigEntry,
        pixoo: Any,
        service_queue: Any,
        device_size: int,
    ) -> None:
        self._hass = hass
        self._entry = entry
        self._pixoo = pixoo
        self._service_queue = service_queue
        self._device_size = device_size

        self._running = False
        self._current_index = -1
        self._cancel: Callable[[], None] | None = None

        self._last_no_active_log: datetime | None = None

        # Basic rate limiting guard (T057): even if multiple triggers fire quickly,
        # avoid calling render back-to-back with 0 delay.
        self._last_render_monotonic: float | None = None

        # Optional YAML-loaded pages cache (T041)
        self._yaml_pages_path: str | None = None
        self._yaml_pages: list[dict[str, Any]] | None = None

        # US3 override/message state (last-wins)
        self._override_active = False
        self._override_cancel: Callable[[], None] | None = None
        self._override_resume_rotation = False

    @property
    def running(self) -> bool:
        return self._running

    async def async_start(self) -> None:
        if self._running:
            return

        config = RotationConfig.from_entry(self._entry)
        if not config.enabled:
            return

        # Best-effort pre-load of YAML pages (if configured).
        if config.pages_yaml_path:
            await self.async_reload_pages()

        self._running = True
        self._schedule(0)

    async def async_stop(self) -> None:
        self._running = False
        if self._cancel is not None:
            self._cancel()
            self._cancel = None
        if self._override_cancel is not None:
            self._override_cancel()
            self._override_cancel = None
        self._override_active = False
        self._override_resume_rotation = False

    async def async_reload_pages(self) -> None:
        """(Re)load pages from the configured YAML file.

        This is best-effort: on failures we keep the previous cache.
        """

        config = RotationConfig.from_entry(self._entry)
        yaml_path = config.pages_yaml_path
        if not yaml_path:
            self._yaml_pages_path = None
            self._yaml_pages = None
            return

        try:
            pages = await load_pages_from_yaml(self._hass, yaml_path)
        except Exception as err:
            _LOGGER.error(
                "Page Engine rotation: failed to load pages from YAML (%s) for entry %s: %s",
                yaml_path,
                self._entry.entry_id,
                err,
            )
            return

        self._yaml_pages_path = yaml_path
        self._yaml_pages = pages

    async def async_next(self) -> None:
        """Immediately advance to the next active page."""

        if not self._running:
            return

        if self._cancel is not None:
            self._cancel()
            self._cancel = None

        await self.async_run_once()

    async def async_show_message(
        self,
        page: dict[str, Any],
        *,
        duration: int,
        variables: dict[str, Any] | None,
        allowlist_mode: str,
    ) -> None:
        """Show a temporary override page.

        Policy: last-wins. A new message cancels the previous expiry timer.
        When the override expires, rotation resumes only if it was running.
        """

        if duration < _MIN_DURATION_S:
            duration = _MIN_DURATION_S

        # Cancel any pending rotation tick while the override is active.
        if self._cancel is not None:
            self._cancel()
            self._cancel = None

        # Cancel any previous override timer (last-wins).
        if self._override_cancel is not None:
            self._override_cancel()
            self._override_cancel = None

        self._override_active = True
        self._override_resume_rotation = self._running

        config = RotationConfig.from_entry(self._entry)
        base_vars = dict(config.variables or {})
        if variables:
            base_vars.update(variables)
        page_vars = dict(page.get("variables") or {}) if isinstance(page.get("variables"), dict) else {}
        merged_vars = {**base_vars, **page_vars}

        async def _execute() -> None:
            await render_page_engine_page(
                self._hass,
                self._pixoo,
                page,
                device_size=self._device_size,
                variables=merged_vars,
                allowlist_mode=allowlist_mode,
                entry_id=self._entry.entry_id,
            )

        # Use the same per-device queue to serialize with rotation and other services.
        await self._service_queue.enqueue(_execute())

        self._override_cancel = async_call_later(self._hass, duration, self._handle_override_expiry)

    def _handle_override_expiry(self, _now: datetime) -> None:
        self._override_active = False
        if self._override_cancel is not None:
            self._override_cancel = None

        if not self._override_resume_rotation:
            self._override_resume_rotation = False
            return

        self._override_resume_rotation = False

        # Resume only if rotation is still enabled.
        config = RotationConfig.from_entry(self._entry)
        if self._running and config.enabled:
            self._schedule(0)

    def _schedule(self, delay: float) -> None:
        if self._cancel is not None:
            self._cancel()
            self._cancel = None

        self._cancel = async_call_later(self._hass, float(delay), self._handle_timer)

    def _handle_timer(self, _now: datetime) -> None:
        if not self._running:
            return
        # async_call_later runs callbacks in the event loop, so we can use
        # hass.async_create_task safely. However, to avoid the thread-safety
        # check in newer HA versions, we use hass.loop.call_soon_threadsafe
        # to schedule the task creation in the event loop thread.
        def _create_task():
            self._hass.async_create_task(self.async_run_once())
        self._hass.loop.call_soon_threadsafe(_create_task)

    async def _is_page_enabled(
        self,
        page: dict[str, Any],
        *,
        variables: dict[str, Any],
        page_index: int | None = None,
    ) -> bool:
        enabled_val = page.get("enabled", True)
        if isinstance(enabled_val, bool):
            return enabled_val
        if enabled_val is None:
            return True
        if isinstance(enabled_val, str):
            try:
                rendered = await async_render_complex(self._hass, enabled_val, variables=variables)
                return _coerce_bool(rendered)
            except Exception as err:
                _LOGGER.warning(
                    "Page Engine rotation: enable-condition render failed (entry %s, page_index=%s), treating as disabled: %s",
                    self._entry.entry_id,
                    page_index,
                    err,
                )
                return False
        return _coerce_bool(enabled_val)

    def _get_duration(self, page: dict[str, Any], *, default_duration: int) -> int:
        raw = page.get("duration", None)
        if raw is None:
            return default_duration
        try:
            duration = int(raw)
        except (TypeError, ValueError):
            return default_duration
        return max(_MIN_DURATION_S, duration)

    async def async_run_once(self) -> None:
        """Run a single rotation step (select next active page, render, reschedule)."""
        if not self._running:
            return

        # US3: while an override is active, rotation is paused.
        if self._override_active:
            return

        config = RotationConfig.from_entry(self._entry)
        if not config.enabled:
            await self.async_stop()
            return

        # Optional YAML page loading (cached). If the configured path changes, reload.
        if config.pages_yaml_path and config.pages_yaml_path != self._yaml_pages_path:
            await self.async_reload_pages()

        # Use YAML pages if configured/loaded; otherwise fall back to entry option pages.
        # This keeps the integration usable without requiring a YAML file.
        pages = list(self._yaml_pages) if self._yaml_pages else list(config.pages or [])

        if not pages:
            # No YAML pages configured - show info message once per hour
            now = dt_util.utcnow()
            if self._last_no_active_log is None or (now - self._last_no_active_log).total_seconds() >= 3600:
                if config.pages_yaml_path:
                    _LOGGER.info(
                        "Page Engine rotation: YAML file '%s' is empty or could not be loaded for entry %s",
                        config.pages_yaml_path,
                        self._entry.entry_id,
                    )
                else:
                    _LOGGER.info(
                        "Page Engine rotation: no pages configured for entry %s (neither pages_yaml_path nor option pages).",
                        self._entry.entry_id,
                    )
                self._last_no_active_log = now
            self._schedule(config.default_duration)
            return

        # T057: basic anti-spam guard - prevent back-to-back immediate renders.
        # We do not skip renders (important for resume semantics), but we add a
        # tiny async delay when triggers fire in rapid succession.
        if self._last_render_monotonic is not None:
            elapsed = time.monotonic() - self._last_render_monotonic
            if elapsed < _MIN_RERENDER_DELAY_S:
                await asyncio.sleep(_MIN_RERENDER_DELAY_S - elapsed)

        base_vars = dict(config.variables or {})

        selected_index: int | None = None
        selected_page: dict[str, Any] | None = None

        for i in range(len(pages)):
            idx = (self._current_index + 1 + i) % len(pages)
            page = pages[idx]

            # Merge page.variables into the template context for enable evaluation.
            page_vars = dict(page.get("variables") or {}) if isinstance(page.get("variables"), dict) else {}
            merged_vars = {**base_vars, **page_vars}

            if await self._is_page_enabled(page, variables=merged_vars, page_index=idx):
                selected_index = idx
                selected_page = page
                break

        if selected_page is None or selected_index is None:
            # All pages disabled: do not force display changes.
            now = dt_util.utcnow()
            if self._last_no_active_log is None or (now - self._last_no_active_log).total_seconds() >= 60:
                _LOGGER.info(
                    "Page Engine rotation: no active pages for entry %s",
                    self._entry.entry_id,
                )
                self._last_no_active_log = now

            self._schedule(config.default_duration)
            return

        self._current_index = selected_index

        duration = self._get_duration(selected_page, default_duration=config.default_duration)

        page_vars = dict(selected_page.get("variables") or {}) if isinstance(selected_page.get("variables"), dict) else {}
        merged_vars = {**base_vars, **page_vars}

        async def _execute() -> None:
            await render_page_engine_page(
                self._hass,
                self._pixoo,
                selected_page,
                device_size=self._device_size,
                variables=merged_vars,
                allowlist_mode=config.allowlist_mode,
                entry_id=self._entry.entry_id,
            )

        try:
            await self._service_queue.enqueue(_execute())
            self._last_render_monotonic = time.monotonic()
        except Exception as err:
            _LOGGER.error(
                "Page Engine rotation: render failed for entry %s (page index %s): %s",
                self._entry.entry_id,
                selected_index,
                err,
            )

        self._schedule(duration)
