# kit/collision_manager/test/test_collision_monitor.py
"""
============================================================
FILE        : test_collision_monitor.py
MODULE      : collision_manager (kit/)
DESCRIPTION : Unit tests for collision detection logic.

TESTS:
    - Distance calculation accuracy
    - Risk level classification
    - Edge cases (same position, very far apart)
============================================================
"""

import math


# ============================================================
# Pure logic for testing
# ============================================================

def compute_distance(pos_a: tuple, pos_b: tuple) -> float:
    """Euclidean distance between two (x, y) positions."""
    return math.sqrt(
        (pos_a[0] - pos_b[0]) ** 2 +
        (pos_a[1] - pos_b[1]) ** 2
    )


def classify_risk(
    distance: float,
    warning_dist: float,
    critical_dist: float
) -> str:
    """Classifies collision risk based on distance."""
    if distance < critical_dist:
        return "critical"
    elif distance < warning_dist:
        return "warning"
    return "none"


# ============================================================
# TEST SUITE
# ============================================================

class TestCollisionMonitor:
    """Unit tests for collision detection logic."""

    WARNING_DIST = 1.5
    CRITICAL_DIST = 0.8

    def test_same_position_is_critical(self):
        """Two robots at same position must be critical."""
        distance = compute_distance((0.0, 0.0), (0.0, 0.0))
        risk = classify_risk(
            distance, self.WARNING_DIST, self.CRITICAL_DIST
        )
        assert risk == "critical"

    def test_far_apart_is_safe(self):
        """Robots far apart must have no risk."""
        distance = compute_distance((0.0, 0.0), (10.0, 0.0))
        risk = classify_risk(
            distance, self.WARNING_DIST, self.CRITICAL_DIST
        )
        assert risk == "none"

    def test_warning_zone(self):
        """Distance between critical and warning must be warning."""
        # 1.2m is between 0.8 (critical) and 1.5 (warning)
        distance = compute_distance((0.0, 0.0), (1.2, 0.0))
        risk = classify_risk(
            distance, self.WARNING_DIST, self.CRITICAL_DIST
        )
        assert risk == "warning"

    def test_critical_zone(self):
        """Distance below critical threshold must be critical."""
        distance = compute_distance((0.0, 0.0), (0.5, 0.0))
        risk = classify_risk(
            distance, self.WARNING_DIST, self.CRITICAL_DIST
        )
        assert risk == "critical"

    def test_distance_calculation_accuracy(self):
        """Distance calculation must match known Pythagorean result."""
        # 3-4-5 triangle: sqrt(3² + 4²) = 5.0
        distance = compute_distance((0.0, 0.0), (3.0, 4.0))
        assert abs(distance - 5.0) < 1e-9

    def test_distance_is_symmetric(self):
        """Distance A→B must equal B→A."""
        pos_a = (1.0, 2.0)
        pos_b = (4.0, 6.0)
        assert compute_distance(pos_a, pos_b) == compute_distance(pos_b, pos_a)

    def test_exactly_at_warning_threshold(self):
        """Distance exactly at warning threshold must be safe (not warning)."""
        distance = self.WARNING_DIST  # exactly 1.5m
        risk = classify_risk(
            distance, self.WARNING_DIST, self.CRITICAL_DIST
        )
        # < 1.5 is warning, = 1.5 is safe
        assert risk == "none"

    def test_exactly_at_critical_threshold(self):
        """Distance exactly at critical threshold must be warning (not critical)."""
        distance = self.CRITICAL_DIST  # exactly 0.8m
        risk = classify_risk(
            distance, self.WARNING_DIST, self.CRITICAL_DIST
        )
        # < 0.8 is critical, = 0.8 is warning
        assert risk == "warning"

    def test_diagonal_distance(self):
        """Diagonal distance must use full 2D formula."""
        # sqrt(1² + 1²) ≈ 1.414m → warning zone
        distance = compute_distance((0.0, 0.0), (1.0, 1.0))
        risk = classify_risk(
            distance, self.WARNING_DIST, self.CRITICAL_DIST
        )
        assert abs(distance - math.sqrt(2)) < 1e-9
        assert risk == "warning"
