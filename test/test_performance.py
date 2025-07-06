"""
Performance tests for LED scrolling animations using pytest-benchmark.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any
from .conftest import get_test_output_dir, Args
from .reference import generate_reference_gif

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import the CLI module
from ledscroll.cli import generate_gif, parse_color

# Test configuration
# TEST_TEXT = "PERFORMANCE TEST"
TEST_TEXT = "CLI utility for generating GIF animations using both text and border animation classes."

# Common arguments for all tests
COMMON_ARGS = {
    'width': 64,
    'height': 16,
    'frame_duration': 40,
    'text_font': 'fonts/8x13.bdf',
    'text': TEST_TEXT,
    'text_animation': 'scrolling_text',
    'text_color': parse_color('255,255,255'),
    'text_bg_color': parse_color('0,0,0'),
    'text_bg_brightness': 100,
    'text_step_duration': 40,
    'total_duration': 30000,  # Limit to 30 seconds
    'output': '',  # Will be set in the test
}

# Border animation configurations
BORDER_CONFIGS = [
    {'border_animation': None},
    {
        'border_animation': 'flashing_border',
        'border_colors': [parse_color('255,0,0'), parse_color('0,0,255')],
        'border_duration': 1000,
    },
    {
        'border_animation': 'running_dots_border',
        'border_color': parse_color('0,255,0'),  # This is the border color
        'dot_color': parse_color('0,255,0'),     # This is the dot color
        'dot_size': 2,
        'dot_spacing': 4,
        'dot_speed': 1,
    },
    {
        'border_animation': 'pulsing_border',
        'border_color': parse_color('255,165,0'),  # Orange
        'border_duration': 1000,  # Duration in ms
        'pulse_min': 50,
        'pulse_max': 255,
        'pulse_speed': 2,
    },
    {
        'border_animation': 'police_lights_border',
        'border_cycle_duration': 2000,
    },
]

def generate_test_gif(args_dict: Dict[str, Any], test_name: str) -> str:
    """Generate a test GIF with the given arguments."""
    output_file = str(get_test_output_dir() / f"{test_name}.gif")
    args = Args(**{**args_dict, 'output': output_file})
    generate_gif(args)
    return output_file

def test_scrolling_text(benchmark, border_config: Dict[str, Any]):
    """Benchmark scrolling text animation with border animation."""
    # Set up the test
    test_name = border_config['border_animation'] or 'no_border'

    # Create the args dictionary once
    args = {**COMMON_ARGS, **border_config}

    # The benchmarked function
    def run_benchmark():
        output_file = generate_test_gif(args, test_name)
        # Clean up the output file after the test
        try:
            os.remove(output_file)
        except OSError:
            pass

    # Run the benchmark
    benchmark(run_benchmark)

# Generate a separate test for each border configuration
def pytest_generate_tests(metafunc):
    if "border_config" in metafunc.fixturenames:
        metafunc.parametrize("border_config", BORDER_CONFIGS, ids=[
            config['border_animation'] or 'no_border'
            for config in BORDER_CONFIGS
        ])

def test_scrolling_text_reference(benchmark):
    """Benchmark reference scrolling text animation."""
    args = {**COMMON_ARGS, 'border_animation': None}
    test_name = "scrolling_text_reference"

    def run_benchmark():
        output_file = generate_reference_gif(args, test_name)
        try:
            os.remove(output_file)
        except OSError:
            pass

    benchmark(run_benchmark)