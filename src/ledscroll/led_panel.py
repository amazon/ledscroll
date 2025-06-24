from io import BytesIO
from pathlib import Path
import logging

import bdflib.reader
from PIL import Image, ImageDraw

# import animations.slide_text
# import animations.simple
from .animations.base import AnimationStrategy
from .animations.registry import animation_registry

log = logging.getLogger(__name__)

class Panel:
    def __init__(self, width, height, font, duration) -> None:
        self.width = width
        self.height = height
        self.frames: list[Image.Image] = []
        self.duration = duration
        # Load the BDF font
        font_path = Path(__file__).parent / font
        log.info("loading %s", font_path.absolute().as_posix())
        with open(font_path, "rb") as file:
            self.font = bdflib.reader.read_bdf(file)

    # def render_text(
    #     self,
    #     text,
    #     x_offset=0,
    #     y_offset=0,
    #     text_color=(255, 0, 0),
    #     bg_color=(0, 0, 0),
    #     border_color=(0, 0, 255),
    # ):
    #     character_nums = [ord(c) for c in text]

    #     # Calculate image size needed
    #     width = sum(self.font[num].bbW for num in character_nums)
    #     height = max(self.font[num].bbH for num in character_nums)

    #     # Create an image with a white background
    #     image = Image.new("RGB", (self.width, self.height), bg_color)
    #     draw = ImageDraw.Draw(image)

    #     x = 0

    #     for num in character_nums:
    #         glyph = self.font[num]
    #         # print(glyph_data)
    #         for y in range(glyph.bbH):
    #             format_str = "0" + str(glyph.bbW) + "b"
    #             line = format(glyph.data[y], format_str)
    #             for x_off in range(glyph.bbW):
    #                 if line[x_off] == "1" and 0 <= x_offset + x + x_off < self.width:
    #                     led_x, led_y = x_offset + x + x_off, height - y
    #                     draw.point((led_x, led_y), fill=text_color)
    #         x += glyph.bbW
    #     # draw border
    #     for y in range(self.height):
    #         if 0 < y < self.height - 1:
    #             draw.point((0, y), fill=border_color)
    #             draw.point((x, y), fill=border_color)
    #         else:
    #             for x in range(0, self.width):
    #                 draw.point((x, y), fill=border_color)

    #     self.frames.append(image)
        # image = image.resize(
        #     (4 * self.width, 4 * self.height), resample=Image.Resampling.NEAREST
        # )
        # image.save("output.jpg", "jpeg")

    def new_frame(self, bg_color) -> Image.Image:
        """Create new empty frame."""
        return Image.new("RGB", (self.width, self.height), bg_color)

    def append_frame(self, image: Image.Image) -> None:
        """Append frame to the buffer."""
        self.frames.append(image)

    def save(self, filename):
        """Save rendered frames into gif file"""
        self.frames[0].save(
            filename,
            "gif",
            save_all=True,
            append_images=self.frames[1:],
            duration=self.duration,
            loop=0,
        )

    def as_gif(self):
        """Retirn frames as animated gif bytes."""
        with BytesIO() as f:
            self.frames[0].save(
                f,
                "gif",
                save_all=True,
                append_images=self.frames[1:],
                duration=self.duration,
                loop=0,
            )
            f.seek(0)
            return f.read()


    def preview(self):
        preview_frames = []
        for im1 in self.frames:
            im2 = Image.new("RGB", (self.width * 3, self.height * 3), (0, 0, 0))
            for y in range(self.height):
                for x in range(self.width):
                    color = im1.getpixel((x, y))
                    color = (50, 50, 50) if color == (0, 0, 0) else color
                    im2.putpixel((3 * x + 1, 3 * y + 1), color)
            preview_frames.append(im2)

        with BytesIO() as f:
            preview_frames[0].save(
                f,
                "gif",
                save_all=True,
                append_images=preview_frames[1:],
                duration=self.duration,
                loop=0,
            )
            f.seek(0)
            return f.read()


class PanelRenderer:
    """
    A class for rendering animations on a panel using a sequence of animation strategies.

    This class manages the application of multiple animation strategies to an image,
    rendering each frame and updating the panel display sequentially.

    Attributes:
        panel: The panel on which to render the animations.
        animations: A list of instances implementing the AnimationStrategy interface.

    Example:
        # Example of how to use the PanelRenderer with a list of animations
        from PIL import Image

        # Assuming 'Panel' is a predefined class with necessary methods
        panel = Panel(...)
        text_animation = ScrollingTextAnimation(font_path, text, step_duration)
        border_animation = FlashingBorderAnimation()

        renderer = PanelRenderer(panel, [text_animation, border_animation])

        # Start rendering the animations
        renderer.render()
    """

    def __init__(self, panel, animations: list[AnimationStrategy]) -> None:
        self.panel = panel
        self.animations: list[AnimationStrategy] = animations

    def render(self, time_limit_sec: int = 25) -> int:
        """
        Render the animations on the panel using the specified sequence of strategies.

        The rendering process continues until one of the animations returns None,
        indicating the completion of the entire animation sequence.

        :param time_limit_sec: Time limit for animation. Defaults to 25 seconds

        :return: Total duration of generated animation in milliseconds
        """
        timestamp_ms: int = 0
        while timestamp_ms <= 1000 * time_limit_sec:
            image: Image.Image | None = self.panel.new_frame(bg_color=(0, 0, 0))

            for animation in self.animations:
                image = animation.render(image, timestamp_ms)
                if image is None:
                    return timestamp_ms # End the animation sequence if any animation returns None

            self.panel.append_frame(image)
            timestamp_ms += self.panel.duration
        return timestamp_ms
