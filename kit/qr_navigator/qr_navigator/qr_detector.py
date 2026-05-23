"""
============================================================
FILE        : qr_detector.py
MODULE      : qr_navigator (kit/)
DESCRIPTION : QR code detection and decoding node.

WHAT IT DOES:
    1. Subscribes to /vision/image_preprocessed (from vision_bridge)
    2. Detects QR codes in each frame using pyzbar
    3. Decodes QR content (expected format: JSON or plain text)
    4. Estimates distance to QR code using apparent size
    5. Publishes detections on /qr/detections
    6. Publishes annotated debug image on /qr/debug_image

QR CODE FORMAT (expected content):
    Simple text : "ZONE_A_PICKUP"
    JSON format : {"id": "WP_01", "zone": "A", "action": "pickup"}

TOPICS:
    Subscribes : /vision/image_preprocessed  sensor_msgs/Image
    Publishes  : /qr/detections              std_msgs/String (JSON)
    Publishes  : /qr/debug_image             sensor_msgs/Image

REUSABILITY:
    Change qr_params.yaml to adapt to different QR sizes
    or content formats. No code changes needed.
============================================================
"""

import json
import time
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from pyzbar import pyzbar
from vision_bridge.image_converter import ImageConverter


class QRDetector(Node):
    """
    Detects and decodes QR codes from camera frames.
    Uses pyzbar for detection and OpenCV for visualization.
    """

    def __init__(self):
        super().__init__('qr_detector')

        # --------------------------------------------------
        # PARAMETERS
        # --------------------------------------------------
        self.declare_parameter(
            'input_topic', '/vision/image_preprocessed'
        )
        self.declare_parameter('qr_real_size_m', 0.15)  # QR physical size
        self.declare_parameter('focal_length_px', 554.0)  # camera focal length
        self.declare_parameter('min_confidence', 0.5)  # detection threshold
        self.declare_parameter('publish_debug', True)
        self.declare_parameter('status_rate', 1.0)

        input_topic = self.get_parameter('input_topic').value
        self.qr_real_size = self.get_parameter('qr_real_size_m').value
        self.focal_length = self.get_parameter('focal_length_px').value
        self.pub_debug = self.get_parameter('publish_debug').value
        status_rate = self.get_parameter('status_rate').value

        # --------------------------------------------------
        # INTERNAL STATE
        # --------------------------------------------------
        self.frames_processed = 0
        self.total_detections = 0
        self.last_detections = []   # list of last detected QR codes
        self.last_detection_time = 0.0

        # --------------------------------------------------
        # PUBLISHERS
        # --------------------------------------------------

        # JSON list of all QR codes detected in current frame
        self.detections_pub = self.create_publisher(
            String, '/qr/detections', 10
        )

        # Annotated image showing QR bounding boxes
        self.debug_pub = self.create_publisher(
            Image, '/qr/debug_image', 1
        )

        # Status for monitoring
        self.status_pub = self.create_publisher(
            String, '/qr/status', 10
        )

        # --------------------------------------------------
        # IMAGE CONVERTER (from vision_bridge)
        # --------------------------------------------------
        self.converter = ImageConverter(
            node=self,
            image_topic=input_topic,
            callback=self._on_frame,
            encoding='bgr8',
            queue_size=1
        )

        # --------------------------------------------------
        # TIMER: status
        # --------------------------------------------------
        self.timer = self.create_timer(
            1.0 / status_rate, self._publish_status
        )

        self.get_logger().info(
            f'QRDetector ready | listening on: {input_topic} | '
            f'QR real size: {self.qr_real_size}m'
        )

    # ----------------------------------------------------------
    # MAIN CALLBACK: process each camera frame
    # ----------------------------------------------------------
    def _on_frame(self, frame: np.ndarray):
        """
        Called for every camera frame.
        Detects QR codes and publishes results.
        """
        self.frames_processed += 1
        detections = []

        # Convert to grayscale for faster QR detection
        # pyzbar works on grayscale images
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect and decode all QR codes in the frame
        # pyzbar returns a list of Decoded objects
        qr_codes = pyzbar.decode(gray)

        for qr in qr_codes:
            # qr.data  : raw bytes of QR content
            # qr.rect  : bounding rectangle (left, top, width, height)
            # qr.polygon : corner points of the QR code

            # Decode bytes to string
            raw_content = qr.data.decode('utf-8', errors='ignore')

            # Try to parse as JSON, fallback to plain text
            try:
                content = json.loads(raw_content)
            except json.JSONDecodeError:
                # Plain text QR code
                content = {"text": raw_content}

            # Estimate distance using apparent size
            # Formula: distance = (real_size × focal_length) / pixel_size
            pixel_size = max(qr.rect.width, qr.rect.height)
            if pixel_size > 0:
                distance_m = (
                    self.qr_real_size * self.focal_length / pixel_size
                )
            else:
                distance_m = -1.0   # unknown

            # Calculate center of QR code in image
            center_x = qr.rect.left + qr.rect.width // 2
            center_y = qr.rect.top + qr.rect.height // 2

            detection = {
                "content": content,
                "raw": raw_content,
                "center_x": center_x,
                "center_y": center_y,
                "width_px": qr.rect.width,
                "height_px": qr.rect.height,
                "distance_m": round(distance_m, 3),
                "timestamp": time.time(),
            }
            detections.append(detection)
            self.total_detections += 1

            self.get_logger().info(
                f'QR detected: "{raw_content}" | '
                f'distance: {distance_m:.2f}m | '
                f'center: ({center_x}, {center_y})'
            )

            # Draw bounding box on debug frame
            if self.pub_debug:
                self._draw_qr_overlay(frame, qr, raw_content, distance_m)

        # Store last detections for status
        self.last_detections = detections
        if detections:
            self.last_detection_time = time.time()

        # Publish detections as JSON
        msg = String()
        msg.data = json.dumps(detections)
        self.detections_pub.publish(msg)

        # Publish debug image
        if self.pub_debug:
            # Add frame counter overlay
            cv2.putText(
                frame,
                f'QR Scanner | frame: {self.frames_processed}',
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 1, cv2.LINE_AA
            )
            ros_debug = ImageConverter.cv2_to_ros(frame, 'bgr8')
            if ros_debug is not None:
                self.debug_pub.publish(ros_debug)

    # ----------------------------------------------------------
    # HELPER: draw QR overlay on frame
    # ----------------------------------------------------------
    def _draw_qr_overlay(
        self,
        frame: np.ndarray,
        qr,
        content: str,
        distance_m: float
    ):
        """
        Draws bounding box, content, and distance on the frame.
        Green box = QR detected and decoded successfully.
        """
        # Draw bounding rectangle
        x, y, w, h = qr.rect
        cv2.rectangle(
            frame,
            (x, y), (x + w, y + h),
            (0, 255, 0),   # green
            2
        )

        # Draw content text above the box
        label = f'{content[:20]} | {distance_m:.2f}m'
        cv2.putText(
            frame, label,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            (0, 255, 0), 2, cv2.LINE_AA
        )

        # Draw corner points
        for point in qr.polygon:
            cv2.circle(frame, (point.x, point.y), 5, (0, 0, 255), -1)

    # ----------------------------------------------------------
    # TIMER: publish status
    # ----------------------------------------------------------
    def _publish_status(self):
        """Publishes QR detector health and statistics."""
        time_since_last = (
            time.time() - self.last_detection_time
            if self.last_detection_time > 0 else -1
        )
        status = {
            "frames_processed": self.frames_processed,
            "total_detections": self.total_detections,
            "current_detections": len(self.last_detections),
            "last_detection_ago_s": round(time_since_last, 1),
            "last_qr_content": (
                self.last_detections[0]["raw"]
                if self.last_detections else None
            ),
        }
        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    """Entry point — ros2 run qr_navigator qr_detector"""
    rclpy.init(args=args)
    node = QRDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
