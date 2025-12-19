# Drawing Examples for Pixoo Home Assistant Integration

This document demonstrates how to use the buffer-based drawing services to create custom graphics and animations on your Pixoo display.

## Table of Contents

1. [Basic Drawing Workflow](#basic-drawing-workflow)
2. [Simple Examples](#simple-examples)
3. [Advanced Examples](#advanced-examples)
4. [Animation Examples](#animation-examples)
5. [Real-World Use Cases](#real-world-use-cases)

---

## Basic Drawing Workflow

The Pixoo drawing system uses a **buffer-based workflow**:

1. **Draw operations** modify an internal buffer (not visible on device yet)
2. **Push buffer** sends the buffer to the display

This allows you to draw multiple elements before displaying them, creating smooth graphics.

### Minimum Example

```yaml
service: pixoo.fill_screen
target:
  entity_id: light.pixoo_display
data:
  rgb: [255, 0, 0]  # Red

# Display the buffer
service: pixoo.push_buffer
target:
  entity_id: light.pixoo_display
```

---

## Simple Examples

### Draw a Single Pixel

```yaml
# Clear to black
service: pixoo.clear_buffer
target:
  entity_id: light.pixoo_display

# Draw white pixel at center
service: pixoo.draw_pixel
target:
  entity_id: light.pixoo_display
data:
  x: 32
  y: 32
  rgb: [255, 255, 255]

# Display
service: pixoo.push_buffer
target:
  entity_id: light.pixoo_display
```

### Draw a Line

```yaml
# Clear buffer
service: pixoo.clear_buffer
target:
  entity_id: light.pixoo_display

# Draw diagonal line (green)
service: pixoo.draw_line
target:
  entity_id: light.pixoo_display
data:
  start_x: 0
  start_y: 0
  end_x: 63
  end_y: 63
  rgb: [0, 255, 0]

# Display
service: pixoo.push_buffer
target:
  entity_id: light.pixoo_display
```

### Draw Text

```yaml
# Clear buffer
service: pixoo.clear_buffer
target:
  entity_id: light.pixoo_display

# Draw text (PICO-8 font)
service: pixoo.draw_text_at_position
target:
  entity_id: light.pixoo_display
data:
  text: "HELLO"
  x: 18
  y: 28
  rgb: [255, 255, 255]

# Display
service: pixoo.push_buffer
target:
  entity_id: light.pixoo_display
```

### Draw a Rectangle

```yaml
# Clear buffer
service: pixoo.clear_buffer
target:
  entity_id: light.pixoo_display

# Draw filled blue rectangle
service: pixoo.draw_rectangle
target:
  entity_id: light.pixoo_display
data:
  top_left_x: 10
  top_left_y: 10
  bottom_right_x: 54
  bottom_right_y: 54
  rgb: [0, 0, 255]
  fill: true

# Display
service: pixoo.push_buffer
target:
  entity_id: light.pixoo_display
```

---

## Advanced Examples

### Gradient Background

```yaml
alias: "Pixoo: Gradient Background"
sequence:
  # Clear to black
  - service: pixoo.clear_buffer
    target:
      entity_id: light.pixoo_display
  
  # Draw horizontal gradient (red to blue)
  - repeat:
      count: 64
      sequence:
        - service: pixoo.draw_line
          target:
            entity_id: light.pixoo_display
          data:
            start_x: "{{ repeat.index - 1 }}"
            start_y: 0
            end_x: "{{ repeat.index - 1 }}"
            end_y: 63
            rgb:
              - "{{ 255 - (repeat.index * 4) }}"  # Red fades out
              - 0
              - "{{ repeat.index * 4 }}"  # Blue fades in
  
  # Display
  - service: pixoo.push_buffer
    target:
      entity_id: light.pixoo_display
```

### Weather Icon

```yaml
alias: "Pixoo: Draw Weather Icon"
sequence:
  # Blue background (sky)
  - service: pixoo.fill_screen
    target:
      entity_id: light.pixoo_display
    data:
      rgb: [0, 100, 200]
  
  # Draw sun (yellow circle)
  - service: pixoo.draw_rectangle
    target:
      entity_id: light.pixoo_display
    data:
      top_left_x: 45
      top_left_y: 5
      bottom_right_x: 58
      bottom_right_y: 18
      rgb: [255, 255, 0]
      fill: true
  
  # Draw ground (green)
  - service: pixoo.draw_rectangle
    target:
      entity_id: light.pixoo_display
    data:
      top_left_x: 0
      top_left_y: 50
      bottom_right_x: 63
      bottom_right_y: 63
      rgb: [0, 150, 0]
      fill: true
  
  # Draw temperature text
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: "{{ states('sensor.outdoor_temperature') }}C"
      x: 10
      y: 28
      rgb: [255, 255, 255]
  
  # Display
  - service: pixoo.push_buffer
    target:
      entity_id: light.pixoo_display
```

### Progress Bar

```yaml
alias: "Pixoo: Draw Progress Bar"
variables:
  progress: 75  # 0-100
  bar_width: "{{ (progress * 0.6) | int }}"  # 60 pixels max
sequence:
  # Clear background
  - service: pixoo.clear_buffer
    target:
      entity_id: light.pixoo_display
  
  # Draw outline
  - service: pixoo.draw_rectangle
    target:
      entity_id: light.pixoo_display
    data:
      top_left_x: 1
      top_left_y: 26
      bottom_right_x: 62
      bottom_right_y: 37
      rgb: [255, 255, 255]
      fill: false
  
  # Draw filled progress (green)
  - service: pixoo.draw_rectangle
    target:
      entity_id: light.pixoo_display
    data:
      top_left_x: 2
      top_left_y: 27
      bottom_right_x: "{{ bar_width + 2 }}"
      bottom_right_y: 36
      rgb: [0, 255, 0]
      fill: true
  
  # Draw percentage text
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: "{{ progress }}%"
      x: 24
      y: 40
      rgb: [255, 255, 255]
  
  # Display
  - service: pixoo.push_buffer
    target:
      entity_id: light.pixoo_display
```

---

## Animation Examples

### Blinking Pixel

```yaml
alias: "Pixoo: Blinking Pixel Animation"
sequence:
  - repeat:
      count: 10
      sequence:
        # Frame 1: White pixel
        - service: pixoo.clear_buffer
          target:
            entity_id: light.pixoo_display
        - service: pixoo.draw_pixel
          target:
            entity_id: light.pixoo_display
          data:
            x: 32
            y: 32
            rgb: [255, 255, 255]
        - service: pixoo.push_buffer
          target:
            entity_id: light.pixoo_display
        - delay: 0.5
        
        # Frame 2: Black (off)
        - service: pixoo.clear_buffer
          target:
            entity_id: light.pixoo_display
        - service: pixoo.push_buffer
          target:
            entity_id: light.pixoo_display
        - delay: 0.5
```

### Moving Line

```yaml
alias: "Pixoo: Moving Line Animation"
sequence:
  - repeat:
      count: 64
      sequence:
        # Clear
        - service: pixoo.clear_buffer
          target:
            entity_id: light.pixoo_display
        
        # Draw vertical line at current position
        - service: pixoo.draw_line
          target:
            entity_id: light.pixoo_display
          data:
            start_x: "{{ repeat.index - 1 }}"
            start_y: 0
            end_x: "{{ repeat.index - 1 }}"
            end_y: 63
            rgb: [0, 255, 0]
        
        # Display
        - service: pixoo.push_buffer
          target:
            entity_id: light.pixoo_display
        
        - delay: 0.05  # 50ms between frames
```

### Color Cycle

```yaml
alias: "Pixoo: Color Cycle Animation"
sequence:
  - repeat:
      count: 360
      sequence:
        # Calculate RGB from hue
        - service: pixoo.fill_screen
          target:
            entity_id: light.pixoo_display
          data:
            rgb:
              # Simplified HSV to RGB conversion (red channel)
              - "{{ (255 * ((repeat.index % 60) / 60.0)) | int }}"
              - "{{ (255 * ((120 - repeat.index) % 60 / 60.0)) | int }}"
              - "{{ (255 * ((repeat.index - 120) % 60 / 60.0)) | int }}"
        
        - service: pixoo.push_buffer
          target:
            entity_id: light.pixoo_display
        
        - delay: 0.1
```

### Bouncing Ball

```yaml
alias: "Pixoo: Bouncing Ball Animation"
variables:
  ball_x: 32
  ball_y: 5
  velocity_y: 1
sequence:
  - repeat:
      count: 100
      sequence:
        # Calculate new position
        - variables:
            new_y: "{{ ball_y + velocity_y }}"
            new_velocity: >
              {% if new_y >= 58 %}
                {{ -velocity_y }}
              {% elif new_y <= 5 %}
                {{ -velocity_y }}
              {% else %}
                {{ velocity_y }}
              {% endif %}
        
        # Clear
        - service: pixoo.clear_buffer
          target:
            entity_id: light.pixoo_display
        
        # Draw ball (5x5 filled rectangle)
        - service: pixoo.draw_rectangle
          target:
            entity_id: light.pixoo_display
          data:
            top_left_x: "{{ ball_x - 2 }}"
            top_left_y: "{{ new_y - 2 }}"
            bottom_right_x: "{{ ball_x + 2 }}"
            bottom_right_y: "{{ new_y + 2 }}"
            rgb: [255, 0, 0]
            fill: true
        
        # Display
        - service: pixoo.push_buffer
          target:
            entity_id: light.pixoo_display
        
        # Update variables for next frame
        - variables:
            ball_y: "{{ new_y }}"
            velocity_y: "{{ new_velocity }}"
        
        - delay: 0.05
```

---

## Real-World Use Cases

### Smart Home Dashboard

```yaml
alias: "Pixoo: Smart Home Dashboard"
sequence:
  # Clear background
  - service: pixoo.clear_buffer
    target:
      entity_id: light.pixoo_display
  
  # Draw temperature icon (top left)
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: "{{ states('sensor.living_room_temperature') | round(0) }}C"
      x: 2
      y: 2
      rgb: [255, 100, 0]
  
  # Draw humidity (top right)
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: "{{ states('sensor.living_room_humidity') | round(0) }}%"
      x: 35
      y: 2
      rgb: [0, 150, 255]
  
  # Draw separator line
  - service: pixoo.draw_line
    target:
      entity_id: light.pixoo_display
    data:
      start_x: 0
      start_y: 15
      end_x: 63
      end_y: 15
      rgb: [128, 128, 128]
  
  # Draw lights status
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: >
        {% set count = states.light | selectattr('state', 'eq', 'on') | list | count %}
        LIGHTS:{{ count }}
      x: 2
      y: 20
      rgb: [255, 255, 0]
  
  # Draw door status
  - service: pixoo.draw_rectangle
    target:
      entity_id: light.pixoo_display
    data:
      top_left_x: 2
      top_left_y: 35
      bottom_right_x: 10
      bottom_right_y: 43
      rgb: >
        {% if is_state('binary_sensor.front_door', 'on') %}
          [255, 0, 0]
        {% else %}
          [0, 255, 0]
        {% endif %}
      fill: true
  
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: "DOOR"
      x: 14
      y: 38
      rgb: [255, 255, 255]
  
  # Display
  - service: pixoo.push_buffer
    target:
      entity_id: light.pixoo_display
```

### Washing Machine Timer

```yaml
alias: "Pixoo: Washing Machine Timer Display"
trigger:
  - platform: state
    entity_id: sensor.washing_machine_time_remaining
sequence:
  - variables:
      minutes_left: "{{ states('sensor.washing_machine_time_remaining') | int }}"
      progress: "{{ ((60 - minutes_left) / 60 * 100) | int }}"
  
  # Clear
  - service: pixoo.clear_buffer
    target:
      entity_id: light.pixoo_display
  
  # Draw "WASH" text
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: "WASH"
      x: 18
      y: 10
      rgb: [0, 200, 255]
  
  # Draw time remaining (large)
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: "{{ minutes_left }}m"
      x: 18
      y: 28
      rgb: [255, 255, 255]
  
  # Draw progress bar
  - service: pixoo.draw_rectangle
    target:
      entity_id: light.pixoo_display
    data:
      top_left_x: 2
      top_left_y: 50
      bottom_right_x: "{{ (progress * 0.6) | int + 2 }}"
      bottom_right_y: 56
      rgb: [0, 255, 0]
      fill: true
  
  # Display
  - service: pixoo.push_buffer
    target:
      entity_id: light.pixoo_display
```

### Music Visualizer (Simple)

```yaml
alias: "Pixoo: Simple Music Visualizer"
trigger:
  - platform: time_pattern
    seconds: "/1"  # Update every second
condition:
  - condition: state
    entity_id: media_player.spotify
    state: "playing"
sequence:
  # Clear
  - service: pixoo.clear_buffer
    target:
      entity_id: light.pixoo_display
  
  # Draw bars (simulate spectrum with random heights)
  - repeat:
      count: 16
      sequence:
        - service: pixoo.draw_rectangle
          target:
            entity_id: light.pixoo_display
          data:
            top_left_x: "{{ (repeat.index - 1) * 4 }}"
            top_left_y: "{{ 63 - (range(10, 50) | random) }}"
            bottom_right_x: "{{ (repeat.index - 1) * 4 + 2 }}"
            bottom_right_y: 63
            rgb:
              - "{{ range(100, 255) | random }}"
              - "{{ range(100, 255) | random }}"
              - 255
            fill: true
  
  # Display
  - service: pixoo.push_buffer
    target:
      entity_id: light.pixoo_display
```

### Notification Badge

```yaml
alias: "Pixoo: Notification Badge"
variables:
  notification_count: 3
sequence:
  # Clear
  - service: pixoo.clear_buffer
    target:
      entity_id: light.pixoo_display
  
  # Draw red circle background
  - service: pixoo.draw_rectangle
    target:
      entity_id: light.pixoo_display
    data:
      top_left_x: 20
      top_left_y: 20
      bottom_right_x: 44
      bottom_right_y: 44
      rgb: [255, 0, 0]
      fill: true
  
  # Draw notification count
  - service: pixoo.draw_text_at_position
    target:
      entity_id: light.pixoo_display
    data:
      text: "{{ notification_count }}"
      x: 30
      y: 30
      rgb: [255, 255, 255]
  
  # Display
  - service: pixoo.push_buffer
    target:
      entity_id: light.pixoo_display
  
  # Flash animation
  - repeat:
      count: 3
      sequence:
        - service: light.turn_off
          target:
            entity_id: light.pixoo_display
        - delay: 0.3
        - service: light.turn_on
          target:
            entity_id: light.pixoo_display
        - delay: 0.3
```

---

## Tips and Best Practices

1. **Always push the buffer**: Drawing operations don't display until you call `push_buffer`

2. **Clear between frames**: For animations, clear the buffer before drawing each frame

3. **Use variables**: Store frequently used values as variables for easier maintenance

4. **Color codes**: RGB values are [red, green, blue] with each value 0-255
   - Red: `[255, 0, 0]`
   - Green: `[0, 255, 0]`
   - Blue: `[0, 0, 255]`
   - White: `[255, 255, 255]`
   - Black: `[0, 0, 0]`

5. **Coordinate system**: Origin (0,0) is top-left corner, (63,63) is bottom-right (for Pixoo64)

6. **Text limitations**: Uses PICO-8 font (3x5 pixels per character, 4-pixel spacing)

7. **Performance**: The device can handle about 10-20 frames per second for smooth animations

8. **Templates**: Use Jinja2 templates to integrate sensor values and dynamic content

---

## Complete Automation Template

```yaml
alias: "Pixoo: Custom Drawing Template"
description: "Template for creating custom Pixoo graphics"
mode: single
sequence:
  # Step 1: Clear or fill background
  - service: pixoo.clear_buffer
    target:
      entity_id: light.pixoo_display
    data:
      rgb: [0, 0, 0]  # Black background
  
  # Step 2: Draw your graphics
  # (Add multiple draw calls here)
  
  # Step 3: Display the result
  - service: pixoo.push_buffer
    target:
      entity_id: light.pixoo_display
```

Happy drawing! 🎨
