"""Pixoo Page Engine.

This submodule provides a small DSL to render "pages" (composed of components)
onto Pixoo displays.

Implementation is tracked in `specs/002-page-engine/`.
"""

from __future__ import annotations

from typing import NoReturn

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError, TemplateError
from pydantic import ValidationError

from .display_buffer import DisplayBuffer, PillowDisplayBuffer, PixooDisplayBuffer


class PageEngineError(Exception):
    """Base error for Page Engine."""


class PageEngineValidationError(PageEngineError):
    """Raised when a page/component definition is invalid."""


__all__ = [
    "PageEngineError",
    "PageEngineValidationError",
    "DisplayBuffer",
    "PillowDisplayBuffer",
    "PixooDisplayBuffer",
    "raise_service_error",
]


def raise_service_error(err: Exception, *, context: str | None = None) -> NoReturn:
    """Raise a Home Assistant service-appropriate exception.

    Contract (specs/002-page-engine/contracts/page-services.md):
    - Invalid user inputs / templates -> ServiceValidationError (or TemplateError)
    - Device I/O and operational failures -> HomeAssistantError
    """

    prefix = f"{context}: " if context else ""

    if isinstance(err, (ServiceValidationError,)):
        raise err

    if isinstance(err, (ValidationError, PageEngineValidationError, TemplateError, ValueError)):
        raise ServiceValidationError(f"{prefix}{err}") from err

    raise HomeAssistantError(f"{prefix}{err}") from err
