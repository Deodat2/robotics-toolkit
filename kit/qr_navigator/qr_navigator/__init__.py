"""
============================================================
FILE        : __init__.py
MODULE      : qr_navigator (kit/)
DESCRIPTION : QR code detection and warehouse localization.

WHAT THIS MODULE DOES:
    Detects QR codes in camera frames using OpenCV + pyzbar.
    Decodes their content to extract location metadata.
    Publishes detected QR positions for navigation use.

    Use case: QR codes placed on warehouse floor/walls
    act as landmarks. Robot reads them to know exactly
    where it is, even if odometry has drifted.

REUSABILITY:
    Works with any robot that has a camera and uses
    vision_bridge. QR code format is configurable.
============================================================
"""

__version__ = "0.1.0"
__author__  = "Kossi"
__license__ = "Apache-2.0"