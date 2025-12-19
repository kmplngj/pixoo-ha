"""Constants for the Divoom Pixoo integration."""

from typing import Final

# Integration domain
DOMAIN: Final = "pixoo"

# Default values
DEFAULT_NAME: Final = "Pixoo"
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds
DEFAULT_GALLERY_INTERVAL: Final = 10  # seconds

# Entity ID prefixes
ENTITY_ID_FORMAT_LIGHT: Final = "light.pixoo_{}"
ENTITY_ID_FORMAT_MEDIA_PLAYER: Final = "media_player.pixoo_{}"
ENTITY_ID_FORMAT_NUMBER: Final = "number.pixoo_{}"
ENTITY_ID_FORMAT_SWITCH: Final = "switch.pixoo_{}"
ENTITY_ID_FORMAT_SELECT: Final = "select.pixoo_{}"
ENTITY_ID_FORMAT_SENSOR: Final = "sensor.pixoo_{}"
ENTITY_ID_FORMAT_BUTTON: Final = "button.pixoo_{}"

# Service names - Display
SERVICE_DISPLAY_IMAGE: Final = "display_image"
SERVICE_DISPLAY_IMAGE_DATA: Final = "display_image_data"
SERVICE_DISPLAY_GIF: Final = "display_gif"
SERVICE_DISPLAY_TEXT: Final = "display_text"
SERVICE_CLEAR_DISPLAY: Final = "clear_display"

# Service names - Drawing (buffer operations)
SERVICE_DRAW_PIXEL: Final = "draw_pixel"
SERVICE_DRAW_TEXT_AT_POSITION: Final = "draw_text_at_position"
SERVICE_DRAW_LINE: Final = "draw_line"
SERVICE_DRAW_RECTANGLE: Final = "draw_rectangle"
SERVICE_DRAW_FILLED_RECTANGLE: Final = "draw_filled_rectangle"
SERVICE_DRAW_IMAGE_AT_POSITION: Final = "draw_image_at_position"
SERVICE_FILL_SCREEN: Final = "fill_screen"
SERVICE_CLEAR_BUFFER: Final = "clear_buffer"
SERVICE_PUSH_BUFFER: Final = "push_buffer"

# Service names - Tool modes
SERVICE_SET_TIMER: Final = "set_timer"
SERVICE_SET_ALARM: Final = "set_alarm"
SERVICE_START_STOPWATCH: Final = "start_stopwatch"
SERVICE_RESET_STOPWATCH: Final = "reset_stopwatch"
SERVICE_SET_SCOREBOARD: Final = "set_scoreboard"
SERVICE_PLAY_BUZZER: Final = "play_buzzer"

# Service names - Configuration
SERVICE_SET_WHITE_BALANCE: Final = "set_white_balance"
SERVICE_SET_WEATHER_LOCATION: Final = "set_weather_location"
SERVICE_SET_TIMEZONE: Final = "set_timezone"
SERVICE_SET_TIME: Final = "set_time"

# Service names - Animation
SERVICE_PLAY_ANIMATION: Final = "play_animation"
SERVICE_STOP_ANIMATION: Final = "stop_animation"
SERVICE_SEND_PLAYLIST: Final = "send_playlist"
SERVICE_SET_PLAYLIST: Final = "set_playlist"
SERVICE_LIST_ANIMATIONS: Final = "list_animations"

# Service names - Media Player
SERVICE_LOAD_IMAGE: Final = "load_image"
SERVICE_LOAD_FOLDER: Final = "load_folder"
SERVICE_LOAD_PLAYLIST: Final = "load_playlist"

# Attribute names
ATTR_URL: Final = "url"
ATTR_TEXT: Final = "text"
ATTR_COLOR: Final = "color"
ATTR_SCROLL_DIRECTION: Final = "scroll_direction"
ATTR_X: Final = "x"
ATTR_Y: Final = "y"
ATTR_WIDTH: Final = "width"
ATTR_HEIGHT: Final = "height"
ATTR_FILL: Final = "fill"
ATTR_MINUTES: Final = "minutes"
ATTR_SECONDS: Final = "seconds"
ATTR_HOUR: Final = "hour"
ATTR_MINUTE: Final = "minute"
ATTR_ENABLED: Final = "enabled"
ATTR_RED_SCORE: Final = "red_score"
ATTR_BLUE_SCORE: Final = "blue_score"
ATTR_ACTIVE_MS: Final = "active_ms"
ATTR_OFF_MS: Final = "off_ms"
ATTR_COUNT: Final = "count"
ATTR_RED: Final = "red"
ATTR_GREEN: Final = "green"
ATTR_BLUE: Final = "blue"
ATTR_LATITUDE: Final = "latitude"
ATTR_LONGITUDE: Final = "longitude"
ATTR_TIMEZONE: Final = "timezone"
ATTR_ANIMATION_ID: Final = "animation_id"
ATTR_PLAYLIST: Final = "playlist"
ATTR_PATH: Final = "path"
ATTR_DURATION: Final = "duration"
ATTR_SHUFFLE: Final = "shuffle"
ATTR_ITEMS: Final = "items"
ATTR_START_X: Final = "start_x"
ATTR_START_Y: Final = "start_y"
ATTR_END_X: Final = "end_x"
ATTR_END_Y: Final = "end_y"
ATTR_TOP_LEFT_X: Final = "top_left_x"
ATTR_TOP_LEFT_Y: Final = "top_left_y"
ATTR_BOTTOM_RIGHT_X: Final = "bottom_right_x"
ATTR_BOTTOM_RIGHT_Y: Final = "bottom_right_y"
ATTR_RGB: Final = "rgb"

# Config flow
CONF_DEVICE_IP: Final = "device_ip"
CONF_DEVICE_NAME: Final = "device_name"

# Coordinator update intervals
UPDATE_INTERVAL_DEVICE: Final = None  # Once at startup
UPDATE_INTERVAL_SYSTEM: Final = 30  # seconds
UPDATE_INTERVAL_NETWORK: Final = 60  # seconds
UPDATE_INTERVAL_WEATHER: Final = 300  # seconds (5 minutes)
UPDATE_INTERVAL_TOOL: Final = 1  # second (when active)
UPDATE_INTERVAL_GALLERY: Final = 10  # seconds (on demand)

# Download limits
DOWNLOAD_TIMEOUT: Final = 30  # seconds
DOWNLOAD_MAX_SIZE: Final = 10 * 1024 * 1024  # 10MB

# Service queue
SERVICE_QUEUE_WARNING_DEPTH: Final = 20
