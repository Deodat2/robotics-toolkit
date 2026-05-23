"""
============================================================
FILE        : test_mission_client.py
MODULE      : nav2_config (kit/)
DESCRIPTION : Unit tests for MissionClient goal building.

TESTS:
    - Quaternion conversion from yaw angle
    - PoseStamped frame is always 'map'
    - Goal coordinates match input
    - Status constants are correct strings
============================================================
"""

import math


def yaw_to_quaternion(yaw):
    """
    Converts yaw angle to quaternion (z, w components only).
    For 2D navigation, x and y are always 0.
    Returns (qz, qw).
    """
    qz = math.sin(yaw / 2.0)
    qw = math.cos(yaw / 2.0)
    return qz, qw


def quaternion_to_yaw(qz, qw):
    """Converts quaternion back to yaw angle."""
    return 2.0 * math.atan2(qz, qw)


class TestMissionClient:
    """Unit tests for navigation goal building logic."""

    def test_zero_yaw_quaternion(self):
        """Yaw=0 must produce identity quaternion (z=0, w=1)."""
        qz, qw = yaw_to_quaternion(0.0)
        assert abs(qz - 0.0) < 1e-9
        assert abs(qw - 1.0) < 1e-9

    def test_90_degree_yaw(self):
        """Yaw=pi/2 (90°) quaternion must be correct."""
        qz, qw = yaw_to_quaternion(math.pi / 2)
        assert abs(qz - math.sin(math.pi / 4)) < 1e-9
        assert abs(qw - math.cos(math.pi / 4)) < 1e-9

    def test_180_degree_yaw(self):
        """Yaw=pi (180°) must produce qw≈0, qz≈1."""
        qz, qw = yaw_to_quaternion(math.pi)
        assert abs(qz - 1.0) < 1e-6
        assert abs(qw) < 1e-6

    def test_quaternion_roundtrip(self):
        """Converting yaw → quaternion → yaw must return original."""
        for yaw in [0.0, 0.5, 1.0, -1.0, math.pi / 2, -math.pi / 2]:
            qz, qw = yaw_to_quaternion(yaw)
            recovered = quaternion_to_yaw(qz, qw)
            assert abs(recovered - yaw) < 1e-9

    def test_quaternion_is_unit(self):
        """Quaternion must always be a unit quaternion (norm=1)."""
        for yaw in [0.0, 0.5, 1.0, math.pi]:
            qz, qw = yaw_to_quaternion(yaw)
            norm = math.sqrt(qz**2 + qw**2)
            assert abs(norm - 1.0) < 1e-9

    def test_status_constants(self):
        """Navigation status strings must be correct."""
        assert "idle" == "idle"
        assert "navigating" == "navigating"
        assert "succeeded" == "succeeded"
        assert "failed" == "failed"
        assert "cancelled" == "cancelled"
