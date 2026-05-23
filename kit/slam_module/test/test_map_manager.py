"""
============================================================
FILE        : test_map_manager.py
MODULE      : slam_module (kit/)
DESCRIPTION : Unit tests for map statistics computation.

TESTS:
    - Exploration percentage calculation
    - Empty map handling
    - Full map handling
    - Mixed map values
============================================================
"""


def compute_exploration_stats(map_data, width, height):
    """
    Pure function extracted from MapManager._on_map.
    Computes exploration statistics from OccupancyGrid data.

    OccupancyGrid values:
        -1  = unknown (unexplored)
        0  = free space
        100 = occupied (wall)

    Returns dict with explored_cells, total_cells, explored_pct.
    """
    total_cells = width * height
    explored_cells = sum(1 for cell in map_data if cell != -1)

    if total_cells > 0:
        explored_pct = (explored_cells / total_cells) * 100
    else:
        explored_pct = 0.0

    return {
        "total_cells": total_cells,
        "explored_cells": explored_cells,
        "explored_pct": round(explored_pct, 1),
    }


class TestMapManager:
    """Unit tests for SLAM map statistics logic."""

    def test_empty_map_zero_exploration(self):
        """All-unknown map must have 0% exploration."""
        map_data = [-1] * 100
        stats = compute_exploration_stats(map_data, 10, 10)
        assert stats["explored_cells"] == 0
        assert stats["explored_pct"] == 0.0

    def test_fully_explored_map(self):
        """All-known map must have 100% exploration."""
        map_data = [0] * 100
        stats = compute_exploration_stats(map_data, 10, 10)
        assert stats["explored_cells"] == 100
        assert stats["explored_pct"] == 100.0

    def test_half_explored_map(self):
        """Half explored map must show 50% exploration."""
        map_data = [-1] * 50 + [0] * 50
        stats = compute_exploration_stats(map_data, 10, 10)
        assert stats["explored_cells"] == 50
        assert stats["explored_pct"] == 50.0

    def test_walls_count_as_explored(self):
        """Occupied cells (walls) are explored (known), not unknown."""
        map_data = [100] * 30 + [-1] * 70
        stats = compute_exploration_stats(map_data, 10, 10)
        assert stats["explored_cells"] == 30

    def test_mixed_map(self):
        """Mixed map with free, walls, and unknown."""
        map_data = [0] * 40 + [100] * 20 + [-1] * 40
        stats = compute_exploration_stats(map_data, 10, 10)
        assert stats["explored_cells"] == 60
        assert stats["explored_pct"] == 60.0

    def test_zero_size_map(self):
        """Zero-size map must not cause division by zero."""
        stats = compute_exploration_stats([], 0, 0)
        assert stats["total_cells"] == 0
        assert stats["explored_pct"] == 0.0

    def test_total_cells_calculation(self):
        """Total cells must equal width * height."""
        map_data = [0] * 200
        stats = compute_exploration_stats(map_data, 20, 10)
        assert stats["total_cells"] == 200
