# Feature Specification: Divoom Pixoo Home Assistant Integration

**Feature Branch**: `001-pixoo-integration`  
**Created**: 2025-11-10  
**Last Updated**: 2025-11-10 (Enhanced with pixooasync package analysis)  
**Status**: Draft  
**Input**: User description: "a home assistant integration for divoom pixoo. it should support all the stuff a user would like to use in this integration. so every function from the python pixoo packages and stuff that could be done with the pixoo rest client but then internally in the integration. it should support the display as a light, the integration should support notifications and displaying album arts with track information from home assistant and also display images from home assistant and from external urls."

**Enhancement Scope**: Comprehensive analysis of pixooasync Python package (v1.0.0+) including:
- 105+ methods for device control, drawing, tools, and configuration
- Pydantic v2 models for type-safe data validation
- Type-safe enums for all device modes and settings
- Async-first architecture with PixooAsync client
- Built-in tool modes: timer, alarm, stopwatch, scoreboard, noise meter
- Comprehensive sensor entities for device monitoring and diagnostics
- Advanced configuration: white balance, weather location, timezone, playlists

## Clarifications

### Session 2025-11-10

- Q: Service call queue strategy for handling concurrent display commands? → A: Unlimited queue with warning log when depth exceeds 20
- Q: Notification acknowledgment implementation mechanism? → A: Button entity (button.pixoo_dismiss_notification) that clears display and restores previous state
- Q: Tool mode mutual exclusivity behavior when activating conflicting tools? → A: Automatically disable conflicting tool mode and log info message
- Q: Image download security limits and automatic resizing? → A: 10MB limit, 30s timeout, validate content-type, with automatic downsampling to device resolution using Pillow
- Q: Sensor update polling strategy and intervals? → A: Tiered polling - Device info (once at startup), network status (60s), system config (30s), weather info (5min), tool state sensors (1s when active)
- Q: Should Pixoo be represented as light or media_player entity? → A: Both - light entity for brightness/power control (HA best practice), media_player entity for image/GIF playback with slideshow capabilities
- Q: How should image galleries/slideshows be implemented? → A: Media player entity with play_media service accepting playlists, custom attributes for timing/shuffle/repeat, next_track/previous_track for manual navigation

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Device Setup and Control (Priority: P1)

Users can easily add their Pixoo device to Home Assistant and control basic settings like power, brightness, and channel selection through the UI or automations.

**Why this priority**: Core functionality that every user needs. Without device setup and basic controls, the integration is unusable. This represents the minimum viable product.

**Independent Test**: Can be fully tested by adding a device through the config flow, verifying it appears in Home Assistant, and testing brightness/power controls. Delivers immediate value by making the device controllable.

**Acceptance Scenarios**:

1. **Given** user has a Pixoo device on their network, **When** they add the integration in Home Assistant, **Then** device is discovered automatically or can be added manually with IP address
2. **Given** device is configured, **When** user adjusts brightness slider, **Then** device brightness changes immediately
3. **Given** device is on, **When** user toggles power switch, **Then** device screen turns off/on
4. **Given** device is configured, **When** user selects a channel from dropdown, **Then** device switches to selected channel (Faces, Cloud, Visualizer, Custom)
5. **Given** device connection fails, **When** device becomes unreachable, **Then** entity shows unavailable state and logs warning

---

### User Story 2 - Display Custom Content (Priority: P1)

Users can send images, GIFs, and text to their Pixoo device through Home Assistant services, enabling personalized displays and notifications.

**Why this priority**: Primary use case for home automation. Users want to display custom content triggered by automations (doorbell camera snapshots, weather alerts, notifications).

**Independent Test**: Can be tested independently by calling the display services with test content. Delivers value by enabling custom notifications and displays.

**Acceptance Scenarios**:

1. **Given** device is configured, **When** user calls display_image service with local file path, **Then** image appears on Pixoo screen
2. **Given** device is configured, **When** user calls display_gif service with animation file, **Then** GIF plays on device
3. **Given** device is configured, **When** user calls display_text service with message, **Then** text scrolls across screen
4. **Given** user provides image URL, **When** display_image service called with URL, **Then** image downloads and displays
5. **Given** invalid file format provided, **When** display service called, **Then** service fails gracefully with clear error message

---

### User Story 3 - Clock and Visualizer Selection (Priority: P2)

Users can switch between different clock faces and audio visualizers through Home Assistant, personalizing their Pixoo display to match their home aesthetic.

**Why this priority**: Enhances user experience with customization options. Not critical for basic functionality but important for user satisfaction.

**Independent Test**: Can be tested by selecting different clocks/visualizers and verifying display changes. Delivers aesthetic customization value.

**Acceptance Scenarios**:

1. **Given** device is on Faces channel, **When** user selects clock face number from dropdown, **Then** device displays selected clock
2. **Given** device is on Visualizer channel, **When** user selects visualizer mode, **Then** device shows selected audio visualization
3. **Given** user browses available clocks, **When** integration fetches from Divoom cloud, **Then** list of available clock faces appears
4. **Given** device is on wrong channel, **When** user selects clock face, **Then** device switches to Faces channel automatically

---

### User Story 4 - Advanced Drawing and Animation (Priority: P3)

Power users can programmatically draw on the Pixoo screen using drawing primitives (pixels, lines, shapes, text) through Home Assistant services for custom visualizations.

**Why this priority**: Advanced feature for technical users. Enables custom animations and dynamic content but not required for typical use cases.

**Independent Test**: Can be tested by calling drawing services and verifying rendered output. Delivers value for custom scripting scenarios.

**Acceptance Scenarios**:

1. **Given** user wants custom display, **When** calls draw_pixel service with coordinates and color, **Then** pixel appears at specified location
2. **Given** user wants shapes, **When** calls draw_rectangle/draw_line services, **Then** shapes render on screen
3. **Given** user wants dynamic text, **When** calls draw_text with position and color, **Then** text renders at specified location
4. **Given** user creates animation sequence, **When** multiple drawing calls executed, **Then** animation plays smoothly
5. **Given** drawing buffer created, **When** send_buffer service called, **Then** entire buffer displays on device

---

### User Story 5 - Automation Integration (Priority: P2)

Users can trigger Pixoo displays based on Home Assistant events and sensor states, creating contextual notifications and ambient information displays.

**Why this priority**: Core value of Home Assistant integration. Enables reactive displays based on smart home state.

**Independent Test**: Can be tested by creating test automation and verifying it triggers correct display changes. Delivers automation value.

**Acceptance Scenarios**:

1. **Given** doorbell pressed, **When** automation triggers, **Then** camera snapshot appears on Pixoo
2. **Given** weather changes, **When** sensor updates, **Then** weather icon and temperature display
3. **Given** package delivered, **When** sensor triggered, **Then** notification scrolls on screen
4. **Given** timer expires, **When** timer entity updates, **Then** completion message displays
5. **Given** multiple automations active, **When** conditions met, **Then** displays queue and execute in order

---

### User Story 6 - Device Discovery and Multi-Device Support (Priority: P2)

Users with multiple Pixoo devices can manage all of them through Home Assistant, with automatic discovery making setup effortless.

**Why this priority**: Important for users with multiple devices. Automatic discovery improves user experience significantly.

**Independent Test**: Can be tested with multiple devices on network. Delivers multi-device management value.

**Acceptance Scenarios**:

1. **Given** multiple Pixoo devices on network, **When** integration loads, **Then** all devices discovered automatically
2. **Given** new device added to network, **When** Home Assistant restarts, **Then** new device discovered
3. **Given** multiple devices configured, **When** user targets specific device in service call, **Then** correct device responds
4. **Given** device has unique name, **When** discovered, **Then** device name shows in Home Assistant
5. **Given** device removed from network, **When** integration polls, **Then** device marked unavailable

---

### User Story 7 - Notification and Alert System (Priority: P1)

Users can create persistent visual and audio notifications for important events (appliance status, reminders, alerts) that remain visible until acknowledged.

**Why this priority**: Primary real-world use case from community feedback. Users rely on Pixoo for visual reminders of washing machine completion, birthdays, trash day, etc. Audio alerts enhance notification effectiveness.

**Independent Test**: Can be tested by triggering automation with notification, verifying it displays with optional buzzer, and remains until user acknowledges. Delivers practical home assistant value.

**Acceptance Scenarios**:

1. **Given** washing machine finishes cycle, **When** automation detects completion, **Then** washing machine GIF displays with buzzer alert
2. **Given** notification is showing, **When** user presses acknowledgment button, **Then** display returns to previous state
3. **Given** birthday reminder set, **When** date matches, **Then** birthday cake GIF displays with person's name until acknowledged
4. **Given** trash collection day, **When** morning arrives, **Then** appropriate trash icon displays (recycling/general/organic)
5. **Given** doorbell pressed, **When** event triggers, **Then** camera snapshot displays with buzzer and optional message overlay

---

### User Story 8 - Device Configuration and Display Options (Priority: P2)

Users can configure device settings like screen rotation, temperature units, time format, and display mirroring to match their physical setup and preferences.

**Why this priority**: Essential for physical installation flexibility and user preference. Users mount devices in different orientations and locations.

**Independent Test**: Can be tested by changing configuration options and verifying display updates. Delivers customization value.

**Acceptance Scenarios**:

1. **Given** device mounted sideways, **When** user sets rotation to 90 degrees, **Then** display rotates to match orientation
2. **Given** user prefers Celsius, **When** temperature mode set to metric, **Then** all temperatures display in Celsius
3. **Given** user wants 24-hour time, **When** time format changed, **Then** clocks show 24-hour format
4. **Given** device mounted on mirror, **When** mirror mode enabled, **Then** display flips horizontally
5. **Given** gallery slideshow active, **When** user adjusts timing, **Then** slides advance at configured interval

---

### User Story 9 - Custom Channel Management (Priority: P2)

Users can organize content into three custom channel pages and quickly switch between them, enabling different display modes for different times or contexts.

**Why this priority**: Community users actively request this for organizing different display scenarios (morning info, work mode, evening relaxation).

**Independent Test**: Can be tested by configuring custom pages and switching between them. Delivers organization value.

**Acceptance Scenarios**:

1. **Given** user configured three custom pages, **When** custom channel 1 button pressed, **Then** device switches to first custom page
2. **Given** user on custom page 2, **When** custom channel 3 selected, **Then** device switches to third custom page
3. **Given** automation needs specific layout, **When** service called with page number, **Then** device switches to specified custom page
4. **Given** device on custom channel, **When** restart occurs, **Then** device remains on same custom page
5. **Given** user creates morning dashboard, **When** schedule triggers, **Then** device automatically switches to morning custom page

---

### User Story 10 - Built-in Tool Modes (Priority: P2)

Users can activate and configure Pixoo's built-in tools (timer, alarm, stopwatch, scoreboard, noise meter) through Home Assistant for versatile display modes.

**Why this priority**: Leverages unique device capabilities that make Pixoo more than just a display. Timer/alarm features are frequently requested for kitchen/office use. Scoreboard and noise meter enable creative home automation scenarios.

**Independent Test**: Can be tested by activating each tool mode and verifying display/functionality. Delivers device-native feature value.

**Acceptance Scenarios**:

1. **Given** user wants countdown timer, **When** timer service called with minutes/seconds, **Then** device displays countdown and alerts when complete
2. **Given** user sets alarm for specific time, **When** alarm time reached, **Then** device displays alarm notification with optional buzzer
3. **Given** user starts stopwatch, **When** stopwatch enabled, **Then** device shows elapsed time counting up
4. **Given** user wants to track game score, **When** scoreboard activated with red/blue scores, **Then** device displays scoreboard with team scores
5. **Given** user enables noise meter, **When** ambient sound detected, **Then** device displays audio level visualization in real-time

---

### User Story 11 - Device Monitoring and Diagnostics (Priority: P2)

Users can view detailed device information, network status, and system configuration through sensor entities, enabling health monitoring and troubleshooting.

**Why this priority**: Essential for reliable operation and troubleshooting. Users need visibility into device health, network connectivity, and current configuration to diagnose issues.

**Independent Test**: Can be tested by reading sensor entities and verifying data matches device state. Delivers monitoring value.

**Acceptance Scenarios**:

1. **Given** device is online, **When** diagnostics page viewed, **Then** shows device model, MAC address, firmware version, hardware revision
2. **Given** device connected to WiFi, **When** network sensor checked, **Then** shows WiFi signal strength, IP address, connection status
3. **Given** device has current configuration, **When** system config sensor viewed, **Then** shows brightness, rotation, mirror mode, time format, temperature mode
4. **Given** device has weather location set, **When** weather sensor checked, **Then** shows current weather conditions and forecast
5. **Given** device clock is set, **When** time info sensor viewed, **Then** shows timezone, UTC offset, local time

---

### User Story 12 - Advanced Configuration (Priority: P3)

Power users can fine-tune device settings like white balance, weather location, timezone, and custom page playlists for optimal display quality and personalization.

**Why this priority**: Advanced features for users who want precise control over display characteristics and content. Not required for basic use but enhances experience for enthusiasts.

**Independent Test**: Can be tested by adjusting advanced settings and verifying display changes. Delivers fine-tuning value.

**Acceptance Scenarios**:

1. **Given** user wants color correction, **When** white balance service called with RGB values, **Then** device adjusts color temperature accordingly
2. **Given** user sets weather location, **When** location coordinates provided, **Then** device displays weather for specified location
3. **Given** user wants custom timezone, **When** timezone service called, **Then** device clock displays in specified timezone
4. **Given** user creates playlist, **When** playlist service called with animation IDs and timing, **Then** device plays animations in sequence
5. **Given** device has animation library, **When** user requests available animations, **Then** integration returns list of animation IDs and names

---

### User Story 13 - Media Player Image Gallery (Priority: P2)

Users can play image slideshows from local Home Assistant folders or URL lists with configurable timing, shuffle, and repeat modes through the media player interface.

**Why this priority**: Transforms Pixoo into dynamic photo frame. Common use case for displaying family photos, art collections, or rotating information dashboards. Aligns with Home Assistant media player patterns.

**Independent Test**: Can be tested by creating media player playlist with local images or URLs, verifying slideshow playback with timing controls. Delivers photo frame value.

**Acceptance Scenarios**:

1. **Given** user has image folder in Home Assistant, **When** media_player.play_media called with folder path, **Then** Pixoo displays images as slideshow
2. **Given** slideshow is playing, **When** user sets display_duration attribute to 10 seconds, **Then** each image displays for 10 seconds before transitioning
3. **Given** user provides list of image URLs, **When** play_media called with URL playlist, **Then** Pixoo displays each URL in sequence
4. **Given** slideshow is active, **When** user enables shuffle mode, **Then** images display in random order
5. **Given** slideshow reaches end, **When** repeat mode is enabled, **Then** slideshow restarts from beginning
6. **Given** slideshow is playing, **When** user calls media_next_track service, **Then** Pixoo skips to next image immediately
7. **Given** slideshow is playing, **When** user calls media_previous_track service, **Then** Pixoo returns to previous image
8. **Given** slideshow is paused, **When** user calls media_play service, **Then** slideshow resumes from current position
9. **Given** user mixes local and URL images in playlist, **When** play_media called, **Then** all images display regardless of source type

---

### Edge Cases

- What happens when device IP changes (DHCP reassignment)?
- How does system handle network timeouts during image upload?
- What if user sends image larger than device resolution?
- How are concurrent service calls to same device handled?
- What if device is offline when automation triggers?
- How does integration handle invalid color values or coordinates?
- What happens when GIF file is too large for device memory?
- How are service calls queued when device is busy?
- What if user triggers notification while another notification is active?
- How does acknowledgment work when user is away and can't dismiss?
- What happens if buzzer is playing and another buzzer call is made?
- How are custom page assignments preserved during device restarts?
- What if rotation is changed while content is displaying?
- How does multi-line text handle overflow beyond screen bounds?
- What if user deletes image file while it's queued to display?
- What happens when timer reaches zero while device is on different channel?
- How does alarm handle when set time is in the past?
- What if user sets scoreboard scores beyond reasonable limits (negative, huge numbers)?
- How does noise meter behave in completely silent environment vs loud environment?
- What happens if weather location service is unavailable or coordinates are invalid?
- How does white balance adjustment affect existing displayed content?
- What if playlist contains non-existent animation IDs?
- How does stopwatch handle extremely long elapsed times (days)?
- When timer/alarm/stopwatch activated while another tool is active: conflicting tool automatically disabled with info log
- How are sensor entity states handled during device restart or firmware update?

## Requirements *(mandatory)*

### Functional Requirements

#### Core Integration (FR-001 to FR-025)

- **FR-001**: Integration MUST support config flow setup with manual IP entry and automatic device discovery
- **FR-002**: Integration MUST expose brightness control as a number entity (0-100%)
- **FR-003**: Integration MUST expose power control as a switch entity
- **FR-004**: Integration MUST expose channel selection as a select entity (Faces, Cloud, Visualizer, Custom)
- **FR-005**: Integration MUST provide service to display static images from local file paths
- **FR-006**: Integration MUST provide service to display static images from URLs with 10MB size limit, 30s timeout, content-type validation, and automatic downsampling to device resolution using Pillow
- **FR-007**: Integration MUST provide service to display animated GIFs from local files
- **FR-008**: Integration MUST provide service to display animated GIFs from URLs with 10MB size limit, 30s timeout, content-type validation, and automatic downsampling to device resolution using Pillow
- **FR-009**: Integration MUST provide service to display scrolling text messages
- **FR-010**: Integration MUST support clock face selection when device is in Faces mode
- **FR-011**: Integration MUST support visualizer selection when device is in Visualizer mode
- **FR-012**: Integration MUST fetch available clock faces from Divoom cloud service
- **FR-013**: Integration MUST provide drawing services for pixels, lines, rectangles, and text
- **FR-014**: Integration MUST handle drawing buffer management for complex animations
- **FR-015**: Integration MUST report device availability status
- **FR-016**: Integration MUST support multiple Pixoo devices simultaneously
- **FR-017**: Integration MUST persist device configuration across restarts
- **FR-018**: Integration MUST provide device diagnostics information
- **FR-019**: Integration MUST handle device connection errors gracefully
- **FR-020**: Integration MUST validate image formats and automatically downsample images to device resolution (64x64 for Pixoo 64) using Pillow library before sending
- **FR-021**: Integration MUST implement proper entity naming following Home Assistant conventions
- **FR-022**: Integration MUST support reconfiguration of device IP address
- **FR-023**: Integration MUST log all communication errors for troubleshooting
- **FR-024**: Integration MUST implement all operations asynchronously using pixooasync.PixooAsync
- **FR-025**: Integration MUST use the pixooasync Python package for device communication
- **FR-025a**: Integration MUST queue service calls using unlimited FIFO queue and log warning when queue depth exceeds 20 commands

#### Display Features (FR-026 to FR-035)

- **FR-026**: Integration MUST provide buzzer service for audio alerts with configurable timing
- **FR-027**: Integration MUST support screen rotation (0, 90, 180, 270 degrees)
- **FR-028**: Integration MUST support switching between custom channel pages (1, 2, 3)
- **FR-029**: Integration MUST support multi-line text display with positioning control
- **FR-030**: Integration MUST expose temperature unit selection (Celsius/Fahrenheit)
- **FR-031**: Integration MUST expose time format selection (12-hour/24-hour)
- **FR-032**: Integration MUST expose gallery timing configuration
- **FR-033**: Integration MUST support display mirror/flip mode
- **FR-034**: Integration MUST provide service for multi-step display sequences (reset+gif+text)
- **FR-035**: Integration MUST support notification acknowledgment pattern for persistent displays via button entity (button.pixoo_dismiss_notification) that restores previous channel/content state

#### Built-in Tools (FR-036 to FR-045)

- **FR-036**: Integration MUST expose timer control with configurable minutes and seconds
- **FR-037**: Integration MUST expose alarm control with configurable hour and minute
- **FR-038**: Integration MUST expose stopwatch control (start/stop/reset)
- **FR-039**: Integration MUST expose scoreboard with red and blue team score tracking
- **FR-040**: Integration MUST expose noise meter visualization control
- **FR-041**: Integration MUST provide service to play buzzer with configurable active/off timing
- **FR-042**: Integration MUST handle timer completion events for automation triggers
- **FR-043**: Integration MUST handle alarm trigger events for automation triggers
- **FR-044**: Integration MUST automatically disable conflicting tool modes (timer/alarm/stopwatch are mutually exclusive) when activating a new tool, logging info message for transparency
- **FR-045**: Integration MUST validate tool configuration parameters (time ranges, score limits)

#### Sensor Entities (FR-046 to FR-055)

- **FR-046**: Integration MUST expose device info sensor with model, MAC, firmware, hardware version (update once at startup)
- **FR-047**: Integration MUST expose network status sensor with WiFi signal, IP address (update every 60 seconds)
- **FR-048**: Integration MUST expose system config sensor with current brightness, rotation, mirror mode (update every 30 seconds)
- **FR-049**: Integration MUST expose weather info sensor when weather location is configured (update every 5 minutes)
- **FR-050**: Integration MUST expose time info sensor with timezone and local time (update every 60 seconds)
- **FR-051**: Integration MUST expose available animations list sensor (update on demand)
- **FR-052**: Integration MUST expose current channel sensor (read-only state, update every 30 seconds)
- **FR-053**: Integration MUST expose timer remaining sensor (update every 1 second when timer active)
- **FR-054**: Integration MUST expose alarm next trigger sensor (update every 60 seconds when alarm enabled)
- **FR-055**: Integration MUST expose stopwatch elapsed sensor (update every 1 second when stopwatch active)

#### Advanced Configuration (FR-056 to FR-065)

- **FR-056**: Integration MUST provide service to configure white balance RGB values
- **FR-057**: Integration MUST provide service to set weather location by coordinates
- **FR-058**: Integration MUST provide service to set device timezone
- **FR-059**: Integration MUST provide service to set device local time
- **FR-060**: Integration MUST provide service to create and play animation playlists
- **FR-061**: Integration MUST provide service to fetch available animations from device
- **FR-062**: Integration MUST provide service to play animation by ID
- **FR-063**: Integration MUST provide service to stop current animation playback
- **FR-064**: Integration MUST handle playlist item types (animation, cloud animation, visualization, custom page)
- **FR-065**: Integration MUST validate playlist configuration before sending to device

#### Media Player Entity (FR-066 to FR-075)

- **FR-066**: Integration MUST expose Pixoo as media_player entity for image/GIF slideshow playback (following HA best practice: light entity for brightness, media_player for content)
- **FR-067**: Integration MUST support media_player.play_media service with media_content_type "image/jpeg", "image/png", "image/gif"
- **FR-068**: Integration MUST accept local file paths via media-source:// URLs resolved through Home Assistant media source integration
- **FR-069**: Integration MUST accept external image URLs (http/https) as media_content_id with same validation as display_image service (10MB, 30s timeout, content-type)
- **FR-070**: Integration MUST support playlist playback where media_content_id is JSON array of image paths/URLs
- **FR-071**: Integration MUST implement media_player attributes: shuffle (boolean), repeat (off/all), media_duration (display time per image in seconds)
- **FR-072**: Integration MUST implement media_next_track and media_previous_track services for manual slideshow navigation
- **FR-073**: Integration MUST implement media_play, media_pause, media_stop services for slideshow control
- **FR-074**: Integration MUST maintain internal playlist state with current index, allowing pause/resume at same position
- **FR-075**: Integration MUST support mixed playlists containing both local media-source:// paths and external URLs

### Key Entities

#### Core Platform Entities

- **Pixoo Device**: Represents a physical Divoom Pixoo device, includes model information, IP address, firmware version, and connection state
- **Light Entity**: Controls device power and brightness (light.pixoo_{name}), following HA best practice for LED displays with brightness control
- **Media Player Entity**: Controls image/GIF slideshow playback (media_player.pixoo_{name}), implements playlist, shuffle, repeat, next/previous track

#### Device & Configuration Entities

- **Brightness Entity**: Number entity controlling screen brightness percentage, supports range 0-100
- **Power Entity**: Switch entity controlling device power state (screen on/off)
- **Channel Entity**: Select entity for switching between device modes (Faces, Cloud, Visualizer, Custom)
- **Clock Face Selector**: Select entity (when in Faces mode) listing available clock faces by ID
- **Visualizer Selector**: Select entity (when in Visualizer mode) listing available visualizer modes
- **Custom Page Selector**: Select entity for switching between custom channel pages (1, 2, 3)
- **Rotation Entity**: Select entity for screen rotation angle (0, 90, 180, 270 degrees)
- **Temperature Mode Entity**: Select entity for temperature unit (Celsius/Fahrenheit)
- **Time Format Entity**: Select entity for time display format (12-hour/24-hour)
- **Mirror Mode Entity**: Switch entity for horizontal display flip

#### Tool Mode Entities

- **Timer Minutes Entity**: Number entity for setting timer duration in minutes (0-99)
- **Timer Seconds Entity**: Number entity for setting timer duration in seconds (0-59)
- **Timer Enabled Entity**: Switch entity to start/stop countdown timer
- **Alarm Hour Entity**: Number entity for setting alarm hour (0-23)
- **Alarm Minute Entity**: Number entity for setting alarm minute (0-59)
- **Alarm Enabled Entity**: Switch entity to enable/disable alarm
- **Stopwatch Entity**: Switch entity to start/stop/reset stopwatch
- **Scoreboard Red Score Entity**: Number entity for red team score (0-999)
- **Scoreboard Blue Score Entity**: Number entity for blue team score (0-999)
- **Scoreboard Enabled Entity**: Switch entity to show/hide scoreboard display
- **Noise Meter Entity**: Switch entity to enable/disable noise level visualization

#### Button Entities

- **Dismiss Notification Button**: Button entity to acknowledge and dismiss persistent notifications, restoring previous channel/content state
- **Buzzer Button**: Button entity to trigger buzzer alert with configurable timing
- **Reset Buffer Button**: Button entity to clear drawing buffer
- **Push Buffer Button**: Button entity to send drawing buffer to device

#### Sensor Entities

- **Device Info Sensor**: Attributes include model, MAC address, firmware version, hardware revision
- **Network Status Sensor**: Attributes include WiFi signal strength, IP address, SSID, connection status
- **System Config Sensor**: Attributes include brightness, rotation, mirror mode, time format, temperature mode
- **Weather Info Sensor**: Attributes include current weather type, temperature, forecast (when configured)
- **Time Info Sensor**: Attributes include timezone, UTC offset, local time, 24-hour mode
- **Animation List Sensor**: Provides list of available animation IDs and names
- **Current Channel Sensor**: Read-only sensor showing active channel (Faces/Cloud/Visualizer/Custom)
- **Timer Remaining Sensor**: Shows countdown remaining time (when timer active)
- **Alarm Next Trigger Sensor**: Shows next alarm trigger time (when alarm enabled)
- **Stopwatch Elapsed Sensor**: Shows elapsed time (when stopwatch active)

#### Internal Components

- **Display Buffer**: Temporary storage for drawing operations before sending to device
- **Service Call Queue**: Manages sequential execution of display commands to prevent conflicts. Uses unlimited FIFO queue with warning log when depth exceeds 20 commands to detect automation issues.
- **Notification State**: Tracks active notifications requiring acknowledgment. Stores previous channel/content state for restoration on dismissal via button entity.
- **PixooAsync Client**: Async HTTP client from pixooasync package handling all device communication
- **Device Coordinator**: Manages device state polling with tiered update intervals: device info (once), network status (60s), system config (30s), weather (5min), tool states (1s when active)

## Success Criteria *(mandatory)*

### Measurable Outcomes

#### Core Functionality (SC-001 to SC-010)

- **SC-001**: Users can complete device setup in under 2 minutes from discovery to first control action
- **SC-002**: Brightness adjustments reflect on device within 500ms of user interaction
- **SC-003**: Image display service calls complete within 3 seconds for images under 1MB
- **SC-004**: Integration handles 10+ concurrent devices without performance degradation
- **SC-005**: 95% of automation-triggered displays execute successfully on first attempt
- **SC-006**: Device state updates in Home Assistant within 2 seconds of physical changes
- **SC-007**: Integration maintains stable connection with less than 1% failed communications over 24 hours
- **SC-008**: Users can create working automation using Pixoo services within 5 minutes
- **SC-009**: Error messages provide actionable troubleshooting guidance in 100% of failure cases
- **SC-010**: Integration supports all major Pixoo device models (Pixoo 64, Pixoo Max, Timebox Evo)

#### Display & Notifications (SC-011 to SC-015)

- **SC-011**: Notification displays with buzzer complete within 1 second of trigger
- **SC-012**: Screen rotation changes apply within 2 seconds without display corruption
- **SC-013**: Multi-line text displays correctly position all lines within screen boundaries
- **SC-014**: Custom channel switching responds within 1 second of user command
- **SC-015**: 90% of users successfully set up washing machine notification automation within 10 minutes

#### Tool Modes (SC-016 to SC-020)

- **SC-016**: Timer countdown displays update in real-time with 1-second accuracy
- **SC-017**: Alarm triggers within 5 seconds of scheduled time
- **SC-018**: Stopwatch elapsed time displays with 1-second precision
- **SC-019**: Scoreboard score updates reflect on device within 500ms of entity change
- **SC-020**: Noise meter visualization responds to ambient sound within 1 second

#### Sensors & Monitoring (SC-021 to SC-025)

- **SC-021**: Device info sensor populates all attributes within 5 seconds of integration startup
- **SC-022**: Network status sensor updates WiFi signal strength within 30 seconds of network change
- **SC-023**: System config sensor reflects configuration changes within 2 seconds
- **SC-024**: Weather info sensor updates within 60 seconds of location change
- **SC-025**: All sensor entities maintain <1% state read failure rate over 24 hours

#### Advanced Features (SC-026 to SC-030)

- **SC-026**: White balance adjustments apply without requiring device restart
- **SC-027**: Weather location service successfully geocodes and sets location in 95% of attempts
- **SC-028**: Playlist playback transitions smoothly between items without visible gaps
- **SC-029**: Animation list fetch completes within 10 seconds even for large libraries
- **SC-030**: Integration handles all 105+ pixooasync methods without exceptions when called correctly

#### Media Player Slideshow (SC-031 to SC-035)

- **SC-031**: Media player playlist with 20 images completes slideshow within expected time (20 images × duration setting ± 10%)
- **SC-032**: Image transitions in slideshow occur within 2 seconds of duration expiration
- **SC-033**: Shuffle mode randomizes playlist order with no more than 20% adjacent duplicates in 10 iterations
- **SC-034**: Next/previous track commands respond within 500ms and skip to correct image
- **SC-035**: Pause/resume maintains exact playlist position across 95% of test cases

## Real-World Use Cases *(from community feedback)*

Based on active Home Assistant community users and pixooasync capabilities, here are validated real-world applications:

### Display & Notification Use Cases

1. **Appliance Status Monitoring**: Display washing machine/dryer completion with animated GIF and buzzer, auto-dismiss when appliance emptied (using door/power sensors)
2. **Personal Reminders**: Birthday reminders with person's name and cake animation, visible until acknowledged via button helper
3. **Household Task Alerts**: Trash day reminders showing appropriate bin type (recycling/general/organic) based on schedule
4. **Security Notifications**: Doorbell press displays camera snapshot with optional buzzer alert
5. **Weather Dashboard**: Morning weather display on custom page 1 with temperature, conditions, and icon
6. **Contextual Dashboards**: Different custom pages for morning info, work focus mode, and evening relaxation visuals
7. **Package Delivery**: Delivery sensor triggers friendly notification GIF until user acknowledges receipt

### Tool Mode Use Cases

8. **Kitchen Timer**: Set cooking timer from Home Assistant automation, get visual countdown on Pixoo with buzzer alert when complete
9. **Morning Alarm**: Use Pixoo as bedroom alarm clock with visual and audio alert, integrated with wake-up routine automation
10. **Meeting Timer**: Display countdown during video calls or focus sessions, trigger break reminder when timer expires
11. **Game Score Tracking**: Use scoreboard mode for family game nights (board games, darts, cornhole), update scores from Home Assistant dashboard
12. **Noise Monitoring**: Enable noise meter during baby naptime or study sessions, trigger automation if ambient noise exceeds threshold
13. **Workout Timer**: Use stopwatch mode to track exercise duration, log workout time to Home Assistant recorder

### Sensor & Monitoring Use Cases

14. **Device Health Dashboard**: Monitor Pixoo WiFi signal strength, display warning if connection degrades
15. **Network Diagnostics**: Track device IP address and connection status, alert if device goes offline
16. **Weather Integration**: Automatically update weather location when traveling (using phone GPS), display local weather on Pixoo
17. **Time Zone Automation**: Adjust Pixoo timezone based on location for travelers, ensure clock stays accurate

### Advanced Automation Use Cases

18. **Dynamic Playlists**: Create morning playlist (weather, calendar, news animations), evening playlist (relaxation visuals), switch based on time
19. **Adaptive Brightness**: Use brightness sensor entity to adjust Pixoo brightness based on ambient light (brighter during day, dimmer at night)
20. **Color Temperature Automation**: Adjust white balance throughout day for comfortable viewing (cooler white during day, warmer at night)
21. **Multi-Device Synchronization**: Control multiple Pixoo devices together (e.g., matching displays in different rooms for whole-home notifications)
22. **Smart Scene Integration**: Include Pixoo channel/brightness in Home Assistant scenes (Movie Mode: dim Pixoo + switch to ambient visualizer)

### Media Player Gallery Use Cases

23. **Digital Photo Frame**: Use media player with local photo folder, display family photos on shuffle with 30-second intervals
24. **Rotating Art Display**: Create playlist of art images from URLs (museums, galleries), display as rotating art gallery in living room
25. **Security Camera Montage**: Build playlist of camera snapshot URLs, rotate through all security cameras every 10 seconds
26. **Dashboard Rotation**: Mix local dashboard screenshots with live URL snapshots, create rotating information display (weather, traffic, calendar)
27. **Kids' Bedtime Stories**: Create visual story sequences with image playlists, advance manually with next_track button or automatically with timer
28. **Recipe Display**: Kitchen playlist with recipe step images, use next/previous track to navigate while cooking

## Assumptions

- Users have Pixoo devices with Wi-Fi connectivity configured and connected to same network as Home Assistant
- Network allows local communication between Home Assistant host and Pixoo devices (no firewall blocking)
- Users have basic familiarity with Home Assistant UI and automation concepts
- Image files provided by users are in supported formats (PNG, JPG, GIF) - integration automatically downsamples to device resolution
- Divoom cloud API remains accessible for clock face listings and weather data
- Device firmware is reasonably up-to-date and supports core features (timer, alarm, stopwatch, etc.)
- Pillow (PIL) library is available for image processing and downsampling
- Home Assistant instance is running Python 3.12 or newer (required for pixooasync package)
- Users accept that some advanced features may require technical knowledge
- Standard Home Assistant image size limits apply (reasonable file sizes, not multi-GB uploads)
- Users can create or obtain 64x64 pixel GIF animations for custom notifications
- For notification acknowledgment, users will create helper buttons or use existing UI elements
- pixooasync package (v1.0.0+) is available and installed as integration dependency
- Device supports all tool modes (timer, alarm, stopwatch, scoreboard, noise meter) - older firmware may have limitations
- Timer, alarm, and stopwatch are mutually exclusive on device - activating one automatically disables the others
- Weather location requires valid latitude/longitude coordinates
- White balance adjustment values are in RGB format (0-100 per channel)
- Playlist animations must exist in device's animation library
- Device local time and timezone may require manual setting if not automatically configured

## Technical Foundation

### pixooasync Package Integration

This integration is built on the **pixooasync** Python package (v1.0.0+), a modern async-first library for Divoom Pixoo devices.

#### Key Package Features

**Dual Client Support**:
- `Pixoo`: Synchronous client for blocking operations
- `PixooAsync`: Asynchronous client (primary for Home Assistant integration)
- Both clients share identical API surface with async/await variants

**Type Safety**:
- Comprehensive Pydantic v2 models for all configurations and responses
- Full type hints throughout codebase (mypy validated)
- Enums for all device modes (Channel, Rotation, TemperatureMode, etc.)

**Feature Categories** (105+ methods mapped):

1. **Device Information** (8 methods):
   - `get_device_info()` - Model, MAC, firmware, hardware
   - `get_network_status()` - WiFi signal, IP, SSID
   - `get_system_config()` - Brightness, rotation, settings
   - `get_weather_info()` - Current weather and forecast
   - `get_time_info()` - Timezone, local time
   - `get_animation_list()` - Available animations
   - `get_image()` - Current display buffer
   - `ping()` - Connection check

2. **Display Control** (12 methods):
   - `set_brightness(0-100)` - Screen brightness
   - `set_screen(on/off)` - Power control
   - `set_channel(Channel)` - Mode selection
   - `set_clock(id)` - Clock face selection
   - `set_face(id)` - Alternative clock selection
   - `set_visualizer(id)` - Visualizer mode
   - `set_custom_page(1-3)` - Custom channel pages
   - `set_rotation(0/90/180/270)` - Screen orientation
   - `set_mirror_mode(bool)` - Horizontal flip
   - `set_white_balance(r, g, b)` - Color correction
   - `reset_buffer()` - Clear display buffer
   - `push_buffer()` - Send buffer to device

3. **Drawing Primitives** (8 methods):
   - `draw_pixel(x, y, color)` - Single pixel
   - `draw_character(ch, pos, color)` - Single character
   - `draw_text(text, pos, color)` - Text rendering
   - `draw_line(x1, y1, x2, y2, color)` - Line drawing
   - `draw_filled_rectangle(x1, y1, x2, y2, color)` - Filled rectangle
   - `draw_image(image)` - PIL Image display
   - `send_text(text, color, scroll)` - Scrolling text
   - `clear_text()` - Clear text display

4. **Tool Modes** (10 methods):
   - `set_timer(minutes, seconds, enabled)` - Countdown timer
   - `set_alarm(hour, minute, enabled)` - Daily alarm
   - `set_stopwatch(enabled)` - Elapsed time tracker
   - `set_scoreboard(red, blue, enabled)` - Score display
   - `set_noise_meter(enabled)` - Audio level meter
   - `play_buzzer(active_ms, off_ms, count)` - Beeper alerts
   - `get_timer_status()` - Timer state
   - `get_alarm_status()` - Alarm state
   - `get_stopwatch_status()` - Stopwatch state
   - `get_scoreboard_status()` - Current scores

5. **Animation & Playlists** (6 methods):
   - `play_animation(id)` - Play animation by ID
   - `stop_animation()` - Stop playback
   - `send_playlist(items, duration)` - Playlist creation
   - `get_animation_list()` - Fetch available animations
   - `send_gif(path)` - Upload and play GIF
   - `send_image(path)` - Upload and display image

6. **Configuration** (8 methods):
   - `set_weather_location(lat, lon)` - Weather location
   - `set_time(year, month, day, hour, minute, second)` - Device time
   - `set_timezone(timezone)` - Timezone setting
   - `set_temperature_mode(mode)` - Celsius/Fahrenheit
   - `set_time_format(format_24h)` - 12/24 hour
   - `set_gallery_timing(interval)` - Slideshow timing
   - `set_screen_brightness_auto(enabled)` - Auto brightness
   - `set_screen_rotation_auto(enabled)` - Auto rotation

#### Pydantic Models

All data structures use Pydantic v2 for validation:

- `DeviceInfo`: Device metadata (model, MAC, firmware, hardware)
- `NetworkStatus`: Network information (signal, IP, SSID)
- `SystemConfig`: Current settings (brightness, rotation, mirror, time format, temp mode)
- `WeatherInfo`: Weather data (type, temperature, forecast)
- `TimeInfo`: Time information (timezone, UTC offset, local time)
- `AlarmConfig`: Alarm settings (hour, minute, enabled)
- `TimerConfig`: Timer settings (minutes, seconds, enabled)
- `StopwatchConfig`: Stopwatch state (enabled, elapsed)
- `ScoreboardConfig`: Scoreboard state (red, blue, enabled)
- `NoiseMeterConfig`: Noise meter state (enabled)
- `BuzzerConfig`: Buzzer settings (active_ms, off_ms, count)
- `Animation`: Animation metadata (id, name)
- `PlaylistItem`: Playlist entry (type, file_id, duration)
- `Location`: Geographic coordinates (latitude, longitude)
- `WhiteBalance`: RGB balance values (r, g, b)

#### Enums

Type-safe enumerations for all device modes:

- `Channel`: FACES (0), CLOUD (1), VISUALIZER (2), CUSTOM (3)
- `Rotation`: DEG_0 (0), DEG_90 (1), DEG_180 (2), DEG_270 (3)
- `TemperatureMode`: CELSIUS (0), FAHRENHEIT (1)
- `WeatherType`: CLEAR, CLOUDY, OVERCAST, RAIN, THUNDERSTORM, SNOW, FOG, FROST (1-11)
- `TextScrollDirection`: LEFT (0), RIGHT (1)
- `PlaylistItemType`: ANIMATION, CLOUD_ANIMATION, VISUALIZATION, CUSTOM_PAGE, etc. (0-6)
- `ImageResampleMode`: PIXEL_PERFECT (0), SMOOTH (1)

#### Integration Architecture

**Primary Client**: `PixooAsync` class
- All Home Assistant operations use async methods
- Context manager support for connection lifecycle
- Automatic retry on transient failures
- Comprehensive error handling with typed exceptions

**Entity State Source**: Pydantic model attributes
- Device entities read from `DeviceInfo`, `NetworkStatus`, `SystemConfig`
- Tool entities read from `TimerConfig`, `AlarmConfig`, `StopwatchConfig`, etc.
- Sensor entities populated from model attributes

**Service Implementation**: Direct method mapping
- HA service calls map 1:1 to `PixooAsync` methods
- Pydantic validation ensures parameter correctness
- Type hints enable Home Assistant's service validation

**Discovery**: Network scanning via pixooasync
- Integration may use `pixooasync.discovery` module (if available)
- Fallback to manual IP entry in config flow

## Out of Scope

The following items are explicitly excluded from this feature:

### Device Management

- Firmware updates for Pixoo devices
- Device pairing or initial Wi-Fi setup
- Backup/restore of device content
- Device factory reset or advanced diagnostics beyond pixooasync API

### Content Creation

- Custom clock face creation tools (use Divoom mobile app)
- Custom visualizer creation
- Integration with third-party image generation services (stable diffusion, DALL-E, etc.)
- Built-in image editing or manipulation (cropping, filtering, effects)
- GIF creation or animation editing within Home Assistant

### Media & Playback

- Audio playback control (music, sounds beyond buzzer)
- Direct integration with music services (Spotify, Apple Music, etc.)
- Real-time video streaming to device
- Album art extraction from media players (users can implement via automation + image service)
- Bluetooth speaker control (if device has speakers)

### Advanced Features

- Touch screen input handling (if device supports touch)
- Device-to-device synchronization features (use Home Assistant automations for coordinated control)
- Power monitoring or energy usage tracking
- Motion detection or camera features (some Pixoo models have cameras, not in scope)
- Mobile app companion features (use native Divoom app or Home Assistant mobile app)

### Technical Limitations

- Pixel-level animation recording/playback (beyond what pixooasync provides)
- Advanced drawing features not in pixooasync (gradient fills, bezier curves, etc.)
- Real-time performance monitoring beyond basic device/network sensors
- Custom protocol extensions or reverse engineering beyond pixooasync capabilities
- Low-level buffer manipulation outside pixooasync API
- Direct hardware control (LED arrays, sensors) without pixooasync abstraction
