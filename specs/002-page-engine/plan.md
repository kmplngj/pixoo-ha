#+#+#+#+---------------------------------------------------------------------
# Implementation Plan: 002-page-engine (Pixoo Page Engine)

**Branch**: `002-page-engine` | **Date**: 2026-01-01 | **Spec**: `specs/002-page-engine/spec.md`
**Input**: Feature specification from `specs/002-page-engine/spec.md`

Ziel dieses Plans: die Page-Engine (Components DSL + `pixoo.render_page` + optionale Rotation + `pixoo.show_message`) **HA-native, async-first und testgetrieben** in die bestehende `pixoo-ha` Integration einzubauen.

## Summary

Die Page Engine bringt ein „Mini-Dashboard“-Konzept in `pixoo-ha`:

- **P1**: `pixoo.render_page` rendert eine Page ad-hoc auf ein oder mehrere Pixoo-Geräte.
- **P2**: Optionaler Rotations-Controller zeigt eine konfigurierbare Page-Liste zyklisch.
- **P3**: `pixoo.show_message` zeigt temporär eine Override-Page und resümiert Rotation.

Technischer Ansatz:

- Zeichnen erfolgt über den bestehenden Buffer-Workflow (`draw_*` + `push_buffer`) und Image-Pipeline (`download_image()`), plus robustes **per-component best-effort** Verhalten.
- Templates werden **HA-native** gerendert (`Template.async_render` / `render_complex`).
- Multi-Device Targeting ist **best-effort** (ServiceCall schlägt nur fehl, wenn alle Targets fehlschlagen).

Referenz-Entscheidungen und Begründungen: `specs/002-page-engine/research.md`.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12+ (Home Assistant Core, Integration-Code)  
**Primary Dependencies**:
- Home Assistant Core (Custom Integration Patterns)
- `pixooasync` (Geräte-Client, Buffer Drawing, Pydantic Models)
- `aiohttp` (HTTP fetch in Integration; bereits Standard in HA)
- Pillow (Bildverarbeitung, CPU-bound via Executor)

**Storage**:
- Rotation-Konfiguration: ConfigEntry Options (enabled/default_duration + Page-Refs)
- Optionale Rotation-Pages: YAML-Datei unter `/config/` (Hybrid-Ansatz, siehe Spec Clarifications)
- Override-Zustand: in-memory pro ConfigEntry (Restore ist nicht zwingend; Verhalten ist temporär)

**Testing**:
- `pytest` + `pytest-homeassistant-custom-component`
- Async Tests (HA fixtures: `hass`, `config_entry`, Mocks für PixooAsync)

**Target Platform**: Home Assistant Core (Linux/Container/HAOS), Entwicklung auf macOS ok  
**Project Type**: Home Assistant Custom Integration (Python package under `custom_components/pixoo/`)  

**Performance Goals**:
- Render einer einfachen Page (Text/Rect ohne Remote-Bild) typischerweise < 2s bis „sichtbar“ im LAN
- Keine Event-Loop-Blocker; Pillow/Decoding im Executor

**Constraints**:
- Keine unbounded Downloads: Timeouts + Size-Limits + Content-Type Checks
- Allowlisting für `image.source.url/path` standardmäßig strikt, optional permissive (Spec FR-006a)
- Robustheit: per-component best-effort; ServiceCall nur Fehler wenn „nichts“ gerendert werden konnte

**Scale/Scope**:
- Mehrere Geräte parallel möglich (Multi-Target best-effort)
- Rotation als optionales Feature (P2), darf nicht dauerhaft Log-Spam erzeugen

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I - Async-First Architecture**:
- [x] All I/O operations use async/await
- [x] No blocking calls in event loop
- [x] Blocking operations wrapped with `hass.async_add_executor_job()`

**Principle II - Home Assistant Native Integration**:
- [x] Config flow implemented (bestehende Integration)
- [x] Device registry properly used (bestehende Integration)
- [x] Entity lifecycle methods implemented (bestehende Integration; für Rotation Tasks: Entry lifecycle)
- [x] Proper integration manifest (bestehende Integration)

**Principle III - Python Package Dependency**:
- [x] Uses `pixooasync` as sole device client package for Pixoo I/O
- [x] No direct device protocol implementation
- [x] Package version pinned in integration requirements

**Principle IV - Modern Python Standards**:
- [x] Python 3.12+ features used
- [x] Type hints present (project standard)
- [x] Uses pyproject.toml with modern tooling
- [x] Follows ruff formatting standards

**Principle V - AI Agent Friendly Code**:
- [x] Clear, descriptive naming
- [x] Comprehensive docstrings
- [x] Single Responsibility Principle followed
- [x] Logical directory structure

**Principle VI - Test-Driven Development**:
- [x] Tests written before implementation (siehe `specs/002-page-engine/tasks.md`)
- [x] Red-Green-Refactor cycle followed
- [x] Home Assistant test fixtures used

**Principle VII - Maintainability & Simplicity**:
- [x] YAGNI principle applied (Rotation optional; MVP startet bei render_page)
- [x] DRY principle without premature abstraction
- [x] Simple, clear code over clever solutions
- [x] Technical debt documented if introduced

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

Applied to this feature:

```text
specs/002-page-engine/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── README.md
│   └── page-services.md
└── tasks.md
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
custom_components/pixoo/
├── __init__.py
├── const.py
├── coordinator.py
├── services.yaml
├── utils.py
└── page_engine/                # neu (Feature-Code)
  ├── __init__.py
  ├── models.py               # Page/Component Modelle (Pydantic oder HA Schema-Models)
  ├── templating.py           # Template Rendering Helpers (render_complex, safe bool/color)
  ├── colors.py               # parse_color + CSS4 optional + hex + rgb
  ├── renderer.py             # Page -> Buffer Drawing + push
  ├── rotation.py             # optional: Rotation Controller (entry-bound background task)
  └── storage.py              # optional: YAML page loading / references

tests/
├── test_page_engine_models.py
├── test_page_engine_templating.py
├── test_page_engine_renderer.py
├── test_page_engine_services.py
└── test_page_engine_rotation.py
```

**Structure Decision**: Erweiterung der bestehenden Home Assistant Custom Integration unter `custom_components/pixoo/` um ein dediziertes, klar abgegrenztes Submodul `page_engine/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

**No violations expected**: Das Feature bleibt innerhalb der bestehenden Integration, ohne zusätzliche Subprojekte oder nicht-HA-native Abstraktionen.
