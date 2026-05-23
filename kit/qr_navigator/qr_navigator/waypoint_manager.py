"""
============================================================
FILE        : waypoint_manager.py
MODULE      : qr_navigator (kit/)
DESCRIPTION : Maps QR code content to navigation waypoints.

WHAT IT DOES:
    Subscribes to /qr/detections.
    When a QR is detected, looks up its associated waypoint
    in the waypoints map (defined in qr_params.yaml).
    Publishes the waypoint as a navigation goal.

    Example workflow:
        Robot sees QR "ZONE_A" → looks up waypoint for ZONE_A
        → publishes goal (x=2.0, y=1.5) → robot navigates there

TOPICS:
    Subscribes : /qr/detections    std_msgs/String (JSON)
    Publishes  : /qr/waypoint_goal geometry_msgs/PoseStamped

REUSABILITY:
    Define your own QR→waypoint mapping in qr_params.yaml.
    No code changes needed for new warehouses or environments.
============================================================
"""

import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
import math


class WaypointManager(Node):
    """
    Maps detected QR codes to navigation waypoints.
    Acts as a semantic localization layer on top of QR detection.
    """

    def __init__(self):
        super().__init__('waypoint_manager')

        # --------------------------------------------------
        # PARAMETERS
        # Waypoints defined as flat list:
        # [qr_id, x, y, yaw, qr_id2, x2, y2, yaw2, ...]
        # ROS 2 parameters don't support nested dicts natively
        # --------------------------------------------------
        self.declare_parameter('cooldown_seconds', 3.0)

        self.cooldown = self.get_parameter('cooldown_seconds').value

        # --------------------------------------------------
        # WAYPOINT MAP
        # In a real project, load from YAML via rosparam
        # For now, hardcoded defaults — override in launch file
        # Format: {"QR_CONTENT": (x, y, yaw)}
        # --------------------------------------------------
        self.waypoint_map = {
            "ZONE_A": (2.0, 1.0, 0.0),
            "ZONE_B": (2.0, -1.0, 0.0),
            "ZONE_C": (-2.0, 1.0, 3.14),
            "HOME": (0.0, 0.0, 0.0),
            "PICKUP_01": (3.0, 0.0, 0.0),
            "PICKUP_02": (3.0, 1.5, 0.0),
            "DROPOFF_01": (-3.0, 0.0, 3.14),
        }

        # --------------------------------------------------
        # INTERNAL STATE
        # --------------------------------------------------
        self.last_qr_seen = None
        self.last_trigger_time = 0.0

        # --------------------------------------------------
        # SUBSCRIBER + PUBLISHER
        # --------------------------------------------------
        self.detections_sub = self.create_subscription(
            String,
            '/qr/detections',
            self._on_detections,
            10
        )

        self.goal_pub = self.create_publisher(
            PoseStamped,
            '/qr/waypoint_goal',
            10
        )

        self.get_logger().info(
            f'WaypointManager ready | '
            f'{len(self.waypoint_map)} waypoints loaded | '
            f'cooldown: {self.cooldown}s'
        )
        self.get_logger().info(
            f'Known QR codes: {list(self.waypoint_map.keys())}'
        )

    def _on_detections(self, msg: String):
        """
        Called when QR detections arrive.
        Looks up waypoints and publishes navigation goals.
        """
        try:
            detections = json.loads(msg.data)
        except json.JSONDecodeError:
            return

        if not detections:
            return

        import time
        now = time.time()

        for detection in detections:
            raw_content = detection.get('raw', '').strip().upper()

            # Skip if same QR seen recently (cooldown prevents spamming goals)
            if (raw_content == self.last_qr_seen and
                    now - self.last_trigger_time < self.cooldown):
                continue

            # Look up waypoint for this QR code
            if raw_content in self.waypoint_map:
                x, y, yaw = self.waypoint_map[raw_content]

                self.get_logger().info(
                    f'QR "{raw_content}" → waypoint '
                    f'({x:.1f}, {y:.1f}, yaw={yaw:.2f})'
                )

                # Build and publish the goal
                goal = self._build_goal(x, y, yaw)
                self.goal_pub.publish(goal)

                self.last_qr_seen = raw_content
                self.last_trigger_time = now

            else:
                self.get_logger().warn(
                    f'QR "{raw_content}" has no waypoint mapping. '
                    f'Add it to waypoint_map in qr_params.yaml'
                )

    def _build_goal(self, x: float, y: float, yaw: float) -> PoseStamped:
        """Builds a PoseStamped goal message from x, y, yaw."""
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.header.stamp = self.get_clock().now().to_msg()

        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = 0.0

        # Convert yaw to quaternion
        goal.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.orientation.w = math.cos(yaw / 2.0)

        return goal


def main(args=None):
    """Entry point — ros2 run qr_navigator waypoint_manager"""
    rclpy.init(args=args)
    node = WaypointManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
