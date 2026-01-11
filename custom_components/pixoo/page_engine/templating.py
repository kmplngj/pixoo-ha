"""Templating helpers for Pixoo Page Engine.

Phase 2 will implement HA-native template rendering using Template + render_complex.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template


_LOGGER = logging.getLogger(__name__)


def _looks_like_template(s: str) -> bool:
    return "{{" in s or "{%" in s


async def _render_variables_multi_pass(
    hass: HomeAssistant,
    variables: dict[str, Any],
    max_passes: int = 10,
) -> dict[str, Any]:
    """Render variables with multiple passes to resolve dependencies.
    
    Variables can reference other variables (e.g., battery_flow uses battery_charge).
    We render in multiple passes until no more templates remain or max_passes is reached.
    
    Key insight: Within each pass, we merge already-rendered values so that
    variables processed later in the iteration can use the rendered values
    from variables processed earlier in the same pass.
    """
    result = dict(variables)
    
    for pass_num in range(max_passes):
        changed = False
        new_result = {}
        
        for key, value in result.items():
            if isinstance(value, str) and _looks_like_template(value):
                try:
                    template = Template(value, hass)
                    # Merge result with new_result so we use already-rendered values
                    # from this pass. new_result takes precedence.
                    render_context = {**result, **new_result}
                    rendered = template.async_render(render_context, parse_result=False, strict=False)
                    rendered_str = str(rendered)
                    new_result[key] = rendered_str
                    # Check if the value actually changed (was rendered)
                    if rendered_str != value:
                        changed = True
                        _LOGGER.debug(
                            "Variable %s rendered in pass %d: %s -> %s",
                            key, pass_num + 1, value[:50] if len(value) > 50 else value,
                            rendered_str[:50] if len(rendered_str) > 50 else rendered_str
                        )
                except Exception as err:
                    _LOGGER.debug(
                        "Variable %s could not be rendered in pass %d: %s",
                        key, pass_num + 1, err
                    )
                    new_result[key] = value
            else:
                new_result[key] = value
        
        result = new_result
        
        # Check if any templates still remain
        has_templates = any(
            isinstance(v, str) and _looks_like_template(v)
            for v in result.values()
        )
        
        if not has_templates:
            _LOGGER.debug("All variables rendered after %d passes", pass_num + 1)
            break
        
        if not changed:
            # No progress made in this pass, remaining templates have unresolvable dependencies
            _LOGGER.debug(
                "No progress in pass %d, %d unrendered templates remain",
                pass_num + 1,
                sum(1 for v in result.values() if isinstance(v, str) and _looks_like_template(v))
            )
            break
    
    return result


async def async_render_complex(
    hass: HomeAssistant,
    value: Any,
    *,
    variables: dict[str, Any] | None = None,
) -> Any:
    """Render Jinja templates inside a complex (dict/list/scalar) structure.

    This is intentionally small and HA-native: it uses `Template.async_render`.
    """

    vars_ = variables or {}
    
    # Pre-render variables with multiple passes to resolve dependencies
    if vars_:
        vars_ = await _render_variables_multi_pass(hass, vars_)

    if isinstance(value, str) and _looks_like_template(value):
        template = Template(value, hass)
        # parse_result=False keeps output stable as string, which is what most
        # services and YAML payloads expect.
        return template.async_render(vars_, parse_result=False, strict=True)

    if isinstance(value, dict):
        return {
            k: await async_render_complex(hass, v, variables=vars_)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [await async_render_complex(hass, v, variables=vars_) for v in value]

    return value


# Backwards-compatible alias for early scaffolding (kept intentionally small).
async def render_templates(
    hass: HomeAssistant,
    value: Any,
    *,
    variables: dict[str, Any] | None = None,
) -> Any:
    return await async_render_complex(hass, value, variables=variables)
