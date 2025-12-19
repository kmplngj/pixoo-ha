# Implementation Tasks: Divoom Pixoo Home Assistant Integration

**Feature**: 001-pixoo-integration  
**Branch**: `001-pixoo-integration`  
**Generated**: 2025-11-10  
**Total Tasks**: 89 tasks across 15 phases

## Overview

This document breaks down the implementation into executable tasks organized by user story. Each user story represents an independently testable increment that delivers value.

**MVP Scope**: User Story 1 (Basic Device Setup and Control) - 21 tasks  
**Full Feature**: All 13 user stories - 89 tasks

## Implementation Strategy

**Approach**: MVP-first with incremental story delivery

1. **Phase 1-2**: Setup & Foundation (11 tasks) - Blocking prerequisites for all stories
2. **Phase 3**: User Story 1 (P1) - MVP (21 tasks) - Basic setup and control
3. **Phase 4-5**: User Stories 2, 7 (P1) - Core automation features (20 tasks)
4. **Phase 6-12**: User Stories 3, 5, 6, 8, 9, 10, 11, 13 (P2) - Enhanced features (29 tasks)
5. **Phase 13-14**: User Stories 4, 12 (P3) - Advanced features (6 tasks)
6. **Phase 15**: Polish & Cross-Cutting (2 tasks)

Each phase represents a complete, independently testable increment.

---

## Phase 1: Setup (5 tasks)

**Goal**: Initialize project structure and dependencies

**Duration**: ~1 hour

### Tasks

- [X] T001 Create custom_components/pixoo/ directory structure per plan.md
- [X] T002 Create manifest.json with pixooasync v1.0.0+ dependency, SSDP config, HA version requirement
- [X] T003 Create const.py with DOMAIN, entity prefixes, service names, default values
- [X] T004 Create strings.json with config flow UI strings and entity state translations
- [X] T005 Create translations/en.json with English translations for all UI strings

---

## Phase 2: Foundation (6 tasks)

**Goal**: Implement shared infrastructure required by all user stories

**Duration**: ~3 hours

**Dependencies**: Phase 1 complete

### Tasks

- [X] T006 Implement PixooEntity base class in entity.py with device_info, availability, coordinator listener
- [X] T007 [P] Implement DeviceCoordinator in coordinator.py with device info polling (once at startup)
- [X] T008 [P] Implement SystemCoordinator in coordinator.py with system/network polling (30s system, 60s network)
- [X] T009 [P] Implement ToolCoordinator in coordinator.py with tool state polling (1s when active)
- [X] T010 [P] Implement GalleryCoordinator in coordinator.py with animation list polling (on demand)
- [X] T011 Create utils.py with download_image() helper (aiohttp download, Pillow processing in executor)

**Parallel Opportunity**: T007-T010 can be implemented simultaneously (4 independent coordinators)

---

## Phase 3: User Story 1 - Basic Device Setup and Control (P1) (21 tasks)

**Goal**: MVP - Users can add device and control power, brightness, channel

**Duration**: ~8 hours

**Dependencies**: Phase 2 complete

**Independent Test**: 
- Add device through config flow (SSDP or manual IP)
- Verify light entity appears with brightness control
- Verify select entities (channel) work correctly
- Test availability handling when device unreachable

**Value Delivered**: Minimum viable product - device is controllable in Home Assistant

### Config Flow Setup

- [X] T012 [US1] Implement ConfigFlow class in config_flow.py with async_step_user (manual IP entry)
- [X] T013 [US1] Implement async_step_ssdp in config_flow.py for automatic device discovery
- [X] T014 [US1] Implement _test_connection() helper in config_flow.py using pixoo.get_device_info()
- [X] T015 [US1] Implement async_step_reauth in config_flow.py for IP address changes

### Integration Setup

- [X] T016 [US1] Implement async_setup_entry in __init__.py with coordinator initialization
- [X] T017 [US1] Implement async_unload_entry in __init__.py with cleanup
- [X] T018 [US1] Register light platform in async_setup_entry (__init__.py)
- [X] T019 [US1] Register select platform in async_setup_entry (__init__.py)

### Entity Implementations

- [X] T020 [P] [US1] Create PixooLight class in light.py with async_turn_on/async_turn_off, brightness control
- [X] T021 [P] [US1] Create PixooChannelSelect class in select.py for channel selection (Faces, Cloud, Visualizer, Custom)
- [X] T022 [P] [US1] Create PixooRotationSelect class in select.py for screen rotation (0, 90, 180, 270)
- [X] T023 [P] [US1] Create PixooTemperatureModeSelect class in select.py for temperature unit (Celsius, Fahrenheit)
- [X] T024 [P] [US1] Create PixooTimeFormatSelect class in select.py for time format (12h, 24h)

### Testing (US1)

- [X] T025 [P] [US1] Create conftest.py with hass fixture, mock_pixoo fixture, config_entry fixture
- [X] T026 [P] [US1] Create test_config_flow.py with tests for user flow, SSDP discovery, reauth
- [X] T027 [P] [US1] Create test_init.py with integration lifecycle tests (setup, unload)
- [X] T028 [P] [US1] Create test_coordinator.py with coordinator polling tests (all 4 coordinators)
- [X] T029 [P] [US1] Create test_light.py with light entity tests (turn_on, turn_off, brightness)
- [X] T030 [P] [US1] Create test_select.py with select entity tests (channel, rotation, temperature, time format)

**Parallel Opportunity**: T020-T024 (entity implementations), T025-T030 (tests) can be done simultaneously

---

## Phase 4: User Story 2 - Display Custom Content (P1) (12 tasks)

**Goal**: Enable image/GIF/text display services

**Duration**: ~4 hours

**Dependencies**: Phase 3 complete (needs integration setup)

**Independent Test**:
- Call display_image service with local file and URL
- Call display_gif service with animation
- Call display_text service with message
- Verify downloads respect 10MB limit and 30s timeout
- Test error handling for invalid files

**Value Delivered**: Core automation capability - display custom content

### Service Implementation

- [X] T031 [P] [US2] Create services.yaml with display_image schema (url, entity_id)
- [X] T032 [P] [US2] Add display_gif schema to services.yaml (url, entity_id)
- [X] T033 [P] [US2] Add display_text schema to services.yaml (text, color, scroll_direction, entity_id)
- [X] T034 [P] [US2] Add clear_display schema to services.yaml (entity_id)
- [X] T035 [US2] Implement async_setup_services in __init__.py with service registration
- [X] T036 [P] [US2] Implement handle_display_image service handler in __init__.py with download_image, pixoo.display_image_from_bytes
- [X] T037 [P] [US2] Implement handle_display_gif service handler in __init__.py with download_image, pixoo.display_gif_from_bytes
- [X] T038 [P] [US2] Implement handle_display_text service handler in __init__.py with pixoo.send_text
- [X] T039 [P] [US2] Implement handle_clear_display service handler in __init__.py with pixoo.clear_display

### Testing (US2)

- [X] T040 [P] [US2] Create test_services.py with display_image service tests (local, URL, validation)
- [X] T041 [P] [US2] Add display_gif service tests to test_services.py
- [X] T042 [P] [US2] Add display_text and clear_display service tests to test_services.py

**Parallel Opportunity**: T031-T034 (service schemas), T036-T039 (handlers), T040-T042 (tests) can be done simultaneously

---

## Phase 5: User Story 7 - Notification and Alert System (P1) (8 tasks)

**Goal**: Persistent notifications with acknowledgment and buzzer

**Duration**: ~3 hours

**Dependencies**: Phase 4 complete (needs display services)

**Independent Test**:
- Trigger notification with buzzer
- Verify notification persists
- Press dismiss button
- Verify display returns to previous state

**Value Delivered**: Practical automation - washing machine alerts, reminders

### Entity Implementation

- [X] T043 [US7] Register button platform in async_setup_entry (__init__.py)
- [X] T044 [P] [US7] Create PixooDismissNotificationButton class in button.py with async_press() restoring previous state
- [X] T045 [P] [US7] Create PixooBuzzerButton class in button.py with async_press() triggering buzzer
- [X] T046 [P] [US7] Create PixooResetBufferButton class in button.py with async_press() calling pixoo.reset_buffer
- [X] T047 [P] [US7] Create PixooPushBufferButton class in button.py with async_press() calling pixoo.push_buffer

### Service Implementation

- [X] T048 [US7] Add play_buzzer schema to services.yaml (active_ms, off_ms, count, entity_id)
- [X] T049 [US7] Implement handle_play_buzzer service handler in __init__.py with pixoo.play_buzzer

### Testing (US7)

- [X] T050 [P] [US7] Create test_button.py with button entity tests (dismiss, buzzer, buffer operations)

**Parallel Opportunity**: T044-T047 (button entities), T048-T049 (buzzer service) can be done simultaneously

---

## Phase 6: User Story 3 - Clock and Visualizer Selection (P2) (5 tasks)

**Goal**: Dynamic clock face and visualizer selection

**Duration**: ~2 hours

**Dependencies**: Phase 3 complete

**Independent Test**:
- Select different clock faces
- Verify device switches to Faces channel automatically
- Select visualizers
- Verify animation list fetches from cloud

**Value Delivered**: Aesthetic customization

### Entity Implementation

- [X] T051 [P] [US3] Create PixooClockFaceSelect class in select.py with dynamic options from cloud
- [X] T052 [P] [US3] Create PixooVisualizerSelect class in select.py with dynamic options from device
- [X] T053 [P] [US3] Create PixooCustomPageSelect class in select.py for custom channel pages (1, 2, 3)

### Service Implementation

- [X] T054 [US3] Add list_animations schema to services.yaml (entity_id)
- [X] T055 [US3] Implement handle_list_animations service handler in __init__.py with pixoo.get_animation_list

**Parallel Opportunity**: T051-T053 (select entities) can be done simultaneously

---

## Phase 7: User Story 5 - Automation Integration (P2) (2 tasks)

**Goal**: Ensure service queue handles automation load

**Duration**: ~1 hour

**Dependencies**: Phase 4 complete

**Independent Test**:
- Trigger multiple automations simultaneously
- Verify service calls queue (FIFO)
- Verify warning logged at 20+ depth
- Confirm no display corruption

**Value Delivered**: Reliable automation execution

### Implementation

- [X] T056 [US5] Implement service call queue in __init__.py with FIFO processing per device
- [X] T057 [US5] Add queue depth monitoring in __init__.py with warning log at 20+ commands

**Parallel Opportunity**: None (sequential queue implementation)

---

## Phase 8: User Story 6 - Device Discovery and Multi-Device Support (P2) (3 tasks)

**Goal**: Support multiple devices seamlessly

**Duration**: ~1.5 hours

**Dependencies**: Phase 3 complete

**Independent Test**:
- Add multiple devices
- Verify each device gets unique entity IDs
- Target specific device in service call
- Verify correct device responds

**Value Delivered**: Multi-device management

### Implementation

- [X] T058 [US6] Enhance ConfigFlow in config_flow.py to handle multiple device discovery
- [X] T059 [US6] Implement unique_id generation in config_flow.py using MAC address
- [X] T060 [US6] Add multi-device service targeting in __init__.py with async_get_entities

**Parallel Opportunity**: None (sequential config flow enhancements)

---

## Phase 9: User Story 8 - Device Configuration and Display Options (P2) (3 tasks)

**Goal**: Configuration entities for rotation, mirror mode, gallery timing

**Duration**: ~1.5 hours

**Dependencies**: Phase 3 complete

**Independent Test**:
- Change rotation, verify display rotates
- Enable mirror mode, verify horizontal flip
- Adjust gallery timing, verify interval changes

**Value Delivered**: Physical setup flexibility

### Entity Implementation

- [X] T061 [US8] Register switch platform in async_setup_entry (__init__.py)
- [X] T062 [P] [US8] Create PixooMirrorModeSwitch class in switch.py with pixoo.set_mirror_mode
- [X] T063 [US8] Register number platform in async_setup_entry (__init__.py)
- [X] T064 [P] [US8] Create PixooGalleryIntervalNumber class in number.py with pixoo.set_gallery_timing

**Parallel Opportunity**: T062, T064 can be done simultaneously

---

## Phase 10: User Story 9 - Custom Channel Management (P2) (1 task)

**Goal**: Custom page switching service

**Duration**: ~30 minutes

**Dependencies**: Phase 6 complete (needs PixooCustomPageSelect)

**Independent Test**:
- Switch between custom pages
- Verify device displays correct page
- Test persistence across restarts

**Value Delivered**: Content organization

### Implementation

- [X] T065 [US9] Enhance PixooCustomPageSelect in select.py with page switching via pixoo.set_custom_page

**Parallel Opportunity**: None (enhancement to existing entity)

---

## Phase 11: User Story 10 - Built-in Tool Modes (P2) (10 tasks)

**Goal**: Timer, alarm, stopwatch, scoreboard, noise meter entities

**Duration**: ~4 hours

**Dependencies**: Phase 9 complete (needs number and switch platforms)

**Independent Test**:
- Set timer, verify countdown
- Set alarm, verify trigger
- Start stopwatch, verify elapsed time
- Update scoreboard, verify scores display
- Enable noise meter, verify visualization

**Value Delivered**: Device-native features

### Entity Implementation

- [X] T066 [P] [US10] Create PixooTimerMinutesNumber class in number.py with pixoo.set_timer
- [X] T067 [P] [US10] Create PixooTimerSecondsNumber class in number.py with pixoo.set_timer
- [X] T068 [P] [US10] Create PixooTimerSwitch class in switch.py with pixoo.set_timer(enabled)
- [X] T069 [P] [US10] Create PixooAlarmHourNumber class in number.py with pixoo.set_alarm
- [X] T070 [P] [US10] Create PixooAlarmMinuteNumber class in number.py with pixoo.set_alarm
- [X] T071 [P] [US10] Create PixooAlarmSwitch class in switch.py with pixoo.set_alarm(enabled)
- [X] T072 [P] [US10] Create PixooStopwatchSwitch class in switch.py with pixoo.set_stopwatch
- [X] T073 [P] [US10] Create PixooScoreboardRedNumber, PixooScoreboardBlueNumber classes in number.py with pixoo.set_scoreboard
- [X] T074 [P] [US10] Create PixooScoreboardSwitch class in switch.py with pixoo.set_scoreboard(enabled)
- [X] T075 [P] [US10] Create PixooNoiseMeterSwitch class in switch.py with pixoo.set_noise_meter

**Parallel Opportunity**: All entity classes (T066-T075) can be implemented simultaneously

---

## Phase 12: User Story 11 - Device Monitoring and Diagnostics (P2) (6 tasks)

**Goal**: Sensor entities for device health monitoring

**Duration**: ~2.5 hours

**Dependencies**: Phase 2 complete (coordinators provide data)

**Independent Test**:
- Read device info sensor
- Check network status sensor
- View system config sensor
- Verify weather/time sensors (if configured)

**Value Delivered**: Health monitoring and troubleshooting

### Entity Implementation

- [X] T076 [US11] Register sensor platform in async_setup_entry (__init__.py)
- [X] T077 [P] [US11] Create PixooDeviceInfoSensor class in sensor.py with DeviceInfo attributes
- [X] T078 [P] [US11] Create PixooNetworkStatusSensor class in sensor.py with network attributes
- [X] T079 [P] [US11] Create PixooSystemConfigSensor class in sensor.py with system attributes
- [X] T080 [P] [US11] Create PixooWeatherInfoSensor, PixooTimeInfoSensor classes in sensor.py
- [X] T081 [P] [US11] Create tool state sensors in sensor.py (timer remaining, alarm next, stopwatch elapsed)

**Parallel Opportunity**: All sensor classes (T077-T081) can be implemented simultaneously

---

## Phase 13: User Story 13 - Media Player Image Gallery (P2) (6 tasks)

**Goal**: Media player entity for image slideshows

**Duration**: ~3 hours

**Dependencies**: Phase 4 complete (needs download_image utility)

**Independent Test**:
- Play single image via media_player.play_media
- Create playlist with local images and URLs
- Test shuffle and repeat modes
- Navigate with next/previous track
- Pause and resume slideshow

**Value Delivered**: Photo frame functionality

### Entity Implementation

- [X] T082 [US13] Register media_player platform in async_setup_entry (__init__.py)
- [X] T083 [US13] Create PixooMediaPlayer class in media_player.py with MediaPlayerEntity base
- [X] T084 [US13] Implement async_play_media in media_player.py with playlist parsing, media-source:// resolution
- [X] T085 [US13] Implement playlist state management in media_player.py with _schedule_next, _auto_advance
- [X] T086 [US13] Implement navigation methods in media_player.py (async_media_next_track, async_media_previous_track)
- [X] T087 [US13] Implement playback control in media_player.py (async_media_play, async_media_pause, async_media_stop)

**Parallel Opportunity**: T084-T087 can be implemented in parallel after T083 base class exists

---

## Phase 14: User Story 4, 12 - Advanced Features (P3) (6 tasks)

**Goal**: Drawing primitives and advanced configuration services

**Duration**: ~2.5 hours

**Dependencies**: Phase 2 complete

**Independent Test**:
- Call drawing services (pixel, line, rectangle, text)
- Verify buffer operations work
- Call advanced config services (white balance, weather, timezone)
- Verify playlist creation

**Value Delivered**: Power user features

### Drawing Services (US4)

- [ ] T088 [P] [US4] Add drawing service schemas to services.yaml (draw_pixel, draw_line, draw_rectangle, draw_text, draw_image)
- [ ] T089 [P] [US4] Implement drawing service handlers in __init__.py with pixoo drawing methods

### Advanced Config Services (US12)

- [ ] T090 [P] [US12] Add advanced config schemas to services.yaml (set_white_balance, set_weather_location, set_timezone, set_time)
- [ ] T091 [P] [US12] Implement advanced config service handlers in __init__.py with pixoo config methods

### Animation Services (US12)

- [ ] T092 [P] [US12] Add animation service schemas to services.yaml (play_animation, stop_animation, set_playlist)
- [ ] T093 [P] [US12] Implement animation service handlers in __init__.py with pixoo playlist methods

**Parallel Opportunity**: T088-T089 (drawing), T090-T091 (config), T092-T093 (animation) can be done in parallel

---

## Phase 15: Polish & Cross-Cutting Concerns (2 tasks)

**Goal**: Documentation, CI/CD, final validation

**Duration**: ~2 hours

**Dependencies**: All user stories complete

### Tasks

- [X] T094 [P] Create docs/README.md with user guide, setup instructions, service examples
- [X] T095 [P] Create .github/workflows/ci.yml with pytest, ruff, mypy checks

**Parallel Opportunity**: T094-T095 can be done simultaneously

---

## Task Dependencies Graph

### Story Completion Order

```
Phase 1 (Setup)
  └─> Phase 2 (Foundation)
        ├─> Phase 3 (US1 - P1) ✓ MVP DELIVERABLE
        │     ├─> Phase 4 (US2 - P1)
        │     │     ├─> Phase 5 (US7 - P1)
        │     │     └─> Phase 13 (US13 - P2)
        │     ├─> Phase 6 (US3 - P2)
        │     │     └─> Phase 10 (US9 - P2)
        │     ├─> Phase 7 (US5 - P2)
        │     ├─> Phase 8 (US6 - P2)
        │     ├─> Phase 9 (US8 - P2)
        │     │     └─> Phase 11 (US10 - P2)
        │     ├─> Phase 12 (US11 - P2)
        │     └─> Phase 14 (US4, US12 - P3)
        └─> Phase 15 (Polish)
```

### Critical Path

**Setup → Foundation → US1 (MVP)** = 11 + 21 = 32 tasks (minimum viable product)

All other stories can be developed independently after US1 is complete.

---

## Parallel Execution Examples

### Phase 2 (Foundation) - 4 parallel tasks

```bash
# Team member 1: DeviceCoordinator
work on T007

# Team member 2: SystemCoordinator
work on T008

# Team member 3: ToolCoordinator
work on T009

# Team member 4: GalleryCoordinator
work on T010
```

### Phase 3 (US1) - 5 parallel entity implementations

```bash
# Team member 1: Light entity
work on T020

# Team member 2: Channel select
work on T021

# Team member 3: Rotation select
work on T022

# Team member 4: Temperature select
work on T023

# Team member 5: Time format select
work on T024
```

### Phase 3 (US1) - 6 parallel test files

```bash
# All tests can be written in parallel after entities exist
work on T025, T026, T027, T028, T029, T030 in parallel
```

### Phase 4 (US2) - 4 parallel service handlers

```bash
# Team member 1: Image display
work on T036

# Team member 2: GIF display
work on T037

# Team member 3: Text display
work on T038

# Team member 4: Clear display
work on T039
```

### Phase 11 (US10) - 10 parallel tool entities

```bash
# All tool entities are independent
work on T066-T075 in parallel (timer, alarm, stopwatch, scoreboard, noise meter)
```

### Phase 12 (US11) - 5 parallel sensor entities

```bash
# All sensors are independent
work on T077-T081 in parallel (device info, network, system, weather, time, tools)
```

---

## Implementation Milestones

### Milestone 1: MVP (Phases 1-3)
- **Tasks**: T001-T030 (30 tasks)
- **Duration**: ~12 hours
- **Deliverable**: Working integration with basic device control
- **Test**: User can add device and control power/brightness/channel

### Milestone 2: Core Automation (Phases 4-5)
- **Tasks**: T031-T050 (20 tasks)
- **Duration**: ~7 hours
- **Deliverable**: Display services and notification system
- **Test**: User can trigger image displays and persistent notifications

### Milestone 3: Enhanced Features (Phases 6-12)
- **Tasks**: T051-T087 (37 tasks)
- **Duration**: ~17 hours
- **Deliverable**: Full P2 feature set
- **Test**: All P2 user stories independently verified

### Milestone 4: Complete Integration (Phases 13-15)
- **Tasks**: T088-T095 (8 tasks)
- **Duration**: ~5 hours
- **Deliverable**: Production-ready integration
- **Test**: All 13 user stories complete, CI/CD passing

---

## Testing Strategy

### Unit Tests (Per Entity Platform)

- **Config Flow**: test_config_flow.py (T026)
- **Coordinators**: test_coordinator.py (T028)
- **Light**: test_light.py (T029)
- **Select**: test_select.py (T030)
- **Buttons**: test_button.py (T050)
- **Services**: test_services.py (T040-T042)
- **Media Player**: test_media_player.py (to be added in Phase 13)

### Integration Tests

- **Lifecycle**: test_init.py (T027) - setup, unload, reload
- **Multi-device**: Verify unique entity IDs, service targeting
- **Service Queue**: Verify FIFO ordering, warning at 20+ depth

### Manual Testing

- **Real Device**: Test with actual Pixoo 64/Max/Timebox Evo
- **Network Conditions**: Test timeout handling, reconnection
- **SSDP Discovery**: Verify automatic device detection

---

## Task Completion Checklist

### Phase 1: Setup ✓
- [ ] T001-T005 complete
- [ ] Project structure matches plan.md
- [ ] manifest.json has correct dependencies

### Phase 2: Foundation ✓
- [ ] T006-T011 complete
- [ ] All 4 coordinators functional
- [ ] PixooEntity base class tested

### Phase 3: User Story 1 (MVP) ✓
- [ ] T012-T030 complete
- [ ] Config flow works (SSDP + manual)
- [ ] Light entity controllable
- [ ] Select entities work
- [ ] All US1 tests passing

### Phase 4: User Story 2 ✓
- [ ] T031-T042 complete
- [ ] Display services functional
- [ ] Image download works with limits
- [ ] All US2 tests passing

### Phase 5: User Story 7 ✓
- [ ] T043-T050 complete
- [ ] Button entities functional
- [ ] Notification persistence works
- [ ] All US7 tests passing

### Phase 6: User Story 3 ✓
- [ ] T051-T055 complete
- [ ] Clock/visualizer selection works
- [ ] Animation list fetches
- [ ] All US3 tests passing

### Phase 7: User Story 5 ✓
- [ ] T056-T057 complete
- [ ] Service queue handles load
- [ ] Warning logged at 20+ depth
- [ ] All US5 tests passing

### Phase 8: User Story 6 ✓
- [ ] T058-T060 complete
- [ ] Multiple devices supported
- [ ] Service targeting works
- [ ] All US6 tests passing

### Phase 9: User Story 8 ✓
- [ ] T061-T064 complete
- [ ] Configuration entities work
- [ ] All US8 tests passing

### Phase 10: User Story 9 ✓
- [ ] T065 complete
- [ ] Custom page switching works
- [ ] All US9 tests passing

### Phase 11: User Story 10 ✓
- [ ] T066-T075 complete
- [ ] All tool modes functional
- [ ] All US10 tests passing

### Phase 12: User Story 11 ✓
- [ ] T076-T081 complete
- [ ] All sensor entities work
- [ ] All US11 tests passing

### Phase 13: User Story 13 ✓
- [ ] T082-T087 complete
- [ ] Media player functional
- [ ] Playlist/shuffle/repeat work
- [ ] All US13 tests passing

### Phase 14: User Stories 4, 12 ✓
- [ ] T088-T093 complete
- [ ] Drawing services work
- [ ] Advanced config services work
- [ ] All US4, US12 tests passing

### Phase 15: Polish ✓
- [ ] T094-T095 complete
- [ ] Documentation complete
- [ ] CI/CD passing
- [ ] Ready for release

---

## Success Criteria

### MVP (Milestone 1) Success

- [ ] User can add Pixoo device via SSDP or manual IP
- [ ] Light entity controls power and brightness
- [ ] Select entities control channel, rotation, temperature, time format
- [ ] Device availability tracked correctly
- [ ] All US1 acceptance scenarios pass

### Core Automation (Milestone 2) Success

- [ ] Display image/GIF/text services work
- [ ] Image downloads respect 10MB/30s limits
- [ ] Notification system with dismiss button works
- [ ] Buzzer alerts functional
- [ ] All US2, US7 acceptance scenarios pass

### Enhanced Features (Milestone 3) Success

- [ ] Clock face and visualizer selection works
- [ ] Multiple devices supported simultaneously
- [ ] Configuration entities functional
- [ ] Tool modes (timer, alarm, stopwatch, scoreboard, noise meter) work
- [ ] Sensor entities report device health
- [ ] Media player slideshow functional
- [ ] All P2 acceptance scenarios pass

### Production Ready (Milestone 4) Success

- [ ] Drawing services work
- [ ] Advanced configuration services work
- [ ] All 13 user stories complete
- [ ] All tests passing
- [ ] CI/CD green
- [ ] Documentation complete
- [ ] All 35 success criteria from spec.md verified

---

## Notes

### Estimated Total Duration

- **Sequential**: ~41 hours (all tasks in order)
- **With Parallelization**: ~25 hours (leveraging parallel tasks)
- **MVP Only**: ~12 hours (Phases 1-3)

### Team Recommendations

- **Solo Developer**: Focus on MVP first (12 hours), then P1 stories (7 hours), then P2/P3 incrementally
- **Small Team (2-3)**: Parallelize entity implementations within each phase
- **Larger Team (4+)**: Parallelize entire user stories after MVP (US2-US13 can be done simultaneously)

### Constitution Alignment

All tasks align with the 7 constitution principles:
- ✅ Async-First: All operations use PixooAsync
- ✅ HA Native: Config flow, entities, services follow HA patterns
- ✅ Package Dependency: All tasks use pixooasync exclusively
- ✅ Modern Python: Python 3.12+, Pydantic models, type hints
- ✅ AI Agent Friendly: Clear task structure, file paths, dependencies
- ✅ TDD: Tests included for each user story
- ✅ Maintainability: Organized by user story, incremental delivery
