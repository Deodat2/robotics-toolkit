"""
============================================================
FILE        : __init__.py
MODULE      : sensor_interface (kit/)
DESCRIPTION : Sensor abstraction layer for any ROS 2 robot.

WHAT THIS MODULE DOES:
    Acts as a bridge between raw hardware/simulation topics
    and the rest of the system (SLAM, Nav2, AI modules).

    Raw data in → filter/normalize → clean data out

    If you swap your LiDAR model tomorrow, only this module
    changes. Everything else keeps working unchanged.

REUSABILITY:
    Works with any robot that publishes:
        - /scan          (sensor_msgs/LaserScan)
        - /odom          (nav_msgs/Odometry)
        - /joint_states  (sensor_msgs/JointState)
============================================================
"""

__version__ = "0.1.0"
__author__  = "Kossi"
__license__ = "Apache-2.0"