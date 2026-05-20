"""
============================================================
FILE        : __init__.py
MODULE      : slam_module (kit/)
DESCRIPTION : SLAM (Simultaneous Localization And Mapping)
              module for any ROS 2 mobile robot.

WHAT THIS MODULE DOES:
    Builds a 2D map of the environment in real time while
    simultaneously tracking the robot's position on that map.
    Uses slam_toolbox under the hood (industry standard).

    Input  : /sensors/lidar/filtered + /odom (or /tf)
    Output : /map (OccupancyGrid) + robot pose on the map

REUSABILITY:
    Works with any robot that has a 2D LiDAR.
    Tune slam_params.yaml for your specific environment
    (warehouse, office, outdoor...) without touching code.
============================================================
"""

__version__ = "0.1.0"
__author__  = "Kossi"
__license__ = "Apache-2.0"