# Pixoo Media Player - Testing Checklist

## Manual Testing

### ✅ Basic Image Display

- [ ] Load image from HTTPS URL
- [ ] Load image from HTTP URL  
- [ ] Load image from local file (file://)
- [ ] Load image from media source (media-source://)
- [ ] Verify image displays correctly on device
- [ ] Verify entity state updates to IDLE (duration=0)

### ✅ Image with Duration

- [ ] Load image with duration=10
- [ ] Verify entity state updates to PLAYING
- [ ] Wait 10 seconds, verify image clears
- [ ] Verify entity state returns to IDLE
- [ ] Load image with duration=30
- [ ] Verify auto-clear after 30 seconds

### ✅ Folder Loading

- [ ] Load folder with images
- [ ] Verify all images detected
- [ ] Verify slideshow starts
- [ ] Wait for auto-advance (duration seconds)
- [ ] Verify second image displays
- [ ] Verify playlist loops (repeat ON)
- [ ] Verify stops at end (repeat OFF)

### ✅ Playlist Loading

- [ ] Load 3-item playlist
- [ ] Verify first image displays
- [ ] Wait for duration, verify auto-advance
- [ ] Verify all images play in order
- [ ] Load playlist with different durations
- [ ] Verify each image respects its duration

### ✅ Playback Controls

- [ ] Load slideshow and pause immediately
- [ ] Verify state = PAUSED
- [ ] Verify image stays on screen
- [ ] Call media_play, verify resume
- [ ] Call media_pause again
- [ ] Call media_stop, verify display clears
- [ ] Verify state = IDLE after stop

### ✅ Navigation

- [ ] Load 5-image playlist
- [ ] Call media_next_track
- [ ] Verify advances to image 2
- [ ] Call media_next_track 3 more times
- [ ] Verify wraps to image 1 (or stops if repeat OFF)
- [ ] Call media_previous_track
- [ ] Verify goes to last image
- [ ] Navigate forward and backward multiple times

### ✅ Shuffle Mode

- [ ] Load folder with shuffle=true
- [ ] Verify images play in random order
- [ ] Note first 3 images
- [ ] Reload with shuffle=true
- [ ] Verify different order
- [ ] Enable shuffle on existing playlist
- [ ] Verify order changes

### ✅ Repeat Mode

- [ ] Load 3-image playlist
- [ ] Enable repeat mode
- [ ] Wait for playlist to complete
- [ ] Verify loops back to first image
- [ ] Disable repeat mode
- [ ] Wait for playlist to complete
- [ ] Verify stops at end

### ✅ Media Browser

- [ ] Open HA Media Browser
- [ ] Navigate to Pixoo media player
- [ ] Browse media folders
- [ ] Click on image
- [ ] Verify displays on device
- [ ] Browse folder with multiple images
- [ ] Verify can select individual images

## Error Handling

### ✅ Invalid URLs

- [ ] Load non-existent URL
- [ ] Verify error logged
- [ ] Verify entity stays in current state
- [ ] Load URL with wrong protocol
- [ ] Verify graceful error

### ✅ Invalid Image Formats

- [ ] Try to load PDF file
- [ ] Verify error logged
- [ ] Try to load text file
- [ ] Verify error logged
- [ ] Load corrupted image
- [ ] Verify graceful handling

### ✅ Network Issues

- [ ] Load image, disconnect network during download
- [ ] Verify timeout after 30s
- [ ] Verify error logged
- [ ] Reconnect network
- [ ] Verify next operation succeeds

### ✅ Empty Folders

- [ ] Load empty folder
- [ ] Verify warning logged
- [ ] Verify entity stays in current state
- [ ] Load folder with no images (only videos)
- [ ] Verify warning about no images

### ✅ Large Files

- [ ] Try to load 15MB image
- [ ] Verify rejection (10MB limit)
- [ ] Verify error logged
- [ ] Load 9MB image
- [ ] Verify succeeds

## Automation Testing

### ✅ Doorbell Snapshot

```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.doorbell
    to: "on"
action:
  - service: pixoo.load_image
    data:
      url: "{{ state_attr('camera.front', 'entity_picture') }}"
      duration: 30
```

- [ ] Trigger doorbell
- [ ] Verify snapshot displays
- [ ] Wait 30 seconds
- [ ] Verify clears

### ✅ Scheduled Slideshow

```yaml
trigger:
  - platform: time
    at: "09:00:00"
action:
  - service: pixoo.load_folder
    data:
      path: "media-source://media_source/local/photos"
      duration: 15
      shuffle: true
```

- [ ] Set time trigger for 1 minute from now
- [ ] Wait for trigger
- [ ] Verify slideshow starts
- [ ] Verify shuffle is active
- [ ] Verify 15s per image

### ✅ Album Art Display

```yaml
trigger:
  - platform: state
    entity_id: media_player.spotify
    attribute: entity_picture
condition:
  - condition: state
    entity_id: media_player.spotify
    state: "playing"
action:
  - service: pixoo.load_image
    data:
      url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
      duration: 0
```

- [ ] Start playing music
- [ ] Verify album art displays
- [ ] Change song
- [ ] Verify new album art displays
- [ ] Pause music
- [ ] Verify album art stays (duration=0)

### ✅ Weather Rotation

```yaml
action:
  - service: pixoo.load_playlist
    data:
      items:
        - url: "{{ state_attr('weather.home', 'forecast_url') }}"
          duration: 20
        - url: "https://radar.weather.gov/image.gif"
          duration: 15
```

- [ ] Trigger automation
- [ ] Verify forecast displays for 20s
- [ ] Verify radar displays for 15s
- [ ] Verify loops back to forecast

## Edge Cases

### ✅ Concurrent Operations

- [ ] Start slideshow
- [ ] Immediately load new image
- [ ] Verify old slideshow cancelled
- [ ] Verify new image displays
- [ ] Start slideshow
- [ ] Immediately pause
- [ ] Verify pause happens immediately

### ✅ State Persistence

- [ ] Load slideshow
- [ ] Restart Home Assistant
- [ ] Verify state recovered
- [ ] Verify slideshow continues (or restarts appropriately)

### ✅ Device Offline

- [ ] Turn off Pixoo device
- [ ] Try to load image
- [ ] Verify error handling
- [ ] Verify entity marked unavailable
- [ ] Turn on device
- [ ] Verify entity becomes available

### ✅ Long Playlists

- [ ] Load 50-image playlist
- [ ] Verify all images loaded
- [ ] Verify performance acceptable
- [ ] Navigate through playlist
- [ ] Verify no memory leaks

### ✅ Special Characters

- [ ] Load image with spaces in filename
- [ ] Load image with unicode characters
- [ ] Load image with URL-encoded characters
- [ ] Verify all succeed

## Performance Testing

### ✅ Load Times

- [ ] Measure time to load 1MB image
- [ ] Should be < 5 seconds
- [ ] Measure time to load 5MB image  
- [ ] Should be < 15 seconds
- [ ] Measure time to scan 20-image folder
- [ ] Should be < 10 seconds

### ✅ Memory Usage

- [ ] Start HA, note memory usage
- [ ] Load 50-image playlist
- [ ] Note memory increase
- [ ] Stop slideshow
- [ ] Verify memory released
- [ ] Run slideshow for 1 hour
- [ ] Verify no memory leaks

### ✅ CPU Usage

- [ ] Monitor CPU during image load
- [ ] Should spike briefly then drop
- [ ] Monitor CPU during slideshow
- [ ] Should be low (<5%) between images
- [ ] Verify no CPU thrashing

## Integration Testing

### ✅ With Other Entities

- [ ] Control via light entity (brightness affects display)
- [ ] Control via select entity (channel)
- [ ] Verify entities don't conflict
- [ ] Load image via media_player
- [ ] Switch channel via select
- [ ] Verify image display cleared

### ✅ With Automations

- [ ] Multiple automations trigger media player
- [ ] Verify queue handling works
- [ ] Verify no race conditions
- [ ] Test parallel automations
- [ ] Verify proper serialization

### ✅ With Scripts

- [ ] Create script that loads images
- [ ] Call script multiple times
- [ ] Verify reliable operation
- [ ] Create template script
- [ ] Verify dynamic URL resolution

## Documentation Validation

### ✅ Examples Work

- [ ] Test all YAML examples in MEDIA_PLAYER.md
- [ ] Verify all syntax correct
- [ ] Verify all examples produce expected results
- [ ] Test automation examples
- [ ] Verify all work as documented

### ✅ Service Definitions

- [ ] Verify services.yaml matches implementation
- [ ] Verify all parameters documented
- [ ] Verify selectors work in UI
- [ ] Verify examples provided
- [ ] Verify defaults correct

## UI Testing

### ✅ Lovelace Cards

- [ ] Add media player card
- [ ] Verify play/pause/stop buttons work
- [ ] Verify next/previous buttons work
- [ ] Verify shuffle toggle works
- [ ] Verify repeat toggle works
- [ ] Verify media_image_url displays

### ✅ Service Calls

- [ ] Call pixoo.load_image from Developer Tools
- [ ] Verify UI shows all parameters
- [ ] Verify selectors work correctly
- [ ] Verify validation works
- [ ] Verify error messages clear

## Sign-off

- [ ] All critical tests passed
- [ ] All error handling verified
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Examples tested
- [ ] Ready for production

**Tested by**: ________________  
**Date**: ________________  
**Version**: ________________  
**Notes**:
