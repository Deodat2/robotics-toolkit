"""
============================================================
FILE        : lidar_filter.py
MODULE      : sensor_interface (kit/)
DESCRIPTION : LiDAR data filter and normalizer node.

WHAT IT DOES:
    Subscribes to raw /scan data from Gazebo or real hardware.
    Filters out invalid readings (NaN, Inf, out-of-range).
    Publishes clean data on /sensors/lidar/filtered.
    Publishes sensor health on /sensors/diagnostics.

WHY THIS EXISTS:
    Real LiDAR sensors produce noisy/invalid readings:
        - 0.0      : sensor too close (below min range)
        - inf/nan  : no return (beam hit nothing, or error)
        - spikes   : single readings far from neighbors
    Feeding raw data to SLAM or Nav2 causes bad maps
    and navigation failures. This node cleans it first.

TOPICS:
    Subscribes : /scan                    sensor_msgs/LaserScan
    Publishes  : /sensors/lidar/filtered  sensor_msgs/LaserScan
    Publishes  : /sensors/diagnostics     diagnostic_msgs/DiagnosticArray

REUSABILITY:
    Change input/output topic names in sensor_params.yaml.
    The filtering logic works for any 2D LiDAR.
============================================================
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue


class LidarFilter(Node):
    """
    Filters and normalizes raw LiDAR scan data.

    Pipeline:
        raw /scan → remove NaN/Inf → clamp range → publish clean scan
    """

    def __init__(self):
        super().__init__('lidar_filter')

        # --------------------------------------------------
        # PARAMETERS
        # --------------------------------------------------
        self.declare_parameter('input_topic', '/scan')
        self.declare_parameter('output_topic', '/sensors/lidar/filtered')
        self.declare_parameter('min_range', 0.12)   # meters
        self.declare_parameter('max_range', 10.0)   # meters

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.min_range = self.get_parameter('min_range').value
        self.max_range = self.get_parameter('max_range').value

        # --------------------------------------------------
        # INTERNAL STATS (for diagnostics)
        # --------------------------------------------------
        self.total_scans = 0   # total scans received
        self.total_filtered = 0   # total invalid rays removed
        self.last_scan_ok = False

        # --------------------------------------------------
        # SUBSCRIBER: raw LiDAR data
        # --------------------------------------------------
        self.scan_sub = self.create_subscription(
            LaserScan,
            input_topic,
            self._on_scan,
            10
        )

        # --------------------------------------------------
        # PUBLISHERS
        # --------------------------------------------------

        # Clean LiDAR data — consumed by SLAM, Nav2, object_detector
        self.filtered_pub = self.create_publisher(
            LaserScan,
            output_topic,
            10
        )

        # Diagnostics — consumed by dashboard, fleet_manager
        self.diag_pub = self.create_publisher(
            DiagnosticArray,
            '/sensors/diagnostics',
            10
        )

        # --------------------------------------------------
        # TIMER: publish diagnostics every second
        # --------------------------------------------------
        self.diag_timer = self.create_timer(1.0, self._publish_diagnostics)

        self.get_logger().info(
            f'LidarFilter ready | '
            f'{input_topic} → {output_topic} | '
            f'range: [{self.min_range}, {self.max_range}] m'
        )

    # ----------------------------------------------------------
    # CALLBACK: raw scan received
    # ----------------------------------------------------------
    def _on_scan(self, msg: LaserScan):
        """
        Called for every incoming LiDAR scan.
        Filters invalid rays and republishes clean data.
        """
        self.total_scans += 1
        self.last_scan_ok = True

        filtered_ranges = []
        invalid_count = 0

        for r in msg.ranges:
            if (math.isnan(r) or          # Not a Number → sensor error
                math.isinf(r) or          # Infinity → no return (beam missed)
                r < self.min_range or     # Too close → below sensor minimum
                    r > self.max_range):      # Too far → outside reliable range
                # Replace invalid reading with max_range
                # (safer than 0.0 — tells Nav2 "nothing detected here")
                filtered_ranges.append(self.max_range)
                invalid_count += 1
            else:
                filtered_ranges.append(r)

        self.total_filtered += invalid_count

        # Build output message — copy all header/metadata from input
        # Only the ranges array is modified
        filtered_msg = LaserScan()
        filtered_msg.header = msg.header      # same timestamp + frame_id
        filtered_msg.angle_min = msg.angle_min
        filtered_msg.angle_max = msg.angle_max
        filtered_msg.angle_increment = msg.angle_increment
        filtered_msg.time_increment = msg.time_increment
        filtered_msg.scan_time = msg.scan_time
        filtered_msg.range_min = self.min_range
        filtered_msg.range_max = self.max_range
        filtered_msg.ranges = filtered_ranges
        filtered_msg.intensities = msg.intensities  # pass through unchanged

        self.filtered_pub.publish(filtered_msg)

    # ----------------------------------------------------------
    # TIMER CALLBACK: publish sensor health diagnostics
    # ----------------------------------------------------------
    def _publish_diagnostics(self):
        """
        Publishes sensor health status.
        Other modules (dashboard, fleet_manager) use this
        to know if the LiDAR is working correctly.
        """
        # Determine health level
        if not self.last_scan_ok:
            level = DiagnosticStatus.ERROR
            message = 'No scan received — LiDAR may be offline'
        elif self.total_scans > 0:
            # Calculate percentage of invalid rays
            invalid_ratio = (
                self.total_filtered / max(self.total_scans * 360, 1)
            )
            if invalid_ratio > 0.3:   # >30% invalid → warning
                level = DiagnosticStatus.WARN
                message = f'High invalid ray ratio: {invalid_ratio:.1%}'
            else:
                level = DiagnosticStatus.OK
                message = 'LiDAR operating normally'
        else:
            level = DiagnosticStatus.WARN
            message = 'Waiting for first scan...'

        # Build diagnostic message
        status = DiagnosticStatus()
        status.level = level
        status.name = 'lidar_filter'
        status.message = message
        status.values = [
            KeyValue(key='total_scans', value=str(self.total_scans)),
            KeyValue(key='total_filtered', value=str(self.total_filtered)),
        ]

        diag_array = DiagnosticArray()
        diag_array.header.stamp = self.get_clock().now().to_msg()
        diag_array.status = [status]

        self.diag_pub.publish(diag_array)

        # Reset last_scan_ok each cycle to detect dropouts
        self.last_scan_ok = False


def main(args=None):
    """Entry point — ros2 run sensor_interface lidar_filter"""
    rclpy.init(args=args)
    node = LidarFilter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
