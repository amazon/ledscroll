from typing import Dict, Any
import bdflib.reader
from PIL import Image
import math
from .conftest import get_test_output_dir, Args


def generate_reference_gif(args_dict: Dict[str, Any], test_name: str) -> str:
    """Generate a test GIF using a standalone scrolling text renderer implementation."""
    # Import only the bare minimum required libraries

    # Set up the output file
    output_file = str(get_test_output_dir() / f"{test_name}.gif")
    args = Args(**{**args_dict, 'output': output_file})

    # Extract parameters
    width = args.width
    height = args.height
    text = args.text
    font_path = args.text_font
    text_color = args.text_color
    bg_color = args.text_bg_color
    frame_duration = args.frame_duration
    step_duration = args.text_step_duration
    total_duration_ms = args.total_duration

    # Helper function to apply brightness to a color
    def apply_brightness(color, brightness_pct):
        if brightness_pct >= 100 or color == (0, 0, 0):
            return color
        brightness_factor = max(0, min(brightness_pct, 100)) / 100.0
        return tuple(int(c * brightness_factor) for c in color)

    # Apply background brightness
    bg_color = apply_brightness(bg_color, args.text_bg_brightness)

    # 1. Load the BDF font - ensure using absolute path
    # First check if the path is already absolute
    import os
    if not os.path.isabs(font_path):
        # Try to locate the font relative to project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        font_path_candidates = [
            os.path.join(project_root, font_path),
            os.path.join(project_root, 'src', 'ledscroll', font_path),
            os.path.join(project_root, 'src', font_path),
        ]

        for candidate in font_path_candidates:
            if os.path.exists(candidate):
                font_path = candidate
                break
        else:
            raise FileNotFoundError(f"Could not find font file: {font_path}")

    with open(font_path, "rb") as font_file:
        font = bdflib.reader.read_bdf(font_file)

    # 2. Render text to an image
    # Calculate text dimensions using character metrics
    character_nums = [ord(c) for c in text]
    # Sum up the width of all characters and find the maximum height
    try:
        text_width = sum(font[num].bbW for num in character_nums if num in font)
        text_height = max((font[num].bbH for num in character_nums if num in font), default=16)
    except AttributeError:
        # Fallback if bbW/bbH not available - use 8x16 as a reasonable default
        text_width = len(text) * 8
        text_height = 16

    # Create a new image for the text with transparency
    text_img = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))

    # Render each character in the text
    x_pos = 0
    for char in text:
        try:
            glyph = font[ord(char)]
            char_width = getattr(glyph, 'bbW', 8)  # Default to 8 if bbW not available
            char_height = getattr(glyph, 'bbH', 16)  # Default to 16 if bbH not available

            # Render the glyph - check if it has data attribute (bitmap representation)
            if hasattr(glyph, 'data'):
                # bdflib style - get bitmap from data
                for y in range(char_height):
                    # Convert bitmap row to binary string representation
                    try:
                        format_str = "0" + str(char_width) + "b"
                        line = format(glyph.data[y], format_str)
                        for x in range(char_width):
                            if line[x] == "1":
                                led_x, led_y = x_pos + x, text_height - y - 1
                                if 0 <= led_x < text_width and 0 <= led_y < text_height:
                                    text_img.putpixel((led_x, led_y), text_color + (255,))
                    except (IndexError, AttributeError):
                        pass
            else:
                # Alternative approach - try to use get_pixel if available
                for y in range(char_height):
                    for x in range(char_width):
                        try:
                            if hasattr(glyph, 'get_pixel') and glyph.get_pixel(x, y):
                                led_x, led_y = x_pos + x, y
                                if 0 <= led_x < text_width and 0 <= led_y < text_height:
                                    text_img.putpixel((led_x, led_y), text_color + (255,))
                        except (IndexError, AttributeError):
                            pass

            # Move to next character position
            x_pos += char_width
        except (KeyError, IndexError):
            # Character not in font, skip it with a default width
            x_pos += 8

    # 3. Generate animation frames
    num_frames = math.ceil(total_duration_ms / frame_duration)
    frames = []

    for frame_idx in range(num_frames):
        # Create a new frame
        frame = Image.new("RGBA", (width, height), bg_color + (255,))

        # Calculate x position for the text based on time
        timestamp_ms = frame_idx * frame_duration
        x_offset = width - int(timestamp_ms / step_duration)

        # Check if animation is complete
        if x_offset <= -text_width:
            break

        # Calculate source and destination coordinates for text rendering
        src_x1 = max(0, -x_offset)
        dst_x1 = max(x_offset, 0)
        crop_width = min(text_width - src_x1, width - dst_x1)

        if crop_width > 0:
            # Crop the portion of text that's visible in this frame
            box = (src_x1, 0, src_x1 + crop_width, min(height, text_height))
            text_region = text_img.crop(box)

            # Paste the text onto the frame using alpha channel as mask
            frame.paste(text_region, (dst_x1, 0), mask=text_region)

        # Convert to RGB for GIF compatibility
        frames.append(frame.convert("RGB"))

    # 4. Save the animation as a GIF
    if frames:
        frames[0].save(
            output_file,
            "GIF",
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,
            loop=0,
        )

    return output_file
