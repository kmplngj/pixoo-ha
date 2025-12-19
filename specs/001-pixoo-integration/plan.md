# Implementation Plan: Divoom Pixoo Home Assistant Integration

**Branch**: `001-pixoo-integration` | **Date**: 2025-11-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-pixoo-integration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a platinum-grade Home Assistant integration for Divoom Pixoo LED displays (64x64, Max, Timebox Evo) that provides complete device control, notification system, built-in tool modes, and comprehensive monitoring through 40+ entities. The integration leverages the modern async `pixooasync` Python package (v1.0.0+) with Pydantic v2 models for type safety, supports automatic device discovery, handles multiple devices simultaneously, and implements all 105+ device methods including display control, drawing primitives, timer/alarm/stopwatch tools, sensor monitoring, and advanced configuration.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: 
- Home Assistant Core 2025.1+
- pixooasync v1.0.0+ (async Pixoo device client with Pydantic models)
- aiohttp 3.9+ (async HTTP client, HA dependency)
- Pillow 10.0+ (image processing and downsampling)
- Pydantic v2.0+ (data validation, included in pixooasync)

**Storage**: Home Assistant config entries (JSON), state machine for entity states  
**Testing**: pytest + pytest-homeassistant-custom-component + pytest-aiohttp  
**Target Platform**: Home Assistant OS / Container / Core (Linux, macOS, Windows via Python)  
**Project Type**: Home Assistant Custom Integration (single Python package structure)  
**Performance Goals**: 
- Entity state updates <500ms (SC-002, SC-019, SC-023)
- Image display <3s for 1MB files (SC-003)
- Sensor updates within defined intervals (1s to 5min tiered)
- Support 10+ concurrent devices without degradation (SC-004)

**Constraints**: 
- All operations must be async (non-blocking event loop)
- Device communication via pixooasync package only (no direct protocol)
- Image downloads: 10MB limit, 30s timeout, content-type validation
- Service call queue: unlimited FIFO with warning at 20+ depth
- Tool modes timer/alarm/stopwatch mutually exclusive

**Scale/Scope**: 
- 40+ entities per device (1 light, 1 media_player, 8 number, 7 switch, 7 select, 10 sensor, 4 button)
- 25 integration services (4 display, 7 drawing, 6 tool, 4 config, 4 animation)
- 7 media player services (play_media, play, pause, stop, next, previous, shuffle, repeat)
- 13 user stories covering basic control to advanced features (media player gallery added)
- Target: Silver tier HA quality scale minimum, Gold tier aspirational

## Constitution Check

The constitution defines rules for making implementation choices. After the research
phase, evaluate each requirement (skim first, mark each ✅/❌).

### Principle I: Async-First Architecture

**Status**: [✅] COMPLIANT / [ ] NEEDS WORK / [ ] NOT APPLICABLE

**Evidence**: FR-024 mandates PixooAsync class for all device operations. All entity platforms, services, and coordinator updates will use async/await. No blocking operations in event loop (FR-006 uses aiohttp for downloads, Pillow operations on executor). Success criteria SC-002, SC-019, SC-023 measure async performance targets.

### Principle II: HA Native Integration

**Status**: [✅] COMPLIANT / [ ] NEEDS WORK / [ ] NOT APPLICABLE

**Evidence**: FR-001 requires config flow implementation. FR-003 uses HA device registry. FR-046-055 define 10 sensor types following HA conventions. FR-021 mandates HA entity naming conventions. FR-002 implements SSDP discovery. 40+ entities across 7 platforms (light, media_player, number, switch, select, sensor, button) follow HA entity patterns. FR-066 to FR-075 implement media player with standard HA MediaPlayerEntity pattern.

### Principle III: Python Package Dependency (pixooasync)

**Status**: [✅] COMPLIANT / [ ] NEEDS WORK / [ ] NOT APPLICABLE

**Evidence**: FR-025 states "all Pixoo device communication must use the pixooasync package exclusively". FR-024 specifies PixooAsync class. Technical Foundation section documents 105+ methods and 15 Pydantic models from pixooasync. No direct protocol implementation allowed.

### Principle IV: Modern Python Standards

**Status**: [✅] COMPLIANT / [ ] NEEDS WORK / [ ] NOT APPLICABLE

**Evidence**: Python 3.12+ required in Technical Context. FR-026 requires Pydantic v2 for validation. Entity mapping documents 15 Pydantic models (DeviceInfo, SystemConfig, WeatherInfo, etc). Type hints mandatory per AI Agent Friendly principle. Uses modern async/await (not callbacks).

### Principle V: AI Agent Friendly Code

**Status**: [✅] COMPLIANT / [ ] NEEDS WORK / [ ] NOT APPLICABLE

**Evidence**: Comprehensive documentation includes spec (687 lines), ENTITY_MAPPING.md (quick reference), ENHANCEMENT_SUMMARY.md (evolution). 40+ entities clearly defined with fields and relationships. 65 functional requirements organized by category. Internal Components section details architecture. Type-safe enums and Pydantic models document contracts.

### Principle VI: Test-Driven Development

**Status**: [✅] COMPLIANT / [ ] NEEDS WORK / [ ] NOT APPLICABLE

**Evidence**: 30 success criteria defined (SC-001 to SC-030) with measurable outcomes. FR-061 requires unit tests for entity platforms. FR-062 requires integration tests. pytest-homeassistant-custom-component framework specified. Performance targets measurable (SC-002: <500ms, SC-003: <3s).

### Principle VII: Maintainability & Simplicity

**Status**: [✅] COMPLIANT / [ ] NEEDS WORK / [ ] NOT APPLICABLE

**Evidence**: Single integration project (not multi-repo). Clear requirements organized by feature (65 FRs in 8 categories). Leverages pixooasync package (don't reinvent protocol). FR-005 enables/disables features via config. Edge cases documented (25 cases). No overengineering - uses HA patterns (coordinator, entity platforms, config flow).

## Project Structure

### Home Assistant Custom Integration Structure

```
custom_components/pixoo/
├── __init__.py              # Integration setup, async_setup_entry, async_unload_entry
├── manifest.json            # Integration metadata, dependencies, version
├── config_flow.py           # ConfigFlow class, SSDP discovery, options flow
├── const.py                 # Domain, entity IDs, service names, defaults
├── coordinator.py           # PixooDataUpdateCoordinator (tiered polling strategy)
├── entity.py                # PixooEntity base class (common attributes, device_info)
├── light.py                 # Light platform (power, brightness) - 1 entity
├── media_player.py          # Media player platform (image gallery/slideshow) - 1 entity
├── number.py                # Number entities (brightness, timer, alarm, scoreboard, gallery) - 8 entities
├── switch.py                # Switch entities (tools, mirror mode) - 7 entities
├── select.py                # Select entities (channel, rotation, temperature, formats) - 7 entities
├── sensor.py                # Sensor entities (device info, network, system, weather, time) - 10 entities
├── button.py                # Button entities (dismiss notification, buzzer, buffer ops) - 4 entities
├── services.yaml            # Service definitions with schemas
├── strings.json             # UI strings for config flow and entity states
└── translations/            # Localization files
    └── en.json              # English translations

tests/
├── __init__.py              # Test package
├── conftest.py              # pytest fixtures (hass, config_entry, mock_pixoo)
├── test_config_flow.py      # Config flow tests (user, discovery, options)
├── test_init.py             # Integration lifecycle tests
├── test_coordinator.py      # Data coordinator tests (polling, updates)
├── test_light.py            # Light platform tests
├── test_media_player.py     # Media player tests (playlist, shuffle, repeat, navigation)
├── test_number.py           # Number entities tests
├── test_switch.py           # Switch entities tests
├── test_select.py           # Select entities tests
├── test_sensor.py           # Sensor entities tests
├── test_button.py           # Button entities tests
└── test_services.py         # Service tests (display, drawing, tool, animation)

docs/
├── README.md                # Integration documentation for users
├── DEVELOPMENT.md           # Developer setup and contribution guide
├── SERVICES.md              # Service documentation with examples
└── ENTITY_REFERENCE.md      # Entity descriptions and attributes

.github/
├── workflows/
│   └── ci.yml               # CI/CD: pytest, ruff, mypy
└── copilot-instructions.md  # AI agent context (pixooasync, HA patterns)
```

**Key Files**:
- `manifest.json`: Declares pixooasync dependency, SSDP config, integration metadata
- `coordinator.py`: Implements tiered sensor updates (device 1x, network 60s, system 30s, weather 5min, tools 1s)
- `config_flow.py`: Handles SSDP discovery (FR-002), manual entry, options for feature toggles (FR-005)
- Entity platforms: Each file implements 1-10 entities following HA conventions
- `services.yaml`: Defines 25 services with parameter schemas and validation

**Testing Structure**:
- Unit tests per entity platform (pytest fixtures mock PixooAsync)
- Integration tests with HomeAssistant test harness
- Service tests validate parameter schemas and execution
- Config flow tests cover discovery and manual flows

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations identified. All design decisions comply with the 7 principles.

---

## Phase 0: Research (Completed ✅)

**Status**: Complete  
**Date**: 2025-11-10  
**Deliverable**: `research.md`

### Topics Researched

1. **Home Assistant Config Flow Patterns** ✅
   - SSDP discovery with fallback to manual entry
   - Options flow for feature toggles
   - Reference: esphome, hue, sonos integrations

2. **Device Discovery for Pixoo** ✅
   - pixooasync does NOT include discovery
   - Divoom devices broadcast SSDP (manufacturer: "Divoom")
   - Use HA's built-in SSDP helper

3. **Coordinator Update Strategies** ✅
   - Multiple coordinators for tiered polling (recommended)
   - Device coordinator (once), System (30s), Tool (1s), Gallery (10s)
   - Alternative: Single coordinator with internal timing

4. **Button Entity Implementation** ✅
   - ButtonEntity base class with async_press() method
   - Stateless entities with last-pressed timestamp
   - Example: Neato vacuum dismiss_alert button

5. **Service Schema Validation** ✅
   - HA uses voluptuous (not Pydantic) for service schemas
   - Pydantic can be used internally for extra validation
   - services.yaml defines voluptuous schemas

6. **Image Processing with Pillow** ✅
   - Use hass.async_add_executor_job() for CPU-bound operations
   - Download with aiohttp (async), process in executor (sync)
   - Automatic resizing with LANCZOS resampling

### Key Decisions

- **Discovery**: SSDP via manifest.json configuration
- **Coordinators**: Multiple coordinators (device, system, tool, gallery)
- **Button Pattern**: ButtonEntity with async_press() restoring previous channel
- **Service Validation**: voluptuous schemas with optional Pydantic internally
- **Image Processing**: aiohttp download → executor processing → async upload
- **Polling**: Tiered intervals (device once, network 60s, system 30s, weather 5min, tools 1s)

### Constitution Compliance

All research findings align with constitution principles:
- ✅ Async operations (executor for blocking code)
- ✅ HA native patterns (coordinators, config flow, SSDP)
- ✅ Leverages pixooasync package (no protocol reimplementation)

---

## Phase 1: Design & Contracts (Completed ✅)

**Status**: Complete  
**Date**: 2025-11-10  
**Deliverables**: 
- `data-model.md` (entity models, coordinator data structures)
- `contracts/` (service schemas and parameters)
- `quickstart.md` (developer onboarding guide)

### Data Model Defined

**Entity Platforms**: 6 platforms, 40+ entities
- Light (1): Power and brightness control
- Number (8): Timer, alarm, scoreboard, gallery, brightness
- Switch (7): Tools, mirror mode, 24h format
- Select (7): Channel, rotation, temperature, time format, pages
- Sensor (10): Device info, network, system, weather, time, tools
- Button (4): Dismiss notification, buzzer, buffer operations

**Coordinators**: 4 coordinators with tiered updates
- PixooDeviceCoordinator: One-time device info
- PixooSystemCoordinator: 30s (network, system, time) + 5min (weather)
- PixooToolCoordinator: 1s (active channel, tool states)
- PixooGalleryCoordinator: 10s (animations, clocks, visualizers)

**Pydantic Models**: 15 models from pixooasync
- DeviceInfo, NetworkStatus, SystemConfig, WeatherInfo, TimeInfo
- AlarmConfig, TimerConfig, StopwatchConfig, ScoreboardConfig, NoiseMeterConfig
- Animation, PlaylistItem, Location, WhiteBalance

**Config Entry**: JSON storage in HA config entries
- Device data: host, unique_id, title, options
- Runtime data: coordinators, pixoo_client

### Contracts Defined

**Display Services** (4/4 complete): `contracts/display-services.md`
- `pixoo.display_image`: Show image from URL with validation
- `pixoo.display_gif`: Show animated GIF
- `pixoo.display_text`: Scrolling/static text with positioning
- `pixoo.clear_display`: Reset display to default channel

**Remaining Services** (21/25 pending):
- Drawing services (7): pixel, text, line, rectangle, image, buffer ops
- Tool services (6): timer, alarm, stopwatch, scoreboard, buzzer
- Configuration services (4): white balance, weather, timezone, time
- Animation services (4): play, stop, playlist, list

**Service Patterns**:
- Voluptuous schemas for HA validation
- aiohttp for async downloads with timeout
- Pillow processing in executor
- FIFO queue per device with 20+ depth warning
- Error handling with HomeAssistantError and ServiceValidationError

### Developer Documentation

**Quickstart Guide**: `quickstart.md`
- Development environment setup (uv or pip)
- Project structure overview
- Running tests (unit, integration, coverage)
- Manual testing with HA dev server
- Common tasks (add entity, add service, update coordinator)
- Troubleshooting common issues
- Development workflow and code quality

---

## Phase 2: Implementation (Pending ⏳)

**Next Steps**:

1. **Update Agent Context** (Run `update-agent-context.sh copilot`)
   - Add pixooasync package context
   - Document HA integration patterns
   - Add Pydantic v2 and Pillow usage notes

2. **Create Integration Skeleton**
   - `manifest.json` with dependencies and SSDP
   - `__init__.py` with async_setup_entry
   - `const.py` with constants
   - `strings.json` with translations

3. **Implement Config Flow**
   - SSDP discovery flow
   - Manual entry flow
   - Options flow for feature toggles
   - Tests for all flows

4. **Implement Coordinators**
   - PixooDeviceCoordinator (one-time)
   - PixooSystemCoordinator (30s/5min tiered)
   - PixooToolCoordinator (1s)
   - PixooGalleryCoordinator (10s)
   - Tests with mock PixooAsync

5. **Implement Entity Platforms**
   - Light platform (power, brightness)
   - Number entities (8 entities)
   - Switch entities (7 entities)
   - Select entities (7 entities)
   - Sensor entities (10 entities)
   - Button entities (4 entities)
   - Tests per platform

6. **Implement Services**
   - Display services (4 services)
   - Drawing services (7 services)
   - Tool services (6 services)
   - Configuration services (4 services)
   - Animation services (4 services)
   - Service tests with mocks

7. **Integration Testing**
   - End-to-end tests with test harness
   - Manual testing with physical device
   - Performance validation (SC-002, SC-003, SC-004, etc.)
   - Edge case testing (25 edge cases from spec)

---

**Plan Status**: ✅ Complete through Phase 1  
**Ready for**: Agent context update and implementation  
**Last Updated**: 2025-11-10
