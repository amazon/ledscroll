"""pytest configuration and fixtures for performance testing."""
import os
import pytest
from pathlib import Path

TEST_OUTPUT_DIR = "test_output"

# Configure pytest-benchmark
def pytest_benchmark_update_json(config, benchmarks, output_json):
    """Update benchmark JSON output with additional metadata."""
    output_json.update({
        'project': 'ledscroll',
        'commit': os.environ.get('GIT_COMMIT_HASH', 'unknown'),
        'branch': os.environ.get('GIT_BRANCH', 'unknown'),
    })

# Fixtures for common test data
@pytest.fixture(scope='session')
def benchmark_config():
    """Default benchmark configuration."""
    return {
        'min_rounds': 5,
        'max_time': 30.0,
        'warmup': True,
        'warmup_iterations': 2,
    }

class Args:
    """Simple argument namespace class."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def get_test_output_dir() -> Path:
    """Get the test output directory, creating it if it doesn't exist."""
    output_dir = Path(__file__).parent / TEST_OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    return output_dir

