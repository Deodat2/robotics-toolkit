"""
============================================================
FILE        : image_converter.py
MODULE      : vision_bridge (kit/)
DESCRIPTION : ROS 2 Image ↔ OpenCV converter utility class.

WHAT IT DOES:
    Wraps cv_bridge to convert between:
        - sensor_msgs/Image (ROS 2 format)
        - numpy ndarray    (OpenCV format)

    Also provides camera stream subscriber that delivers
    frames directly as numpy arrays to a callback function.

REUSABILITY:
    Import ImageConverter in any vision module:
        from vision_bridge.image_converter import ImageConverter
    Then just implement a callback that receives numpy frames.

USAGE EXAMPLE:
    def my_callback(frame: np.ndarray):
        # frame is a BGR numpy array ready for OpenCV
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    converter = ImageConverter(node, '/camera/image_raw', my_callback)
============================================================
"""

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge, CvBridgeError
from typing import Callable, Optional


class ImageConverter:
    """
    Utility class that subscribes to a ROS 2 image topic
    and delivers frames as OpenCV numpy arrays to a callback.

    Handles all cv_bridge complexity internally.
    """

    def __init__(
        self,
        node: Node,
        image_topic: str,
        callback: Callable[[np.ndarray], None],
        encoding: str = 'bgr8',
        queue_size: int = 1,
    ):
        """
        Args:
            node        : the ROS 2 node that owns this converter
            image_topic : ROS 2 topic with sensor_msgs/Image
            callback    : function called with each frame as numpy array
            encoding    : OpenCV color encoding ('bgr8' or 'rgb8')
            queue_size  : subscriber queue depth (1 = always latest frame)
        """
        self._node     = node
        self._callback = callback
        self._encoding = encoding
        self._bridge   = CvBridge()

        # Track stats for diagnostics
        self.frames_received  = 0
        self.frames_failed    = 0
        self.last_frame_shape = None

        # Subscribe to the image topic
        self._sub = node.create_subscription(
            Image,
            image_topic,
            self._on_image,
            queue_size
        )

        node.get_logger().info(
            f'ImageConverter subscribed to: {image_topic} '
            f'(encoding: {encoding})'
        )

    def _on_image(self, msg: Image):
        """
        Called for every incoming ROS 2 image message.
        Converts to numpy array and calls the user callback.
        """
        try:
            # Convert ROS 2 Image message → OpenCV numpy array
            # 'bgr8' = Blue Green Red, 8 bits per channel
            # This is OpenCV's native format
            frame = self._bridge.imgmsg_to_cv2(msg, self._encoding)

            self.frames_received += 1
            self.last_frame_shape = frame.shape  # (height, width, channels)

            # Deliver frame to the consuming module
            self._callback(frame)

        except CvBridgeError as e:
            self.frames_failed += 1
            self._node.get_logger().warn(
                f'ImageConverter: cv_bridge error: {e}'
            )

    @staticmethod
    def ros_to_cv2(msg: Image, encoding: str = 'bgr8') -> Optional[np.ndarray]:
        """
        Static utility: convert a single ROS 2 Image to numpy array.
        Use when you don't need a persistent subscription.

        Returns None if conversion fails.
        """
        bridge = CvBridge()
        try:
            return bridge.imgmsg_to_cv2(msg, encoding)
        except CvBridgeError:
            return None

    @staticmethod
    def cv2_to_ros(
        frame: np.ndarray,
        encoding: str = 'bgr8'
    ) -> Optional[Image]:
        """
        Static utility: convert an OpenCV numpy array to ROS 2 Image.
        Use to publish processed images back to ROS 2 topics.

        Returns None if conversion fails.
        """
        bridge = CvBridge()
        try:
            return bridge.cv2_to_imgmsg(frame, encoding)
        except CvBridgeError:
            return None

    def draw_debug_overlay(
        self,
        frame: np.ndarray,
        text: str,
        color: tuple = (0, 255, 0)
    ) -> np.ndarray:
        """
        Draws a debug text overlay on a frame.
        Used by qr_navigator and object_detector for visualization.

        Args:
            frame : OpenCV BGR numpy array
            text  : text to draw
            color : BGR color tuple (default: green)

        Returns:
            frame with overlay drawn (modifies in place)
        """
        cv2.putText(
            frame,
            text,
            (10, 30),                    # position: top-left
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,                         # font scale
            color,
            2,                           # thickness
            cv2.LINE_AA                  # anti-aliased
        )
        return frame