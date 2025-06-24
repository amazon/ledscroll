"""
animation.py

This module defines a set of classes for creating and applying various animation
strategies to images. These strategies are designed to be used in contexts where
animated visual effects are required, such as in GUI applications, digital signage,
or other graphical displays.

Classes:
    - AnimationStrategy (ABC): An abstract base class that defines a common interface
      for all animation strategies. It mandates the implementation of a `render` method.

    - TextAnimationStrategy (AnimationStrategy): An abstract subclass of AnimationStrategy
      tailored for text animations. It establishes the foundation for concrete text animation
      strategies.

    - FlashingBorderAnimation (AnimationStrategy): A concrete implementation of
      BorderAnimationStrategy that creates a flashing effect on the border of an image.

    - MovingDotsBorderAnimation (AnimationStrategy): A concrete class implementing
      a moving dots animation on an image's border, providing a dynamic visual effect.

    - PulsingBorderAnimation (AnimationStrategy): Another concrete border animation
      class that varies the width of the border, creating a pulsing effect.


    - ScrollingTextAnimation (TextAnimationStrategy): A concrete implementation of
      TextAnimationStrategy that animates text by scrolling it horizontally across
      the display area.

Usage:
    The classes in this module are intended to be used as part of a larger system that
    requires dynamic visual effects. Create an instance of the desired animation class
    and call its `render` method, passing the image to be animated and the current
    timestamp. This will apply the animation effect to the image.

Example:
    # Example of using a concrete animation strategy
    image = Image.new('RGB', (100, 100))
    animation = FlashingBorderAnimation()
    animated_image = animation.render(image, timestamp_ms=500)

Note:
    This module requires PIL (Python Imaging Library) for image manipulation.
"""

from PIL import Image

import logging as log

from .registry import register_strategy
from .base import (
    apply_dimming,
    AnimationStrategy,
    TextAnimationStrategy,
    DEFAULT_FONT,
    DEFAULT_STEP_DURATION,
)

log.basicConfig(level=log.DEBUG)


@register_strategy("no_border")
class NoBorderAnimation(AnimationStrategy):
    """Flashing border animation."""

    def __init__(
        self,
    ) -> None:
        """
        Constructor.
        """

    def render(self, image, timestamp_ms) -> Image.Image:
        return image


@register_strategy("flashing_border")
class FlashingBorderAnimation(AnimationStrategy):
    """Flashing border animation."""

    def __init__(
        self,
        colors: list[tuple[int, int, int]] = [(255, 0, 0), (0, 0, 0)],
        duration: int = 500,
    ) -> None:
        """
        Constructor.

        :param colors: Sequence of colors
        :param duration: Duration of each color in milliseconds
        """
        self.colors = colors
        self.duration = duration

    def render(self, image, timestamp_ms) -> Image.Image:
        step = timestamp_ms // self.duration
        border_color = self.colors[step % len(self.colors)]
        # border_color = (255, 0, 0) if timestamp_ms % 1000 < 500 else (0, 0, 255)
        for y in range(image.height):
            for x in range(image.width):
                if y == 0 or y == image.height - 1 or x == 0 or x == image.width - 1:
                    image.putpixel((x, y), border_color)
        return image


@register_strategy("running_dots_border")
class RunningDotsBorderAnimation(AnimationStrategy):
    """Running dots border animation."""

    def __init__(
        self,
        border_color: tuple[int, int, int] = (0, 0, 255),
        dot_color: tuple[int, int, int] = (255, 0, 0),
        dot_spacing: int = 2,
    ) -> None:
        """
        Constructor.

        :param border_color: Border color
        :param dot_color: Running dots color
        :param dot_spacing: Pixel interval between dots
        """
        super().__init__()
        self.border_color = border_color
        self.dot_color = dot_color
        self.dot_spacing = dot_spacing

    def render(self, image, timestamp_ms) -> Image.Image:
        dot_position = (timestamp_ms // 100) % (self.dot_spacing + 1)

        # Draw blue border
        for y in range(image.height):
            for x in range(image.width):
                if y == 0 or y == image.height - 1 or x == 0 or x == image.width - 1:
                    image.putpixel((x, y), self.border_color)

        # Place red dots
        # Top and right edges (clockwise)
        for x in range(dot_position, image.width, self.dot_spacing + 1):
            image.putpixel((x, 0), self.dot_color)  # Top edge
        for y in range(dot_position, image.height, self.dot_spacing + 1):
            image.putpixel((image.width - 1, y), self.dot_color)  # Right edge

        # Bottom and left edges (counterclockwise)
        for x in range(image.width - dot_position - 1, -1, -(self.dot_spacing + 1)):
            image.putpixel((x, image.height - 1), self.dot_color)  # Bottom edge
        for y in range(image.height - dot_position - 1, -1, -(self.dot_spacing + 1)):
            image.putpixel((0, y), self.dot_color)  # Left edge

        return image


@register_strategy("pulsing_border")
class PulsingBorderAnimation(AnimationStrategy):
    """Pulsing border animation."""

    def __init__(
        self, border_color: tuple[int, int, int] = (255, 0, 255), duration: int = 500
    ) -> None:
        """Constructor.

        :param border_color: Border color
        :param duration: Pulse duration in milliseconds
        """
        super().__init__()
        self.border_color = border_color
        self.cycle_ms = duration

    def render(self, image, timestamp_ms) -> Image.Image:

        # Calculate the pulsing border width
        # Assuming a full cycle (0 to 3 to 0) takes 2000ms
        phase = (
            timestamp_ms % self.cycle_ms
        ) / self.cycle_ms  # Phase of the cycle, ranges from 0 to 1
        if phase > 0.5:
            phase = 1 - phase  # Reverse phase in the second half of the cycle
        border_width = int(
            phase * 2 * 3
        )  # Multiply by 4 for a full 0-1-0 cycle, then by 3 for max width

        # Draw the border
        for y in range(image.height):
            for x in range(image.width):
                # Check if the pixel is within the border width
                if (
                    y < border_width
                    or y >= image.height - border_width
                    or x < border_width
                    or x >= image.width - border_width
                ):
                    image.putpixel((x, y), self.border_color)

        return image


@register_strategy("scrolling_text")
class ScrollingTextAnimation(TextAnimationStrategy):
    """Scrolling text animation."""

    def __init__(
        self,
        text: str,
        font: str = DEFAULT_FONT,
        step_duration: int = DEFAULT_STEP_DURATION,
        text_color: tuple[int, int, int] = (255, 255, 255),
        bg_color: tuple[int, int, int] = (0, 0, 0),
        bg_brightness: int = 100,
    ) -> None:
        """
        Initialize the ScrollingTextAnimation strategy.

        :param text: Text to be rendered
        :param font: Path to the BDF font file
        :param step_duration: Duration for each animation step in milliseconds
        :param text_color: Text color
        :param bg_color: Background color
        :param bg_brightness: Background brightness (0-100)
        """
        bg_color = apply_dimming(bg_color, bg_brightness)
        super().__init__(text, font, text_color, bg_color)
        self._duration = step_duration
        self._bg_color = bg_color

        # Ensure text image has an alpha channel
        self._text_img = self._text_img.convert("RGBA")

    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
        """
        Implements a scrolling text animation.

        :param image: The source image
        :param timestamp_ms: The current time in milliseconds
        :return: Updated image or None if all done
        """
        x_offset = image.width - int(timestamp_ms / self._duration)

        if x_offset > -self._text_img.width:
            # Ensure the image is in RGBA mode
            if image.mode != "RGBA":
                image = image.convert("RGBA")

            # Fill the background with the specified background color
            background = Image.new("RGBA", image.size, self._bg_color + (255,))
            image.paste(background)

            src_x1 = max(0, -x_offset)
            dst_x1 = max(x_offset, 0)
            crop_width = min(self._text_img.width - src_x1, image.width - dst_x1)

            if crop_width > 0:
                box = (
                    src_x1,
                    0,
                    src_x1 + crop_width,
                    min(image.height, self._text_img.height),
                )
                region = self._text_img.crop(box)

                # Paste the region onto the image using the alpha channel as mask
                image.paste(region, (dst_x1, 0), mask=region)
            return image
        else:
            return None


# @register_strategy("slide_text")
# class SlideTextAnimation(TextAnimationStrategy):

#     def __init__(self, font: str, text: str, step_duration: int, slide_duration: int, pause_duration: int) -> None:
#         """
#         Initialize the SlideTextAnimation strategy.

#         :param font: Path to the BDF font file.
#         :param text: Text to be rendered.
#         :param step_duration: Duration for each animation step in milliseconds.
#         :param slide_duration: Duration to scroll the text to the center in milliseconds.
#         :param pause_duration: Duration to pause the text in the center in milliseconds.
#         """
#         super().__init__(text, font, step_duration)
#         self._duration = step_duration
#         self._pause_duration = pause_duration
#         self._slide_duration = slide_duration
#         self._center_position = None

#     def _calculate_x_offset(self, timestamp_ms: int, image_width: int) -> int:
#         """
#         Calculate the x offset for the text based on the current timestamp.

#         :param timestamp_ms: The current time in milliseconds.
#         :param image_width: The width of the image.
#         :return: The calculated x offset.
#         """

#         if self._center_position is None:
#             self._center_position = (image_width - self._text_img.width) // 2
#             log.debug("center position: %d", self._center_position)

#         speed_factor = (image_width - self._center_position) * self._duration // self._slide_duration

#         phase = timestamp_ms // self._duration * speed_factor
#         log.debug("phase: %s", phase)
#         pause_start_phase =  image_width - self._center_position
#         pause_end_phase = pause_start_phase + speed_factor * self._pause_duration // self._duration
#         # return image_width - phase

#         if phase < pause_start_phase:
#             return image_width - phase
#         elif phase < pause_end_phase:
#             return image_width - pause_start_phase
#         else:
#             return image_width - pause_start_phase + pause_end_phase - phase
#         # - int(timestamp_ms / self._duration)


#     def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
#         """
#         Implements the center-paused scrolling text animation.

#         :param image: The source image.
#         :param timestamp_ms: The current time in milliseconds.
#         :return: Updated image or None if all done.
#         """
#         x_offset = self._calculate_x_offset(timestamp_ms, image.width)

#         if -self._text_img.width <= x_offset <= image.width:
#             src_x1 = max(0, -x_offset)
#             dst_x1 = max(x_offset, 0)
#             crop_width = min(self._text_img.width - src_x1, image.width - dst_x1)

#             if crop_width > 0:
#                 box = (src_x1, 0, src_x1 + crop_width, min(image.height, self._text_img.height))
#                 region = self._text_img.crop(box)
#                 image.paste(region, (dst_x1, 0))
#             return image

#         return None


@register_strategy("flashing_text")
class FlashingTextAnimation(TextAnimationStrategy):
    """Flashing text animation."""

    def __init__(
        self,
        text: str,
        font: str = DEFAULT_FONT,
        total_duration: int = 1000,
        cycle_duration: int = 200,
        colors: list[tuple[int, int, int]] = [(0, 0, 0), (255, 0, 0)],
        bg_color: tuple[int, int, int] = (0, 0, 0),
        bg_brightness: int = 100,
    ) -> None:
        """
        Initialize the FlashingTextAnimation strategy.

        :param text: Text to be rendered
        :param font: Path to the BDF font file
        :param total_duration: Total duration of the animation in milliseconds
        :param cycle_duration: Duration of each color cycle in milliseconds
        :param colors: List of colors to cycle through, each as an RGB tuple
        :param bg_color: Background color
        :param bg_brightness: Background brightness (0-100)
        """
        # Pass bg_color=None to have a transparent background in the text image
        super().__init__(text, font, text_color=(255, 255, 255), bg_color=None)
        self._total_duration = total_duration
        self._cycle_duration = cycle_duration
        self._colors = colors
        self._bg_color = apply_dimming(bg_color, bg_brightness)
        self._center_position = None

    def _calculate_color(self, timestamp_ms: int) -> tuple[int, int, int]:
        """
        Calculate the current color based on the timestamp.

        :param timestamp_ms: The current time in milliseconds
        :return: The calculated color as an RGB tuple
        """
        cycle_index = (timestamp_ms // self._cycle_duration) % len(self._colors)
        return self._colors[cycle_index]

    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
        """
        Implements the flashing text animation.

        :param image: The source image
        :param timestamp_ms: The current time in milliseconds
        :return: Updated image or None if all done
        """
        if timestamp_ms > self._total_duration:
            return None  # End the animation after the total duration

        current_color = self._calculate_color(timestamp_ms)

        if self._center_position is None:
            self._center_position = (image.width - self._text_img.width) // 2

        # Create a new image with the specified background color
        image = Image.new("RGBA", image.size, self._bg_color + (255,))

        # Create a colored text image using the current color
        colored_text = Image.new("RGBA", self._text_img.size, current_color + (0,))
        # Use the alpha channel of the text image as the mask
        mask = self._text_img.split()[-1]
        colored_text.putalpha(mask)

        # Paste the colored text onto the image using the mask
        image.paste(colored_text, (self._center_position, 0), mask=mask)

        return image


@register_strategy("police_lights_border")
class PoliceLightsBorderAnimation(AnimationStrategy):
    """Police lights border animation."""

    def __init__(self, cycle_duration: int = 400) -> None:
        """
        Initialize the PoliceLightsBorderAnimation strategy.

        :param cycle_duration: Duration of each color cycle in milliseconds
        """
        self._cycle_duration = cycle_duration

    def _calculate_phase(self, timestamp_ms: int) -> int:
        """
        Calculate the current phase of the animation based on the timestamp.

        :param timestamp_ms: The current time in milliseconds
        :return: The current phase of the animation cycle
        """
        return (timestamp_ms // self._cycle_duration) % 2

    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image:
        """
        Implements the police car lights border animation.

        :param image: The source image
        :param timestamp_ms: The current time in milliseconds
        :return: Updated image with the police car lights border
        """
        phase = self._calculate_phase(timestamp_ms)
        colors = [(255, 0, 0), (0, 0, 255)]  # Red and Blue
        if (timestamp_ms // 80) % 2:
            return image
        for y in range(image.height):
            for x in range(
                int(image.width * (phase / 2)), int(image.width * (0.5 + phase / 2))
            ):
                if y <= 1 or y >= image.height - 2 or x <= 1 or x >= image.width - 2:
                    color_index = int(2 * x / image.width)
                    image.putpixel((x, y), colors[color_index])

        return image


class SlideInTextAnimation(TextAnimationStrategy):
    """Slide-in text animation."""

    def __init__(
        self,
        text: str,
        font: str = DEFAULT_FONT,
        step_duration: int = DEFAULT_STEP_DURATION,
        slide_duration: int = 500,
        text_color: tuple[int, int, int] = (0, 0, 0),
        bg_color: tuple[int, int, int] = None,
        bg_brightness: int = 100,
    ) -> None:
        """
        Initialize the SlideInTextAnimation strategy.

        :param text: Text to be rendered
        :param font: Path to the BDF font file
        :param step_duration: Duration for each animation step in milliseconds
        :param slide_duration: Total duration for the slide-in effect
        :param text_color: Text color
        :param bg_color: Background color. If None, background is transparent.
        :param bg_brightness: Background brightness (0-100)
        """
        bg_color = apply_dimming(bg_color, bg_brightness)
        super().__init__(text, font, text_color=text_color, bg_color=bg_color)
        self._step_duration = step_duration
        self._slide_duration = slide_duration
        self._center_position = None
        self._bg_color = bg_color

    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
        """
        Implements the slide-in text animation.

        :param image: The source image
        :param timestamp_ms: The current time in milliseconds
        :return: Updated image or None if the animation is done
        """
        if self._center_position is None:
            self._center_position = (image.width - self._text_img.width) // 2
            log.debug("center position: %d", self._center_position)

        # Calculate the total number of steps
        total_steps = self._slide_duration // self._step_duration
        current_step = timestamp_ms // self._step_duration
        if current_step > total_steps:
            return None  # Animation is done

        # Calculate x_offset for sliding in from the right
        x_offset = image.width - int(
            (current_step / total_steps) * (image.width - self._center_position)
        )

        # Ensure the image is in RGBA mode
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Fill the background if bg_color is specified
        if self._bg_color is not None:
            background = Image.new("RGBA", image.size, self._bg_color + (255,))
            image.paste(background)

        # Paste the text image onto the image at the calculated position using alpha mask
        image.paste(self._text_img, (x_offset, 0), mask=self._text_img)

        return image


class SlideOutTextAnimation(TextAnimationStrategy):
    """Slide-out text animation."""

    def __init__(
        self,
        text: str,
        font: str = DEFAULT_FONT,
        step_duration: int = DEFAULT_STEP_DURATION,
        slide_duration: int = 500,
        text_color: tuple[int, int, int] = (0, 0, 0),
        bg_color: tuple[int, int, int] = None,
        bg_brightness: int = 100,
    ) -> None:
        """
        Initialize the SlideOutTextAnimation strategy.

        :param text: Text to be rendered
        :param font: Path to the BDF font file
        :param step_duration: Duration for each animation step in milliseconds
        :param slide_duration: Total duration for the slide-out effect
        :param text_color: Text color
        :param bg_color: Background color. If None, background is transparent.
        :param bg_brightness: Background brightness (0-100)
        """
        bg_color = apply_dimming(bg_color, bg_brightness)
        super().__init__(text, font, text_color=text_color, bg_color=bg_color)
        self._step_duration = step_duration
        self._slide_duration = slide_duration
        self._center_position = None
        self._bg_color = bg_color

    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
        """
        Implements the slide-out text animation.

        :param image: The source image
        :param timestamp_ms: The current time in milliseconds
        :return: Updated image or None if the animation is done
        """
        if self._center_position is None:
            self._center_position = (image.width - self._text_img.width) // 2
            log.debug("center position: %d", self._center_position)

        # Calculate the total number of steps
        total_steps = self._slide_duration // self._step_duration
        current_step = timestamp_ms // self._step_duration
        if current_step > total_steps:
            return None  # Animation is done

        # Calculate x_offset for sliding out to the left
        x_offset = self._center_position - int(
            (current_step / total_steps) * (self._center_position + self._text_img.width)
        )

        # Ensure the image is in RGBA mode
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Fill the background if bg_color is specified
        if self._bg_color is not None:
            background = Image.new("RGBA", image.size, self._bg_color + (255,))
            image.paste(background)

        # Paste the text image onto the image at the calculated position using alpha mask
        image.paste(self._text_img, (x_offset, 0), mask=self._text_img)

        return image


@register_strategy("static_text")
class StaticTextAnimation(TextAnimationStrategy):
    """Static text animation."""

    def __init__(
        self,
        text: str,
        font: str = DEFAULT_FONT,
        duration: int = 1000,
        text_color: tuple[int, int, int] = (255, 255, 255),
        bg_color: tuple[int, int, int] = None,
        bg_brightness: int = 100,
    ) -> None:
        """
        Initialize the StaticTextAnimation strategy.

        :param text: Text to be rendered
        :param font: Path to the BDF font file
        :param duration: Duration to display the text in milliseconds
        :param text_color: Text color
        :param bg_color: Background color. If None, background is transparent.
        :param bg_brightness: Background brightness (0-100)
        """
        bg_color = apply_dimming(bg_color, bg_brightness)
        super().__init__(text, font, text_color, bg_color)
        self._duration = duration
        self._center_position = None

    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
        """
        Implements the static text animation.

        :param image: The source image
        :param timestamp_ms: The current time in milliseconds
        :return: Updated image or None if the duration has elapsed
        """
        if timestamp_ms > self._duration:
            return None  # End the animation after the specified duration

        if self._center_position is None:
            self._center_position = (
                (image.width - self._text_img.width) // 2,
                (image.height - self._text_img.height) // 2 - 1,
            )

        # Ensure the image is in RGBA mode
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Fill the background with the specified background color
        if self._bg_color is not None:
            background = Image.new("RGBA", image.size, self._bg_color + (255,))
            image.paste(background)

        # Paste the pre-rendered text image onto the center of the source image using the alpha channel as mask
        image.paste(self._text_img, self._center_position, mask=self._text_img)

        return image
