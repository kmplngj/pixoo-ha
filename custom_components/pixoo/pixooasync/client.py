"""Main Pixoo client with sync and async support."""

import base64
import logging
from typing import TYPE_CHECKING

import httpx
from PIL import Image, ImageOps

from .enums import Channel, ImageResampleMode, Rotation, TextScrollDirection
from .font import retrieve_glyph
from .models import (
    AlarmConfig,
    Animation,
    AnimationList,
    BuzzerConfig,
    CounterResponse,
    DeviceInfo,
    Location,
    NetworkStatus,
    NoiseMeterConfig,
    PixooConfig,
    PixooResponse,
    PlaylistItem,
    ScoreboardConfig,
    StopwatchConfig,
    SystemConfig,
    TimerConfig,
    TimeInfo,
    WeatherInfo,
    WhiteBalance,
)
from .palette import Palette, RGBColor
from .utils import (
    clamp,
    clamp_color,
    lerp_location,
    minimum_amount_of_steps,
    rgb_to_hex_color,
    round_location,
)

# Optional import - simulator requires tkinter which may not be available
try:
    from .simulator import Simulator
    SIMULATOR_AVAILABLE = True
except ImportError:
    Simulator = None  # type: ignore
    SIMULATOR_AVAILABLE = False

if TYPE_CHECKING:
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)


class PixooBase:
    """Base class with common Pixoo functionality."""

    def __init__(self, config: PixooConfig) -> None:
        """Initialize Pixoo base.

        Args:
            config: Pixoo configuration
        """
        self.config = config
        self.size = config.size
        self.debug = config.debug
        self.pixel_count = self.size * self.size

        self._url = f"http://{config.address}/post"
        self._buffer: list[int] = []
        self._counter = 0
        self._buffers_sent = 0
        self._refresh_counter_limit = 32
        self._simulator: Simulator | None = None

        # Initialize buffer
        self.fill()

    def _create_command_payload(self, command: str, **kwargs: object) -> dict[str, object]:
        """Create a command payload.

        Args:
            command: Command name
            **kwargs: Command parameters

        Returns:
            Command payload dictionary
        """
        return {"Command": command, **kwargs}

    def _error(self, error: dict[str, object]) -> None:
        """Log error if debug enabled.

        Args:
            error: Error dictionary
        """
        if self.debug:
            print(f"[x] Error on request {self._counter}")
            print(error)

    def _clamp_location(self, xy: tuple[int, int]) -> tuple[int, int]:
        """Clamp coordinates to screen bounds.

        Args:
            xy: Coordinates to clamp

        Returns:
            Clamped coordinates
        """
        return (
            int(clamp(xy[0], 0, self.size - 1)),
            int(clamp(xy[1], 0, self.size - 1)),
        )

    # Drawing methods
    def clear(self, rgb: RGBColor = Palette.BLACK) -> None:
        """Clear the display with a color."""
        self.fill(rgb)

    def clear_rgb(self, r: int, g: int, b: int) -> None:
        """Clear the display with RGB values."""
        self.fill((r, g, b))

    def fill(self, rgb: RGBColor = Palette.BLACK) -> None:
        """Fill the entire buffer with a color."""
        self._buffer = []
        rgb = clamp_color(rgb)
        for _ in range(self.pixel_count):
            self._buffer.extend(rgb)

    def fill_rgb(self, r: int, g: int, b: int) -> None:
        """Fill buffer with RGB values."""
        self.fill((r, g, b))

    def draw_pixel(self, xy: tuple[int, int], rgb: RGBColor) -> None:
        """Draw a single pixel.

        Args:
            xy: Pixel coordinates
            rgb: RGB color
        """
        if xy[0] < 0 or xy[0] >= self.size or xy[1] < 0 or xy[1] >= self.size:
            if self.debug:
                limit = self.size - 1
                print(f"[!] Invalid coordinates: ({xy[0]}, {xy[1]}) (max: ({limit}, {limit}))")
            return

        index = xy[0] + (xy[1] * self.size)
        self.draw_pixel_at_index(index, rgb)

    def draw_pixel_at_index(self, index: int, rgb: RGBColor) -> None:
        """Draw pixel at buffer index.

        Args:
            index: Buffer index
            rgb: RGB color
        """
        if index < 0 or index >= self.pixel_count:
            if self.debug:
                print(f"[!] Invalid index: {index} (max: {self.pixel_count - 1})")
            return

        rgb = clamp_color(rgb)
        index = index * 3
        self._buffer[index] = rgb[0]
        self._buffer[index + 1] = rgb[1]
        self._buffer[index + 2] = rgb[2]

    def draw_pixel_at_location_rgb(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Draw pixel with RGB values."""
        self.draw_pixel((x, y), (r, g, b))

    def draw_pixel_at_index_rgb(self, index: int, r: int, g: int, b: int) -> None:
        """Draw pixel at index with RGB values."""
        self.draw_pixel_at_index(index, (r, g, b))

    def draw_character(
        self, character: str, xy: tuple[int, int] = (0, 0), rgb: RGBColor = Palette.WHITE
    ) -> None:
        """Draw a single character.

        Args:
            character: Character to draw
            xy: Position
            rgb: Color
        """
        matrix = retrieve_glyph(character)
        if matrix is not None:
            for index, bit in enumerate(matrix):
                if bit == 1:
                    local_x = index % 3
                    local_y = index // 3
                    self.draw_pixel((xy[0] + local_x, xy[1] + local_y), rgb)

    def draw_character_at_location_rgb(
        self, character: str, x: int = 0, y: int = 0, r: int = 255, g: int = 255, b: int = 255
    ) -> None:
        """Draw character with RGB values."""
        self.draw_character(character, (x, y), (r, g, b))

    def draw_text(self, text: str, xy: tuple[int, int] = (0, 0), rgb: RGBColor = Palette.WHITE) -> None:
        """Draw text string.

        Args:
            text: Text to draw
            xy: Position
            rgb: Color
        """
        for index, character in enumerate(text):
            self.draw_character(character, (index * 4 + xy[0], xy[1]), rgb)

    def draw_text_at_location_rgb(self, text: str, x: int, y: int, r: int, g: int, b: int) -> None:
        """Draw text with RGB values."""
        self.draw_text(text, (x, y), (r, g, b))

    def draw_line(
        self,
        start_xy: tuple[int, int],
        stop_xy: tuple[int, int],
        rgb: RGBColor = Palette.WHITE,
    ) -> None:
        """Draw a line between two points.

        Args:
            start_xy: Start coordinates
            stop_xy: End coordinates
            rgb: Line color
        """
        line: set[tuple[int, int]] = set()
        amount_of_steps = minimum_amount_of_steps(start_xy, stop_xy)

        for step in range(amount_of_steps):
            interpolant = 0.0 if amount_of_steps == 0 else step / amount_of_steps
            line.add(round_location(lerp_location(start_xy, stop_xy, interpolant)))

        for pixel in line:
            self.draw_pixel(pixel, rgb)

    def draw_line_from_start_to_stop_rgb(
        self, start_x: int, start_y: int, stop_x: int, stop_y: int, r: int = 255, g: int = 255, b: int = 255
    ) -> None:
        """Draw line with RGB values."""
        self.draw_line((start_x, start_y), (stop_x, stop_y), (r, g, b))

    def draw_filled_rectangle(
        self,
        top_left_xy: tuple[int, int] = (0, 0),
        bottom_right_xy: tuple[int, int] = (1, 1),
        rgb: RGBColor = Palette.BLACK,
    ) -> None:
        """Draw a filled rectangle.

        Args:
            top_left_xy: Top-left corner
            bottom_right_xy: Bottom-right corner
            rgb: Fill color
        """
        for y in range(top_left_xy[1], bottom_right_xy[1] + 1):
            for x in range(top_left_xy[0], bottom_right_xy[0] + 1):
                self.draw_pixel((x, y), rgb)

    def draw_filled_rectangle_from_top_left_to_bottom_right_rgb(
        self,
        top_left_x: int = 0,
        top_left_y: int = 0,
        bottom_right_x: int = 1,
        bottom_right_y: int = 1,
        r: int = 0,
        g: int = 0,
        b: int = 0,
    ) -> None:
        """Draw filled rectangle with RGB values."""
        self.draw_filled_rectangle((top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (r, g, b))

    def draw_image(
        self,
        image_path_or_object: "str | Path | Image.Image",
        xy: tuple[int, int] = (0, 0),
        image_resample_mode: ImageResampleMode = ImageResampleMode.PIXEL_ART,
        pad_resample: bool = False,
    ) -> None:
        """Draw an image on the display.

        Args:
            image_path_or_object: Image path or PIL Image object
            xy: Position to draw at
            image_resample_mode: Resampling mode for scaling
            pad_resample: Whether to pad when resampling
        """
        image = (
            image_path_or_object
            if isinstance(image_path_or_object, Image.Image)
            else Image.open(image_path_or_object)
        )
        width, height = image.size

        # Resize if needed
        if width > self.size or height > self.size:
            pil_resample = (
                Image.Resampling.NEAREST
                if image_resample_mode == ImageResampleMode.PIXEL_ART
                else Image.Resampling.LANCZOS
            )

            if pad_resample:
                image = ImageOps.pad(image, (self.size, self.size), pil_resample)
            else:
                image.thumbnail((self.size, self.size), pil_resample)

            if self.debug:
                print(f"[.] Resized image: {(width, height)} -> {image.size}")

        # Draw pixels
        rgb_image = image.convert("RGB")
        for y in range(image.size[1]):
            for x in range(image.size[0]):
                placed_x = x + xy[0]
                placed_y = y + xy[1]

                if placed_x < 0 or placed_x >= self.size or placed_y < 0 or placed_y >= self.size:
                    continue

                self.draw_pixel((placed_x, placed_y), rgb_image.getpixel((x, y)))  # type: ignore

    def draw_image_at_location(
        self,
        image_path_or_object: "str | Path | Image.Image",
        x: int,
        y: int,
        image_resample_mode: ImageResampleMode = ImageResampleMode.PIXEL_ART,
    ) -> None:
        """Draw image at location."""
        self.draw_image(image_path_or_object, (x, y), image_resample_mode)


class Pixoo(PixooBase):
    """Synchronous Pixoo client."""

    def __init__(
        self,
        address: str,
        size: int = 64,
        debug: bool = False,
        refresh_connection_automatically: bool = True,
        simulated: bool = False,
        simulation_config: object | None = None,
    ) -> None:
        """Initialize synchronous Pixoo client.

        Args:
            address: IP address of device
            size: Display size (16, 32, or 64)
            debug: Enable debug output
            refresh_connection_automatically: Auto-reset counter
            simulated: Run in simulator mode
            simulation_config: Simulator configuration
        """
        from .models import SimulatorConfig

        if simulation_config is None:
            simulation_config = SimulatorConfig()

        config = PixooConfig(
            address=address,
            size=size,  # type: ignore
            debug=debug,
            refresh_connection_automatically=refresh_connection_automatically,
            simulated=simulated,
            simulation_config=simulation_config,  # type: ignore
        )
        super().__init__(config)

        self._client = httpx.Client(timeout=config.timeout)

        # Load counter first
        self._load_counter()

        # Reset if needed
        if self.config.refresh_connection_automatically and self._counter > self._refresh_counter_limit:
            self._reset_counter()

        # Setup simulator LAST (after counter is loaded)
        # This prevents tkinter window creation issues in tests
        if self.config.simulated:
            if not SIMULATOR_AVAILABLE:
                raise ImportError(
                    "Simulator requires tkinter which is not available. "
                    "Install tkinter or set simulated=False in PixooConfig."
                )
            self._simulator = Simulator(self, self.config.simulation_config)

    def _load_counter(self) -> None:
        """Load current counter from device."""
        if self.config.simulated:
            self._counter = 1
            return

        response = self._client.post(
            self._url, json=self._create_command_payload("Draw/GetHttpGifId")
        )
        data = CounterResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())
        else:
            self._counter = data.counter
            if self.debug:
                print(f"[.] Counter loaded: {self._counter}")

    def _reset_counter(self) -> None:
        """Reset the device counter."""
        if self.debug:
            print("[.] Resetting counter remotely")

        if self.config.simulated:
            return

        response = self._client.post(
            self._url, json=self._create_command_payload("Draw/ResetHttpGifId")
        )
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def push(self) -> None:
        """Push the current buffer to the device."""
        self._send_buffer()

    def _send_buffer(self) -> None:
        """Send buffer to device or simulator."""
        self._counter += 1

        if (
            self.config.refresh_connection_automatically
            and self._counter >= self._refresh_counter_limit
        ):
            self._reset_counter()
            self._counter = 1

        if self.debug:
            print(f"[.] Counter set to {self._counter}")

        if self.config.simulated:
            if self._simulator:
                self._simulator.display(self._buffer, self._counter)
            self._buffers_sent += 1
            return

        payload = self._create_command_payload(
            "Draw/SendHttpGif",
            PicNum=1,
            PicWidth=self.size,
            PicOffset=0,
            PicID=self._counter,
            PicSpeed=1000,
            PicData=base64.b64encode(bytearray(self._buffer)).decode(),
        )

        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())
        else:
            self._buffers_sent += 1
            if self.debug:
                print(f"[.] Pushed {self._buffers_sent} buffers")

    def send_text(
        self,
        text: str,
        xy: tuple[int, int] = (0, 0),
        color: RGBColor = Palette.WHITE,
        identifier: int = 1,
        font: int = 2,
        width: int = 64,
        movement_speed: int = 0,
        direction: TextScrollDirection = TextScrollDirection.LEFT,
    ) -> None:
        """Send scrolling text to device.

        Args:
            text: Text to display
            xy: Position
            color: Text color
            identifier: Text ID (0-19)
            font: Font ID
            width: Text width
            movement_speed: Scroll speed
            direction: Scroll direction
        """
        if self.config.simulated:
            return

        identifier = int(clamp(identifier, 0, 19))

        payload = self._create_command_payload(
            "Draw/SendHttpText",
            TextId=identifier,
            x=xy[0],
            y=xy[1],
            dir=direction,
            font=font,
            TextWidth=width,
            speed=movement_speed,
            TextString=text,
            color=rgb_to_hex_color(color),
        )

        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def set_brightness(self, brightness: int) -> None:
        """Set display brightness.

        Args:
            brightness: Brightness level (0-100)
        """
        if self.config.simulated:
            return

        brightness = int(clamp(brightness, 0, 100))

        payload = self._create_command_payload("Channel/SetBrightness", Brightness=brightness)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def set_channel(self, channel: Channel) -> None:
        """Set display channel.

        Args:
            channel: Channel to switch to
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/SetIndex", SelectIndex=int(channel))
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def set_clock(self, clock_id: int) -> None:
        """Set clock face.

        Args:
            clock_id: Clock face ID
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/SetClockSelectId", ClockId=clock_id)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def set_face(self, face_id: int) -> None:
        """Set clock face (alias for set_clock)."""
        self.set_clock(face_id)

    def set_custom_page(self, index: int) -> None:
        """Set custom page index.

        Args:
            index: Page index
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/SetCustomPageIndex", CustomPageIndex=index)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def set_custom_channel(self, index: int) -> None:
        """Set custom channel and page.

        Args:
            index: Page index
        """
        self.set_custom_page(index)
        self.set_channel(Channel.CUSTOM)

    def set_screen(self, on: bool = True) -> None:
        """Turn screen on or off.

        Args:
            on: True to turn on, False to turn off
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/OnOffScreen", OnOff=1 if on else 0)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def set_screen_on(self) -> None:
        """Turn screen on."""
        self.set_screen(True)

    def set_screen_off(self) -> None:
        """Turn screen off."""
        self.set_screen(False)

    def set_visualizer(self, equalizer_position: int) -> None:
        """Set visualizer position.

        Args:
            equalizer_position: Equalizer position
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/SetEqPosition", EqPosition=equalizer_position)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def get_device_info(self) -> DeviceInfo:
        """Get device information.

        Returns:
            Device information including name, ID, MAC address, versions, and brightness

        Example:
            >>> pixoo = Pixoo(PixooConfig(address="192.168.1.100"))
            >>> info = pixoo.get_device_info()
            >>> print(f"Device: {info.device_model} v{info.software_version}")
        """
        if self.config.simulated:
            # Return mock data for simulator
            return DeviceInfo(
                device_name="Pixoo Simulator",
                device_id="SIM-0000",
                device_mac="00:00:00:00:00:00",
                hardware_version="1.0",
                software_version="1.0.0",
                device_model=f"Pixoo-{self.size}",
                brightness=100,
            )

        payload = self._create_command_payload("Device/GetDeviceInfo")
        response = self._client.post(self._url, json=payload)
        data = response.json()

        # Parse response and create DeviceInfo
        # Note: Actual field names may vary - adjust based on real API response
        device_data = data.get("DeviceInfo", {})
        return DeviceInfo(
            device_name=device_data.get("DeviceName", "Unknown"),
            device_id=device_data.get("DeviceId", "0"),
            device_mac=device_data.get("DeviceMac", "00:00:00:00:00:00"),
            hardware_version=device_data.get("HardwareVersion", "1.0"),
            software_version=device_data.get("SoftwareVersion", "1.0.0"),
            device_model=device_data.get("DeviceModel", f"Pixoo-{self.size}"),
            brightness=device_data.get("Brightness", 50),
        )

    def get_network_status(self) -> NetworkStatus:
        """Get network status information.

        Returns:
            Network status including IP, MAC, WiFi signal strength and SSID

        Example:
            >>> pixoo = Pixoo(PixooConfig(address="192.168.1.100"))
            >>> status = pixoo.get_network_status()
            >>> print(f"WiFi: {status.ssid} (Signal: {status.rssi} dBm)")
        """
        if self.config.simulated:
            # Return mock data for simulator
            return NetworkStatus(
                ip_address=self.config.address,
                mac_address="00:00:00:00:00:00",
                rssi=-45,
                ssid="Simulator-WiFi",
                connected=True,
            )

        payload = self._create_command_payload("Device/GetNetworkStatus")
        response = self._client.post(self._url, json=payload)
        data = response.json()

        # Parse response and create NetworkStatus
        network_data = data.get("NetworkStatus", {})
        return NetworkStatus(
            ip_address=network_data.get("IpAddress", self.config.address),
            mac_address=network_data.get("MacAddress", "00:00:00:00:00:00"),
            rssi=network_data.get("RSSI", -50),
            ssid=network_data.get("SSID", "Unknown"),
            connected=network_data.get("Connected", True),
        )

    def get_system_config(self) -> SystemConfig:
        """Get system configuration settings.

        Returns:
            System configuration including brightness, rotation, white balance, and display settings

        Example:
            >>> pixoo = Pixoo(PixooConfig(address="192.168.1.100"))
            >>> config = pixoo.get_system_config()
            >>> print(f"Brightness: {config.brightness}%, Rotation: {config.rotation * 90}°")
        """
        if self.config.simulated:
            # Return mock data for simulator
            return SystemConfig(
                brightness=100,
                rotation=0,
                mirror_mode=False,
                white_balance_r=255,
                white_balance_g=255,
                white_balance_b=255,
                time_zone="UTC",
                hour_mode=24,
                temperature_mode=0,
                screen_power=True,
            )

        payload = self._create_command_payload("Device/GetSystemConfig")
        response = self._client.post(self._url, json=payload)
        data = response.json()

        # Parse response and create SystemConfig
        config_data = data.get("SystemConfig", {})
        return SystemConfig(
            brightness=config_data.get("Brightness", 50),
            rotation=config_data.get("Rotation", 0),
            mirror_mode=config_data.get("MirrorMode", False),
            white_balance_r=config_data.get("WhiteBalanceR", 255),
            white_balance_g=config_data.get("WhiteBalanceG", 255),
            white_balance_b=config_data.get("WhiteBalanceB", 255),
            time_zone=config_data.get("TimeZone", "UTC"),
            hour_mode=config_data.get("HourMode", 24),
            temperature_mode=config_data.get("TemperatureMode", 0),
            screen_power=config_data.get("ScreenPower", True),
        )

    def send_playlist(self, items: list[PlaylistItem]) -> None:
        """Send a playlist of items to display in sequence.

        Args:
            items: List of playlist items to display

        Example:
            >>> from pixoo import Pixoo, PlaylistItem, PlaylistItemType
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> playlist = [
            ...     PlaylistItem(type=PlaylistItemType.IMAGE, duration=5000, pic_id=1),
            ...     PlaylistItem(type=PlaylistItemType.CLOCK, duration=10000, clock_id=1),
            ... ]
            >>> pixoo.send_playlist(playlist)
        """
        if self.config.simulated:
            return

        # Convert playlist items to API format
        item_list = []
        for item in items:
            item_dict = {"type": item.type, "duration": item.duration}
            if item.pic_id is not None:
                item_dict["pic_id"] = item.pic_id
            if item.text_id is not None:
                item_dict["text_id"] = item.text_id
            if item.clock_id is not None:
                item_dict["clock_id"] = item.clock_id
            item_list.append(item_dict)

        payload = self._create_command_payload("Draw/SendHttpItemList", ItemList=item_list)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def play_animation(self, pic_id: int) -> None:
        """Play an animation by ID.

        Args:
            pic_id: Animation ID to play

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> pixoo.play_animation(pic_id=5)
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Draw/PlayHttpGif", FileType=2, PicId=pic_id)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def stop_animation(self) -> None:
        """Stop the currently playing animation.

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> pixoo.stop_animation()
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Draw/StopHttpGif")
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def get_animation_list(self) -> AnimationList:
        """Get list of animations stored on the device.

        Returns:
            List of animations with metadata

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> animations = pixoo.get_animation_list()
            >>> for anim in animations.animations:
            ...     print(f"Animation {anim.pic_id}: {anim.pic_width}x{anim.pic_width}")
        """
        if self.config.simulated:
            return AnimationList.model_validate({"TotalNumber": 0, "PicList": []})

        payload = self._create_command_payload("Draw/GetHttpGifList")
        response = self._client.post(self._url, json=payload)
        data = response.json()

        # Check for error response
        if "error_code" in data and data.get("error_code") != 0:
            if self.debug:
                print(f"[!] GetHttpGifList returned error: {data}")
            # Return empty list on error
            return AnimationList.model_validate({"TotalNumber": 0, "PicList": []})

        # Parse response using model_validate to handle aliases
        return AnimationList.model_validate(data)

    def clear_text(self, text_id: int = 0) -> None:
        """Clear text display by ID.

        Args:
            text_id: Text ID to clear (default: 0 for all)

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> pixoo.clear_text(text_id=1)
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Draw/ClearHttpText", TextId=text_id)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    # ===== Phase 3: Weather & Time APIs =====

    def set_weather_location(self, location: Location) -> None:
        """Set weather location for weather display.

        Args:
            location: Location with longitude, latitude, and optional city/country

        Example:
            >>> from .models import Location
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> loc = Location(longitude="13.404954", latitude="52.520008",
            ...                city="Berlin", country="DE")
            >>> pixoo.set_weather_location(loc)
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload(
            "Channel/SetWeatherArea",
            Longitude=location.longitude,
            Latitude=location.latitude,
        )
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def get_weather_info(self) -> WeatherInfo | None:
        """Get current weather information.

        Returns:
            WeatherInfo object or None if not available

        Note:
            This API may not be fully implemented in all firmware versions.
            Returns None if weather data is not available.

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> weather = pixoo.get_weather_info()
            >>> if weather:
            ...     print(f"Temperature: {weather.temperature}°C")
        """
        if self.config.simulated:
            return None

        response = self._client.post(
            self._url, json=self._create_command_payload("Device/GetWeatherInfo")
        )
        result = response.json()

        # API may return error if weather not configured
        if result.get("error_code") != 0:
            return None

        try:
            return WeatherInfo.model_validate(result)
        except Exception:
            return None

    def set_time(self, utc_timestamp: int) -> None:
        """Set device time using UTC timestamp.

        Args:
            utc_timestamp: Unix timestamp in seconds (UTC)

        Example:
            >>> import time
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> pixoo.set_time(int(time.time()))
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Device/SetUTC", Utc=utc_timestamp)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def set_timezone(self, timezone: str) -> None:
        """Set device timezone.

        Args:
            timezone: Timezone string (e.g., "GMT-8", "GMT+1")

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> pixoo.set_timezone("GMT+1")
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Sys/TimeZone", TimeZoneValue=timezone)
        response = self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    def get_time_info(self) -> TimeInfo | None:
        """Get current time information from device.

        Returns:
            TimeInfo object or None if not available

        Note:
            This API may not be fully implemented in all firmware versions.

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> time_info = pixoo.get_time_info()
            >>> if time_info:
            ...     print(f"UTC: {time_info.utc_timestamp}")
        """
        if self.config.simulated:
            return None

        response = self._client.post(
            self._url, json=self._create_command_payload("Device/GetDeviceTime")
        )
        result = response.json()

        # API may return error if not supported
        if result.get("error_code") != 0:
            return None

        try:
            return TimeInfo.model_validate(result)
        except Exception:
            return None

    # ===== Phase 4: Display Controls =====

    def set_rotation(self, rotation: Rotation) -> bool:
        """Set screen rotation angle.

        Args:
            rotation: Rotation angle (NORMAL, ROTATE_90, ROTATE_180, ROTATE_270)

        Returns:
            True if successful, False if not supported by firmware

        Note:
            This API may not be implemented in all firmware versions.

        Example:
            >>> from pixoo import Pixoo, Rotation
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> if pixoo.set_rotation(Rotation.ROTATE_180):
            ...     print("Rotation set")
        """
        if self.config.simulated:
            return True

        payload = self._create_command_payload(
            "Device/SetScreenRotationAngle", Mode=rotation.value
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def set_white_balance(self, red: int, green: int, blue: int) -> bool:
        """Set white balance/color calibration.

        Args:
            red: Red channel value (0-255)
            green: Green channel value (0-255)
            blue: Blue channel value (0-255)

        Returns:
            True if successful, False if not supported by firmware

        Note:
            This API may not be implemented in all firmware versions.

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> if pixoo.set_white_balance(255, 200, 200):  # Warm tint
            ...     print("White balance set")
        """
        if self.config.simulated:
            return True

        # Validate ranges
        red = int(clamp(red, 0, 255))
        green = int(clamp(green, 0, 255))
        blue = int(clamp(blue, 0, 255))

        payload = self._create_command_payload(
            "Device/SetWhiteBalance", RValue=red, GValue=green, BValue=blue
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def set_mirror_mode(self, enabled: bool) -> bool:
        """Enable or disable mirror mode (horizontal flip).

        Args:
            enabled: True to enable mirror mode, False to disable

        Returns:
            True if successful, False if not supported by firmware

        Note:
            This API may not be implemented in all firmware versions.

        Example:
            >>> pixoo = Pixoo(address="192.168.1.100")
            >>> if pixoo.set_mirror_mode(True):  # Mirror display
            ...     print("Mirror mode enabled")
        """
        if self.config.simulated:
            return True

        payload = self._create_command_payload(
            "Device/SetMirrorMode", Mode=1 if enabled else 0
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def set_timer(self, minutes: int = 0, seconds: int = 0, enabled: bool = True) -> bool:
        """Set countdown timer.

        Args:
            minutes: Timer duration in minutes (0-59)
            seconds: Timer duration in seconds (0-59)
            enabled: Whether to enable (True) or disable (False) the timer

        Returns:
            True if timer was set successfully, False if not supported

        Example:
            >>> pixoo.set_timer(minutes=5, seconds=30)  # 5:30 countdown
            True
            >>> pixoo.set_timer(minutes=0, seconds=0, enabled=False)  # Disable timer
            True
        """
        from .utils import clamp

        config = TimerConfig(
            enabled=enabled,
            minutes=int(clamp(minutes, 0, 59)),
            seconds=int(clamp(seconds, 0, 59)),
        )

        payload = self._create_command_payload(
            "Tools/SetTimer",
            Status=1 if config.enabled else 0,
            Minute=config.minutes,
            Second=config.seconds,
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def set_alarm(self, hour: int, minute: int, enabled: bool = True) -> bool:
        """Set alarm clock.

        Args:
            hour: Alarm hour in 24-hour format (0-23)
            minute: Alarm minute (0-59)
            enabled: Whether to enable (True) or disable (False) the alarm

        Returns:
            True if alarm was set successfully, False if not supported

        Example:
            >>> pixoo.set_alarm(hour=7, minute=30)  # 7:30 AM alarm
            True
            >>> pixoo.set_alarm(hour=0, minute=0, enabled=False)  # Disable alarm
            True
        """
        from .utils import clamp

        config = AlarmConfig(
            enabled=enabled,
            hour=int(clamp(hour, 0, 23)),
            minute=int(clamp(minute, 0, 59)),
        )

        payload = self._create_command_payload(
            "Device/SetAlarm",
            Status=1 if config.enabled else 0,
            Hour=config.hour,
            Minute=config.minute,
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def play_buzzer(
        self, active_time: int = 500, off_time: int = 500, total_time: int = 3000
    ) -> bool:
        """Play buzzer sound with specified timing pattern.

        Args:
            active_time: Time buzzer is on in each cycle (milliseconds)
            off_time: Time buzzer is off in each cycle (milliseconds)
            total_time: Total duration of buzzer sequence (milliseconds)

        Returns:
            True if buzzer played successfully, False if not supported

        Example:
            >>> pixoo.play_buzzer(active_time=500, off_time=500, total_time=3000)
            True
            >>> pixoo.play_buzzer(active_time=100, off_time=100, total_time=1000)  # Fast beep
            True
        """
        config = BuzzerConfig(
            active_time=max(1, active_time),
            off_time=max(1, off_time),
            total_time=max(1, total_time),
        )

        payload = self._create_command_payload(
            "Device/PlayBuzzer",
            ActiveTimeInCycle=config.active_time,
            OffTimeInCycle=config.off_time,
            PlayTotalTime=config.total_time,
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def set_stopwatch(self, enabled: bool = True) -> bool:
        """Control stopwatch.

        Args:
            enabled: True to start stopwatch, False to stop/reset

        Returns:
            True if stopwatch was controlled successfully, False if not supported

        Example:
            >>> pixoo.set_stopwatch(enabled=True)  # Start stopwatch
            True
            >>> pixoo.set_stopwatch(enabled=False)  # Stop/reset stopwatch
            True
        """
        config = StopwatchConfig(enabled=enabled)

        payload = self._create_command_payload(
            "Tools/SetStopWatch",
            Status=1 if config.enabled else 0,
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def set_scoreboard(self, red_score: int = 0, blue_score: int = 0) -> bool:
        """Set scoreboard scores.

        Args:
            red_score: Red team score (0-999)
            blue_score: Blue team score (0-999)

        Returns:
            True if scoreboard was set successfully, False if not supported

        Example:
            >>> pixoo.set_scoreboard(red_score=3, blue_score=5)
            True
            >>> pixoo.set_scoreboard(red_score=0, blue_score=0)  # Reset scores
            True
        """
        from .utils import clamp

        config = ScoreboardConfig(
            red_score=int(clamp(red_score, 0, 999)),
            blue_score=int(clamp(blue_score, 0, 999)),
        )

        payload = self._create_command_payload(
            "Tools/SetScoreBoard",
            RedScore=config.red_score,
            BlueScore=config.blue_score,
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def set_noise_meter(self, enabled: bool = True) -> bool:
        """Control noise meter display.

        Args:
            enabled: True to enable noise meter, False to disable

        Returns:
            True if noise meter was controlled successfully, False if not supported

        Example:
            >>> pixoo.set_noise_meter(enabled=True)
            True
            >>> pixoo.set_noise_meter(enabled=False)
            True
        """
        config = NoiseMeterConfig(enabled=enabled)

        payload = self._create_command_payload(
            "Tools/SetNoiseStatus",
            NoiseStatus=1 if config.enabled else 0,
        )
        response = self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    def __enter__(self) -> "Pixoo":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self._client.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()


class PixooAsync(PixooBase):
    """Asynchronous Pixoo client."""

    def __init__(
        self,
        address: str,
        size: int = 64,
        debug: bool = False,
        refresh_connection_automatically: bool = True,
        simulated: bool = False,
        simulation_config: object | None = None,
    ) -> None:
        """Initialize async Pixoo client.

        Args:
            address: IP address of device
            size: Display size (16, 32, or 64)
            debug: Enable debug output
            refresh_connection_automatically: Auto-reset counter
            simulated: Run in simulator mode
            simulation_config: Simulator configuration
        """
        from .models import SimulatorConfig

        if simulation_config is None:
            simulation_config = SimulatorConfig()

        config = PixooConfig(
            address=address,
            size=size,  # type: ignore
            debug=debug,
            refresh_connection_automatically=refresh_connection_automatically,
            simulated=simulated,
            simulation_config=simulation_config,  # type: ignore
        )
        super().__init__(config)

        self._client: httpx.AsyncClient | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the async client (load counter, setup simulator).

        This must be called before using the client to avoid blocking SSL operations.
        """
        if self._initialized:
            return

        # Create client in executor to avoid blocking SSL operations
        if self._client is None:
            import asyncio
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None, lambda: httpx.AsyncClient(timeout=self.config.timeout)
            )

        await self._load_counter()

        if self.config.refresh_connection_automatically and self._counter > self._refresh_counter_limit:
            await self._reset_counter()

        if self.config.simulated:
            if not SIMULATOR_AVAILABLE:
                raise ImportError(
                    "Simulator requires tkinter which is not available. "
                    "Install tkinter or set simulated=False in PixooConfig."
                )
            self._simulator = Simulator(self, self.config.simulation_config)

        self._initialized = True

    async def _load_counter(self) -> None:
        """Load current counter from device."""
        if self.config.simulated:
            self._counter = 1
            return

        response = await self._client.post(
            self._url, json=self._create_command_payload("Draw/GetHttpGifId")
        )
        data = CounterResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())
        else:
            self._counter = data.counter
            if self.debug:
                print(f"[.] Counter loaded: {self._counter}")

    async def _reset_counter(self) -> None:
        """Reset the device counter."""
        if self.debug:
            print("[.] Resetting counter remotely")

        if self.config.simulated:
            return

        response = await self._client.post(
            self._url, json=self._create_command_payload("Draw/ResetHttpGifId")
        )
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def push(self) -> None:
        """Push the current buffer to the device."""
        await self._send_buffer()

    async def _send_buffer(self) -> None:
        """Send buffer to device or simulator."""
        self._counter += 1

        if (
            self.config.refresh_connection_automatically
            and self._counter >= self._refresh_counter_limit
        ):
            await self._reset_counter()
            self._counter = 1

        if self.debug:
            print(f"[.] Counter set to {self._counter}")

        if self.config.simulated:
            if self._simulator:
                self._simulator.display(self._buffer, self._counter)
            self._buffers_sent += 1
            return

        payload = self._create_command_payload(
            "Draw/SendHttpGif",
            PicNum=1,
            PicWidth=self.size,
            PicOffset=0,
            PicID=self._counter,
            PicSpeed=1000,
            PicData=base64.b64encode(bytearray(self._buffer)).decode(),
        )

        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())
        else:
            self._buffers_sent += 1
            if self.debug:
                print(f"[.] Pushed {self._buffers_sent} buffers")

    async def send_text(
        self,
        text: str,
        xy: tuple[int, int] = (0, 0),
        color: RGBColor = Palette.WHITE,
        identifier: int = 1,
        font: int = 2,
        width: int = 64,
        movement_speed: int = 0,
        direction: TextScrollDirection = TextScrollDirection.LEFT,
    ) -> None:
        """Send scrolling text to device."""
        if self.config.simulated:
            return

        identifier = int(clamp(identifier, 0, 19))

        payload = self._create_command_payload(
            "Draw/SendHttpText",
            TextId=identifier,
            x=xy[0],
            y=xy[1],
            dir=direction,
            font=font,
            TextWidth=width,
            speed=movement_speed,
            TextString=text,
            color=rgb_to_hex_color(color),
        )

        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def set_brightness(self, brightness: int) -> None:
        """Set display brightness."""
        if self.config.simulated:
            return

        brightness = int(clamp(brightness, 0, 100))

        payload = self._create_command_payload("Channel/SetBrightness", Brightness=brightness)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def set_channel(self, channel: Channel) -> None:
        """Set display channel."""
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/SetIndex", SelectIndex=int(channel))
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def set_clock(self, clock_id: int) -> None:
        """Set clock face."""
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/SetClockSelectId", ClockId=clock_id)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def set_face(self, face_id: int) -> None:
        """Set clock face (alias for set_clock)."""
        await self.set_clock(face_id)

    async def set_custom_page(self, index: int) -> None:
        """Set custom page index."""
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/SetCustomPageIndex", CustomPageIndex=index)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def set_custom_channel(self, index: int) -> None:
        """Set custom channel and page."""
        await self.set_custom_page(index)
        await self.set_channel(Channel.CUSTOM)

    async def set_screen(self, on: bool = True) -> None:
        """Turn screen on or off."""
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/OnOffScreen", OnOff=1 if on else 0)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def set_screen_on(self) -> None:
        """Turn screen on."""
        await self.set_screen(True)

    async def set_screen_off(self) -> None:
        """Turn screen off."""
        await self.set_screen(False)

    async def set_visualizer(self, equalizer_position: int) -> None:
        """Set visualizer position."""
        if self.config.simulated:
            return

        payload = self._create_command_payload("Channel/SetEqPosition", EqPosition=equalizer_position)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    # get_device_info() and get_network_status() removed:
    # Device/GetDeviceInfo and Device/GetNetworkStatus APIs don't work (return "Request data illegal json")
    # Use find_device_on_lan() for real MAC address via cloud discovery API instead

    async def get_all_channel_config(self) -> dict:
        """Get all channel configuration (works on real devices!).

        This API actually works and returns real values including brightness,
        rotation, mirror mode, power state, clock settings, and more.

        Returns:
            Dictionary with all channel configuration settings

        Example:
            >>> async with PixooAsync(PixooConfig(address="192.168.1.100")) as pixoo:
            ...     config = await pixoo.get_all_channel_config()
            ...     print(f"Brightness: {config['Brightness']}%")
            ...     print(f"Current Clock: {config['CurClockId']}")
        """
        if self.config.simulated:
            # Return mock data for simulator
            return {
                "Brightness": 100,
                "RotationFlag": 0,
                "MirrorFlag": 0,
                "LightSwitch": 1,
                "Time24Flag": 1,
                "TemperatureMode": 0,
                "GyrateAngle": 0,
                "CurClockId": 182,
                "PowerOnChannelId": 1,
                "ClockTime": 5,
                "GalleryTime": 5,
                "SingleGalleyTime": 5,
                "GalleryShowTimeFlag": 0,
            }

        payload = self._create_command_payload("Channel/GetAllConf")
        response = await self._client.post(self._url, json=payload)
        
        # Check response status
        response.raise_for_status()
        
        # Parse JSON with error handling
        try:
            data = response.json()
        except Exception as json_err:
            raise ValueError(f"Failed to parse response from Channel/GetAllConf: {json_err}") from json_err
        
        return data

    async def get_current_channel(self) -> int:
        """Get current channel index.

        Returns:
            Channel index: 0=Faces, 1=Cloud, 2=Visualizer, 3=Custom

        Example:
            >>> async with PixooAsync(PixooConfig(address="192.168.1.100")) as pixoo:
            ...     channel_idx = await pixoo.get_current_channel()
            ...     channels = ["Faces", "Cloud", "Visualizer", "Custom"]
            ...     print(f"Current channel: {channels[channel_idx]}")
        """
        if self.config.simulated:
            return 1  # Default to Cloud channel in simulator

        payload = self._create_command_payload("Channel/GetIndex")
        response = await self._client.post(self._url, json=payload)
        
        # Check response status
        response.raise_for_status()
        
        # Parse JSON with error handling
        try:
            data = response.json()
        except Exception as json_err:
            raise ValueError(f"Failed to parse response from Channel/GetIndex: {json_err}") from json_err
        
        return data.get("SelectIndex", 0)

    @staticmethod
    async def find_device_on_lan() -> dict | None:
        """Find Pixoo device on local network via cloud discovery API.

        This method uses Divoom's cloud API to discover devices on the same LAN.
        Returns the first device found.

        Returns:
            Device information dict with DeviceName, DevicePrivateIP, DeviceMac, DeviceId,
            or None if no device found

        Example:
            >>> device = await PixooAsync.find_device_on_lan()
            >>> if device:
            ...     print(f"Found: {device['DeviceName']} at {device['DevicePrivateIP']}")
            ...     print(f"MAC: {device['DeviceMac']}")
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://app.divoom-gz.com/Device/ReturnSameLANDevice"
                )
                data = response.json()
                if data.get("ReturnCode") == 0:
                    device_list = data.get("DeviceList", [])
                    if device_list:
                        return device_list[0]  # Return first device
        except Exception:
            pass
        return None

    async def get_system_config(self) -> SystemConfig:
        """Get system configuration settings.

        Note: This method now uses Channel/GetAllConf API which actually works
        on real devices, unlike Device/GetSystemConfig which returns errors.

        Returns:
            System configuration including brightness, rotation, white balance, and display settings

        Example:
            >>> async with PixooAsync(PixooConfig(address="192.168.1.100")) as pixoo:
            ...     config = await pixoo.get_system_config()
            ...     print(f"Brightness: {config.brightness}%, Rotation: {config.rotation * 90}°")
        """
        if self.config.simulated:
            # Return mock data for simulator
            return SystemConfig(
                brightness=100,
                rotation=0,
                mirror_mode=False,
                white_balance_r=255,
                white_balance_g=255,
                white_balance_b=255,
                time_zone="UTC",
                hour_mode=24,
                temperature_mode=0,
                screen_power=True,
            )

        # Use Channel/GetAllConf instead of broken Device/GetSystemConfig
        data = await self.get_all_channel_config()

        # Map Channel/GetAllConf response to SystemConfig
        return SystemConfig(
            brightness=data.get("Brightness", 50),
            rotation=data.get("GyrateAngle", 0) // 90,  # 0,90,180,270 -> 0,1,2,3
            mirror_mode=bool(data.get("MirrorFlag", 0)),
            screen_power=bool(data.get("LightSwitch", 1)),
            hour_mode=24 if data.get("Time24Flag", 1) else 12,
            temperature_mode=data.get("TemperatureMode", 0),
            # These aren't in Channel/GetAllConf, use defaults
            white_balance_r=255,
            white_balance_g=255,
            white_balance_b=255,
            time_zone="UTC",
        )

    async def send_playlist(self, items: list[PlaylistItem]) -> None:
        """Send a playlist of items to display in sequence.

        Args:
            items: List of playlist items to display

        Example:
            >>> from pixoo import PixooAsync, PlaylistItem, PlaylistItemType
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     playlist = [
            ...         PlaylistItem(type=PlaylistItemType.IMAGE, duration=5000, pic_id=1),
            ...         PlaylistItem(type=PlaylistItemType.CLOCK, duration=10000, clock_id=1),
            ...     ]
            ...     await pixoo.send_playlist(playlist)
        """
        if self.config.simulated:
            return

        # Convert playlist items to API format
        item_list = []
        for item in items:
            item_dict = {"type": item.type, "duration": item.duration}
            if item.pic_id is not None:
                item_dict["pic_id"] = item.pic_id
            if item.text_id is not None:
                item_dict["text_id"] = item.text_id
            if item.clock_id is not None:
                item_dict["clock_id"] = item.clock_id
            item_list.append(item_dict)

        payload = self._create_command_payload("Draw/SendHttpItemList", ItemList=item_list)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def play_animation(self, pic_id: int) -> None:
        """Play an animation by ID.

        Args:
            pic_id: Animation ID to play

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     await pixoo.play_animation(pic_id=5)
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Draw/PlayHttpGif", FileType=2, PicId=pic_id)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def stop_animation(self) -> None:
        """Stop the currently playing animation.

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     await pixoo.stop_animation()
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Draw/StopHttpGif")
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def get_animation_list(self) -> AnimationList:
        """Get list of animations stored on the device.

        Returns:
            List of animations with metadata

        Note:
            Draw/GetHttpGifList API returns "Request data illegal json" on most devices.
            This method always returns an empty list.

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     animations = await pixoo.get_animation_list()
            ...     for anim in animations.animations:
            ...         print(f"Animation {anim.pic_id}: {anim.pic_width}x{anim.pic_width}")
        """
        if self.config.simulated:
            return AnimationList.model_validate({"TotalNumber": 0, "PicList": []})

        payload = self._create_command_payload("Draw/GetHttpGifList")
        response = await self._client.post(self._url, json=payload)
        data = response.json()

        # API returns "Request data illegal json" on real devices - always return empty list
        if "error_code" in data and data.get("error_code") != 0:
            if self.debug:
                print(f"[!] GetHttpGifList returned error: {data}")
            return AnimationList.model_validate({"TotalNumber": 0, "PicList": []})

        # Parse response using model_validate to handle aliases
        return AnimationList.model_validate(data)

    async def clear_text(self, text_id: int = 0) -> None:
        """Clear text display by ID.

        Args:
            text_id: Text ID to clear (default: 0 for all)

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     await pixoo.clear_text(text_id=1)
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Draw/ClearHttpText", TextId=text_id)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    # ===== Phase 3: Weather & Time APIs =====

    async def set_weather_location(self, location: Location) -> None:
        """Set weather location for weather display.

        Args:
            location: Location with longitude, latitude, and optional city/country

        Example:
            >>> from .models import Location
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     loc = Location(longitude="13.404954", latitude="52.520008",
            ...                    city="Berlin", country="DE")
            ...     await pixoo.set_weather_location(loc)
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload(
            "Channel/SetWeatherArea",
            Longitude=location.longitude,
            Latitude=location.latitude,
        )
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def get_weather_info(self) -> WeatherInfo | None:
        """Get current weather information.

        Returns:
            WeatherInfo object or None if not available

        Note:
            This API may not be fully implemented in all firmware versions.
            Returns None if weather data is not available.

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     weather = await pixoo.get_weather_info()
            ...     if weather:
            ...         print(f"Temperature: {weather.temperature}°C")
        """
        if self.config.simulated:
            return None

        response = await self._client.post(
            self._url, json=self._create_command_payload("Device/GetWeatherInfo")
        )
        
        # Check response status
        try:
            response.raise_for_status()
            result = response.json()
        except Exception as err:
            _LOGGER.debug("Failed to get weather info: %s", err)
            return None

        # API may return error if weather not configured
        if result.get("error_code") != 0:
            return None

        try:
            return WeatherInfo.model_validate(result)
        except Exception:
            return None

    async def set_time(self, utc_timestamp: int) -> None:
        """Set device time using UTC timestamp.

        Args:
            utc_timestamp: Unix timestamp in seconds (UTC)

        Example:
            >>> import time
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     await pixoo.set_time(int(time.time()))
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Device/SetUTC", Utc=utc_timestamp)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def set_timezone(self, timezone: str) -> None:
        """Set device timezone.

        Args:
            timezone: Timezone string (e.g., "GMT-8", "GMT+1")

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     await pixoo.set_timezone("GMT+1")
        """
        if self.config.simulated:
            return

        payload = self._create_command_payload("Sys/TimeZone", TimeZoneValue=timezone)
        response = await self._client.post(self._url, json=payload)
        data = PixooResponse.model_validate(response.json())

        if not data.success:
            self._error(response.json())

    async def get_time_info(self) -> TimeInfo | None:
        """Get current time information from device.

        Returns:
            TimeInfo object or None if not available

        Note:
            This API may not be fully implemented in all firmware versions.

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     time_info = await pixoo.get_time_info()
            ...     if time_info:
            ...         print(f"UTC: {time_info.utc_timestamp}")
        """
        if self.config.simulated:
            return None

        response = await self._client.post(
            self._url, json=self._create_command_payload("Device/GetDeviceTime")
        )
        
        # Check response status and parse JSON
        try:
            response.raise_for_status()
            result = response.json()
        except Exception as err:
            _LOGGER.debug("Failed to get time info: %s", err)
            return None

        # API may return error if not supported
        if result.get("error_code") != 0:
            return None

        try:
            return TimeInfo.model_validate(result)
        except Exception:
            return None

    # ===== Phase 4: Display Controls =====

    async def set_rotation(self, rotation: Rotation) -> bool:
        """Set screen rotation angle.

        Args:
            rotation: Rotation angle (NORMAL, ROTATE_90, ROTATE_180, ROTATE_270)

        Returns:
            True if successful, False if not supported by firmware

        Note:
            This API may not be implemented in all firmware versions.

        Example:
            >>> from pixoo import PixooAsync, Rotation
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     if await pixoo.set_rotation(Rotation.ROTATE_180):
            ...         print("Rotation set")
        """
        if self.config.simulated:
            return True

        payload = self._create_command_payload(
            "Device/SetScreenRotationAngle", Mode=rotation.value
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def set_white_balance(self, red: int, green: int, blue: int) -> bool:
        """Set white balance/color calibration.

        Args:
            red: Red channel value (0-255)
            green: Green channel value (0-255)
            blue: Blue channel value (0-255)

        Returns:
            True if successful, False if not supported by firmware

        Note:
            This API may not be implemented in all firmware versions.

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     if await pixoo.set_white_balance(255, 200, 200):  # Warm tint
            ...         print("White balance set")
        """
        if self.config.simulated:
            return True

        # Validate ranges
        red = int(clamp(red, 0, 255))
        green = int(clamp(green, 0, 255))
        blue = int(clamp(blue, 0, 255))

        payload = self._create_command_payload(
            "Device/SetWhiteBalance", RValue=red, GValue=green, BValue=blue
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def set_mirror_mode(self, enabled: bool) -> bool:
        """Enable or disable mirror mode (horizontal flip).

        Args:
            enabled: True to enable mirror mode, False to disable

        Returns:
            True if successful, False if not supported by firmware

        Note:
            This API may not be implemented in all firmware versions.

        Example:
            >>> async with PixooAsync(address="192.168.1.100") as pixoo:
            ...     if await pixoo.set_mirror_mode(True):  # Mirror display
            ...         print("Mirror mode enabled")
        """
        if self.config.simulated:
            return True

        payload = self._create_command_payload(
            "Device/SetMirrorMode", Mode=1 if enabled else 0
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def set_timer(
        self, minutes: int = 0, seconds: int = 0, enabled: bool = True
    ) -> bool:
        """Set countdown timer (async).

        Args:
            minutes: Timer duration in minutes (0-59)
            seconds: Timer duration in seconds (0-59)
            enabled: Whether to enable (True) or disable (False) the timer

        Returns:
            True if timer was set successfully, False if not supported

        Example:
            >>> await pixoo.set_timer(minutes=5, seconds=30)  # 5:30 countdown
            True
            >>> await pixoo.set_timer(minutes=0, seconds=0, enabled=False)  # Disable
            True
        """
        from .utils import clamp

        config = TimerConfig(
            enabled=enabled,
            minutes=int(clamp(minutes, 0, 59)),
            seconds=int(clamp(seconds, 0, 59)),
        )

        payload = self._create_command_payload(
            "Tools/SetTimer",
            Status=1 if config.enabled else 0,
            Minute=config.minutes,
            Second=config.seconds,
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def set_alarm(self, hour: int, minute: int, enabled: bool = True) -> bool:
        """Set alarm clock (async).

        Args:
            hour: Alarm hour in 24-hour format (0-23)
            minute: Alarm minute (0-59)
            enabled: Whether to enable (True) or disable (False) the alarm

        Returns:
            True if alarm was set successfully, False if not supported

        Example:
            >>> await pixoo.set_alarm(hour=7, minute=30)  # 7:30 AM alarm
            True
            >>> await pixoo.set_alarm(hour=0, minute=0, enabled=False)  # Disable
            True
        """
        from .utils import clamp

        config = AlarmConfig(
            enabled=enabled,
            hour=int(clamp(hour, 0, 23)),
            minute=int(clamp(minute, 0, 59)),
        )

        payload = self._create_command_payload(
            "Device/SetAlarm",
            Status=1 if config.enabled else 0,
            Hour=config.hour,
            Minute=config.minute,
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def play_buzzer(
        self, active_time: int = 500, off_time: int = 500, total_time: int = 3000
    ) -> bool:
        """Play buzzer sound with specified timing pattern (async).

        Args:
            active_time: Time buzzer is on in each cycle (milliseconds)
            off_time: Time buzzer is off in each cycle (milliseconds)
            total_time: Total duration of buzzer sequence (milliseconds)

        Returns:
            True if buzzer played successfully, False if not supported

        Example:
            >>> await pixoo.play_buzzer(active_time=500, off_time=500, total_time=3000)
            True
            >>> await pixoo.play_buzzer(active_time=100, off_time=100, total_time=1000)
            True
        """
        config = BuzzerConfig(
            active_time=max(1, active_time),
            off_time=max(1, off_time),
            total_time=max(1, total_time),
        )

        payload = self._create_command_payload(
            "Device/PlayBuzzer",
            ActiveTimeInCycle=config.active_time,
            OffTimeInCycle=config.off_time,
            PlayTotalTime=config.total_time,
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def set_stopwatch(self, enabled: bool = True) -> bool:
        """Control stopwatch (async).

        Args:
            enabled: True to start stopwatch, False to stop/reset

        Returns:
            True if stopwatch was controlled successfully, False if not supported

        Example:
            >>> await pixoo.set_stopwatch(enabled=True)  # Start
            True
            >>> await pixoo.set_stopwatch(enabled=False)  # Stop/reset
            True
        """
        config = StopwatchConfig(enabled=enabled)

        payload = self._create_command_payload(
            "Tools/SetStopWatch",
            Status=1 if config.enabled else 0,
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def set_scoreboard(self, red_score: int = 0, blue_score: int = 0) -> bool:
        """Set scoreboard scores (async).

        Args:
            red_score: Red team score (0-999)
            blue_score: Blue team score (0-999)

        Returns:
            True if scoreboard was set successfully, False if not supported

        Example:
            >>> await pixoo.set_scoreboard(red_score=3, blue_score=5)
            True
            >>> await pixoo.set_scoreboard(red_score=0, blue_score=0)  # Reset
            True
        """
        from .utils import clamp

        config = ScoreboardConfig(
            red_score=int(clamp(red_score, 0, 999)),
            blue_score=int(clamp(blue_score, 0, 999)),
        )

        payload = self._create_command_payload(
            "Tools/SetScoreBoard",
            RedScore=config.red_score,
            BlueScore=config.blue_score,
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def set_noise_meter(self, enabled: bool = True) -> bool:
        """Control noise meter display (async).

        Args:
            enabled: True to enable noise meter, False to disable

        Returns:
            True if noise meter was controlled successfully, False if not supported

        Example:
            >>> await pixoo.set_noise_meter(enabled=True)
            True
            >>> await pixoo.set_noise_meter(enabled=False)
            True
        """
        config = NoiseMeterConfig(enabled=enabled)

        payload = self._create_command_payload(
            "Tools/SetNoiseStatus",
            NoiseStatus=1 if config.enabled else 0,
        )
        response = await self._client.post(self._url, json=payload)
        result = response.json()

        # API may return string error instead of error_code
        if isinstance(result.get("error_code"), str):
            return False

        try:
            data = PixooResponse.model_validate(result)
            return data.success
        except Exception:
            return False

    async def __aenter__(self) -> "PixooAsync":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self._client.aclose()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
