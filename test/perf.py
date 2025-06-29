"""
Performance test for measuring scrolling text animation with different border animations.
"""
import os
import sys
import time
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import the CLI module
from ledscroll.cli import generate_gif as generate_gif
from ledscroll.cli_simple import parse_color

# Test configuration
TEST_TEXT = "PERFORMANCE TEST"
TEST_OUTPUT_DIR = "test_output"
TEST_ITERATIONS = 50  # Number of measurements per animation

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
    'total_duration': 2000,  # 2 seconds per test
    'output': '',  # Will be set in the test
}

# List of border animations to test
BORDER_ANIMATIONS = [
    None,  # No border animation
    'no_border',
    'flashing_border',
    'running_dots_border',
    'pulsing_border',
    'police_lights_border',
]

# Border animation parameters
BORDER_PARAMS = {
    'flashing_border': {
        'border_colors': [parse_color('255,0,0'), parse_color('0,0,255')],
        'border_duration': 500,
    },
    'running_dots_border': {
        'border_color': parse_color('0,255,0'),
        'dot_color': parse_color('255,0,0'),
        'dot_spacing': 2,
    },
    'pulsing_border': {
        'border_color': parse_color('255,0,255'),
        'border_duration': 1000,
    },
    'police_lights_border': {
        'border_cycle_duration': 400,  # Parameter name must match CLI argument
    },
}

class Args:
    """Simple argument namespace class."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def run_animation_test(args_dict: Dict[str, Any], output_file: str) -> float:
    """
    Run a single animation test and return the execution time.

    Args:
        args_dict: Dictionary of arguments for the animation (without output)
        output_file: Path to save the output GIF

    Returns:
        Execution time in seconds
    """
    # Create a copy of args_dict to avoid modifying the original
    test_args = args_dict.copy()
    test_args['output'] = output_file
    args = Args(**test_args)
    start_time = time.time()
    generate_gif(args)
    return time.time() - start_time

def measure_animation_performance() -> Dict[str, List[float]]:
    """
    Measure performance of all border animations with scrolling text.
    Uses a round-robin measurement sequence for more consistent results.

    Returns:
        Dictionary mapping animation names to lists of execution times
    """
    results = {}

    # Initialize results dictionary
    for border_anim in BORDER_ANIMATIONS:
        anim_name = border_anim if border_anim is not None else 'no_border'
        results[anim_name] = []

    # Create output directory if it doesn't exist
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    # Run tests in round-robin fashion
    for i in range(TEST_ITERATIONS):
        print(f"\nMeasurement round {i+1}/{TEST_ITERATIONS}")
        print("-" * 30)

        for border_anim in BORDER_ANIMATIONS:
            # Prepare test arguments
            test_args = COMMON_ARGS.copy()
            test_args['border_animation'] = border_anim

            # Add border-specific parameters if they exist
            if border_anim in BORDER_PARAMS:
                test_args.update(BORDER_PARAMS[border_anim])

            # Set output file
            anim_name = border_anim if border_anim is not None else 'no_border'
            output_file = os.path.join(TEST_OUTPUT_DIR, f"{anim_name}_{i+1}.gif")

            # Run the test
            print(f"  Running {anim_name}...", end=' ', flush=True)
            try:
                elapsed = run_animation_test(test_args, output_file)
                results[anim_name].append(elapsed)
                print(f"{elapsed:.3f}s")

                # Clean up the output file
                try:
                    os.remove(output_file)
                except OSError:
                    pass

            except Exception as e:
                print(f"Error: {e}")
                results[anim_name].append(float('inf'))

    return results

def calculate_statistics(results: Dict[str, List[float]]) -> Dict[str, Dict[str, Union[float, str]]]:
    """
    Calculate statistics from the raw timing results.

    Args:
        results: Dictionary mapping animation names to lists of execution times

    Returns:
        Dictionary containing statistics for each animation
    """
    stats = {}
    for anim_name, times in results.items():
        valid_times = [t for t in times if t != float('inf')]
        if not valid_times:
            stats[anim_name] = {
                'avg': float('nan'),
                'std': float('nan'),
                'min': float('nan'),
                'max': float('nan'),
                'samples': 0
            }
            continue

        stats[anim_name] = {
            'avg': statistics.mean(valid_times),
            'std': statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
            'min': min(valid_times),
            'max': max(valid_times),
            'samples': len(valid_times)
        }
    return stats

def save_results_to_json(
    results: Dict[str, List[float]],
    output_dir: str = TEST_OUTPUT_DIR,
    filename: str = None
) -> str:
    """
    Save the performance test results to a JSON file.

    Args:
        results: Raw timing results
        output_dir: Directory to save the JSON file
        filename: Optional custom filename (without extension)

    Returns:
        Path to the saved JSON file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with timestamp if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_results_{timestamp}.json"
    elif not filename.endswith('.json'):
        filename += '.json'

    filepath = os.path.join(output_dir, filename)

    # Prepare data for JSON serialization
    stats = calculate_statistics(results)

    # Create result dictionary
    result_data = {
        'metadata': {
            'test_date': datetime.now().isoformat(),
            'test_iterations': TEST_ITERATIONS,
            'animation_duration_ms': COMMON_ARGS['total_duration'],
            'test_environment': {
                'python_version': sys.version,
                'platform': sys.platform
            }
        },
        'raw_results': results,
        'statistics': stats,
        'relative_performance': {}
    }

    # Calculate relative performance
    sorted_anims = sorted(
        [(k, v) for k, v in stats.items() if v['avg'] != float('inf')],
        key=lambda x: x[1]['avg']
    )

    if sorted_anims:
        fastest_avg = sorted_anims[0][1]['avg']
        for anim_name, s in sorted_anims[1:]:
            if s['avg'] > 0:
                result_data['relative_performance'][anim_name] = {
                    'slower_than_fastest_pct': ((s['avg'] / fastest_avg) - 1) * 100,
                    'relative_to_fastest': s['avg'] / fastest_avg
                }

    # Write to file
    with open(filepath, 'w') as f:
        json.dump(result_data, f, indent=2)

    return filepath

def print_results(results: Dict[str, List[float]]) -> None:
    """
    Print the performance test results in a formatted table.

    Args:
        results: Dictionary mapping animation names to lists of execution times
    """
    stats = calculate_statistics(results)

    # Sort animations by average time (fastest first)
    sorted_anims = sorted(stats.items(), key=lambda x: x[1]['avg'] if not x[1]['avg'] != x[1]['avg'] else float('inf'))

    # Print results
    print("\n" + "=" * 80)
    print("Performance Test Results: Scrolling Text with Different Border Animations")
    print("=" * 80)
    print(f"Test iterations: {TEST_ITERATIONS}")
    print(f"Test duration per animation: {COMMON_ARGS['total_duration']/1000:.1f} seconds")
    print("-" * 80)
    print(f"{'Animation':<25} {'Avg (s)':>10} {'StdDev':>10} {'Min (s)':>10} {'Max (s)':>10} {'Samples':>8}")
    print("-" * 80)

    for anim_name, s in sorted_anims:
        if s['avg'] != s['avg']:  # Check for NaN
            print(f"{anim_name:<25} {'ERROR':>10} {'':>10} {'':>10} {'':>10} {s['samples']:>8}")
        else:
            print(
                f"{anim_name:<25} "
                f"{s['avg']:>10.3f} "
                f"{s['std']:>10.3f} "
                f"{s['min']:>10.3f} "
                f"{s['max']:>10.3f} "
                f"{s['samples']:>8}"
            )

    # Print relative performance
    print("\nRelative Performance (compared to fastest):")
    print("-" * 50)
    if sorted_anims and sorted_anims[0][1]['avg'] > 0:
        fastest_avg = sorted_anims[0][1]['avg']
        for anim_name, s in sorted_anims[1:]:
            if s['avg'] != float('inf'):
                slower = ((s['avg'] / fastest_avg) - 1) * 100
                print(f"{anim_name:<25} is {slower:>6.1f}% slower")

    print("=" * 80)

def main():
    """Main function to run performance tests."""
    print("=" * 50)
    print("Performance Test: Scrolling Text with Different Border Animations")
    print(f"Number of measurements: {TEST_ITERATIONS}")
    print("=" * 50)

    # Run tests
    results = measure_animation_performance()

    # Print results to console
    print_results(results)

    # Save results to JSON file
    try:
        json_path = save_results_to_json(results)
        print(f"\nResults saved to: {json_path}")
    except Exception as e:
        print(f"\nError saving results to JSON: {e}")


if __name__ == "__main__":
    main()