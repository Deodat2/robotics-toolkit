# Module : `sensor_interface` 👁️‍🗨️

**kit/** — Reusable sensor abstraction layer for any ROS 2 robot.

## What this module does

Acts as a **bridge between raw hardware data and the rest of the system**.
Filters invalid sensor readings and normalizes data formats so that
SLAM, Nav2, and vision modules always receive clean, reliable data.

/scan  (raw LiDAR)  →  [lidar_filter]  →  /sensors/lidar/filtered
/odom  (raw odom)   →  [odom_filter]   →  /sensors/odom/filtered
↓
/sensors/diagnostics  (health status)


## Why this module exists

Real sensors produce invalid data:
- **NaN** — sensor error, beam returned no value
- **Inf** — beam hit nothing (open space beyond range)
- **0.0** — below minimum range (too close)
- **Spikes** — single erroneous readings

Feeding raw data to SLAM or Nav2 causes bad maps and navigation failures.
This module ensures all downstream modules receive valid data only.

## ROS 2 Interface

| Direction | Topic | Type | Description |
|-----------|-------|------|-------------|
| IN | `/scan` | `sensor_msgs/LaserScan` | Raw LiDAR data |
| IN | `/odom` | `nav_msgs/Odometry` | Raw wheel odometry |
| OUT | `/sensors/lidar/filtered` | `sensor_msgs/LaserScan` | Clean LiDAR |
| OUT | `/sensors/odom/filtered` | `nav_msgs/Odometry` | Validated odom |
| OUT | `/sensors/diagnostics` | `diagnostic_msgs/DiagnosticArray` | Health |

## Filtering rules

| Input value | Reason | Replacement |
|-------------|--------|-------------|
| `NaN` | Sensor error | `max_range` |
| `Inf` | No return | `max_range` |
| `< min_range` | Too close | `max_range` |
| `> max_range` | Too far | `max_range` |
| Valid | — | Unchanged |

## Configurable parameters (`config/sensor_params.yaml`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `input_topic` | `/scan` | Raw LiDAR topic |
| `output_topic` | `/sensors/lidar/filtered` | Clean output topic |
| `min_range` | `0.12` m | Minimum valid range |
| `max_range` | `10.0` m | Maximum valid range |

## Monitor sensor health

```bash
ros2 topic echo /sensors/diagnostics
```

## Standalone usage

```bash
# Terminal 1 — robot base (provides /scan and /odom)
ros2 launch robot_base robot_base.launch.py

# Terminal 2 — sensor interface
cd ~/robotics/robotics-toolkit/projects/amr_ros2
colcon build --packages-select sensor_interface --symlink-install
source install/setup.bash
ros2 launch sensor_interface sensor_interface.launch.py
```

## Run unit tests

```bash
colcon test --packages-select sensor_interface
colcon test-result --verbose
```

## Reuse in another project

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

sensors = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        FindPackageShare('sensor_interface'),
        '/launch/sensor_interface.launch.py'
    ]),
    launch_arguments={
        'use_sim_time': 'true',
    }.items()
)
```