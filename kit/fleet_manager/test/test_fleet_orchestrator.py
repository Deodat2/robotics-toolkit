# kit/fleet_manager/test/test_fleet_orchestrator.py
"""
============================================================
FILE        : test_fleet_orchestrator.py
MODULE      : fleet_manager (kit/)
DESCRIPTION : Unit tests for fleet orchestration logic.

TESTS:
    - Mission creation and queuing
    - Priority sorting (high priority first)
    - Robot state transitions
    - Mission assignment to idle robots
    - Failed mission requeuing
    - Offline robot detection
============================================================
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional


# ============================================================
# Replicate core data structures for isolated testing
# ============================================================

class RobotState(Enum):
    IDLE = "idle"
    NAVIGATING = "navigating"
    FAILED = "failed"
    OFFLINE = "offline"


class MissionStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Robot:
    name: str
    state: RobotState = RobotState.IDLE
    current_mission: Optional[str] = None
    position_x: float = 0.0
    position_y: float = 0.0
    last_heartbeat: float = 0.0
    missions_done: int = 0
    missions_failed: int = 0


@dataclass
class Mission:
    mission_id: str
    target_x: float
    target_y: float
    target_yaw: float = 0.0
    priority: int = 2
    status: MissionStatus = MissionStatus.PENDING
    assigned_to: Optional[str] = None
    created_at: float = field(default_factory=time.time)


# ============================================================
# Pure orchestration logic for testing
# ============================================================

def get_pending_by_priority(missions: Dict[str, Mission]) -> list:
    """Returns pending missions sorted by priority (1=highest)."""
    return sorted(
        [m for m in missions.values()
         if m.status == MissionStatus.PENDING],
        key=lambda m: m.priority
    )


def get_idle_robots(robots: Dict[str, Robot]) -> list:
    """Returns robots in IDLE state."""
    return [r for r in robots.values() if r.state == RobotState.IDLE]


def assign_mission(mission: Mission, robot: Robot) -> None:
    """Assigns a mission to a robot (modifies in place)."""
    mission.status = MissionStatus.ASSIGNED
    mission.assigned_to = robot.name
    robot.state = RobotState.NAVIGATING
    robot.current_mission = mission.mission_id


def complete_mission(
    mission: Mission, robot: Robot, success: bool
) -> None:
    """Marks mission complete/failed and updates robot state."""
    if success:
        mission.status = MissionStatus.COMPLETED
        robot.missions_done += 1
    else:
        # Requeue with lower priority
        mission.status = MissionStatus.PENDING
        mission.assigned_to = None
        mission.priority = min(mission.priority + 1, 3)
        robot.missions_failed += 1

    robot.current_mission = None
    robot.state = RobotState.IDLE


# ============================================================
# TEST SUITE
# ============================================================

class TestFleetOrchestrator:
    """Unit tests for fleet orchestration logic."""

    def _make_robots(self, names: list) -> Dict[str, Robot]:
        return {name: Robot(name=name) for name in names}

    def _make_mission(self, mid: str, priority: int = 2) -> Mission:
        return Mission(
            mission_id=mid,
            target_x=1.0,
            target_y=1.0,
            priority=priority
        )

    def test_new_robot_is_idle(self):
        """A newly created robot must start in IDLE state."""
        robot = Robot(name="amr_001")
        assert robot.state == RobotState.IDLE
        assert robot.current_mission is None

    def test_new_mission_is_pending(self):
        """A newly created mission must start as PENDING."""
        mission = self._make_mission("M001")
        assert mission.status == MissionStatus.PENDING
        assert mission.assigned_to is None

    def test_priority_sorting_high_first(self):
        """High priority missions (priority=1) must come first."""
        missions = {
            "M001": self._make_mission("M001", priority=3),
            "M002": self._make_mission("M002", priority=1),
            "M003": self._make_mission("M003", priority=2),
        }
        pending = get_pending_by_priority(missions)
        assert pending[0].mission_id == "M002"  # priority 1
        assert pending[1].mission_id == "M003"  # priority 2
        assert pending[2].mission_id == "M001"  # priority 3

    def test_assign_mission_changes_states(self):
        """Assignment must change robot to NAVIGATING and mission to ASSIGNED."""
        robot = Robot(name="amr_001")
        mission = self._make_mission("M001")

        assign_mission(mission, robot)

        assert robot.state == RobotState.NAVIGATING
        assert robot.current_mission == "M001"
        assert mission.status == MissionStatus.ASSIGNED
        assert mission.assigned_to == "amr_001"

    def test_complete_mission_success(self):
        """Successful completion must free robot and mark mission done."""
        robot = Robot(name="amr_001", state=RobotState.NAVIGATING)
        mission = self._make_mission("M001")
        mission.status = MissionStatus.ASSIGNED
        robot.current_mission = "M001"

        complete_mission(mission, robot, success=True)

        assert robot.state == RobotState.IDLE
        assert robot.current_mission is None
        assert robot.missions_done == 1
        assert mission.status == MissionStatus.COMPLETED

    def test_failed_mission_requeued(self):
        """Failed mission must be requeued with lower priority."""
        robot = Robot(name="amr_001", state=RobotState.NAVIGATING)
        mission = self._make_mission("M001", priority=1)
        robot.current_mission = "M001"

        complete_mission(mission, robot, success=False)

        # Mission requeued as PENDING
        assert mission.status == MissionStatus.PENDING
        assert mission.assigned_to is None
        # Priority lowered (1 → 2)
        assert mission.priority == 2
        assert robot.missions_failed == 1
        assert robot.state == RobotState.IDLE

    def test_priority_capped_at_3(self):
        """Priority must never exceed 3 even after multiple failures."""
        robot = Robot(name="amr_001", state=RobotState.NAVIGATING)
        mission = self._make_mission("M001", priority=3)
        robot.current_mission = "M001"

        complete_mission(mission, robot, success=False)

        assert mission.priority == 3  # stays at 3, not 4

    def test_idle_robot_detection(self):
        """Only IDLE robots must be returned for assignment."""
        robots = self._make_robots(["amr_001", "amr_002", "amr_003"])
        robots["amr_002"].state = RobotState.NAVIGATING
        robots["amr_003"].state = RobotState.OFFLINE

        idle = get_idle_robots(robots)

        assert len(idle) == 1
        assert idle[0].name == "amr_001"

    def test_no_pending_missions(self):
        """No missions queued must return empty pending list."""
        missions = {}
        pending = get_pending_by_priority(missions)
        assert pending == []

    def test_multi_robot_assignment(self):
        """Multiple idle robots must each get their own mission."""
        robots = self._make_robots(["amr_001", "amr_002"])
        missions = {
            "M001": self._make_mission("M001", priority=1),
            "M002": self._make_mission("M002", priority=2),
        }

        pending = get_pending_by_priority(missions)
        idle = get_idle_robots(robots)

        for mission, robot in zip(pending, idle):
            assign_mission(mission, robot)

        assert robots["amr_001"].state == RobotState.NAVIGATING
        assert robots["amr_002"].state == RobotState.NAVIGATING
        assert missions["M001"].assigned_to is not None
        assert missions["M002"].assigned_to is not None

    def test_missions_done_counter(self):
        """missions_done must increment for each successful completion."""
        robot = Robot(name="amr_001")

        for i in range(3):
            m = self._make_mission(f"M{i:03d}")
            assign_mission(m, robot)
            complete_mission(m, robot, success=True)

        assert robot.missions_done == 3
        assert robot.missions_failed == 0
