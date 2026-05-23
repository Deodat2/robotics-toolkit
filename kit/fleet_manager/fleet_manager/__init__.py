"""
============================================================
FILE        : __init__.py
MODULE      : fleet_manager (kit/)
DESCRIPTION : Multi-robot fleet orchestration module.

WHAT THIS MODULE DOES:
    Manages a fleet of N autonomous robots:
        - Maintains a queue of pending missions
        - Assigns missions to available robots
        - Tracks each robot's status in real time
        - Requeues failed missions automatically

    Each robot is identified by a unique name (amr_001, etc.)
    and communicates via namespaced ROS 2 topics.

REUSABILITY:
    Works with any number of robots that run nav2_config.
    Add robots by listing them in fleet_params.yaml.
    No code changes needed.
============================================================
"""

__version__ = "0.1.0"
__author__  = "Kossi"
__license__ = "Apache-2.0"