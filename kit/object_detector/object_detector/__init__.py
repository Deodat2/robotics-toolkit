"""
============================================================
FILE        : __init__.py
MODULE      : object_detector (kit/)
DESCRIPTION : Real-time object detection using YOLOv8.

WHAT THIS MODULE DOES:
  Detects and classifies objects in camera frames in
  real time using YOLOv8 (You Only Look Once v8).

  Detectable objects (COCO dataset, 80 classes):
    person, bicycle, car, truck, forklift, box,
    bottle, chair, laptop, phone, and 70+ more.

  Use case: warehouse robot detects humans and dynamic
  obstacles to avoid them, identifies packages to pick up,
  recognizes hazards in its path.

REUSABILITY:
  Works with any robot that has a camera and vision_bridge.
  Swap the YOLO model file for a custom-trained one to
  detect domain-specific objects (your own packages, robots).
============================================================
"""

__version__ = "0.1.0"
__author__ = "Kossi"
__license__ = "Apache-2.0"
