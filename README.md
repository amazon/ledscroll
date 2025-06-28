# LED Scroll: GIF Animation Generator

LED Scroll is a Python package that allows you to create LED panel-like animations as GIF files. It provides both a command-line interface (CLI) and a Python library for generating various animations including scrolling text, flashing borders, pulsing effects, and more.

## Installation

LED Scroll can be installed using `uv` package manager:

```bash
# Install dependencies
uv add pillow bdflib docstring_parser

# Run the LED Scroll package
uv run ledscroll
```

## Command-Line Usage

The CLI utility allows you to generate GIF animations by specifying a text animation, a border animation, or both.

### Basic Usage

```bash
uv run ledscroll [animation options] --output animation.gif
```

### Combining Text and Border Animations

You can combine text and border animations to create more complex effects:

```bash
uv run ledscroll --text-animation scrolling_text --text "Hello World" \
                --text-color 255,0,0 \
                --border-animation flashing_border \
                --border-colors "0,0,255;255,0,0" \
                --output combined_animation.gif
```

### Text Animation Types

The following text animation types are available:

- `scrolling_text`: Text that scrolls from right to left
- `flashing_text`: Text that flashes between different colors
- `static_text`: Text that remains static
- `slide_text`: Text that slides in, pauses, and slides out
- `slide_in_text`: Text that slides in from the right
- `slide_out_text`: Text that slides out to the left

### Border Animation Types

The following border animation types are available:

- `no_border`: No border animation
- `flashing_border`: Border that flashes between different colors
- `running_dots_border`: Border with dots running around it
- `pulsing_border`: Border that pulses in brightness
- `police_lights_border`: Border that alternates between blue and red

### Text Animation Options

```bash
# Scrolling Text Animation
uv run ledscroll --text-animation scrolling_text --text "Hello World" \
                --text-color 255,0,0 --text-step-duration 40 \
                --output scrolling_text.gif

# Flashing Text Animation
uv run ledscroll --text-animation flashing_text --text "ALERT!" \
                --text-colors "255,0,0;0,0,0" --text-cycle-duration 300 \
                --output flashing_text.gif

# Static Text Animation
uv run ledscroll --text-animation static_text --text "HELLO" \
                --text-color 0,255,0 --text-duration 2000 \
                --output static_text.gif

# Slide Text Animation
uv run ledscroll --text-animation slide_text --text "Welcome!" \
                --text-color 255,255,0 --text-slide-duration 500 \
                --text-pause-duration 1000 --output slide_text.gif
```

### Border Animation Options

```bash
# Flashing Border Animation
uv run ledscroll --border-animation flashing_border \
                --border-colors "255,0,0;0,0,255" --border-duration 300 \
                --output flashing_border.gif

# Running Dots Border Animation
uv run ledscroll --border-animation running_dots_border \
                --border-color 0,0,255 --dot-color 255,0,0 \
                --dot-spacing 2 --output running_dots.gif

# Pulsing Border Animation
uv run ledscroll --border-animation pulsing_border \
                --border-color 0,255,0 --border-duration 400 \
                --output pulsing_border.gif

# Police Lights Border Animation
uv run ledscroll --border-animation police_lights_border \
                --border-cycle-duration 300 --output police_lights.gif
```

### Common Options

```bash
--width INT           Width of the GIF in pixels (default: 64)
--height INT          Height of the GIF in pixels (default: 16)
--frame-duration INT  Duration of each frame in milliseconds (default: 40)
--total-duration INT  Total maximum duration of the animation in milliseconds (default: 3000)
-o, --output FILE     Output GIF filename (default: animation.gif)
```

## Library Usage

LED Scroll can also be used as a Python library, allowing for more customization and integration into your own applications.

### Creating Basic Animations

```python
from ledscroll.animations.registry import animation_registry
from ledscroll.led_panel import Panel, PanelRenderer

# Create a panel
panel = Panel(width=64, height=16, font="fonts/8x13.bdf", duration=40)

# Create animations
text_animation = animation_registry.create_animation(
    "scrolling_text",
    text="Hello World",
    text_color=(255, 0, 0),
    step_duration=40
)

border_animation = animation_registry.create_animation(
    "flashing_border",
    colors=[(0, 0, 255), (255, 0, 0)],
    duration=300
)

# Combine animations
renderer = PanelRenderer(panel, [text_animation, border_animation])

# Render the animation
renderer.render(time_limit_sec=3)

# Save the animation as a GIF
panel.save("combined_animation.gif")
```

### Available Animation Classes

#### Base Classes

- `AnimationStrategy`: Base class for all animations
- `TextAnimationStrategy`: Base class for text-based animations

#### Text Animation Classes

```python
from ledscroll.animations.simple import ScrollingTextAnimation, FlashingTextAnimation, StaticTextAnimation
from ledscroll.animations.slide_text import SlideTextAnimation

# Scrolling Text Animation
scrolling_text = ScrollingTextAnimation(
    text="Hello World",
    font="fonts/8x13.bdf",
    text_color=(255, 0, 0),
    step_duration=40
)

# Flashing Text Animation
flashing_text = FlashingTextAnimation(
    text="ALERT!",
    font="fonts/8x13.bdf",
    total_duration=2000,
    cycle_duration=200,
    colors=[(255, 0, 0), (0, 0, 0)],
    bg_color=(0, 0, 0),
    bg_brightness=100
)
```

#### Border Animation Classes

```python
from ledscroll.animations.simple import FlashingBorderAnimation, RunningDotsBorderAnimation, PulsingBorderAnimation

# Flashing Border Animation
flashing_border = FlashingBorderAnimation(
    colors=[(0, 0, 255), (255, 0, 0)],
    duration=300
)

# Running Dots Border Animation
running_dots = RunningDotsBorderAnimation(
    border_color=(0, 0, 255),
    dot_color=(255, 0, 0),
    dot_spacing=2
)
```

#### Complex Animations

```python
from ledscroll.animations.complex import ComplexAnimation
from ledscroll.animations.simple import StaticTextAnimation, SlideInTextAnimation, SlideOutTextAnimation

# Create individual animations
slide_in = SlideInTextAnimation(text="Welcome!", text_color=(255, 255, 0), slide_duration=500)
static = StaticTextAnimation(text="Welcome!", text_color=(255, 255, 0), duration=1000)
slide_out = SlideOutTextAnimation(text="Welcome!", text_color=(255, 255, 0), slide_duration=500)

# Combine into a complex animation
complex_animation = ComplexAnimation([slide_in, static, slide_out])
```

## Architecture

LED Scroll uses a component-based architecture:

- `Panel`: Manages the LED panel display and frame rendering
- `PanelRenderer`: Coordinates multiple animations on a panel
- `AnimationStrategy`: Base class for all animations, with a `render` method
- `animation_registry`: Registry for dynamically discovering and creating animations

## Examples

For more examples, refer to the usage patterns shown in `cli_combined.py` which demonstrates how to create and combine various animation types.

## Dependencies

- `Pillow`: For image processing and GIF generation
- `bdflib`: For reading BDF font files
- `docstring_parser`: For parsing docstrings to get parameter information