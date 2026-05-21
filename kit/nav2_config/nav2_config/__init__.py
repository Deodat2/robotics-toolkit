"""
============================================================
FILE        : __init__.py
MODULE      : nav2_config (kit/)
DESCRIPTION : Nav2 navigation stack configuration module.

WHAT THIS MODULE DOES:
    Provides a fully configured Nav2 stack for autonomous
    point-to-point navigation on a known or live map.

    Input  : /map + /odom + /sensors/lidar/filtered + goal pose
    Output : /cmd_vel (robot moves autonomously to goal)

    Components configured:
        - AMCL      : localizes robot on the map
        - Planner   : computes global path (NavFn/A*)
        - Controller: follows path, avoids obstacles (DWA)
        - BT Navigator: orchestrates the full nav pipeline

REUSABILITY:
    Works with any differential-drive robot.
    Tune nav2_params.yaml for your robot's size and speed.
============================================================
"""

__version__ = "0.1.0"
__author__  = "Kossi"
__license__ = "Apache-2.0"