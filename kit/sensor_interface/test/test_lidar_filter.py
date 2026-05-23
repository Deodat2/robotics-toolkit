"""
============================================================
FILE        : test_lidar_filter.py
MODULE      : sensor_interface (kit/)
DESCRIPTION : Unit tests for LidarFilter node.

TESTS:
    - Filter removes NaN values
    - Filter removes Inf values
    - Filter removes out-of-range values
    - Valid values pass through unchanged
    - Statistics are correctly tracked

RUN:
    cd ~/robotics/robotics-toolkit/projects/amr_ros2
    colcon test --packages-select sensor_interface
    colcon test-result --verbose
============================================================
"""

import math


class MockParameter:
    """Minimal mock for ROS 2 Parameter object."""

    def __init__(self, value):
        self.value = value


class MockLogger:
    """Minimal mock for ROS 2 node logger."""

    def info(self, msg, **kwargs): pass
    def warn(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass


class MockNode:
    """
    Minimal mock for a ROS 2 node.
    Allows testing LidarFilter logic without a running ROS 2 instance.
    """

    def __init__(self):
        self._params = {
            'input_topic': '/scan',
            'output_topic': '/sensors/lidar/filtered',
            'min_range': 0.12,
            'max_range': 10.0,
        }
        self._logger = MockLogger()

    def declare_parameter(self, name, default):
        pass

    def get_parameter(self, name):
        return MockParameter(self._params.get(name))

    def get_logger(self):
        return self._logger

    def create_subscription(self, *args, **kwargs):
        return None

    def create_publisher(self, *args, **kwargs):
        return None

    def create_timer(self, *args, **kwargs):
        return None


# ============================================================
# Pure logic extracted from LidarFilter for testing
# We test the filtering logic directly, without ROS 2
# ============================================================

def filter_ranges(
    ranges: list,
    min_range: float,
    max_range: float
) -> tuple:
    """
    Pure function extracted from LidarFilter._on_scan.
    Filters a list of range values.

    Returns:
        (filtered_ranges, invalid_count)
    """
    filtered = []
    invalid_count = 0

    for r in ranges:
        if (math.isnan(r) or
                math.isinf(r) or
                r < min_range or
                r > max_range):
            filtered.append(max_range)
            invalid_count += 1
        else:
            filtered.append(r)

    return filtered, invalid_count


# ============================================================
# TEST SUITE
# ============================================================

class TestLidarFilter:
    """Unit tests for LiDAR filtering logic."""

    MIN_RANGE = 0.12
    MAX_RANGE = 10.0

    def test_valid_values_pass_through(self):
        """Valid range values must not be modified."""
        ranges = [1.0, 2.5, 5.0, 9.9, 0.5]
        filtered, invalid = filter_ranges(
            ranges, self.MIN_RANGE, self.MAX_RANGE
        )
        assert filtered == ranges
        assert invalid == 0

    def test_nan_values_replaced(self):
        """NaN values must be replaced with max_range."""
        ranges = [1.0, float('nan'), 3.0]
        filtered, invalid = filter_ranges(
            ranges, self.MIN_RANGE, self.MAX_RANGE
        )
        assert not math.isnan(filtered[1])
        assert filtered[1] == self.MAX_RANGE
        assert invalid == 1

    def test_inf_values_replaced(self):
        """Infinite values must be replaced with max_range."""
        ranges = [float('inf'), 2.0, float('-inf')]
        filtered, invalid = filter_ranges(
            ranges, self.MIN_RANGE, self.MAX_RANGE
        )
        assert filtered[0] == self.MAX_RANGE
        assert filtered[2] == self.MAX_RANGE
        assert invalid == 2

    def test_below_min_range_replaced(self):
        """Values below min_range must be replaced."""
        ranges = [0.05, 0.10, 0.11, 0.12]
        filtered, invalid = filter_ranges(
            ranges, self.MIN_RANGE, self.MAX_RANGE
        )
        # 0.05, 0.10, 0.11 are below 0.12 → replaced
        assert filtered[0] == self.MAX_RANGE
        assert filtered[1] == self.MAX_RANGE
        assert filtered[2] == self.MAX_RANGE
        # 0.12 is exactly min_range → valid
        assert filtered[3] == 0.12
        assert invalid == 3

    def test_above_max_range_replaced(self):
        """Values above max_range must be replaced."""
        ranges = [10.0, 10.1, 15.0, 100.0]
        filtered, invalid = filter_ranges(
            ranges, self.MIN_RANGE, self.MAX_RANGE
        )
        # 10.0 is exactly max_range → valid
        assert filtered[0] == 10.0
        # 10.1, 15.0, 100.0 are above max_range → replaced
        assert filtered[1] == self.MAX_RANGE
        assert filtered[2] == self.MAX_RANGE
        assert filtered[3] == self.MAX_RANGE
        assert invalid == 3

    def test_empty_ranges(self):
        """Empty range list must return empty list."""
        filtered, invalid = filter_ranges([], self.MIN_RANGE, self.MAX_RANGE)
        assert filtered == []
        assert invalid == 0

    def test_all_invalid_ranges(self):
        """All invalid ranges must all be replaced with max_range."""
        ranges = [float('nan')] * 5 + [float('inf')] * 5
        filtered, invalid = filter_ranges(
            ranges, self.MIN_RANGE, self.MAX_RANGE
        )
        assert all(r == self.MAX_RANGE for r in filtered)
        assert invalid == 10

    def test_mixed_valid_invalid(self):
        """Mixed list: valid values kept, invalid replaced."""
        ranges = [1.0, float('nan'), 2.0, float('inf'), 0.05, 5.0]
        filtered, invalid = filter_ranges(
            ranges, self.MIN_RANGE, self.MAX_RANGE
        )
        assert filtered[0] == 1.0           # valid
        assert filtered[1] == self.MAX_RANGE  # nan → replaced
        assert filtered[2] == 2.0           # valid
        assert filtered[3] == self.MAX_RANGE  # inf → replaced
        assert filtered[4] == self.MAX_RANGE  # below min → replaced
        assert filtered[5] == 5.0           # valid
        assert invalid == 3

    def test_output_length_preserved(self):
        """Output list must have same length as input."""
        ranges = [float('nan')] * 360  # typical 360-ray scan
        filtered, _ = filter_ranges(
            ranges, self.MIN_RANGE, self.MAX_RANGE
        )
        assert len(filtered) == 360

    def test_invalid_count_accuracy(self):
        """Invalid count must exactly match number of replaced values."""
        ranges = [1.0, float('nan'), float('inf'), 0.05, 11.0, 5.0]
        _, invalid = filter_ranges(ranges, self.MIN_RANGE, self.MAX_RANGE)
        # nan, inf, 0.05 (below min), 11.0 (above max) = 4 invalid
        assert invalid == 4
