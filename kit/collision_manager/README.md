# Module : `collision_manager` 🛡️

**kit/** — Reusable inter-robot collision prevention for any ROS 2 fleet.

## What this module does

Monitors distances between all robots in the fleet.
Issues alerts and emergency stops when robots get too close.

/fleet/status (robot positions)
↓
[CollisionMonitor] — computes pairwise distances
↓
GREEN  > 1.5m  : normal operation
YELLOW < 1.5m  : /fleet/collision_alert (slow down)
RED    < 0.8m  : /fleet/emergency_stop  (stop both robots)


## ROS 2 Interface

| Direction | Topic | Type | Description |
|-----------|-------|------|-------------|
| IN | `/fleet/status` | `std_msgs/String` | Robot positions |
| OUT | `/fleet/collision_alert` | `std_msgs/String` | Warning alert |
| OUT | `/fleet/emergency_stop` | `std_msgs/String` | Stop command |
| OUT | `/fleet/collision_status` | `std_msgs/String` | Monitor stats |

## Alert format

```json
{
  "robot_a":    "amr_001",
  "robot_b":    "amr_002",
  "distance_m": 1.23,
  "risk_level": "warning",
  "timestamp":  1234567890.0
}
```

## Emergency stop format

```json
{
  "robots":   ["amr_001", "amr_002"],
  "reason":   "collision_risk",
  "distance": 0.72
}
```

## Safety zones

| Zone | Distance | Action |
|------|----------|--------|
| 🟢 Safe | > 1.5m | Normal operation |
| 🟡 Warning | < 1.5m | Alert published |
| 🔴 Critical | < 0.8m | Emergency stop |

## Configure distances (`config/collision_params.yaml`)

```yaml
collision_monitor:
  ros__parameters:
    # Rule of thumb: warning = 3x robot radius
    #                critical = 1.5x robot radius
    warning_distance:  1.5   # meters
    critical_distance: 0.8   # meters
    check_rate: 5.0           # Hz
```

## Monitor collision status

```bash
ros2 topic echo /fleet/collision_status
```

```json
{
  "robots_tracked": 2,
  "active_alerts": 1,
  "total_warnings": 3,
  "total_criticals": 0,
  "alert_pairs": [{
    "pair": "amr_001↔amr_002",
    "distance": 1.34,
    "risk": "warning"
  }]
}
```

## Standalone usage

```bash
# Requires fleet_manager running first (provides /fleet/status)
ros2 launch fleet_manager fleet_manager.launch.py
ros2 launch collision_manager collision_manager.launch.py
```

## Reuse in another project

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

collision = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        FindPackageShare('collision_manager'),
        '/launch/collision_manager.launch.py'
    ])
)
```