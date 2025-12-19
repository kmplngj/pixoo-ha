"""Pydantic models for pixooasync configuration and data structures."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SimulatorConfig(BaseModel):
    """Configuration for the Pixoo simulator.

    Attributes:
        scale: Scale factor for display (1, 2, 4, or 8 recommended)
        headless: Run without GUI window (for testing/CI)
    """

    scale: int = Field(default=4, ge=1, le=16, description="Display scale factor")
    headless: bool = Field(default=False, description="Run without GUI window")

    @field_validator("scale")
    @classmethod
    def validate_scale(cls, v: int) -> int:
        """Validate that scale is reasonable."""
        if v < 1:
            raise ValueError("Scale must be at least 1")
        return v


class PixooConfig(BaseModel):
    """Configuration for Pixoo client.

    Attributes:
        address: IP address of the Pixoo device
        size: Display size in pixels (16, 32, or 64)
        debug: Enable debug logging
        refresh_connection_automatically: Auto-reset counter after 32 frames
        simulated: Enable simulator mode (no actual device communication)
        simulation_config: Configuration for simulator
        timeout: HTTP request timeout in seconds
    """

    address: str = Field(description="IP address of Pixoo device")
    size: Literal[16, 32, 64] = Field(default=64, description="Display size in pixels")
    debug: bool = Field(default=False, description="Enable debug output")
    refresh_connection_automatically: bool = Field(
        default=True, description="Automatically reset counter after 32 frames"
    )
    simulated: bool = Field(default=False, description="Run in simulator mode")
    simulation_config: SimulatorConfig = Field(
        default_factory=SimulatorConfig, description="Simulator configuration"
    )
    timeout: float = Field(default=5.0, ge=0.1, le=30.0, description="HTTP timeout in seconds")

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate IP address format."""
        if not v:
            raise ValueError("Address cannot be empty")
        return v


class PixooResponse(BaseModel):
    """Standard response from Pixoo device.

    Attributes:
        error_code: Error code (0 = success)
        error_message: Optional error message
    """

    error_code: int = Field(alias="error_code")
    error_message: str | None = Field(default=None)

    @property
    def success(self) -> bool:
        """Check if the response indicates success."""
        return self.error_code == 0


class CounterResponse(BaseModel):
    """Response from counter reset operation.

    Attributes:
        error_code: Error code (0 = success)
        counter: Current counter value (PicId in API response)
    """

    error_code: int = Field(description="Error code (0 = success)")
    counter: int = Field(alias="PicId", description="Current counter value")

    @property
    def success(self) -> bool:
        """Check if the response indicates success."""
        return self.error_code == 0


class DeviceInfo(BaseModel):
    """Device information response.

    Attributes:
        device_name: Name of the device
        device_id: Unique device identifier
        device_mac: MAC address
        hardware_version: Hardware version string
        software_version: Software/firmware version
        device_model: Model name (e.g., "Pixoo-64")
        brightness: Current brightness level (0-100)
    """

    device_name: str = Field(description="Device name")
    device_id: str = Field(description="Unique device ID")
    device_mac: str = Field(description="MAC address")
    hardware_version: str = Field(description="Hardware version")
    software_version: str = Field(description="Software version")
    device_model: str = Field(description="Device model")
    brightness: int = Field(ge=0, le=100, description="Brightness level")


class NetworkStatus(BaseModel):
    """Network status information.

    Attributes:
        ip_address: Device IP address
        mac_address: Device MAC address
        rssi: WiFi signal strength (negative dBm)
        ssid: Connected WiFi network name
        connected: Whether device is connected
    """

    ip_address: str = Field(description="IP address")
    mac_address: str = Field(description="MAC address")
    rssi: int = Field(description="WiFi signal strength (dBm)")
    ssid: str = Field(description="WiFi SSID")
    connected: bool = Field(description="Connection status")


class SystemConfig(BaseModel):
    """System configuration settings.

    Attributes:
        brightness: Display brightness (0-100)
        rotation: Screen rotation (0, 90, 180, 270)
        mirror_mode: Whether mirror mode is enabled
        white_balance_r: Red channel white balance (0-255)
        white_balance_g: Green channel white balance (0-255)
        white_balance_b: Blue channel white balance (0-255)
        time_zone: Timezone string
        hour_mode: Hour display mode (12 or 24)
        temperature_mode: Temperature unit (0=Celsius, 1=Fahrenheit)
        screen_power: Whether screen is powered on
    """

    brightness: int = Field(ge=0, le=100, description="Brightness level")
    rotation: int = Field(ge=0, le=3, description="Screen rotation")
    mirror_mode: bool = Field(description="Mirror mode enabled")
    white_balance_r: int = Field(ge=0, le=255, description="Red white balance")
    white_balance_g: int = Field(ge=0, le=255, description="Green white balance")
    white_balance_b: int = Field(ge=0, le=255, description="Blue white balance")
    time_zone: str = Field(description="Timezone")
    hour_mode: int = Field(ge=12, le=24, description="12 or 24 hour mode")
    temperature_mode: int = Field(ge=0, le=1, description="Temperature unit")
    screen_power: bool = Field(description="Screen power status")


class DiscoveredDevice(BaseModel):
    """Information about a discovered Pixoo device on the local network.

    Attributes:
        device_name: Name of the device
        device_id: Unique device identifier
        device_private_ip: Local IP address
        device_mac: MAC address
    """

    device_name: str = Field(description="Device name")
    device_id: int = Field(description="Device ID")
    device_private_ip: str = Field(description="Local IP address")
    device_mac: str = Field(description="MAC address")


class PlaylistItem(BaseModel):
    """An item in a display playlist.

    Attributes:
        type: Type of playlist item (image, text, clock, weather, animation, etc.)
        duration: Duration to display in milliseconds
        pic_id: Picture/animation ID (for IMAGE/ANIMATION types)
        text_id: Text ID (for TEXT type)
        clock_id: Clock face ID (for CLOCK type)
    """

    type: int = Field(description="Item type (0=image, 1=text, 2=clock, etc.)")
    duration: int = Field(ge=0, description="Display duration in milliseconds")
    pic_id: int | None = Field(default=None, description="Picture/animation ID")
    text_id: int | None = Field(default=None, description="Text ID")
    clock_id: int | None = Field(default=None, description="Clock face ID")


class Animation(BaseModel):
    """Information about an animation stored on the device.

    Attributes:
        pic_id: Animation ID
        file_type: File type identifier
        pic_width: Animation width in pixels
        pic_offset: Offset position
        pic_speed: Animation playback speed
        timestamp: Upload timestamp (optional)
    """

    pic_id: int = Field(alias="PicId", description="Animation ID")
    file_type: int = Field(alias="FileType", description="File type")
    pic_width: int = Field(alias="PicWidth", description="Width in pixels")
    pic_offset: int = Field(alias="PicOffset", description="Offset position")
    pic_speed: int = Field(alias="PicSpeed", description="Playback speed")
    timestamp: int | None = Field(default=None, alias="TimeStamp", description="Upload timestamp")


class AnimationList(BaseModel):
    """List of animations stored on the device.

    Attributes:
        total_number: Total number of animations
        animations: List of animation metadata
    """

    total_number: int = Field(alias="TotalNumber", description="Total animations")
    animations: list[Animation] = Field(default_factory=list, alias="PicList", description="Animation list")


class Location(BaseModel):
    """Geographic location for weather data.

    Attributes:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        city: City name (optional)
        country: Country name (optional)
    """

    longitude: str = Field(description="Longitude coordinate as string")
    latitude: str = Field(description="Latitude coordinate as string")
    city: str | None = Field(default=None, description="City name")
    country: str | None = Field(default=None, description="Country name")


class WeatherInfo(BaseModel):
    """Weather information from Device/GetWeatherInfo API.

    Attributes:
        Weather: Weather condition description (e.g., "Cloudy", "Sunny")
        CurTemp: Current temperature in Celsius
        MinTemp: Minimum temperature in Celsius
        MaxTemp: Maximum temperature in Celsius
        Pressure: Atmospheric pressure in hPa
        Humidity: Humidity percentage
        Visibility: Visibility in meters
        WindSpeed: Wind speed in m/s
    """

    Weather: str = Field(description="Weather condition")
    CurTemp: float = Field(description="Current temperature (°C)")
    MinTemp: float = Field(description="Minimum temperature (°C)")
    MaxTemp: float = Field(description="Maximum temperature (°C)")
    Pressure: int = Field(description="Atmospheric pressure (hPa)")
    Humidity: int = Field(ge=0, le=100, description="Humidity percentage")
    Visibility: int = Field(description="Visibility (meters)")
    WindSpeed: float = Field(description="Wind speed (m/s)")


class TimeInfo(BaseModel):
    """Time information from Device/GetDeviceTime API.

    Attributes:
        utc_time: UTC timestamp in seconds
        local_time: Local time as formatted string
    """

    utc_time: int = Field(alias="UTCTime", description="UTC timestamp in seconds")
    local_time: str = Field(alias="LocalTime", description="Local time string (YYYY-MM-DD HH:MM:SS)")


class WhiteBalance(BaseModel):
    """White balance/color calibration settings.

    Attributes:
        red: Red channel value (0-255)
        green: Green channel value (0-255)
        blue: Blue channel value (0-255)
    """

    red: int = Field(ge=0, le=255, description="Red channel (0-255)")
    green: int = Field(ge=0, le=255, description="Green channel (0-255)")
    blue: int = Field(ge=0, le=255, description="Blue channel (0-255)")


class TimerConfig(BaseModel):
    """Timer configuration for countdown timer.
    
    Attributes:
        enabled: Whether timer is active
        minutes: Timer duration in minutes (0-59)
        seconds: Timer duration in seconds (0-59)
    """
    enabled: bool = Field(description="Timer enabled state")
    minutes: int = Field(ge=0, le=59, description="Minutes (0-59)")
    seconds: int = Field(ge=0, le=59, description="Seconds (0-59)")


class AlarmConfig(BaseModel):
    """Alarm clock configuration.
    
    Attributes:
        enabled: Whether alarm is active
        hour: Alarm hour in 24-hour format (0-23)
        minute: Alarm minute (0-59)
    """
    enabled: bool = Field(description="Alarm enabled state")
    hour: int = Field(ge=0, le=23, description="Hour in 24-hour format (0-23)")
    minute: int = Field(ge=0, le=59, description="Minute (0-59)")


class BuzzerConfig(BaseModel):
    """Buzzer sound configuration.
    
    Attributes:
        active_time: Time buzzer is on in each cycle (milliseconds)
        off_time: Time buzzer is off in each cycle (milliseconds)
        total_time: Total duration of buzzer sequence (milliseconds)
    """
    active_time: int = Field(gt=0, description="Active time per cycle (ms)")
    off_time: int = Field(gt=0, description="Off time per cycle (ms)")
    total_time: int = Field(gt=0, description="Total play duration (ms)")


class StopwatchConfig(BaseModel):
    """Stopwatch configuration.

    Attributes:
        enabled: Whether stopwatch is active (True=start, False=stop/reset)
    """
    enabled: bool = Field(description="Stopwatch enabled state")


class ScoreboardConfig(BaseModel):
    """Scoreboard configuration.

    Attributes:
        red_score: Red team score (0-999)
        blue_score: Blue team score (0-999)
    """
    red_score: int = Field(ge=0, le=999, description="Red team score (0-999)")
    blue_score: int = Field(ge=0, le=999, description="Blue team score (0-999)")


class NoiseMeterConfig(BaseModel):
    """Noise meter configuration.

    Attributes:
        enabled: Whether noise meter is active
    """
    enabled: bool = Field(description="Noise meter enabled state")
