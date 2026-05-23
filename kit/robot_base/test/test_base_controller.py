"""
============================================================
FILE        : test_base_controller.py
MODULE      : robot_base (kit/)
DESCRIPTION : Unit tests for BaseController safety logic.

TESTS:
    - Velocity clamping within limits
    - Negative velocity clamping
    - Zero velocity passes through
    - Boundary values handled correctly
============================================================
"""


def clamp(value, min_val, max_val):
    """Clamps value between min_val and max_val."""
    return max(min_val, min(max_val, value))


def apply_velocity_limits(linear, angular, max_linear, max_angular):
    """
    Pure function extracted from BaseController._on_cmd_vel.
    Returns (clamped_linear, clamped_angular).
    """
    clamped_linear = clamp(linear, -max_linear, max_linear)
    clamped_angular = clamp(angular, -max_angular, max_angular)
    return clamped_linear, clamped_angular


class TestBaseController:
    """Unit tests for robot base controller safety logic."""

    MAX_LINEAR = 0.5
    MAX_ANGULAR = 1.0

    def test_valid_velocity_passes_through(self):
        """Velocities within limits must not be modified."""
        linear, angular = apply_velocity_limits(
            0.3, 0.5, self.MAX_LINEAR, self.MAX_ANGULAR
        )
        assert linear == 0.3
        assert angular == 0.5

    def test_linear_clamped_above_max(self):
        """Linear velocity above max must be clamped to max."""
        linear, _ = apply_velocity_limits(
            2.0, 0.0, self.MAX_LINEAR, self.MAX_ANGULAR
        )
        assert linear == self.MAX_LINEAR

    def test_linear_clamped_below_negative_max(self):
        """Negative linear velocity below -max must be clamped."""
        linear, _ = apply_velocity_limits(
            -2.0, 0.0, self.MAX_LINEAR, self.MAX_ANGULAR
        )
        assert linear == -self.MAX_LINEAR

    def test_angular_clamped_above_max(self):
        """Angular velocity above max must be clamped to max."""
        _, angular = apply_velocity_limits(
            0.0, 5.0, self.MAX_LINEAR, self.MAX_ANGULAR
        )
        assert angular == self.MAX_ANGULAR

    def test_zero_velocity_passes_through(self):
        """Zero velocity must pass through unchanged."""
        linear, angular = apply_velocity_limits(
            0.0, 0.0, self.MAX_LINEAR, self.MAX_ANGULAR
        )
        assert linear == 0.0
        assert angular == 0.0

    def test_exactly_at_max_passes_through(self):
        """Velocity exactly at max limit must not be clamped."""
        linear, angular = apply_velocity_limits(
            self.MAX_LINEAR, self.MAX_ANGULAR,
            self.MAX_LINEAR, self.MAX_ANGULAR
        )
        assert linear == self.MAX_LINEAR
        assert angular == self.MAX_ANGULAR

    def test_both_clamped_simultaneously(self):
        """Both linear and angular can be clamped in same call."""
        linear, angular = apply_velocity_limits(
            10.0, 10.0, self.MAX_LINEAR, self.MAX_ANGULAR
        )
        assert linear == self.MAX_LINEAR
        assert angular == self.MAX_ANGULAR
