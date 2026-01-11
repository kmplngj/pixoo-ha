"""Tests for Pixoo Page Engine models and helpers."""

import pytest
from pydantic import ValidationError
from homeassistant.exceptions import ServiceValidationError, TemplateError


def test_page_engine_imports() -> None:
    # Ensure modules exist and are importable.
    from custom_components.pixoo.page_engine import colors, models, renderer, rotation, storage, templating  # noqa: F401


def test_models_validate_components_page_ok() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    page = PageModel.model_validate(
        {
            "page_type": "components",
            "components": [
                {"type": "text", "x": 0, "y": 0, "text": "HI"},
            ],
        }
    )

    assert page.page_type == "components"
    assert len(page.components) == 1
    assert page.components[0].type == "text"


def test_models_invalid_page_discriminator() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    with pytest.raises(ValidationError):
        PageModel.model_validate({"page_type": "nope"})


def test_models_invalid_component_missing_field() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    # Missing x
    with pytest.raises(ValidationError):
        PageModel.model_validate(
            {
                "page_type": "components",
                "components": [{"type": "text", "y": 0, "text": "HI"}],
            }
        )


def test_parse_color_rgb_list() -> None:
    from custom_components.pixoo.page_engine.colors import parse_color

    assert parse_color([1, 2, 3]) == (1, 2, 3)


def test_parse_color_hex_and_css_name() -> None:
    from custom_components.pixoo.page_engine.colors import parse_color

    assert parse_color("#FF0000") == (255, 0, 0)
    assert parse_color("red") == (255, 0, 0)


def test_raise_service_error_maps_validation_error() -> None:
    from custom_components.pixoo.page_engine import raise_service_error
    from custom_components.pixoo.page_engine.models import PageModel

    try:
        PageModel.model_validate({"page_type": "nope"})
    except ValidationError as err:
        with pytest.raises(ServiceValidationError):
            raise_service_error(err, context="page")
    else:  # pragma: no cover
        raise AssertionError("Expected ValidationError")


def test_raise_service_error_maps_template_error() -> None:
    from custom_components.pixoo.page_engine import raise_service_error

    with pytest.raises(ServiceValidationError):
        raise_service_error(TemplateError("boom"), context="template")


def test_models_validate_progress_bar_component() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    page = PageModel.model_validate(
        {
            "page_type": "components",
            "components": [
                {
                    "type": "progress_bar",
                    "x": 2,
                    "y": 28,
                    "width": 60,
                    "height": 6,
                    "progress": 75.5,
                    "bar_color": "#00FF00",
                },
            ],
        }
    )

    assert page.page_type == "components"
    assert len(page.components) == 1
    assert page.components[0].type == "progress_bar"
    assert page.components[0].progress == 75.5


def test_models_validate_progress_bar_with_thresholds() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    page = PageModel.model_validate(
        {
            "page_type": "components",
            "components": [
                {
                    "type": "progress_bar",
                    "x": 0,
                    "y": 0,
                    "width": 64,
                    "height": 8,
                    "progress": "sensor.battery_soc",
                    "color_thresholds": [
                        {"value": 80, "color": "#00FF00"},
                        {"value": 50, "color": "#FFFF00"},
                        {"value": 20, "color": "#FF0000"},
                    ],
                    "color_thresholds_transition": "smooth",
                },
            ],
        }
    )

    assert len(page.components[0].color_thresholds) == 3
    assert page.components[0].color_thresholds[0].value == 80


def test_models_validate_graph_component() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    page = PageModel.model_validate(
        {
            "page_type": "components",
            "components": [
                {
                    "type": "graph",
                    "x": 0,
                    "y": 32,
                    "width": 64,
                    "height": 32,
                    "entity_id": "sensor.temperature",
                    "hours": 24,
                    "style": "line",
                },
            ],
        }
    )

    assert page.components[0].type == "graph"
    assert page.components[0].entity_id == "sensor.temperature"
    assert page.components[0].hours == 24


def test_models_validate_graph_with_thresholds() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    page = PageModel.model_validate(
        {
            "page_type": "components",
            "components": [
                {
                    "type": "graph",
                    "x": 0,
                    "y": 0,
                    "width": 64,
                    "height": 32,
                    "entity_id": "sensor.power",
                    "style": "bar",
                    "color_thresholds": [
                        {"value": 5000, "color": "red"},
                        {"value": 2000, "color": "yellow"},
                        {"value": 0, "color": "green"},
                    ],
                },
            ],
        }
    )

    assert page.components[0].style == "bar"
    assert len(page.components[0].color_thresholds) == 3


def test_models_validate_icon_component() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    page = PageModel.model_validate(
        {
            "page_type": "components",
            "components": [
                {
                    "type": "icon",
                    "x": 0,
                    "y": 0,
                    "icon": "mdi:battery",
                    "size": 16,
                    "color": "#00FF00",
                },
            ],
        }
    )

    assert page.components[0].type == "icon"
    assert page.components[0].icon == "mdi:battery"
    assert page.components[0].size == 16


def test_models_validate_icon_with_thresholds() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    page = PageModel.model_validate(
        {
            "page_type": "components",
            "components": [
                {
                    "type": "icon",
                    "x": 24,
                    "y": 24,
                    "icon": "battery",
                    "size": 32,
                    "value": "sensor.battery_soc",
                    "color_thresholds": [
                        {"value": 80, "color": "green"},
                        {"value": 50, "color": "yellow"},
                        {"value": 20, "color": "red"},
                    ],
                    "color_thresholds_transition": "hard",
                },
            ],
        }
    )

    assert page.components[0].value == "sensor.battery_soc"
    assert len(page.components[0].color_thresholds) == 3
    assert page.components[0].color_thresholds_transition == "hard"


def test_models_validate_icon_invalid_size() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    # Icon size now allows any value from 1-64, so test an out-of-range value
    with pytest.raises(ValidationError):
        PageModel.model_validate(
            {
                "page_type": "components",
                "components": [
                    {
                        "type": "icon",
                        "x": 0,
                        "y": 0,
                        "icon": "mdi:battery",
                        "size": 100,  # Invalid: must be between 1 and 64
                    },
                ],
            }
        )


def test_models_validate_component_enabled_field() -> None:
    from custom_components.pixoo.page_engine.models import PageModel

    page = PageModel.model_validate(
        {
            "page_type": "components",
            "components": [
                {
                    "type": "text",
                    "x": 0,
                    "y": 0,
                    "text": "Hi",
                    "enabled": "{{ is_state('binary_sensor.test', 'on') }}",
                },
                {
                    "type": "icon",
                    "x": 0,
                    "y": 16,
                    "icon": "mdi:check",
                    "enabled": False,
                },
            ],
        }
    )

    assert page.components[0].enabled == "{{ is_state('binary_sensor.test', 'on') }}"
    assert page.components[1].enabled is False


# --- storage module tests ---


def test_is_inside_config_dir_returns_true_for_config_path(hass) -> None:
    """Paths inside HA config dir should be auto-allowed."""
    from pathlib import Path
    from custom_components.pixoo.page_engine.storage import _is_inside_config_dir

    config_path = Path(hass.config.config_dir) / "pixoo_pages.yaml"
    assert _is_inside_config_dir(hass, config_path) is True


def test_is_inside_config_dir_returns_false_for_external_path(hass) -> None:
    """Paths outside HA config dir should not be auto-allowed."""
    from pathlib import Path
    from custom_components.pixoo.page_engine.storage import _is_inside_config_dir

    external_path = Path("/etc/passwd")
    assert _is_inside_config_dir(hass, external_path) is False


def test_is_inside_config_dir_returns_false_for_traversal_attempt(hass) -> None:
    """Path traversal attempts should not be auto-allowed."""
    from pathlib import Path
    from custom_components.pixoo.page_engine.storage import _is_inside_config_dir

    traversal_path = Path(hass.config.config_dir) / ".." / "etc" / "passwd"
    assert _is_inside_config_dir(hass, traversal_path) is False
