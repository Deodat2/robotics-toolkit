# Module : `qr_navigator`

**kit/** — Reusable QR-based localization for any ROS 2 robot.

## What this module does

Detects QR codes in camera frames and maps them to navigation
waypoints. Acts as a **semantic localization layer** on top of SLAM —
when odometry drifts, QR codes provide absolute position correction.

Camera frame
↓
[qr_detector]   → pyzbar decodes QR content
↓               → estimates distance (apparent size)
/qr/detections  → JSON list of detected QR codes
↓
[waypoint_manager] → maps QR content → waypoint coordinates
↓
/qr/waypoint_goal  → PoseStamped goal for Nav2


## Dependencies (must run first)

robot_base.launch.py      → provides /camera/image_raw
vision_bridge.launch.py   → provides /vision/image_preprocessed


## ROS 2 Interface

| Direction | Topic | Type | Description |
|-----------|-------|------|-------------|
| IN | `/vision/image_preprocessed` | `sensor_msgs/Image` | Camera frames |
| OUT | `/qr/detections` | `std_msgs/String` | JSON detections |
| OUT | `/qr/waypoint_goal` | `geometry_msgs/PoseStamped` | Nav goal |
| OUT | `/qr/debug_image` | `sensor_msgs/Image` | Annotated frame |
| OUT | `/qr/status` | `std_msgs/String` | JSON health |

## QR detection output format

```json
[{
  "content": {"text": "ZONE_A"},
  "raw": "ZONE_A",
  "center_x": 320,
  "center_y": 240,
  "width_px": 85,
  "height_px": 85,
  "distance_m": 0.98,
  "timestamp": 1234567890.123
}]
```

## Define your waypoints (`config/qr_params.yaml`)

```yaml
# Map QR content → (x, y, yaw) waypoint
# Add as many as needed — no code changes required
waypoints:
  ZONE_A:     [2.0,  1.0,  0.0]
  ZONE_B:     [2.0, -1.0,  0.0]
  HOME:       [0.0,  0.0,  0.0]
  PICKUP_01:  [3.0,  0.0,  0.0]
```

## Reuse in another project

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

qr_nav = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        FindPackageShare('qr_navigator'),
        '/launch/qr_navigator.launch.py'
    ])
)
```