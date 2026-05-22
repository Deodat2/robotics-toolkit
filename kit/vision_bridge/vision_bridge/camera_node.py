"""
============================================================
FILE        : camera_node.py
MODULE      : vision_bridge (kit/)
DESCRIPTION : Camera republisher node with preprocessing.

WHAT IT DOES:
    Subscribes to raw /camera/image_raw from Gazebo.
    Applies basic preprocessing (resize, normalize).
    Republishes on /vision/image_preprocessed for
    qr_navigator and object_detector to consume.

    Also publishes a debug view on /vision/image_debug
    showing what the camera sees with overlays.

TOPICS:
    Subscribes : /camera/image_raw         sensor_msgs/Image
    Publishes  : /vision/image_preprocessed sensor_msgs/Image
    Publishes  : /vision/camera_info        std_msgs/String (JSON)

REUSABILITY:
    Change input_topic in vision_params.yaml to use any
    camera topic. Works with real cameras and simulators.
============================================================
"""

import json
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from vision_bridge.image_converter import ImageConverter


class CameraNode(Node):
    """
    Preprocesses camera frames and republishes for vision modules.
    """

    def __init__(self):
        super().__init__('camera_node')

        # --------------------------------------------------
        # PARAMETERS
        # --------------------------------------------------
        self.declare_parameter('input_topic',   '/camera/image_raw')
        self.declare_parameter('output_width',   640)
        self.declare_parameter('output_height',  480)
        self.declare_parameter('publish_debug',  True)
        self.declare_parameter('status_rate',    1.0)

        input_topic    = self.get_parameter('input_topic').value
        self.out_w     = self.get_parameter('output_width').value
        self.out_h     = self.get_parameter('output_height').value
        self.pub_debug = self.get_parameter('publish_debug').value
        status_rate    = self.get_parameter('status_rate').value

        # --------------------------------------------------
        # PUBLISHERS
        # --------------------------------------------------

        # Preprocessed image for vision modules
        self.preprocessed_pub = self.create_publisher(
            Image, '/vision/image_preprocessed', 1
        )

        # Camera status JSON
        self.status_pub = self.create_publisher(
            String, '/vision/camera_status', 10
        )

        # --------------------------------------------------
        # IMAGE CONVERTER (vision_bridge utility)
        # --------------------------------------------------
        self.converter = ImageConverter(
            node=self,
            image_topic=input_topic,
            callback=self._on_frame,
            encoding='bgr8',
            queue_size=1      # always process latest frame only
        )

        # --------------------------------------------------
        # TIMER: status publisher
        # --------------------------------------------------
        self.timer = self.create_timer(
            1.0 / status_rate, self._publish_status
        )

        self.get_logger().info(
            f'CameraNode ready | {input_topic} → '
            f'/vision/image_preprocessed ({self.out_w}x{self.out_h})'
        )

    def _on_frame(self, frame: np.ndarray):
        """
        Called for every camera frame.
        Preprocesses and republishes.
        """
        # Resize to target resolution if needed
        h, w = frame.shape[:2]
        if w != self.out_w or h != self.out_h:
            frame = cv2.resize(
                frame,
                (self.out_w, self.out_h),
                interpolation=cv2.INTER_LINEAR
            )

        # Convert back to ROS 2 Image and publish
        ros_msg = ImageConverter.cv2_to_ros(frame, 'bgr8')
        if ros_msg is not None:
            self.preprocessed_pub.publish(ros_msg)

    def _publish_status(self):
        """Publishes camera health status as JSON."""
        status = {
            "frames_received": self.converter.frames_received,
            "frames_failed":   self.converter.frames_failed,
            "last_shape":      str(self.converter.last_frame_shape),
            "output_size":     f"{self.out_w}x{self.out_h}",
        }
        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    """Entry point — ros2 run vision_bridge camera_node"""
    rclpy.init(args=args)
    node = CameraNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()