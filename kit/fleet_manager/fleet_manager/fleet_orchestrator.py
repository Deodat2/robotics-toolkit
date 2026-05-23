"""
============================================================
FILE        : fleet_orchestrator.py
MODULE      : fleet_manager (kit/)
DESCRIPTION : Fleet orchestration node.

WHAT IT DOES:
    Maintains a mission queue and assigns missions to robots.
    Monitors robot status and requeues failed missions.
    Publishes fleet-wide status for the dashboard.

MISSION FORMAT (JSON published on /fleet/add_mission):
    {
        "mission_id": "M001",
        "target_x":   3.0,
        "target_y":   2.0,
        "target_yaw": 0.0,
        "priority":   1        (1=high, 2=medium, 3=low)
    }

TOPICS:
    Subscribes : /fleet/add_mission   std_msgs/String  add mission
    Subscribes : /fleet/robot_status  std_msgs/String  robot heartbeat
    Publishes  : /fleet/status        std_msgs/String  fleet JSON status
    Publishes  : /fleet/assign        std_msgs/String  mission assignment

REUSABILITY:
    Configure robot names in fleet_params.yaml.
    The orchestration logic is robot-agnostic.
============================================================
"""

import json
import time
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
import math


class RobotState(Enum):
    """Possible states for a robot in the fleet."""
    IDLE        = "idle"        # available for missions
    NAVIGATING  = "navigating"  # executing a mission
    FAILED      = "failed"      # last mission failed
    OFFLINE     = "offline"     # no heartbeat received


class MissionStatus(Enum):
    """Possible states for a mission."""
    PENDING     = "pending"     # waiting to be assigned
    ASSIGNED    = "assigned"    # assigned to a robot
    COMPLETED   = "completed"   # successfully finished
    FAILED      = "failed"      # robot failed to complete


@dataclass
class Robot:
    """Represents a robot in the fleet."""
    name:           str
    state:          RobotState = RobotState.OFFLINE
    current_mission: Optional[str] = None   # mission_id
    position_x:     float = 0.0
    position_y:     float = 0.0
    last_heartbeat: float = 0.0
    missions_done:  int   = 0
    missions_failed: int  = 0


@dataclass
class Mission:
    """Represents a navigation mission."""
    mission_id:  str
    target_x:   float
    target_y:   float
    target_yaw: float = 0.0
    priority:   int   = 2        # 1=high, 2=medium, 3=low
    status:     MissionStatus = MissionStatus.PENDING
    assigned_to: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class FleetOrchestrator(Node):
    """
    Orchestrates a fleet of AMR robots.
    Assigns missions from queue to available robots.
    """

    def __init__(self):
        super().__init__('fleet_orchestrator')

        # --------------------------------------------------
        # PARAMETERS
        # --------------------------------------------------
        self.declare_parameter(
            'robot_names',
            ['amr_001', 'amr_002']  # default 2-robot fleet
        )
        self.declare_parameter('heartbeat_timeout', 5.0)  # seconds
        self.declare_parameter('status_rate',       1.0)  # Hz
        self.declare_parameter('assign_rate',       2.0)  # Hz

        robot_names    = self.get_parameter('robot_names').value
        self.hb_timeout = self.get_parameter('heartbeat_timeout').value
        status_rate    = self.get_parameter('status_rate').value
        assign_rate    = self.get_parameter('assign_rate').value

        # --------------------------------------------------
        # FLEET STATE
        # --------------------------------------------------
        # Initialize robot registry from config
        self.robots: Dict[str, Robot] = {
            name: Robot(name=name) for name in robot_names
        }

        # Mission queue sorted by priority
        self.missions: Dict[str, Mission] = {}
        self.mission_counter = 0

        # --------------------------------------------------
        # SUBSCRIBERS
        # --------------------------------------------------

        # Add new mission to the queue
        self.add_mission_sub = self.create_subscription(
            String, '/fleet/add_mission',
            self._on_add_mission, 10
        )

        # Receive robot status heartbeats
        self.robot_status_sub = self.create_subscription(
            String, '/fleet/robot_status',
            self._on_robot_status, 10
        )

        # --------------------------------------------------
        # PUBLISHERS
        # --------------------------------------------------

        # Fleet-wide status for dashboard
        self.status_pub = self.create_publisher(
            String, '/fleet/status', 10
        )

        # Mission assignments (robots subscribe to this)
        self.assign_pub = self.create_publisher(
            String, '/fleet/assign', 10
        )

        # --------------------------------------------------
        # TIMERS
        # --------------------------------------------------
        self.status_timer = self.create_timer(
            1.0 / status_rate, self._publish_status
        )
        self.assign_timer = self.create_timer(
            1.0 / assign_rate, self._assign_missions
        )
        self.heartbeat_timer = self.create_timer(
            1.0, self._check_heartbeats
        )

        self.get_logger().info(
            f'FleetOrchestrator ready | '
            f'managing {len(self.robots)} robots: '
            f'{list(self.robots.keys())}'
        )

    # ----------------------------------------------------------
    # CALLBACK: new mission added
    # ----------------------------------------------------------
    def _on_add_mission(self, msg: String):
        """
        Called when a new mission is published on /fleet/add_mission.
        Parses JSON and adds to the priority queue.
        """
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().error('Invalid mission JSON received')
            return

        # Auto-generate mission ID if not provided
        if 'mission_id' not in data:
            self.mission_counter += 1
            data['mission_id'] = f'M{self.mission_counter:04d}'

        mission = Mission(
            mission_id  = data['mission_id'],
            target_x    = float(data.get('target_x',   0.0)),
            target_y    = float(data.get('target_y',   0.0)),
            target_yaw  = float(data.get('target_yaw', 0.0)),
            priority    = int(data.get('priority',      2)),
        )

        self.missions[mission.mission_id] = mission

        self.get_logger().info(
            f'Mission queued: {mission.mission_id} → '
            f'({mission.target_x:.1f}, {mission.target_y:.1f}) '
            f'priority={mission.priority}'
        )

    # ----------------------------------------------------------
    # CALLBACK: robot status heartbeat
    # ----------------------------------------------------------
    def _on_robot_status(self, msg: String):
        """
        Called when a robot publishes its status.
        Updates robot state in the registry.

        Expected JSON format:
        {
          "robot_name": "amr_001",
          "nav_status": "idle",
          "position_x": 1.2,
          "position_y": 0.8
        }
        """
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return

        robot_name = data.get('robot_name')
        if robot_name not in self.robots:
            return

        robot = self.robots[robot_name]
        robot.last_heartbeat = time.time()
        robot.position_x = float(data.get('position_x', 0.0))
        robot.position_y = float(data.get('position_y', 0.0))

        # Update robot state based on nav_status
        nav_status = data.get('nav_status', 'idle')

        if nav_status == 'idle' or nav_status == 'succeeded':
            if robot.state == RobotState.NAVIGATING:
                # Mission completed
                if robot.current_mission:
                    self._complete_mission(
                        robot, robot.current_mission, success=True
                    )
            robot.state = RobotState.IDLE

        elif nav_status == 'navigating':
            robot.state = RobotState.NAVIGATING

        elif nav_status == 'failed':
            if robot.current_mission:
                self._complete_mission(
                    robot, robot.current_mission, success=False
                )
            robot.state = RobotState.IDLE

    # ----------------------------------------------------------
    # TIMER: assign pending missions to idle robots
    # ----------------------------------------------------------
    def _assign_missions(self):
        """
        Main orchestration loop.
        Assigns pending missions to idle robots.
        Prioritizes high-priority missions first.
        """
        # Get pending missions sorted by priority (1=highest first)
        pending = sorted(
            [m for m in self.missions.values()
             if m.status == MissionStatus.PENDING],
            key=lambda m: m.priority
        )

        if not pending:
            return

        # Get idle robots
        idle_robots = [
            r for r in self.robots.values()
            if r.state == RobotState.IDLE
        ]

        if not idle_robots:
            return

        # Assign missions to idle robots (one each)
        for mission, robot in zip(pending, idle_robots):
            self._assign_mission_to_robot(mission, robot)

    def _assign_mission_to_robot(self, mission: Mission, robot: Robot):
        """Assigns a specific mission to a specific robot."""
        mission.status      = MissionStatus.ASSIGNED
        mission.assigned_to = robot.name
        robot.state         = RobotState.NAVIGATING
        robot.current_mission = mission.mission_id

        assignment = {
            "robot_name":  robot.name,
            "mission_id":  mission.mission_id,
            "target_x":    mission.target_x,
            "target_y":    mission.target_y,
            "target_yaw":  mission.target_yaw,
        }

        msg = String()
        msg.data = json.dumps(assignment)
        self.assign_pub.publish(msg)

        self.get_logger().info(
            f'Assigned {mission.mission_id} → {robot.name} | '
            f'target: ({mission.target_x:.1f}, {mission.target_y:.1f})'
        )

    def _complete_mission(
        self, robot: Robot, mission_id: str, success: bool
    ):
        """Marks a mission as completed or failed."""
        if mission_id not in self.missions:
            return

        mission = self.missions[mission_id]
        mission.completed_at = time.time()

        if success:
            mission.status = MissionStatus.COMPLETED
            robot.missions_done += 1
            self.get_logger().info(
                f'Mission {mission_id} COMPLETED by {robot.name}'
            )
        else:
            mission.status = MissionStatus.FAILED
            robot.missions_failed += 1
            self.get_logger().warn(
                f'Mission {mission_id} FAILED by {robot.name} — requeueing'
            )
            # Requeue failed mission with lower priority
            mission.status      = MissionStatus.PENDING
            mission.assigned_to = None
            mission.priority    = min(mission.priority + 1, 3)

        robot.current_mission = None

    # ----------------------------------------------------------
    # TIMER: check for offline robots
    # ----------------------------------------------------------
    def _check_heartbeats(self):
        """Marks robots as offline if no heartbeat received."""
        now = time.time()
        for robot in self.robots.values():
            if (robot.last_heartbeat > 0 and
                    now - robot.last_heartbeat > self.hb_timeout):
                if robot.state != RobotState.OFFLINE:
                    self.get_logger().warn(
                        f'Robot {robot.name} went OFFLINE '
                        f'(no heartbeat for {self.hb_timeout}s)'
                    )
                    robot.state = RobotState.OFFLINE

    # ----------------------------------------------------------
    # TIMER: publish fleet status
    # ----------------------------------------------------------
    def _publish_status(self):
        """Publishes complete fleet status as JSON."""
        pending_count   = sum(
            1 for m in self.missions.values()
            if m.status == MissionStatus.PENDING
        )
        completed_count = sum(
            1 for m in self.missions.values()
            if m.status == MissionStatus.COMPLETED
        )

        status = {
            "timestamp": time.time(),
            "robots": {
                name: {
                    "state":           robot.state.value,
                    "current_mission": robot.current_mission,
                    "position_x":      round(robot.position_x, 2),
                    "position_y":      round(robot.position_y, 2),
                    "missions_done":   robot.missions_done,
                    "missions_failed": robot.missions_failed,
                }
                for name, robot in self.robots.items()
            },
            "queue": {
                "pending":   pending_count,
                "completed": completed_count,
                "total":     len(self.missions),
            }
        }

        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    """Entry point — ros2 run fleet_manager fleet_orchestrator"""
    rclpy.init(args=args)
    node = FleetOrchestrator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()