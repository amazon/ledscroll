"""Base classes for animation strategies."""

from abc import ABC, abstractmethod
from pathlib import Path
import logging

import bdflib.reader
import bdflib.model
from PIL import Image, ImageDraw, ImageColor

DEFAULT_FONT = "fonts/8x13.bdf"
DEFAULT_STEP_DURATION = 40 # milliseconds

log = logging.getLogger(__name__)


def apply_dimming(color_rgb: tuple[int, int, int], brightness: int = 100) -> tuple[int, int, int]:
    """
    Apply dimming to an RGB color by adjusting the Value component in HSV color space.

    :param color_rgb: Original color as an RGB tuple.
    :param brightness: Brightness percentage (0 to 100), where 100 means no dimming, and 0 means black.
    :return: New RGB color after applying dimming.
    """
    if brightness >= 100:
        return color_rgb
    if color_rgb == (0, 0, 0):
        return color_rgb
    # Ensure brightness is within 0 to 100
    brightness = max(0, min(brightness, 100))
    brightness_factor = brightness / 100.0
    log.debug(f"{brightness_factor=}")
    # Convert RGB to HSV
    color_hsv = ImageColor.getcolor(f"rgb{color_rgb}", "HSV")
    log.debug(f"{color_hsv=}")

    # Adjust the Value component
    h, s, v = color_hsv
    h = h * 360 // 255
    s = s * 100 // 255
    v = v * 100 // 255
    v = int(v * brightness_factor)

    # Ensure Value is within 0 to 100
    v = max(0, min(v, 100))

    # Convert back to RGB
    color_rgb_new = ImageColor.getrgb(f"hsv({h},{s}%,{v}%)")
    log.debug(f"{color_rgb_new=}")
    r, g, b, *_ = color_rgb_new
    log.debug(f"adjusted brightness: {color_rgb} > {(h, s, v)} -> {(r, g, b)}")
    return (r, g, b)


class AnimationStrategy(ABC):
    """
    An interface class for animation strategies.

    This class serves as a common interface for different types of
    animation strategies, such as border and text animations. It defines
    the basic structure and ensures consistency across different animation
    implementations.
    """

    @abstractmethod
    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
        """
        Abstract method to render the animation on an image.

        This method should be implemented by all subclasses to apply
        specific animation effects on the given image based on
        the provided timestamp.

        :param image: The PIL Image object on which to render the animation.
        :param timestamp_ms: The current timestamp in milliseconds, used to
                             determine the state of the animation.
        :return: The PIL Image object with the animation applied.
        """
        pass


class TextAnimationStrategy(AnimationStrategy):
    """
    Abstract base class for text animation strategies.

    This class provides functionality to render text using a bitmap font and store it
    as an image with transparency for further animation processing.

    Inherits from AnimationStrategy.
    """

    def __init__(
        self,
        text: str,
        font: str = DEFAULT_FONT,
        text_color: tuple[int, int, int] = (255, 255, 255),
        bg_color: tuple[int, int, int] = None,
    ) -> None:
        """
        Initialize the text animation strategy.

        :param text: Text to be rendered.
        :param font: Path to the BDF font file.
        :param text_color: Text color.
        :param bg_color: Background color. If None, background is transparent.
        """
        self._text: str = text
        self._text_color: tuple[int, int, int] = tuple(text_color)
        self._bg_color: tuple[int, int, int] | None = bg_color
        self._font: bdflib.model.Font = self._load_font(font)
        self._text_img: Image.Image = self._render_text_to_image()

    def _load_font(self, font_path: str) -> bdflib.model.Font:
        """
        Load the BDF font from the specified path.

        :param font_path: Path to the BDF font file.
        :return: The loaded BDF font.
        """
        absolute_font_path = Path(__file__).parent.parent / font_path
        log.info("loading %s", absolute_font_path.as_posix())
        with open(absolute_font_path, "rb") as file:
            return bdflib.reader.read_bdf(file)

    def _render_text_to_image(self) -> Image.Image:
        """
        Render the text into an image using the loaded BDF font.

        :return: The PIL Image object with the rendered text.
        """
        character_nums = [ord(c) for c in self._text]
        width = sum(self._font[num].bbW for num in character_nums)
        height = max(self._font[num].bbH for num in character_nums)

        # Create an image with a transparent background
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        x = 0
        for num in character_nums:
            glyph = self._font[num]
            for y in range(glyph.bbH):
                format_str = "0" + str(glyph.bbW) + "b"
                line = format(glyph.data[y], format_str)
                for x_off in range(glyph.bbW):
                    if line[x_off] == "1":
                        led_x, led_y = x + x_off, height - y
                        # Draw the text pixel with full opacity
                        draw.point((led_x, led_y), fill=self._text_color + (255,))
            x += glyph.bbW

        # If bg_color is specified, composite it with the text image
        if self._bg_color is not None:
            background = Image.new("RGBA", image.size, self._bg_color + (255,))
            image = Image.alpha_composite(background, image)

        return image
