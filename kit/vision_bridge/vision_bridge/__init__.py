"""
============================================================
FILE        : __init__.py
MODULE      : vision_bridge (kit/)
DESCRIPTION : Bridge between ROS 2 image topics and OpenCV.

WHAT THIS MODULE DOES:
    Converts ROS 2 sensor_msgs/Image messages to OpenCV
    numpy arrays and vice versa. Acts as the foundation
    for all vision modules (qr_navigator, object_detector).

    ROS 2 Image → cv_bridge → numpy array → OpenCV processing
    OpenCV result → cv_bridge → ROS 2 Image → publish

REUSABILITY:
    Any module that needs to process camera images imports
    ImageConverter from this module. No cv_bridge knowledge
    needed in the consuming module.
============================================================
"""

__version__ = "0.1.0"
__author__  = "Kossi"
__license__ = "Apache-2.0"