<!--
Sync Impact Report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version Change: INITIAL (0.0.0) → 1.0.0 (Initial Release)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATED PRINCIPLES:
  ✓ I. Async-First Architecture
  ✓ II. Home Assistant Native Integration
  ✓ III. Python Package Dependency
  ✓ IV. Modern Python Standards
  ✓ V. AI Agent Friendly Code
  ✓ VI. Test-Driven Development
  ✓ VII. Maintainability & Simplicity

ADDED SECTIONS:
  ✓ Home Assistant Quality Standards
  ✓ Development Workflow
  ✓ Governance

TEMPLATE CONSISTENCY STATUS:
  ✅ plan-template.md - Updated (Constitution Check section aligned)
  ✅ spec-template.md - Verified (Requirements structure compatible)
  ✅ tasks-template.md - Verified (Task organization compatible)
  ⚠  Command prompts - Review recommended (ensure HA-specific guidance)

FOLLOW-UP ACTIONS:
  □ Review .github/prompts/*.md for Home Assistant-specific guidance
  □ Consider creating HA integration quality checklist
  □ Add Home Assistant testing guidelines document
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-->

# Pixoo Home Assistant Integration Constitution

## Core Principles

### I. Async-First Architecture

**All I/O operations MUST be asynchronous.** The integration shall leverage Python's async/await paradigm throughout:

- All network calls to Pixoo devices MUST use async HTTP clients (aiohttp)
- All Home Assistant API interactions MUST use async methods
- Entity state updates MUST use `async_write_ha_state()`
- Platform setup MUST use `async_setup_entry()` and `async_forward_entry_setups()`
- Blocking operations MUST be wrapped with `hass.async_add_executor_job()`

**Rationale**: Home Assistant's event loop architecture requires non-blocking operations. Async-first design prevents UI freezes, ensures responsive automation execution, and allows concurrent device management.

### II. Home Assistant Native Integration

**Integration MUST follow Home Assistant architectural patterns and quality standards:**

- Config flow MUST be implemented for user-friendly setup
- Discovery MUST be supported where technically feasible (SSDP/mDNS)
- Entities MUST properly implement lifecycle methods (`async_added_to_hass`, `async_will_remove_from_hass`)
- Device registry MUST be used to represent physical Pixoo devices
- Entry unloading MUST properly clean up resources (`async_unload_entry`)
- Home Assistant component types MUST be used correctly (light, sensor, number, select, etc.)
- Integration manifest MUST declare correct `integration_type`, `iot_class`, and dependencies

**Rationale**: Following Home Assistant patterns ensures proper integration with the ecosystem, enables features like device management and diagnostics, and meets user expectations for quality integrations.

### III. Python Package Dependency

**Integration MUST use the official `pixoo` Python package as its sole device communication library:**

- All Pixoo device communication MUST go through the `pixoo` package APIs
- Direct protocol implementation is FORBIDDEN (no raw TCP/HTTP to devices)
- If `pixoo` package lacks needed features, contribute upstream first
- Wrapper abstractions around `pixoo` are permitted for async adaptation only
- Package version MUST be pinned in manifest `requirements` array

**Rationale**: Using the official package ensures protocol correctness, benefits from community maintenance, reduces code duplication, and concentrates effort on integration logic rather than device protocol implementation.

### IV. Modern Python Standards

**Code MUST follow contemporary Python development practices:**

- Python 3.12+ language features MUST be utilized
- Type hints MUST be present on all functions, methods, and class attributes
- Pydantic models SHOULD be used for configuration validation where appropriate
- Project MUST use `pyproject.toml` with modern build system (uv preferred)
- Code MUST pass `mypy --strict` type checking
- Formatting MUST follow `ruff` standards (replaces black + isort + flake8)
- Dependencies MUST follow Semantic Versioning with explicit version constraints

**Rationale**: Modern tooling and standards improve code quality, catch errors early through static analysis, ensure consistent style, and make the codebase welcoming to contributors familiar with contemporary Python development.

### V. AI Agent Friendly Code

**Code structure MUST facilitate AI-assisted development and maintenance:**

- Clear, descriptive names for all functions, classes, methods, and variables
- Comprehensive docstrings using Google or NumPy style (consistently chosen)
- Single Responsibility Principle: one purpose per function/class
- Explicit is better than implicit: avoid "magic" behavior
- Configuration and constants MUST be centralized in `const.py`
- Directory structure MUST be logical and predictable (`custom_components/pixoo/`)
- Each entity type MUST be in its own module file (e.g., `light.py`, `sensor.py`)

**Rationale**: AI assistants perform better with explicit, well-documented code following clear patterns. This accelerates development, reduces maintenance burden, and ensures code remains understandable as the project evolves.

### VI. Test-Driven Development

**Testing MUST precede implementation for all non-trivial features:**

- Acceptance tests MUST be written first based on user stories
- Tests MUST fail initially (Red phase)
- Implementation proceeds only after test approval (Green phase)
- Refactoring MUST maintain passing tests (Refactor phase)
- Integration with Home Assistant test fixtures MUST be utilized (`hass`, `config_entry`)
- Mock Pixoo device responses for deterministic testing
- Async test patterns MUST use `pytest-aiohttp` and `pytest-homeassistant-custom-component`

**Rationale**: TDD ensures requirements are clear before coding begins, provides confidence during refactoring, serves as living documentation, and catches regressions early. The Red-Green-Refactor cycle prevents over-engineering.

### VII. Maintainability & Simplicity

**Favor simplicity and clarity over cleverness:**

- YAGNI: implement only what's needed now, not what might be needed later
- DRY principle: eliminate duplication through abstraction only when pattern emerges
- Comments MUST explain "why", not "what" (code explains "what")
- Complex logic MUST be broken into smaller, named functions
- Error messages MUST be user-friendly and actionable
- Breaking changes MUST be documented in CHANGELOG with migration guidance
- Technical debt MUST be tracked and justified when introduced

**Rationale**: Simple code is easier to understand, debug, and modify. Long-term maintainability trumps short-term cleverness. Open source projects thrive when contributors can quickly understand and safely modify the codebase.

## Home Assistant Quality Standards

**Integration SHALL target Home Assistant Quality Scale Silver tier minimum:**

- **Config Flow**: User-friendly setup without YAML configuration
- **Diagnostics**: Implement `async_get_config_entry_diagnostics` for troubleshooting
- **Documentation**: Complete docs covering setup, configuration, and troubleshooting
- **Entity Naming**: Follow naming conventions (device name + entity type, no integration name)
- **Reconfiguration**: Support reconfigure flow for changing device settings
- **Reauthentication**: Handle authentication failures gracefully (if applicable)
- **Unique IDs**: All entities MUST have stable unique IDs for persistence
- **Device Info**: Proper device registry entries with model, manufacturer, SW version
- **Translations**: All user-facing strings MUST use translations (`strings.json`)

**Progress tracking**: Quality scale compliance MUST be tracked in `.quality_scale.yaml`

**Performance expectations**:
- Entity updates MUST complete within 500ms under normal conditions
- Initial device connection MUST raise `ConfigEntryNotReady` if device unreachable
- Network timeouts MUST be reasonable (5-10s) and user-configurable where appropriate

**Open source requirements**:
- MIT or Apache 2.0 license (compatible with Home Assistant)
- Contribution guidelines MUST be provided (`CONTRIBUTING.md`)
- Issue templates for bugs and feature requests
- Clear code of conduct

## Development Workflow

**Branch Strategy**:
- `main` branch: stable, release-ready code
- Feature branches: `###-feature-name` pattern (issue number + description)
- Hotfix branches: `hotfix-issue-number` for critical production fixes

**Commit Messages**:
- Follow Conventional Commits: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`
- Examples: `feat(light): add brightness control`, `fix(config_flow): handle timeout error`

**Pull Request Requirements**:
- All tests MUST pass (no exceptions)
- Type checking MUST pass (`mypy --strict`)
- Code formatting MUST pass (`ruff check && ruff format --check`)
- Home Assistant integration validation MUST pass (`hassfest`)
- Description MUST reference related issue/spec
- Breaking changes MUST be clearly documented

**Review Process**:
- Constitution compliance verification (principles honored)
- Code readability and maintainability assessment
- Test coverage evaluation (aim for >80% for critical paths)
- Home Assistant patterns verification
- Security review for authentication/network code

**Release Process**:
- Version follows Semantic Versioning 2.0.0
- CHANGELOG.md MUST be updated before release
- Version bumps: MAJOR (breaking), MINOR (features), PATCH (fixes)
- GitHub releases with release notes
- HACS compatibility maintained

## Governance

**Constitutional Authority**: This constitution supersedes all other project practices. When conflicts arise, constitution principles take precedence.

**Amendment Process**:
1. Proposed amendments MUST be documented with rationale
2. Impact analysis MUST identify affected code, templates, and workflows
3. Community discussion period (minimum 7 days for major changes)
4. Approval required before implementation
5. Migration plan MUST be provided for backward-incompatible changes
6. Version MUST be incremented according to semantic versioning rules

**Compliance Verification**:
- All pull requests MUST verify constitution compliance
- Deviations MUST be explicitly justified and documented
- Complexity violations require architectural review
- Templates (plan, spec, tasks) MUST align with principles

**Runtime Development Guidance**:
- Use Home Assistant Developer Documentation as primary reference
- Consult `pixoo` package documentation for device capabilities  
- Leverage AI agents (GitHub Copilot, etc.) while maintaining code quality
- When uncertain, favor explicit over implicit, simple over complex

**Versioning Policy**:
- MAJOR: Breaking changes (incompatible config, entity IDs, or API changes)
- MINOR: New features, platforms, or backward-compatible improvements
- PATCH: Bug fixes, documentation updates, non-functional improvements

**Quality Gates**:
- Bronze tier: Initial release minimum
- Silver tier: Target within 6 months
- Gold tier: Aspirational (requires comprehensive testing + advanced features)

**Version**: 1.0.0 | **Ratified**: 2025-11-10 | **Last Amended**: 2025-11-10
