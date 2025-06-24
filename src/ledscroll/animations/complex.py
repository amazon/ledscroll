"""Complex animation strategy."""

from PIL import Image, ImageDraw, ImageOps

import logging as log

from .base import AnimationStrategy


class ComplexAnimation(AnimationStrategy):
    """Combines a sequence of animations into a one complex animation."""

    def __init__(self, animations: list[AnimationStrategy]) -> None:
        """
        Initialize the ComplexAnimation with a sequence of animation strategies.

        :param animations: A list of AnimationStrategy instances.
        """
        # super().__init__(animations[0].font, animations[0].text, sum(animation.step_duration for animation in animations))
        self.animations = animations
        self.current_animation_index = 0
        self.timestamp_offset = 0

    def render(self, image: Image.Image, timestamp_ms: int) -> Image.Image | None:
        """
        Renders the sequence of animations, moving to the next animation when one completes.

        :param image: The source image.
        :param timestamp_ms: The current time in milliseconds.
        :return: Updated image or None if all animations are complete.
        """
        while self.current_animation_index < len(self.animations):
            animation = self.animations[self.current_animation_index]
            log.debug("rendering timestamp %d with %s", timestamp_ms - self.timestamp_offset, animation)
            result = animation.render(image, timestamp_ms - self.timestamp_offset)
            if result is not None:
                return result
            log.debug("got None result at timestamp %d", timestamp_ms)
            # If the current animation is done, move to the next one
            self.current_animation_index += 1
            self.timestamp_offset = timestamp_ms  # Reset timestamp for the next animation

        return None  # All animations are complete
