"""
============================================================
FILE        : __init__.py
MODULE      : collision_manager (kit/)
DESCRIPTION : Inter-robot collision prevention module.

WHAT THIS MODULE DOES:
    Monitors distances between all robots in the fleet.
    Issues velocity reduction commands when robots get
    too close to each other.
    Publishes collision risk alerts on /fleet/collision_alert.

REUSABILITY:
    Works with any fleet of robots that publish /odom.
    Configure safety distances in collision_params.yaml.
============================================================
"""

__version__ = "0.1.0"
__author__ = "Kossi"
__license__ = "Apache-2.0"
