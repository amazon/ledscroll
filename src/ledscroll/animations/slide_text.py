"""Slide Text Animation."""

from PIL import Image

from .base import apply_dimming, AnimationStrategy, DEFAULT_FONT, DEFAULT_STEP_DURATION
from .complex import ComplexAnimation
from .simple import SlideInTextAnimation, SlideOutTextAnimation, StaticTextAnimation
from .registry import register_strategy


@register_strategy("slide_text")
class SlideTextAnimation(AnimationStrategy):
    """Slide Text Animation."""

    def __init__(
        self,
        text: str,
        font: str = DEFAULT_FONT,
        step_duration: int = DEFAULT_STEP_DURATION,
        slide_duration: int = 500,
        pause_duration: int = 1000,
        text_color: tuple[int, int, int] = (255, 0, 0),
        bg_color: tuple[int, int, int] = None,
        bg_brightness: int = 100,
    ) -> None:
        """
        Initialize the SlideTextAnimation strategy.

        :param text: Text to be rendered.
        :param font: Path to the BDF font file.
        :param step_duration: Duration of a single frame in milliseconds.
        :param slide_duration: Duration for the slide animation in milliseconds.
        :param pause_duration: Duration for the static (pause) animation in milliseconds.
        :param text_color: Color of the text.
        :param bg_color: Background color. If None, background is transparent.
        :param bg_brightness: Background brightness (0-100)
        """
        bg_color = apply_dimming(bg_color, bg_brightness)
        self._duration = step_duration
        # Create individual animations
        animation_sequence = []
        for token in text.split():
            token = token.replace("_", " ")
            slide_in_animation = SlideInTextAnimation(
                token,
                font,
                step_duration=step_duration,
                slide_duration=slide_duration,
                text_color=text_color,
                bg_color=bg_color,
            )
            static_animation = StaticTextAnimation(
                token,
                font,
                duration=pause_duration,
                text_color=text_color,
                bg_color=bg_color,
            )
            slide_out_animation = SlideOutTextAnimation(
                token,
                font,
                step_duration=step_duration,
                slide_duration=slide_duration,
                text_color=text_color,
                bg_color=bg_color,
            )
            animation_sequence.extend(
                [slide_in_animation, static_animation, slide_out_animation]
            )
        # Combine them into a complex animation
        self.complex_animation = ComplexAnimation(animation_sequence)

    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
        """
        Renders the slide-in, pause, and slide-out text animation.

        :param image: The source image.
        :param timestamp_ms: The current time in milliseconds.
        :return: Updated image or None if the animation is complete.
        """
        return self.complex_animation.render(image, timestamp_ms)
