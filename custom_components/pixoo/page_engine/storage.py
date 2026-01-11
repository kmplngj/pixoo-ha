"""Optional YAML/template storage for Pixoo Page Engine.

US2 (optional): rotation pages can be loaded from a YAML file under /config.

This module intentionally keeps responsibilities small:
- resolve a YAML path safely
- load YAML content (async, via executor)
- validate each page payload using Page Engine models
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import yaml as yaml_util

from .models import PageModel


import logging

_LOGGER = logging.getLogger(__name__)

_TEMPLATE_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _resolve_template_path(hass: HomeAssistant, template_name: str) -> Path:
    """Resolve a template file path.

    Templates are loaded from the user's config directory under
    `pixoo_templates/` (e.g., `/config/pixoo_templates/my_template.yaml`).

    We validate the template_name strictly to avoid path traversal.
    """

    if not isinstance(template_name, str) or not template_name.strip():
        raise ServiceValidationError("template_name must be a non-empty string")

    name = template_name.strip()
    if _TEMPLATE_NAME_RE.fullmatch(name) is None:
        raise ServiceValidationError(
            "template_name may only contain letters, numbers, and underscores"
        )

    # Look for templates in user's config directory
    templates_dir = Path(hass.config.config_dir) / "pixoo_templates"
    return templates_dir / f"{name}.yaml"


async def load_builtin_template(hass: HomeAssistant, template_name: str) -> dict[str, Any]:
    """Load and validate a template page from user's config directory.

    Templates should be placed in /config/pixoo_templates/<name>.yaml
    
    For example templates, see the integration's examples/page_templates/ directory.

    Returns a validated page dict (ready to pass to the renderer).
    """

    template_path = _resolve_template_path(hass, template_name)
    if not template_path.exists() or not template_path.is_file():
        templates_dir = Path(hass.config.config_dir) / "pixoo_templates"
        raise ServiceValidationError(
            f"Template '{template_name}' not found. "
            f"Create '{templates_dir}/{template_name}.yaml' or see "
            "examples/page_templates/ in the integration repository for samples."
        )

    try:
        loaded: Any = await hass.async_add_executor_job(
            yaml_util.load_yaml, str(template_path)
        )
    except Exception as err:
        raise ServiceValidationError(f"Failed to load built-in template: {err}") from err

    if not isinstance(loaded, dict):
        raise ServiceValidationError("Built-in template must be a mapping (page dict)")

    # Note: built-in templates may contain Jinja expressions in fields that are
    # validated later (e.g., rectangle.width). Therefore we intentionally do NOT
    # validate here; the renderer will render templates first and validate the
    # resulting payload via PageModel.
    return loaded


def _resolve_yaml_path(hass: HomeAssistant, path: str) -> Path:
    """Resolve a YAML path.

    - Relative paths are resolved under the HA config directory.
    - Absolute paths are used as-is.
    """

    p = Path(path)
    if not p.is_absolute():
        p = Path(hass.config.path(path))
    return p


def _is_inside_config_dir(hass: HomeAssistant, path: Path) -> bool:
    """Check if a path is inside the Home Assistant config directory.

    Paths inside /config are considered safe by default since users have
    full control over files placed there. This prevents requiring manual
    allowlist_external_dirs configuration for YAML files in the config dir.
    """
    try:
        config_dir = Path(hass.config.config_dir).resolve()
        resolved_path = path.resolve()
        return resolved_path.is_relative_to(config_dir)
    except (ValueError, OSError):
        return False


async def load_page_by_name(
    hass: HomeAssistant,
    page_name: str,
    path: str | None = None,
) -> dict[str, Any]:
    """Load a specific page from a YAML file by its name.

    Args:
        hass: Home Assistant instance
        page_name: Name of the page to load (matches 'name' field in page definition)
        path: Optional path to the YAML file. Defaults to 'pixoo_pages.yaml' in config dir.

    Returns:
        Validated page dict ready to pass to the renderer.

    Raises:
        ServiceValidationError: If page not found or YAML file invalid.
    """
    if not isinstance(page_name, str) or not page_name.strip():
        raise ServiceValidationError("page_name must be a non-empty string")

    # Default to pixoo_pages.yaml in config directory
    yaml_path_str = path.strip() if path else "pixoo_pages.yaml"
    pages = await load_pages_from_yaml(hass, yaml_path_str)

    # Find page by name
    for page in pages:
        if page.get("name") == page_name.strip():
            return page

    # Page not found - list available names for helpful error
    available_names = [p.get("name") for p in pages if p.get("name")]
    if available_names:
        raise ServiceValidationError(
            f"Page '{page_name}' not found. Available pages: {', '.join(available_names)}"
        )
    raise ServiceValidationError(
        f"Page '{page_name}' not found. No named pages in '{yaml_path_str}'. "
        "Add a 'name' field to your page definitions."
    )


async def load_pages_from_yaml(hass: HomeAssistant, path: str) -> list[dict[str, Any]]:
    """Load and validate pages from a YAML file.

    Supported YAML formats:
    - list of pages
    - mapping with a top-level `pages:` list

    Returns a list of validated page dicts (ready to pass to the renderer).
    """

    if not isinstance(path, str) or not path.strip():
        raise ServiceValidationError("pages_yaml_path must be a non-empty string")

    yaml_path = _resolve_yaml_path(hass, path.strip())

    # Allow paths inside the HA config directory without explicit allowlisting,
    # or paths that are explicitly allowlisted via allowlist_external_dirs.
    if not _is_inside_config_dir(hass, yaml_path) and not hass.config.is_allowed_path(str(yaml_path)):
        raise ServiceValidationError(f"YAML path not allowlisted: {yaml_path}")

    if not yaml_path.exists() or not yaml_path.is_file():
        raise ServiceValidationError(f"YAML file not found: {yaml_path}")

    try:
        loaded: Any = await hass.async_add_executor_job(yaml_util.load_yaml, str(yaml_path))
    except Exception as err:
        raise ServiceValidationError(f"Failed to load YAML file: {err}") from err

    if loaded is None:
        return []

    pages_raw: Any
    if isinstance(loaded, list):
        pages_raw = loaded
    elif isinstance(loaded, dict) and "pages" in loaded:
        pages_raw = loaded.get("pages")
    else:
        raise ServiceValidationError(
            "Invalid pages YAML format: expected a list of pages or a mapping with top-level 'pages:'"
        )

    if not isinstance(pages_raw, list):
        raise ServiceValidationError("Invalid pages YAML format: 'pages' must be a list")

    pages: list[dict[str, Any]] = []
    for idx, item in enumerate(pages_raw):
        if not isinstance(item, dict):
            raise ServiceValidationError(f"Invalid page at index {idx}: expected a mapping")
        validated = PageModel.model_validate(item)
        pages.append(validated.model_dump(exclude_none=True))

    return pages
