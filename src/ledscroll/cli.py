"""
CLI utility for generating GIF animations using both text and border animation classes.
"""
import argparse
import json
import logging
from pathlib import Path
from time import monotonic
from typing import Any, Dict, List, Tuple

# PIL.Image is imported by the Panel class, no need to import it here

from ledscroll.animations.registry import animation_registry
from ledscroll.animations.base import AnimationStrategy
from ledscroll.led_panel import Panel, PanelRenderer

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Default values
DEFAULT_WIDTH = 64
DEFAULT_HEIGHT = 16
DEFAULT_DURATION = 30000  # milliseconds
DEFAULT_FRAME_DURATION = 40  # milliseconds
DEFAULT_OUTPUT = "animation.gif"

# Border animation types
BORDER_ANIMATIONS = [
    "no_border",
    "flashing_border",
    "running_dots_border",
    "pulsing_border",
    "police_lights_border"
]

# Text animation types
TEXT_ANIMATIONS = [
    "scrolling_text",
    "flashing_text",
    "static_text",
    "slide_text",
    "slide_in_text",
    "slide_out_text"
]


def load_default_params() -> Dict[str, Dict[str, Any]]:
    """
    Load default parameters for animations from params.json

    :return: Dictionary of animation parameters
    """
    params_path = Path(__file__).parent / "animations" / "params.json"
    try:
        with open(params_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        log.warning(f"params.json not found at {params_path}")
        return {}


def parse_color(color_str: str) -> Tuple[int, int, int]:
    """
    Parse a color string in format r,g,b to a tuple of integers.

    :param color_str: Color string in format r,g,b
    :return: Tuple of (r, g, b) integers
    """
    try:
        r, g, b = map(int, color_str.split(','))
        # Validate RGB values are in range 0-255
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError("RGB values must be between 0 and 255")
        return (r, g, b)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid color format: {color_str}. Use format: r,g,b (e.g. 255,0,0 for red)."
        ) from e


def parse_colors(colors_str: str) -> List[Tuple[int, int, int]]:
    """
    Parse a comma-separated list of color strings into a list of RGB tuples.
    Format: r1,g1,b1;r2,g2,b2;...

    :param colors_str: String with multiple colors separated by semicolons
    :return: List of RGB color tuples
    """
    colors = []
    for color in colors_str.split(';'):
        colors.append(parse_color(color))
    return colors


def create_text_animation(args: argparse.Namespace) -> AnimationStrategy:
    """
    Create a text animation based on command-line arguments.

    :param args: Command-line arguments
    :return: The text animation instance
    """
    # No text animation requested
    if args.text_animation is None:
        return None

    animation_class = args.text_animation
    animation_params = {}

    # Common parameters for all text animations
    animation_params["text"] = args.text
    animation_params["font"] = args.text_font

    # Text color only applies to some animations
    if animation_class != "flashing_text":
        animation_params["text_color"] = args.text_color

    if args.text_bg_color is not None:
        animation_params["bg_color"] = args.text_bg_color

    if args.text_bg_brightness is not None:
        animation_params["bg_brightness"] = args.text_bg_brightness

    # Animation-specific parameters
    if animation_class == "scrolling_text":
        animation_params["step_duration"] = args.text_step_duration
    elif animation_class == "flashing_text":
        animation_params["total_duration"] = args.text_total_duration
        animation_params["cycle_duration"] = args.text_cycle_duration
        if args.text_colors:
            animation_params["colors"] = args.text_colors
    elif animation_class == "static_text":
        animation_params["duration"] = args.text_duration
    elif animation_class == "slide_text":
        animation_params["step_duration"] = args.text_step_duration
        animation_params["slide_duration"] = args.text_slide_duration
        animation_params["pause_duration"] = args.text_pause_duration
    elif animation_class in ("slide_in_text", "slide_out_text"):
        animation_params["step_duration"] = args.text_step_duration
        animation_params["slide_duration"] = args.text_slide_duration

    # Create and return the text animation
    try:
        return animation_registry.create_animation(animation_class, **animation_params)
    except Exception as e:
        log.error(f"Failed to create text animation: {e}")
        raise


def create_border_animation(args: argparse.Namespace) -> AnimationStrategy:
    """
    Create a border animation based on command-line arguments.

    :param args: Command-line arguments
    :return: The border animation instance
    """
    # No border animation requested
    if args.border_animation is None:
        return None

    animation_class = args.border_animation
    animation_params = {}

    # Border animation parameters
    if animation_class == "flashing_border":
        if args.border_colors:
            animation_params["colors"] = args.border_colors
        animation_params["duration"] = args.border_duration
    elif animation_class == "running_dots_border":
        animation_params["border_color"] = args.border_color
        animation_params["dot_color"] = args.dot_color
        animation_params["dot_spacing"] = args.dot_spacing
    elif animation_class == "pulsing_border":
        animation_params["border_color"] = args.border_color
        animation_params["duration"] = args.border_duration
    elif animation_class == "police_lights_border":
        animation_params["cycle_duration"] = args.border_cycle_duration

    # Create and return the border animation
    try:
        return animation_registry.create_animation(animation_class, **animation_params)
    except Exception as e:
        log.error(f"Failed to create border animation: {e}")
        raise


def generate_gif(args: argparse.Namespace) -> None:
    """
    Generate a GIF animation with both text and border animations.

    :param args: Command-line arguments
    """
    # Create the animations
    animations = []

    # Create text animation if requested
    text_animation = create_text_animation(args) if args.text_animation else None
    if text_animation:
        animations.append(text_animation)

    # Create border animation if requested
    border_animation = create_border_animation(args) if args.border_animation else None
    if border_animation:
        animations.append(border_animation)

    # Ensure we have at least one animation
    if not animations:
        log.error("No animations specified! Please specify at least one animation.")
        return

    # Create panel and renderer
    panel = Panel(args.width, args.height, args.text_font, args.frame_duration)
    renderer = PanelRenderer(panel, animations)

    # Render the animation
    log.info("Generating animation frames...")
    start_time = monotonic()
    renderer.render(time_limit_sec=args.total_duration / 1000)
    log.info("Generated %s frames in %s ms", len(panel.frames), (monotonic() - start_time) * 1000)

    # Save the GIF
    log.info(f"Saving {len(panel.frames)} frames to {args.output}...")
    start_time = monotonic()
    panel.save(args.output)
    log.info("Saved %s frames in %s ms", len(panel.frames), (monotonic() - start_time) * 1000)
    log.info(f"GIF animation saved to {args.output}")


def add_text_animation_args(parser: argparse.ArgumentParser) -> None:
    """
    Add text animation arguments to the command-line parser.

    :param parser: ArgumentParser instance
    """
    text_group = parser.add_argument_group("Text Animation Options")

    text_group.add_argument(
        "--text-animation",
        choices=TEXT_ANIMATIONS,
        help="Type of text animation to use"
    )
    text_group.add_argument(
        "--text",
        help="Text content for text animations"
    )
    text_group.add_argument(
        "--text-font",
        default="fonts/8x13.bdf",
        help="BDF font file path (relative to the ledscroll module)"
    )
    text_group.add_argument(
        "--text-color",
        type=parse_color,
        default=(255, 255, 255),
        help="Text color in r,g,b format (e.g. 255,0,0 for red)"
    )
    text_group.add_argument(
        "--text-bg-color",
        type=parse_color,
        default=(0, 0, 0),
        help="Text background color in r,g,b format (e.g. 0,0,0 for black)"
    )
    text_group.add_argument(
        "--text-bg-brightness",
        type=int,
        default=100,
        help="Text background brightness percentage (0-100)"
    )

    # Animation-specific parameters
    text_group.add_argument(
        "--text-duration",
        type=int,
        default=1000,
        help="Duration in milliseconds for static_text animation"
    )
    text_group.add_argument(
        "--text-step-duration",
        type=int,
        default=40,
        help="Step duration in milliseconds for scrolling and sliding animations"
    )
    text_group.add_argument(
        "--text-slide-duration",
        type=int,
        default=500,
        help="Slide duration in milliseconds for slide animations"
    )
    text_group.add_argument(
        "--text-pause-duration",
        type=int,
        default=1000,
        help="Pause duration in milliseconds for slide_text animation"
    )
    text_group.add_argument(
        "--text-total-duration",
        type=int,
        default=2000,
        help="Total duration in milliseconds for flashing_text animation"
    )
    text_group.add_argument(
        "--text-cycle-duration",
        type=int,
        default=200,
        help="Cycle duration in milliseconds for flashing_text animation"
    )
    text_group.add_argument(
        "--text-colors",
        type=parse_colors,
        default=None,
        help="Comma-separated list of colors for flashing_text animation (format: r1,g1,b1;r2,g2,b2;...)"
    )


def add_border_animation_args(parser: argparse.ArgumentParser) -> None:
    """
    Add border animation arguments to the command-line parser.

    :param parser: ArgumentParser instance
    """
    border_group = parser.add_argument_group("Border Animation Options")

    border_group.add_argument(
        "--border-animation",
        choices=BORDER_ANIMATIONS,
        help="Type of border animation to use"
    )
    border_group.add_argument(
        "--border-color",
        type=parse_color,
        default=(0, 0, 255),
        help="Border color in r,g,b format for border animations"
    )
    border_group.add_argument(
        "--border-duration",
        type=int,
        default=500,
        help="Duration in milliseconds for flashing_border and pulsing_border animations"
    )
    border_group.add_argument(
        "--border-colors",
        type=parse_colors,
        default=None,
        help="Comma-separated list of colors for flashing_border animation (format: r1,g1,b1;r2,g2,b2;...)"
    )
    border_group.add_argument(
        "--border-cycle-duration",
        type=int,
        default=400,
        help="Cycle duration in milliseconds for police_lights_border animation"
    )

    # Running dots border specific parameters
    border_group.add_argument(
        "--dot-color",
        type=parse_color,
        default=(255, 0, 0),
        help="Dot color in r,g,b format for running_dots_border animation"
    )
    border_group.add_argument(
        "--dot-spacing",
        type=int,
        default=2,
        help="Dot spacing in pixels for running_dots_border animation"
    )


def main() -> None:
    """
    Main entry point for the CLI utility.
    """
    # Load default parameters for reference
    load_default_params()

    # Create the top-level parser
    parser = argparse.ArgumentParser(
        description="Generate GIF animations using the ledscroll animation classes. "
                   "You can specify both a text animation and a border animation together."
    )

    # Common arguments
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output GIF filename (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Width of the GIF in pixels (default: {DEFAULT_WIDTH})"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"Height of the GIF in pixels (default: {DEFAULT_HEIGHT})"
    )
    parser.add_argument(
        "--frame-duration",
        type=int,
        default=DEFAULT_FRAME_DURATION,
        help=f"Duration of each frame in milliseconds (default: {DEFAULT_FRAME_DURATION})"
    )
    parser.add_argument(
        "--total-duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"Total maximum duration of the animation in milliseconds (default: {DEFAULT_DURATION})"
    )

    # Add animation-specific argument groups
    add_text_animation_args(parser)
    add_border_animation_args(parser)

    # Parse arguments
    args = parser.parse_args()

    # Validate that at least one animation type is specified
    if args.text_animation is None and args.border_animation is None:
        parser.error("At least one animation type must be specified. Use --text-animation and/or --border-animation")

    # Check if we have text but no text animation
    if args.text and args.text_animation is None:
        parser.error("You specified text but did not specify a text animation type. Use --text-animation")

    # Check if we have text animation but no text
    if args.text_animation is not None and not args.text:
        parser.error(f"--text is required for {args.text_animation} animation")

    # Generate the GIF animation
    generate_gif(args)


if __name__ == "__main__":
    main()
