---

description: "Task list for Pixoo Page Engine implementation"
---

# Tasks: Pixoo Page Engine

**Input**: Design documents from `specs/002-page-engine/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Branch**: `002-page-engine`

**Tests**: ✅ Included (TDD requested by plan/constitution: tests first).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create feature module skeleton and wire it into the integration without implementing behavior yet.

- [x] T001 Create package skeleton in `custom_components/pixoo/page_engine/__init__.py`
- [x] T002 [P] Add `custom_components/pixoo/page_engine/models.py` (Page/Component model placeholders)
- [x] T003 [P] Add `custom_components/pixoo/page_engine/templating.py` (template helpers placeholders)
- [x] T004 [P] Add `custom_components/pixoo/page_engine/colors.py` (parse_color/render_color placeholders)
- [x] T005 [P] Add `custom_components/pixoo/page_engine/renderer.py` (renderer entrypoints placeholders)
- [x] T006 [P] Add `custom_components/pixoo/page_engine/rotation.py` (rotation controller placeholders)
- [x] T007 [P] Add `custom_components/pixoo/page_engine/storage.py` (optional YAML page loading placeholders)
- [x] T008 [P] Create templates folder `custom_components/pixoo/page_engine/templates/` with `README.md`
- [x] T009 Add new service definitions to `custom_components/pixoo/services.yaml` (stub entries for `render_page`, `show_message`, optional rotation control)
- [x] T010 [P] Add test module stubs: `tests/test_page_engine_models.py`, `tests/test_page_engine_render.py`, `tests/test_page_engine_rotation.py`, `tests/test_page_engine_services.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core primitives shared across ALL stories: models, templating, color parsing, safe image fetching, and error typing.

- [x] T011 Implement discriminated union models in `custom_components/pixoo/page_engine/models.py` (Page, ComponentsPage, TemplatePage, Component union)
- [x] T012 Implement `parse_color()` + `render_color()` in `custom_components/pixoo/page_engine/colors.py` (RGB list/tuple, hex, optional CSS4-name, template-string)
- [x] T013 Implement component bounds checks in `custom_components/pixoo/page_engine/renderer.py` (x/y + width/height; out-of-bounds => skip+log, FR-007b)
- [x] T014 Implement template rendering helpers in `custom_components/pixoo/page_engine/templating.py` using HA Template + `render_complex` (per `research.md` Decision 2)
- [x] T015 Implement safe image source resolution in `custom_components/pixoo/page_engine/renderer.py` (URL/path/base64) inkl. allowlisting strict default + optional permissive flag (FR-006a)
- [x] T016 [P] Ensure `custom_components/pixoo/utils.py` supports Page Engine needs (reuse existing `download_image()`; add helper(s) only if required)
- [x] T017 Define Page Engine exception strategy in `custom_components/pixoo/page_engine/__init__.py` (map to `ServiceValidationError` vs `HomeAssistantError`)
- [x] T018 [P] Add unit tests for model validation in `tests/test_page_engine_models.py` (valid pages, invalid discriminators, invalid component fields)
- [x] T019 [P] Add unit tests for templating in `tests/test_page_engine_render.py` (render_complex + template errors include field/component context)
- [x] T020 [P] Add unit tests for colors in `tests/test_page_engine_models.py` or `tests/test_page_engine_render.py` (rgb/hex/css4/template)

**Checkpoint**: Foundation ready – user story work can begin.

---

## Phase 3: User Story 1 - Seite ad-hoc rendern (Priority: P1) 🎯 MVP

**Goal**: A Home Assistant service `pixoo.render_page` that renders a page (text/rectangle/image) onto one or multiple Pixoo devices.

**Independent Test**: In HA tests, call the service with a components page and assert correct `PixooAsync` drawing calls + `push()`; template rendering resolves; invalid inputs raise `ServiceValidationError`.

### Tests for User Story 1 (TDD)

- [x] T021 [P] [US1] Add service schema validation tests in `tests/test_page_engine_services.py` (missing `page`, invalid types → `ServiceValidationError`)
- [x] T022 [P] [US1] Add renderer unit tests in `tests/test_page_engine_render.py` for:
  - text component → `draw_text()`
  - rectangle component → `draw_filled_rectangle()` / outline behavior
  - image component (URL) → `draw_image()`
- [x] T023 [P] [US1] Add per-component best-effort tests in `tests/test_page_engine_render.py` (one component fails, others still render; fail only if none succeed)
- [x] T024 [P] [US1] Add out-of-bounds skip+log tests in `tests/test_page_engine_render.py` (invalid coords do not fail whole page)
- [x] T025 [P] [US1] Add multi-target tests in `tests/test_page_engine_services.py` (zwei Targets: ein Gerät offline/raises → anderes wird trotzdem bedient; ServiceCall nur Fehler wenn alle fail)

### Implementation for User Story 1

- [x] T026 [US1] Implement `render_page` core entrypoint in `custom_components/pixoo/page_engine/renderer.py` (render → draw buffer ops → `push_buffer`/`push()`)
- [x] T027 [US1] Implement component rendering in `custom_components/pixoo/page_engine/renderer.py` (text/rectangle/image), inkl. z-order
- [x] T028 [US1] Implement robust per-component error handling in `custom_components/pixoo/page_engine/renderer.py` (FR-007a: continue where possible; service error only if none rendered)
- [x] T029 [US1] Register `pixoo.render_page` handler in `custom_components/pixoo/__init__.py` using existing entry resolution + HA targeting
- [x] T030 [US1] Integrate with per-device queueing in `custom_components/pixoo/__init__.py` (ServiceQueue FIFO; avoid flooding)
- [x] T031 [US1] Update `custom_components/pixoo/services.yaml` with final field definitions for `render_page` (target + `page` + `variables` + optional allowlist_mode)
- [x] T032 [US1] Update `specs/002-page-engine/quickstart.md` with a minimal `pixoo.render_page` example payload

**Checkpoint**: US1 works standalone and can be demoed from HA UI.

---

## Phase 4: User Story 2 - Seitenliste rotieren lassen (Priority: P2)

**Goal**: Rotation engine that can cycle through multiple pages with per-page durations and enable conditions.

**Independent Test**: With two pages configured, rotation advances and calls `render_page` with correct page selection; disabled pages are skipped; “all disabled” does not spam.

### Tests for User Story 2 (TDD)

- [x] T033 [P] [US2] Add rotation state machine unit tests in `tests/test_page_engine_rotation.py` (skip disabled, per-page duration, all disabled)
- [x] T034 [P] [US2] Add integration tests in `tests/test_page_engine_services.py` for enabling rotation via options (simulated) and verifying scheduled renders

### Implementation for User Story 2

- [x] T035 [US2] Implement RotationConfig parsing from config entry options in `custom_components/pixoo/page_engine/rotation.py` (per `data-model.md` + spec FR-020)
- [x] T036 [US2] Implement enable-condition evaluation (bool + template-to-bool) in `custom_components/pixoo/page_engine/rotation.py` using helpers in `custom_components/pixoo/page_engine/templating.py`
- [x] T037 [US2] Implement entry-bound scheduler in `custom_components/pixoo/page_engine/rotation.py` using HA lifecycle patterns (per `research.md` Decision 1)
- [x] T038 [US2] Wire rotation start/stop on entry setup/unload in `custom_components/pixoo/__init__.py` (store controller in `hass.data[DOMAIN][entry_id]`)
- [x] T039 [US2] Implement per-page duration scheduling in `custom_components/pixoo/page_engine/rotation.py` (dynamic reschedule)
- [x] T040 [US2] Implement “no active pages” behavior in `custom_components/pixoo/page_engine/rotation.py` (FR-012) with rate-limited logging
- [x] T041 [US2] Implement optional YAML page loading in `custom_components/pixoo/page_engine/storage.py` (load + validate) and reference it from `custom_components/pixoo/page_engine/rotation.py`
- [x] T042 [US2] (Optional) Add rotation control services in `custom_components/pixoo/__init__.py` + `custom_components/pixoo/services.yaml` (`pixoo.rotation_enable`, `pixoo.rotation_next`, `pixoo.rotation_reload_pages`)

**Checkpoint**: Rotation runs stably and is lifecycle-safe (unload cancels tasks).

---

## Phase 5: User Story 3 - Temporäre Override-Message (Priority: P3)

**Goal**: `pixoo.show_message` displays a temporary override page with last-wins policy, then resumes rotation if it was running.

**Independent Test**: Start rotation, call `show_message` for 10s, assert immediate render, then resume rotation; multiple messages cause last-wins replace.

### Tests for User Story 3 (TDD)

- [x] T043 [P] [US3] Add override policy tests in `tests/test_page_engine_rotation.py` (last_wins replaces and resets timer)
- [x] T044 [P] [US3] Add resume behavior tests in `tests/test_page_engine_services.py` (rotation resumes only if previously active)

### Implementation for User Story 3

- [x] T045 [US3] Implement override state in `custom_components/pixoo/page_engine/rotation.py` (oder dediziert `custom_components/pixoo/page_engine/override.py`) per `data-model.md`
- [x] T046 [US3] Implement `pixoo.show_message` handler in `custom_components/pixoo/__init__.py` using entry resolution + per-device queue
- [x] T047 [US3] Implement last-wins cancellation + timer reset in `custom_components/pixoo/page_engine/rotation.py` (cancel previous handle safely)
- [x] T048 [US3] Implement resume logic after expiry in `custom_components/pixoo/page_engine/rotation.py` (resume rotation only if it was active)
- [x] T049 [US3] Update `custom_components/pixoo/services.yaml` fields for `show_message` (target + `page` + `duration` + `variables` + optional allowlist_mode)

**Checkpoint**: Overrides are deterministic and do not leave rotation in a bad state.

---

## Phase 6: User Story 4 - Vorlagen nutzen (Priority: P4)

**Goal**: Provide built-in templates and allow rendering them like normal pages.

**Independent Test**: Render at least two built-in templates (“progress bar”, “now playing”) without extra user config; variable overrides change output.

### Tests for User Story 4 (TDD)

- [x] T050 [P] [US4] Add template resolution tests in `tests/test_page_engine_render.py` (template_name resolves, missing template raises `ServiceValidationError`)
- [x] T051 [P] [US4] Add two golden-path template tests in `tests/test_page_engine_render.py` (progress + now playing payload renders to expected draw calls)

### Implementation for User Story 4

- [x] T052 [US4] Define built-in template format and loader in `custom_components/pixoo/page_engine/storage.py` (or `custom_components/pixoo/page_engine/renderer.py`)
- [x] T053 [US4] Add at least two shipped templates under `custom_components/pixoo/page_engine/templates/`:
  - `progress_bar.yaml`
  - `now_playing.yaml`
- [x] T054 [US4] Implement `TemplatePage` rendering path in `custom_components/pixoo/page_engine/renderer.py` (load → merge vars → render components)
- [x] T055 [US4] Update `specs/002-page-engine/quickstart.md` with examples for rendering templates

**Checkpoint**: Templates are “batteries included” and behave like regular pages.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, performance, documentation, and compatibility.

- [x] T056 [P] Add structured logging across page engine in `custom_components/pixoo/page_engine/*.py` (include entry_id + component index/type)
- [x] T057 Add rate limiting/min-duration enforcement in `custom_components/pixoo/page_engine/rotation.py` (avoid 0s/too-fast spam)
- [x] T058 [P] Add documentation section to `README.md` (repo root) describing Page Engine services and examples
- [x] T059 [P] Add/Update `custom_components/pixoo/services.yaml` descriptions with clear guidance (buffer vs full render)
- [x] T060 Ensure services fail gracefully when Pixoo device is offline in `custom_components/pixoo/__init__.py` (SC-005)
- [x] T061 Run/adjust unit tests for stability: `tests/test_page_engine_*.py`
- [ ] T062 Run quickstart validation steps from `specs/002-page-engine/quickstart.md` (manual smoke test)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → blocks nothing but should be done first to establish files.
- **Foundational (Phase 2)** → BLOCKS all user stories.
- **US1 (Phase 3)** depends on Phase 2 only and is the MVP.
- **US2 (Phase 4)** depends on US1 (uses `render_page` to display pages).
- **US3 (Phase 5)** depends on US1+US2 (override must coexist with rotation).
- **US4 (Phase 6)** depends on US1 (templates ultimately render into components).
- **Polish (Phase 7)** depends on whichever stories are implemented.

### User Story Dependency Graph

- US1 → US2 → US3
- US1 → US4

Graph (high-level):

```text
US1 (render_page)
├─> US2 (rotation)
│    └─> US3 (show_message / override)
└─> US4 (templates)
```

### Parallel Opportunities

- In Phase 1, file scaffolding tasks marked [P] can run in parallel.
- In Phase 2, tests (T016–T017) can be developed in parallel with model implementation (T009–T015) as long as interfaces are agreed.
- In US1, test tasks (T018–T020) and parts of renderer implementation (T021–T023) can be split across different files.
- US4 template files (`progress_bar.yaml`, `now_playing.yaml`) can be authored in parallel with loader implementation.

---

## Parallel Example: User Story 1

- Contract/schema tests: `tests/test_page_engine_services.py`
- Renderer unit tests: `tests/test_page_engine_render.py`
- Service registration/wiring: `custom_components/pixoo/__init__.py`
- Renderer implementation: `custom_components/pixoo/page_engine/renderer.py`

---

## Parallel Example: User Story 2

- Rotation State Machine Tests: `tests/test_page_engine_rotation.py`
- Options Parsing + Scheduler: `custom_components/pixoo/page_engine/rotation.py`
- YAML Loader (optional): `custom_components/pixoo/page_engine/storage.py`

---

## Parallel Example: User Story 3

- Override Policy Tests: `tests/test_page_engine_rotation.py`
- Service Wiring: `custom_components/pixoo/__init__.py`
- Override Implementation: `custom_components/pixoo/page_engine/rotation.py`

---

## Parallel Example: User Story 4

- Template Resolution Tests: `tests/test_page_engine_render.py`
- Template Files: `custom_components/pixoo/page_engine/templates/progress_bar.yaml`, `custom_components/pixoo/page_engine/templates/now_playing.yaml`
- Loader Implementation: `custom_components/pixoo/page_engine/storage.py`

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (`pixoo.render_page`)
4. **STOP and VALIDATE**: Ensure US1 works independently (tests + manual service call)

### Incremental Delivery

- Add US2 rotation next (most visible feature)
- Add US3 override (notifications)
- Add US4 templates (UX polish)

---

## Report Summary (for reviewers)

- **MVP scope**: US1 only (`pixoo.render_page`)
- **Services added**: `pixoo.render_page`, `pixoo.show_message` (+ optional rotation control)
- **New module**: `custom_components/pixoo/page_engine/`
- **New tests**: `tests/test_page_engine_*.py`
