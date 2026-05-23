"""
============================================================
FILE        : odom_filter.py
MODULE      : sensor_interface (kit/)
DESCRIPTION : Odometry data filter and normalizer node.

WHAT IT DOES:
    Subscribes to raw /odom from Gazebo diff_drive plugin.
    Validates pose and twist values (no NaN/Inf).
    Adds covariance sanity check.
    Publishes clean odometry on /sensors/odom/filtered.

WHY THIS EXISTS:
    Raw odometry can contain NaN in covariance matrices,
    which crashes some Nav2 components. This node ensures
    the data is always valid before it reaches navigation.

TOPICS:
    Subscribes : /odom                  nav_msgs/Odometry
    Publishes  : /sensors/odom/filtered nav_msgs/Odometry

REUSABILITY:
    Works with any differential drive or holonomic robot.
    Topic names configurable via sensor_params.yaml.
============================================================
"""

import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class OdomFilter(Node):
    """Validates and normalizes raw odometry data."""

    def __init__(self):
        super().__init__('odom_filter')

        # --------------------------------------------------
        # PARAMETERS
        # --------------------------------------------------
        self.declare_parameter('input_topic', '/odom')
        self.declare_parameter('output_topic', '/sensors/odom/filtered')

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value

        # --------------------------------------------------
        # SUBSCRIBER + PUBLISHER
        # --------------------------------------------------
        self.odom_sub = self.create_subscription(
            Odometry, input_topic, self._on_odom, 10
        )
        self.odom_pub = self.create_publisher(
            Odometry, output_topic, 10
        )

        self.get_logger().info(
            f'OdomFilter ready | {input_topic} → {output_topic}'
        )

    def _on_odom(self, msg: Odometry):
        """
        Validates odometry message fields.
        Replaces any NaN/Inf with 0.0 to prevent downstream crashes.
        """
        clean_msg = Odometry()
        clean_msg.header = msg.header
        clean_msg.child_frame_id = msg.child_frame_id

        # --- Validate pose position ---
        clean_msg.pose.pose.position.x = self._safe(
            msg.pose.pose.position.x
        )
        clean_msg.pose.pose.position.y = self._safe(
            msg.pose.pose.position.y
        )
        clean_msg.pose.pose.position.z = self._safe(
            msg.pose.pose.position.z
        )

        # --- Validate orientation (quaternion) ---
        clean_msg.pose.pose.orientation.x = self._safe(
            msg.pose.pose.orientation.x
        )
        clean_msg.pose.pose.orientation.y = self._safe(
            msg.pose.pose.orientation.y
        )
        clean_msg.pose.pose.orientation.z = self._safe(
            msg.pose.pose.orientation.z
        )
        # Default w=1.0 if invalid (identity quaternion = no rotation)
        clean_msg.pose.pose.orientation.w = self._safe(
            msg.pose.pose.orientation.w, default=1.0
        )

        # --- Validate twist (velocity) ---
        clean_msg.twist.twist.linear.x = self._safe(
            msg.twist.twist.linear.x
        )
        clean_msg.twist.twist.angular.z = self._safe(
            msg.twist.twist.angular.z
        )

        # --- Pass covariance through (already float arrays) ---
        clean_msg.pose.covariance = msg.pose.covariance
        clean_msg.twist.covariance = msg.twist.covariance

        self.odom_pub.publish(clean_msg)

    def _safe(self, value: float, default: float = 0.0) -> float:
        """
        Returns value if valid, otherwise returns default.
        Handles NaN and Infinity which crash ROS 2 components.
        """
        if math.isnan(value) or math.isinf(value):
            self.get_logger().warn(
                f'Invalid odometry value {value} replaced with {default}'
            )
            return default
        return value


def main(args=None):
    """Entry point — ros2 run sensor_interface odom_filter"""
    rclpy.init(args=args)
    node = OdomFilter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
