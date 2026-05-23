# Module : `fleet_manager`

**kit/** — Reusable multi-robot fleet orchestration for any ROS 2 project.

## What this module does

Manages a fleet of N autonomous robots:
- Maintains a **priority mission queue**
- **Assigns missions** to available robots automatically
- **Monitors robot status** via heartbeat
- **Requeues failed missions** automatically

/fleet/add_mission  →  [FleetOrchestrator]  →  /fleet/assign
│
tracks robots
│
/fleet/status  →  dashboard / collision_manager


## ROS 2 Interface

| Direction | Topic | Type | Description |
|-----------|-------|------|-------------|
| IN | `/fleet/add_mission` | `std_msgs/String` | Add mission (JSON) |
| IN | `/fleet/robot_status` | `std_msgs/String` | Robot heartbeat |
| OUT | `/fleet/status` | `std_msgs/String` | Fleet JSON status |
| OUT | `/fleet/assign` | `std_msgs/String` | Mission assignment |

## Mission format

```json
{
  "mission_id": "M001",
  "target_x":   3.0,
  "target_y":   2.0,
  "target_yaw": 0.0,
  "priority":   1
}
```

Priority: `1` = high, `2` = medium, `3` = low.
`mission_id` is optional — auto-generated if omitted.

## Add a mission via command line

```bash
ros2 topic pub /fleet/add_mission std_msgs/msg/String \
  '{"data": "{\"target_x\": 3.0, \"target_y\": 2.0, \"priority\": 1}"}' \
  --once
```

## Fleet status output

```json
{
  "robots": {
    "amr_001": {
      "state": "navigating",
      "current_mission": "M001",
      "position_x": 1.2,
      "position_y": 0.8,
      "missions_done": 3,
      "missions_failed": 0
    },
    "amr_002": {
      "state": "idle",
      "current_mission": null,
      "missions_done": 2,
      "missions_failed": 1
    }
  },
  "queue": {
    "pending": 1,
    "completed": 5,
    "total": 6
  }
}
```

## Robot states

| State | Meaning |
|-------|---------|
| `idle` | Available for new missions |
| `navigating` | Executing a mission |
| `failed` | Last mission failed |
| `offline` | No heartbeat for >5s |

## Configure fleet (`config/fleet_params.yaml`)

```yaml
fleet_orchestrator:
  ros__parameters:
    # Add/remove robots here — no code changes needed
    robot_names:
      - "amr_001"
      - "amr_002"
      - "amr_003"   # add a third robot
    heartbeat_timeout: 5.0
```

## Standalone usage

```bash
cd ~/robotics/robotics-toolkit/projects/amr_ros2
colcon build --packages-select fleet_manager --symlink-install
source install/setup.bash
ros2 launch fleet_manager fleet_manager.launch.py
```

## Reuse in another project

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

fleet = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        FindPackageShare('fleet_manager'),
        '/launch/fleet_manager.launch.py'
    ])
)
```