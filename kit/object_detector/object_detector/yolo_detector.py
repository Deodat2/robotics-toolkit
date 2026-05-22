"""
============================================================
FILE        : yolo_detector.py
MODULE      : object_detector (kit/)
DESCRIPTION : YOLOv8 real-time object detection node.

WHAT IT DOES:
    1. Subscribes to /vision/image_preprocessed
    2. Runs YOLOv8 inference on each frame
    3. Filters detections by confidence threshold
    4. Publishes detection results as JSON
    5. Publishes annotated debug image with bounding boxes

    First run: automatically downloads yolov8n.pt (~6MB)
    from Ultralytics. Subsequent runs use cached model.

YOLO MODEL OPTIONS (trade-off: speed vs accuracy):
    yolov8n.pt  — nano,   fastest,  least accurate  (~6MB)
    yolov8s.pt  — small,  fast,     good accuracy   (~22MB)
    yolov8m.pt  — medium, balanced                  (~52MB)
    yolov8l.pt  — large,  slow,     most accurate   (~87MB)

TOPICS:
    Subscribes : /vision/image_preprocessed  sensor_msgs/Image
    Publishes  : /detections                 std_msgs/String (JSON)
    Publishes  : /detections/image           sensor_msgs/Image
    Publishes  : /detections/status          std_msgs/String (JSON)

REUSABILITY:
    Change model_name in detector_params.yaml to use a
    different YOLO model or a custom-trained one.
============================================================
"""

import json
import time
import os
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from vision_bridge.image_converter import ImageConverter


class YoloDetector(Node):
    """
    Real-time object detector using YOLOv8.
    Publishes detection results and annotated frames.
    """

    def __init__(self):
        super().__init__('yolo_detector')

        # --------------------------------------------------
        # PARAMETERS
        # --------------------------------------------------
        self.declare_parameter(
            'input_topic', '/vision/image_preprocessed'
        )
        self.declare_parameter('model_name',       'yolov8n.pt')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('iou_threshold',        0.45)
        self.declare_parameter('max_detections',       20)
        self.declare_parameter('publish_debug',        True)
        self.declare_parameter('process_every_n',      3)
        self.declare_parameter('status_rate',          1.0)

        input_topic    = self.get_parameter('input_topic').value
        model_name     = self.get_parameter('model_name').value
        self.conf_thr  = self.get_parameter('confidence_threshold').value
        self.iou_thr   = self.get_parameter('iou_threshold').value
        self.max_det   = self.get_parameter('max_detections').value
        self.pub_debug = self.get_parameter('publish_debug').value
        self.every_n   = self.get_parameter('process_every_n').value
        status_rate    = self.get_parameter('status_rate').value

        # --------------------------------------------------
        # INTERNAL STATE
        # --------------------------------------------------
        self.frame_count       = 0
        self.total_detections  = 0
        self.last_detections   = []
        self.inference_times   = []   # track FPS
        self.model             = None

        # --------------------------------------------------
        # LOAD YOLO MODEL
        # --------------------------------------------------
        self._load_model(model_name)

        # --------------------------------------------------
        # PUBLISHERS
        # --------------------------------------------------
        self.detections_pub = self.create_publisher(
            String, '/detections', 10
        )
        self.debug_pub = self.create_publisher(
            Image, '/detections/image', 1
        )
        self.status_pub = self.create_publisher(
            String, '/detections/status', 10
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
            f'YoloDetector ready | model: {model_name} | '
            f'conf: {self.conf_thr} | processing every {self.every_n} frames'
        )

    # ----------------------------------------------------------
    # MODEL LOADING
    # ----------------------------------------------------------
    def _load_model(self, model_name: str):
        """
        Loads the YOLO model.
        Downloads automatically on first run (~6MB for nano).
        Checks models/ directory first for custom models.
        """
        try:
            from ultralytics import YOLO

            # Check if custom model exists in models/ directory
            pkg_models_path = os.path.join(
                os.path.dirname(__file__), '..', 'models', model_name
            )
            pkg_models_path = os.path.abspath(pkg_models_path)

            if os.path.exists(pkg_models_path):
                # Load custom model from models/ directory
                self.model = YOLO(pkg_models_path)
                self.get_logger().info(
                    f'Loaded custom model from: {pkg_models_path}'
                )
            else:
                # Download pretrained model (cached in ~/.config/Ultralytics)
                self.model = YOLO(model_name)
                self.get_logger().info(
                    f'Loaded pretrained model: {model_name}'
                )

        except Exception as e:
            self.get_logger().error(f'Failed to load YOLO model: {e}')
            self.model = None

    # ----------------------------------------------------------
    # MAIN CALLBACK: process each camera frame
    # ----------------------------------------------------------
    def _on_frame(self, frame: np.ndarray):
        """
        Called for every camera frame.
        Runs YOLO inference every N frames to manage CPU load.
        """
        self.frame_count += 1

        # Skip frames to reduce CPU load
        # process_every_n=3 means ~10 FPS if camera is 30 FPS
        if self.frame_count % self.every_n != 0:
            return

        if self.model is None:
            return

        # Run YOLO inference
        t_start = time.time()
        detections = self._run_inference(frame)
        t_inference = (time.time() - t_start) * 1000  # ms

        # Track inference time for FPS calculation
        self.inference_times.append(t_inference)
        if len(self.inference_times) > 30:
            self.inference_times.pop(0)

        self.last_detections = detections
        self.total_detections += len(detections)

        # Publish results
        msg = String()
        msg.data = json.dumps(detections)
        self.detections_pub.publish(msg)

        # Draw and publish debug image
        if self.pub_debug:
            annotated = self._draw_detections(frame.copy(), detections)
            fps = 1000.0 / max(np.mean(self.inference_times), 1)
            cv2.putText(
                annotated,
                f'YOLO | {fps:.1f} FPS | {len(detections)} objects',
                (10, annotated.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 0), 1, cv2.LINE_AA
            )
            ros_img = ImageConverter.cv2_to_ros(annotated, 'bgr8')
            if ros_img is not None:
                self.debug_pub.publish(ros_img)

        if detections:
            names = [d['class_name'] for d in detections]
            self.get_logger().info(
                f'Detected {len(detections)} objects: {names} '
                f'({t_inference:.1f}ms)',
                throttle_duration_sec=1.0
            )

    # ----------------------------------------------------------
    # YOLO INFERENCE
    # ----------------------------------------------------------
    def _run_inference(self, frame: np.ndarray) -> list:
        """
        Runs YOLOv8 inference on a single frame.
        Returns list of detection dicts.
        """
        detections = []

        try:
            # Run inference
            # verbose=False suppresses per-frame console output
            results = self.model(
                frame,
                conf=self.conf_thr,
                iou=self.iou_thr,
                max_det=self.max_det,
                verbose=False
            )

            # Parse results
            # results[0].boxes contains all detections for this frame
            for result in results:
                boxes = result.boxes

                if boxes is None:
                    continue

                for box in boxes:
                    # Bounding box coordinates (pixel space)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # Detection metadata
                    confidence  = float(box.conf[0])
                    class_id    = int(box.cls[0])
                    class_name  = result.names[class_id]

                    # Center and size
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    width    = x2 - x1
                    height   = y2 - y1

                    detection = {
                        "class_id":   class_id,
                        "class_name": class_name,
                        "confidence": round(confidence, 3),
                        "bbox": {
                            "x1": round(x1), "y1": round(y1),
                            "x2": round(x2), "y2": round(y2),
                        },
                        "center_x":   round(center_x),
                        "center_y":   round(center_y),
                        "width_px":   round(width),
                        "height_px":  round(height),
                        "timestamp":  time.time(),
                    }
                    detections.append(detection)

        except Exception as e:
            self.get_logger().warn(f'YOLO inference error: {e}')

        return detections

    # ----------------------------------------------------------
    # VISUALIZATION
    # ----------------------------------------------------------
    def _draw_detections(
        self, frame: np.ndarray, detections: list
    ) -> np.ndarray:
        """
        Draws bounding boxes and labels on the frame.
        Color-coded by class for easy visual distinction.
        """
        # Color palette — cycles through colors for different classes
        colors = [
            (0, 255, 0),    # green
            (255, 0, 0),    # blue
            (0, 0, 255),    # red
            (255, 255, 0),  # cyan
            (0, 255, 255),  # yellow
            (255, 0, 255),  # magenta
        ]

        for det in detections:
            bbox   = det['bbox']
            label  = f"{det['class_name']} {det['confidence']:.0%}"
            color  = colors[det['class_id'] % len(colors)]

            # Draw bounding box
            cv2.rectangle(
                frame,
                (bbox['x1'], bbox['y1']),
                (bbox['x2'], bbox['y2']),
                color, 2
            )

            # Draw label background
            (label_w, label_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                frame,
                (bbox['x1'], bbox['y1'] - label_h - 8),
                (bbox['x1'] + label_w, bbox['y1']),
                color, -1   # filled
            )

            # Draw label text
            cv2.putText(
                frame, label,
                (bbox['x1'], bbox['y1'] - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (0, 0, 0),  # black text on colored background
                1, cv2.LINE_AA
            )

        return frame

    # ----------------------------------------------------------
    # STATUS
    # ----------------------------------------------------------
    def _publish_status(self):
        """Publishes detector health and performance stats."""
        avg_ms = (
            np.mean(self.inference_times)
            if self.inference_times else 0.0
        )
        fps = 1000.0 / max(avg_ms, 1)

        status = {
            "model_loaded":       self.model is not None,
            "frames_processed":   self.frame_count,
            "total_detections":   self.total_detections,
            "current_count":      len(self.last_detections),
            "avg_inference_ms":   round(avg_ms, 1),
            "estimated_fps":      round(fps, 1),
            "current_objects": [
                d['class_name'] for d in self.last_detections
            ],
        }
        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    """Entry point — ros2 run object_detector yolo_detector"""
    rclpy.init(args=args)
    node = YoloDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()