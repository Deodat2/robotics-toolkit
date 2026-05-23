"""
============================================================
FILE        : collision_monitor.py
MODULE      : collision_manager (kit/)
DESCRIPTION : Inter-robot collision prevention node.

WHAT IT DOES:
    Subscribes to /fleet/status to know robot positions.
    Computes pairwise distances between all robots.
    When distance < warning_distance: publishes alert.
    When distance < critical_distance: publishes stop command.

SAFETY ZONES:
    GREEN  (> warning_distance) : normal operation
    YELLOW (< warning_distance) : slow down alert
    RED    (< critical_distance): emergency stop

TOPICS:
    Subscribes : /fleet/status          std_msgs/String  robot positions
    Publishes  : /fleet/collision_alert std_msgs/String  JSON alert
    Publishes  : /fleet/emergency_stop  std_msgs/String  stop command

REUSABILITY:
    Tune warning_distance and critical_distance in
    collision_params.yaml for your robot sizes and speeds.
============================================================
"""

import json
import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class CollisionMonitor(Node):
    """
    Monitors inter-robot distances and prevents collisions.
    """

    # Risk levels
    RISK_NONE     = "none"
    RISK_WARNING  = "warning"
    RISK_CRITICAL = "critical"

    def __init__(self):
        super().__init__('collision_monitor')

        # --------------------------------------------------
        # PARAMETERS
        # --------------------------------------------------
        self.declare_parameter('warning_distance',  1.5)  # meters
        self.declare_parameter('critical_distance', 0.8)  # meters
        self.declare_parameter('check_rate',        5.0)  # Hz
        self.declare_parameter('status_rate',       1.0)  # Hz

        self.warn_dist    = self.get_parameter('warning_distance').value
        self.crit_dist    = self.get_parameter('critical_distance').value
        check_rate        = self.get_parameter('check_rate').value
        status_rate       = self.get_parameter('status_rate').value

        # --------------------------------------------------
        # INTERNAL STATE
        # --------------------------------------------------
        self.robot_positions = {}   # {robot_name: (x, y)}
        self.active_alerts   = {}   # {pair_key: alert_dict}
        self.total_warnings  = 0
        self.total_criticals = 0

        # --------------------------------------------------
        # SUBSCRIBERS
        # --------------------------------------------------
        self.fleet_status_sub = self.create_subscription(
            String, '/fleet/status',
            self._on_fleet_status, 10
        )

        # --------------------------------------------------
        # PUBLISHERS
        # --------------------------------------------------
        self.alert_pub = self.create_publisher(
            String, '/fleet/collision_alert', 10
        )
        self.estop_pub = self.create_publisher(
            String, '/fleet/emergency_stop', 10
        )
        self.status_pub = self.create_publisher(
            String, '/fleet/collision_status', 10
        )

        # --------------------------------------------------
        # TIMERS
        # --------------------------------------------------
        self.check_timer = self.create_timer(
            1.0 / check_rate, self._check_distances
        )
        self.status_timer = self.create_timer(
            1.0 / status_rate, self._publish_status
        )

        self.get_logger().info(
            f'CollisionMonitor ready | '
            f'warning: {self.warn_dist}m | '
            f'critical: {self.crit_dist}m'
        )

    # ----------------------------------------------------------
    # CALLBACK: fleet status received
    # ----------------------------------------------------------
    def _on_fleet_status(self, msg: String):
        """Extracts robot positions from fleet status JSON."""
        try:
            data = json.loads(msg.data)
            robots = data.get('robots', {})

            for name, info in robots.items():
                # Only track robots that are NOT offline
                state = info.get('state', 'offline')
                if state != 'offline':
                    self.robot_positions[name] = (
                        info.get('position_x', 0.0),
                        info.get('position_y', 0.0)
                    )
                elif name in self.robot_positions:
                    # Remove offline robots from tracking
                    del self.robot_positions[name]

        except json.JSONDecodeError:
            pass

    # ----------------------------------------------------------
    # TIMER: check all pairwise distances
    # ----------------------------------------------------------
    def _check_distances(self):
        """
        Computes distance between every pair of robots.
        Only checks robots that have sent at least one status update.
        Issues alerts when robots get too close.
        """

        known_robots = {
            name: pos for name, pos in self.robot_positions.items()
            if name in self.active_robots   # NEW: track active robots
        }

        robot_names = list(known_robots.keys())

        if len(robot_names) < 2:
            return

        self.active_alerts = {}

        # Check every pair (i, j) where i < j (avoid duplicates)
        for i in range(len(robot_names)):
            for j in range(i + 1, len(robot_names)):
                name_a = robot_names[i]
                name_b = robot_names[j]

                pos_a = self.robot_positions[name_a]
                pos_b = self.robot_positions[name_b]

                # Euclidean distance
                distance = math.sqrt(
                    (pos_a[0] - pos_b[0]) ** 2 +
                    (pos_a[1] - pos_b[1]) ** 2
                )

                # Determine risk level
                if distance < self.crit_dist:
                    risk = self.RISK_CRITICAL
                    self.total_criticals += 1
                elif distance < self.warn_dist:
                    risk = self.RISK_WARNING
                    self.total_warnings += 1
                else:
                    risk = self.RISK_NONE

                if risk != self.RISK_NONE:
                    pair_key = f'{name_a}_{name_b}'
                    alert = {
                        "robot_a":    name_a,
                        "robot_b":    name_b,
                        "distance_m": round(distance, 3),
                        "risk_level": risk,
                        "timestamp":  time.time(),
                    }
                    self.active_alerts[pair_key] = alert

                    # Publish alert
                    alert_msg = String()
                    alert_msg.data = json.dumps(alert)
                    self.alert_pub.publish(alert_msg)

                    if risk == self.RISK_CRITICAL:
                        self.get_logger().error(
                            f'CRITICAL: {name_a} ↔ {name_b} = '
                            f'{distance:.2f}m (< {self.crit_dist}m)'
                        )
                        # Publish emergency stop for both robots
                        stop = {
                            "robots":  [name_a, name_b],
                            "reason":  "collision_risk",
                            "distance": round(distance, 3),
                        }
                        stop_msg = String()
                        stop_msg.data = json.dumps(stop)
                        self.estop_pub.publish(stop_msg)

                    else:
                        self.get_logger().warn(
                            f'WARNING: {name_a} ↔ {name_b} = '
                            f'{distance:.2f}m (< {self.warn_dist}m)'
                        )

    # ----------------------------------------------------------
    # TIMER: publish collision monitor status
    # ----------------------------------------------------------
    def _publish_status(self):
        """Publishes collision monitor health and statistics."""
        status = {
            "robots_tracked":   len(self.robot_positions),
            "active_alerts":    len(self.active_alerts),
            "total_warnings":   self.total_warnings,
            "total_criticals":  self.total_criticals,
            "alert_pairs": [
                {
                    "pair":     f"{a['robot_a']}↔{a['robot_b']}",
                    "distance": a['distance_m'],
                    "risk":     a['risk_level'],
                }
                for a in self.active_alerts.values()
            ]
        }

        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    """Entry point — ros2 run collision_manager collision_monitor"""
    rclpy.init(args=args)
    node = CollisionMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()