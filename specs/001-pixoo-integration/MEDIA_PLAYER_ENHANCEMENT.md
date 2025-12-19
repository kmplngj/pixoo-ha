# Media Player Enhancement Summary

**Date**: 2025-11-10  
**Feature**: Image Gallery & Slideshow (User Story 13)  
**Enhancement Type**: Feature Addition

## Overview

Added media player entity platform to enable image gallery and slideshow functionality with playlist support, shuffle, repeat, and manual navigation controls.

## Changes Made

### Specification (spec.md)

**Lines Added**: +69 lines (687 → 756 lines)

**Clarifications** (2 new):
- **Q6**: Light vs Media Player entity approach
  - **A**: Dual entity pattern - light for brightness, media_player for content (HA best practice)
- **Q7**: Image gallery/slideshow implementation
  - **A**: MediaPlayerEntity with playlist support, custom timing/shuffle/repeat attributes

**User Stories** (1 new):
- **User Story 13: Media Player Image Gallery** (Priority P2)
  - 9 acceptance scenarios covering playlist, timing, shuffle, repeat, navigation, pause

**Functional Requirements** (10 new):
- **FR-066**: Media player entity exposure
- **FR-067**: play_media service with MediaType.IMAGE support
- **FR-068**: Local file path support via media-source:// URLs
- **FR-069**: External URL support with validation
- **FR-070**: Playlist support (JSON array format)
- **FR-071**: Shuffle/repeat/duration attributes
- **FR-072**: Navigation services (next/previous track)
- **FR-073**: Playback control (play/pause/stop)
- **FR-074**: Playlist state management
- **FR-075**: Mixed local/URL playlists

**Success Criteria** (5 new):
- **SC-031**: Single image display (<3s)
- **SC-032**: Playlist creation (3+ items)
- **SC-033**: Shuffle mode validation
- **SC-034**: Repeat mode validation
- **SC-035**: Manual navigation validation

**Real-World Use Cases** (6 new):
- Use case #23: Digital Photo Frame
- Use case #24: Rotating Art Display
- Use case #25: Security Camera Montage
- Use case #26: Dashboard Rotation
- Use case #27: Kids' Bedtime Stories
- Use case #28: Recipe Display

### Data Model (data-model.md)

**Lines Added**: +205 lines (638 → 843 lines)

**New Section**: Media Player Platform (1 entity)

**Entity Model**:
```python
@dataclass
class PixooMediaPlayerState:
    state: MediaPlayerState
    media_content_type: str
    media_content_id: str | None
    media_image_url: str | None
    media_position: int = 0
    media_duration: int = 10
    shuffle: bool = False
    repeat: bool = False
    playlist: list[PixooPlaylistItem]
```

**Methods**:
- `async_play_media(media_type, media_id)`: Display image or start playlist
- `async_media_play()`: Resume slideshow
- `async_media_pause()`: Pause slideshow
- `async_media_stop()`: Stop and clear
- `async_media_next_track()`: Next image (respects shuffle)
- `async_media_previous_track()`: Previous image
- `async_set_shuffle(shuffle)`: Enable/disable shuffle
- `async_set_repeat(repeat)`: Enable/disable repeat

**Private Methods**:
- `_display_current_image()`: Display current playlist item
- `_schedule_next()`: Auto-advance timer
- `_auto_advance()`: Automatic progression
- `_load_playlist(items)`: Parse JSON playlist
- `_load_single_image(url)`: Single image mode

**Example Usage**: 3 YAML examples (single image, local folder, mixed playlist)

### Service Contracts (contracts/media-player-services.md)

**New File**: 430+ lines

**Services Documented** (8 services):
1. `media_player.play_media` - Single image or playlist
2. `media_player.media_play` - Resume slideshow
3. `media_player.media_pause` - Pause slideshow
4. `media_player.media_stop` - Stop and clear
5. `media_player.media_next_track` - Next image
6. `media_player.media_previous_track` - Previous image
7. `media_player.shuffle_set` - Enable/disable shuffle
8. `media_player.repeat_set` - Enable/disable repeat

**Content**:
- Voluptuous schemas for validation
- Playlist item schema (url, duration)
- Media content types (image, url, playlist)
- Error handling patterns
- Implementation code examples
- Media source resolution logic
- Auto-advance timer implementation
- Shuffle order generation
- Testing checklist (16 items)
- Example automations (2 complete examples)

### Entity Mapping (ENTITY_MAPPING.md)

**Lines Added**: +60 lines (364 → 424 lines)

**New Sections**:
- **Light Entity**: Mapping for light.pixoo (brightness, power)
- **Media Player Entity**: Comprehensive mapping for media_player.pixoo

**Light Entity**:
- `set_brightness(value)` → brightness control
- `set_screen(on=True/False)` → power control
- Implementation example with async methods

**Media Player Entity**:
- `display_image_from_url()` → single image display
- `display_gif_from_url()` → animated content
- `display_image_from_bytes()` → local/downloaded images
- `clear_display()` → stop service
- Playlist format documentation
- Media source URL resolution
- Service mapping (8 services)

### Implementation Plan (plan.md)

**Lines Changed**: Updated project structure and entity counts

**Changes**:
1. Added `media_player.py` platform file (custom_components/pixoo/)
2. Added `test_media_player.py` test file (tests/)
3. Updated entity count: "40+ entities" now includes media player
4. Updated Scale/Scope:
   - From: "40+ entities per device (8 number, 7 switch, 7 select, 10 sensor, 4 button)"
   - To: "40+ entities per device (1 light, 1 media_player, 8 number, 7 switch, 7 select, 10 sensor, 4 button)"
   - Added: "7 media player services (play_media, play, pause, stop, next, previous, shuffle, repeat)"
   - Updated: "13 user stories" (was 12)
5. Updated Principle II evidence with FR-066 to FR-075 reference
6. Entity platform counts now include media_player

### Contracts Index (contracts/README.md)

**Lines Added**: +17 lines (227 → 244 lines)

**New Section**: Media Player Services (7 services)
- Listed as "Section 0" (before display services)
- Table with service descriptions and key parameters
- Note explaining namespace difference (media_player vs pixoo)

## Constitution Compliance

All 7 principles remain compliant with media player additions:

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Async-First | ✅ | All media player methods use async/await, timer scheduling via hass.loop.call_later |
| II. HA Native | ✅ | Standard MediaPlayerEntity pattern, uses HA media_source integration, follows HA service conventions |
| III. Package Dependency | ✅ | Uses pixooasync display methods (display_image_from_url, display_image_from_bytes, clear_display) |
| IV. Modern Python | ✅ | Pydantic models for playlist items, type hints throughout, Python 3.12+ features |
| V. AI Agent Friendly | ✅ | Comprehensive documentation (data model, service contracts, entity mapping, examples) |
| VI. TDD | ✅ | 5 new success criteria (SC-031 to SC-035), testing checklist (16 items) |
| VII. Maintainability | ✅ | Standard HA media player pattern, clear separation from light entity, well-documented |

## Research Findings

### DeepWiki Query 1: Entity Type for LED Displays

**Question**: "What is the correct entity type for LED matrix displays like Pixoo?"

**Key Findings**:
- Light entity standard for brightness control (LightEntity, ColorMode.BRIGHTNESS)
- Media player entity for content display (MediaPlayerEntity, MediaType.IMAGE)
- Dual entity pattern recommended for displays with both capabilities
- Image entity (camera.ImageEntity) not suitable (static sources, not interactive)
- Examples: Shelly (BlockShellyLight), AirGradient (display brightness as numbers)

**Decision**: Implement both light.pixoo (brightness/power) and media_player.pixoo (content)

### DeepWiki Query 2: Media Player Implementation

**Question**: "What are the HA media_player methods for playing local images and slideshows?"

**Key Findings**:
- `play_media` service takes media_content_id + media_content_type
- Local images via media-source:// URLs (resolved by media_source integration)
- No built-in slideshow feature (custom implementation required)
- MediaPlayerEntity attributes: media_image_url, media_image_local
- Implement next_track/previous_track for manual navigation
- Custom attributes for timing/shuffle/repeat
- MediaPlayerImageView handles HTTP serving of images

**Decision**: Custom playlist implementation with auto-advance timer and shuffle/repeat state management

## Implementation Notes

### Playlist Format

JSON array with per-item duration:

```json
[
  {"url": "media-source://media_source/local/photos/photo1.jpg", "duration": 30},
  {"url": "https://example.com/photo2.jpg", "duration": 15},
  {"url": "media-source://media_source/local/photos/photo3.jpg", "duration": 45}
]
```

### Auto-Advance Logic

1. Display image via `_display_current_image()`
2. Schedule timer: `hass.loop.call_later(duration, _auto_advance)`
3. On timer expiration:
   - Check if PLAYING state (skip if PAUSED)
   - Check if last item (stop if no repeat)
   - Advance to next image (respects shuffle order)
   - Reschedule timer for next item

### Shuffle Implementation

- Generate shuffled indices on shuffle enable: `random.shuffle(range(len(playlist)))`
- Store in `_shuffle_order` list
- Navigate through shuffle_order instead of sequential indices
- Preserve current position when toggling shuffle

### Media Source Resolution

```python
if url.startswith("media-source://"):
    resolved = await media_source.async_resolve_media(self.hass, url)
    url = resolved.url
```

### Image Download Reuse

Use existing `download_image()` utility:
- aiohttp async download
- 10MB size limit
- 30s timeout
- Content-type validation
- Pillow downsampling in executor

## Testing Strategy

### Unit Tests (test_media_player.py)

- Test single image display (media-source:// and https://)
- Test playlist parsing and validation
- Test shuffle order generation
- Test repeat mode behavior
- Test navigation (next/previous) in sequential and shuffle modes
- Test pause/resume state management
- Test auto-advance timer scheduling
- Test error handling (invalid JSON, bad URLs, download failures)

### Integration Tests

- Test with real media_source integration
- Test mixed local/URL playlists
- Test playback from HA lovelace UI
- Test state persistence across HA restarts

### Manual Testing

- Display family photo slideshow
- Navigate playlist with next/previous
- Toggle shuffle during playback
- Test repeat at playlist end
- Pause slideshow, navigate manually, resume
- Mix media-source and external URLs

## Documentation Updates

Files updated:
1. ✅ `specs/001-pixoo-integration/spec.md` - Added User Story 13, FR-066 to FR-075, SC-031 to SC-035
2. ✅ `specs/001-pixoo-integration/data-model.md` - Added MediaPlayerEntity section
3. ✅ `specs/001-pixoo-integration/contracts/media-player-services.md` - Complete service documentation
4. ✅ `specs/001-pixoo-integration/contracts/README.md` - Added media player section
5. ✅ `specs/001-pixoo-integration/ENTITY_MAPPING.md` - Added light and media player sections
6. ✅ `specs/001-pixoo-integration/plan.md` - Updated project structure and entity counts
7. ✅ `specs/001-pixoo-integration/MEDIA_PLAYER_ENHANCEMENT.md` - This summary

## Next Steps

### Immediate

1. ⏳ Update `.github/copilot-instructions.md` with media player patterns
2. ⏳ Update `quickstart.md` with media player example
3. ⏳ Verify all cross-references in documentation

### Implementation Phase

1. Create `custom_components/pixoo/media_player.py`
2. Implement `PixooMediaPlayer` class inheriting from `MediaPlayerEntity`
3. Add media player to `__init__.py` platform setup
4. Create `tests/test_media_player.py` with comprehensive tests
5. Add media player examples to `SERVICES.md`

### Testing Phase

1. Unit tests for all media player methods
2. Integration tests with mock PixooAsync
3. Manual testing with real Pixoo device
4. Test all 16 checklist items from service contract

## Metrics

**Specification Growth**:
- Spec lines: 687 → 756 (+69, +10%)
- User stories: 12 → 13 (+1, +8%)
- Functional requirements: 65 → 75 (+10, +15%)
- Success criteria: 30 → 35 (+5, +17%)
- Entity count: 40+ (now includes light + media_player)
- Service count: 25 integration + 7 media player = 32 total

**Documentation Growth**:
- data-model.md: 638 → 843 lines (+205, +32%)
- New file: contracts/media-player-services.md (430+ lines)
- contracts/README.md: 227 → 244 lines (+17, +7%)
- ENTITY_MAPPING.md: 364 → 424 lines (+60, +16%)
- plan.md: Updated structure and counts

**Total New Content**: ~800+ lines of documentation and specifications

---

**Status**: ✅ Complete  
**Constitution Compliance**: 7/7 principles aligned  
**Ready for Implementation**: Yes
